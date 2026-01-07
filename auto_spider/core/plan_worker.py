"""
Task worker for executing steps.

Worker class with build-prepare-execute lifecycle."""

import time
from typing import Callable, List, Optional, Tuple
from multiprocessing import Process, JoinableQueue, Barrier
from threading import Thread
from queue import Queue
from ..step import Context, execute_steps
from .stage import setup_context_for_stage, save_stage_result
from .operations import initialize_spider, initialize_resources
from ..tools.logger import build_logger

_LOGGER = build_logger('worker')

SHUTDOWN_SIGNAL = '__SHUTDOWN__'


def build_task_feeder(tasks: List, task_queue, rate_limit: Optional[float]) -> Optional[Thread]:
    """
    Build task feeder thread for rate-limited task feeding.
    
    Args:
        tasks: Task list
        task_queue: Queue to put tasks
        rate_limit: Delay between tasks in seconds
        
    Returns:
        Feeder thread if rate_limit enabled, None otherwise
    """
    if rate_limit:
        task_buffer = [(i, task) for i, task in enumerate(tasks)]
        
        def feed_tasks():
            for i, task_item in enumerate(task_buffer):
                task_queue.put(task_item)
                if i < len(task_buffer) - 1:
                    time.sleep(rate_limit)
            _LOGGER.debug(f"Feeder completed: {len(task_buffer)} tasks fed")
        
        feeder_thread = Thread(target=feed_tasks)
        feeder_thread.start()
        _LOGGER.info(f"Rate limiter enabled: {rate_limit}s delay between tasks")
        return feeder_thread
    else:
        for i, task in enumerate(tasks):
            task_queue.put((i, task))
        return None


def shutdown_workers(task_queue, workers: List[TaskWorker], max_workers: int):
    """
    Shutdown workers and wait for completion.
    
    Args:
        task_queue: Task queue
        workers: Worker list
        max_workers: Number of workers
    """
    _LOGGER.info("Waiting for all tasks to complete...")
    task_queue.join()
    _LOGGER.info("All tasks completed! ready to exit...")
    time.sleep(1)
    
    for _ in range(max_workers):
        task_queue.put(SHUTDOWN_SIGNAL)
    
    for worker in workers:
        worker.join()
    
    _LOGGER.debug(f"All workers exited: {max_workers} workers")


class TaskWorker:
    """
    Worker that processes tasks with prepare-execute lifecycle.
    
    Lifecycle:
        1. __init__: create worker with parameters
        2. prepare(): initialize resources (spider, initial, step_funcs)
        3. start(): start processing tasks
        4. join(): wait for completion
    """
    
    def __init__(self, worker_id: int, task_queue, ready_barrier, start_barrier,
                 stage_name: str, step_names: List[str], spider_factory: Callable,
                 initial_factory: Callable, plan_name: str, plan_config):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.ready_barrier = ready_barrier
        self.start_barrier = start_barrier
        self.stage_name = stage_name
        self.step_names = step_names
        self.spider_factory = spider_factory
        self.initial_factory = initial_factory
        self.plan_name = plan_name
        self.plan_config = plan_config
        
        self.spider = None
        self.initial = None
        self.step_funcs = None
        self._thread = None
        self._process = None
    
    def prepare(self):
        """Initialize resources before task execution."""
        from .registry import get_step
        
        if self.stage_name == 'action' and not self.spider_factory:
            raise ValueError("spider_factory is required for action stage")
        
        if not self.initial_factory:
            raise ValueError("initial_factory is required")
        
        self.spider = initialize_spider(self.spider_factory) if self.spider_factory else None
        self.initial = initialize_resources(self.initial_factory)
        self.step_funcs = [get_step(self.stage_name, name) for name in self.step_names]
        
        _LOGGER.debug(f"[Worker-{self.worker_id}] Resources prepared")
    
    def _run(self):
        """Worker run loop."""
        _LOGGER.debug(f"[Worker-{self.worker_id}] Ready, waiting for other workers...")
        self.ready_barrier.wait()
        
        _LOGGER.debug(f"[Worker-{self.worker_id}] Waiting for execution signal...")
        self.start_barrier.wait()
        
        while True:
            item = self.task_queue.get()
            
            if item == SHUTDOWN_SIGNAL:
                self.task_queue.task_done()
                _LOGGER.debug(f"[Worker-{self.worker_id}] Received shutdown signal")
                break
            
            try:
                self._process_task(item)
            finally:
                self.task_queue.task_done()
    
    def _process_task(self, item: tuple):
        """Process single task."""
        task_index, task = item
        task_name = f'task{task_index + 1}'
        
        try:
            _LOGGER.info(f"[Worker-{self.worker_id}] Start task: {task_name}")
            
            original_task = task.get('task', task) if isinstance(task, dict) else task
            context = Context(spider=self.spider, task=original_task, initial=self.initial, config=self.plan_config)
            
            setup_context_for_stage(self.stage_name, context, task)
            execute_steps(self.step_funcs, context)
            
            if self.plan_name and self.stage_name in ('action', 'parse'):
                save_stage_result(self.stage_name, context, self.plan_name, task_name)
            
            if context.tasks:
                _LOGGER.info(f"[Worker-{self.worker_id}] Collected {len(context.tasks)} new tasks")
                for new_task in context.tasks:
                    self.task_queue.put((None, new_task))
            
            _LOGGER.info(f"[Worker-{self.worker_id}] Task completed: {task_name}")
            
        except Exception as e:
            _LOGGER.error(f"[Worker-{self.worker_id}] Task failed: {task_name}, error: {e}")
            
            if self.stage_name == 'action' and self.plan_name:
                from ..storage import save_failed_task
                save_failed_task(task_name, original_task, str(e), self.stage_name, self.worker_id)
    
    def start(self, worker_type: str):
        """Start worker as thread or process."""
        if worker_type == 'process':
            self._process = Process(target=self._run)
            self._process.start()
        else:
            self._thread = Thread(target=self._run)
            self._thread.start()
    
    def join(self):
        """Wait for worker to finish."""
        if self._thread:
            self._thread.join()
        if self._process:
            self._process.join()


def dispatch_workers(
    tasks: List,
    stage_name: str,
    step_names: List[str],
    spider_factory: Callable,
    initial_factory: Callable,
    plan_name: str,
    plan_config,
    worker_type: str = 'process',
    max_workers: int = 4,
    rate_limit: Optional[float] = None
):
    """
    Dispatch tasks to workers with build-prepare-start lifecycle.
    
    Args:
        tasks: Task list
        stage_name: Stage name
        step_names: Step names
        spider_factory: Spider factory
        initial_factory: Initial resources factory
        plan_name: Plan name
        plan_config: PlanConfig instance
        worker_type: 'process' or 'thread'
        max_workers: Number of concurrent workers
        rate_limit: Delay between tasks in seconds
    """
    from .operations import wait_workers_ready
    
    # 1. build worker thread/process
    ready_barrier = Barrier(max_workers + 1)
    start_barrier = Barrier(max_workers + 1)
    task_queue = JoinableQueue() if worker_type == 'process' else Queue()
    
    workers = [
        TaskWorker(
            worker_id=worker_id,
            task_queue=task_queue,
            ready_barrier=ready_barrier,
            start_barrier=start_barrier,
            stage_name=stage_name,
            step_names=step_names,
            spider_factory=spider_factory,
            initial_factory=initial_factory,
            plan_name=plan_name,
            plan_config=plan_config
        )
        for worker_id in range(max_workers)
    ]
    
    # 2. make every worker finish initial spider/resources, get step
    for worker in workers:
        worker.prepare()
    
    _LOGGER.info(f"All workers prepared: {max_workers} {worker_type}s")
    
    # feeder thread for rate-limited task feeding
    feeder_thread = build_task_feeder(tasks, task_queue, rate_limit)
    
    # 3. start every worker
    for worker in workers:
        worker.start(worker_type)
    
    # wait for workers ready and start
    wait_workers_ready(ready_barrier, start_barrier, max_workers)
    
    if feeder_thread:
        _LOGGER.info("Waiting for task feeder to complete...")
        feeder_thread.join()
        _LOGGER.info("All tasks have been fed to queue")
    
    # 4. block until finish
    shutdown_workers(task_queue, workers, max_workers)
