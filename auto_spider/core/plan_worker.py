"""
Task worker for executing steps.

Function-based worker with prepare-in-subprocess lifecycle."""

import time
from typing import Callable, List, Optional
from multiprocessing import Process, JoinableQueue, Barrier
from threading import Thread
from queue import Queue
from ..step import Context, execute_steps
from .stage import setup_context_for_stage, save_stage_result
from .registry import get_step
from .operations import initialize_spider, initialize_resources
from ..storage import save_failed_task
from ..tools.logger import build_logger

_LOGGER = build_logger('worker')

# Module-level configuration
WORKER_PREPARE_TIMEOUT = 30  # seconds to wait for workers to prepare
SHUTDOWN_SIGNAL = '__SHUTDOWN__'


def worker_task_feeder_initial(tasks: List, task_queue, rate_limit: Optional[float]) -> Optional[Thread]:
    """
    Initialize task feeder thread for rate-limited task feeding.
    
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


def worker_shutdown(task_queue, workers: List, max_workers: int):
    """
    Shutdown workers and wait for completion.
    
    Args:
        task_queue: Task queue
        workers: List of Thread or Process instances
        max_workers: Number of workers
    """
    task_queue.join()
    _LOGGER.info("All tasks completed, shutting down...")
    time.sleep(1)
    
    for _ in range(max_workers):
        task_queue.put(SHUTDOWN_SIGNAL)
    
    for worker in workers:
        worker.join()
    
    _LOGGER.debug(f"All workers exited: {max_workers} workers")


def worker_prepare_resources(stage_name: str, step_names: List[str],
                             spider_factory: Callable, initial_factory: Callable):
    """
    Initialize worker resources in subprocess/thread.
    
    Args:
        stage_name: Stage name
        step_names: Step function names
        spider_factory: Spider factory function
        initial_factory: Initial resources factory
        
    Returns:
        Tuple of (spider, initial, step_funcs)
    """
    if stage_name == 'action' and not spider_factory:
        raise ValueError("spider_factory is required for action stage")
    
    if not initial_factory:
        raise ValueError("initial_factory is required")
    
    spider = initialize_spider(spider_factory) if spider_factory else None
    initial = initialize_resources(initial_factory)
    step_funcs = [get_step(stage_name, name) for name in step_names]
    return spider, initial, step_funcs


def task_process(task: dict, task_name: str, spider, initial, step_funcs: List,
                 stage_name: str, plan_name: str, plan_config):
    """
    Process a single task.
    
    Args:
        task: Task dict
        task_name: Task name for saving
        spider: Spider instance
        initial: Initial resources
        step_funcs: Step functions
        stage_name: Stage name
        plan_name: Plan name
        plan_config: PlanConfig instance
        
    Returns:
        List of new tasks collected, or None
    """
    original_task = task.get('task', task) if isinstance(task, dict) else task
    context = Context(spider=spider, task=original_task, initial=initial, config=plan_config, task_name=task_name)
    
    setup_context_for_stage(stage_name, context, task)
    execute_steps(step_funcs, context)
    
    if plan_name and stage_name in ('action', 'parse'):
        save_stage_result(stage_name, context, plan_name, task_name)
    
    return context.tasks if context.tasks else None


def worker_run_loop(worker_id: int, task_queue, ready_barrier, start_barrier,
                    stage_name: str, step_names: List[str], spider_factory: Callable,
                    initial_factory: Callable, plan_name: str, plan_config):
    """
    Worker main loop: prepare resources then process tasks.
    
    Lifecycle:
        1. Prepare resources (spider, initial, step_funcs) in subprocess
        2. Signal ready via ready_barrier
        3. Wait for start signal via start_barrier
        4. Process tasks until shutdown
    """
    # 1. Prepare resources in subprocess/thread
    spider, initial, step_funcs = worker_prepare_resources(
        stage_name, step_names, spider_factory, initial_factory
    )
    _LOGGER.debug(f"[Worker-{worker_id}] Resources prepared")
    
    # 2. Signal ready
    _LOGGER.debug(f"[Worker-{worker_id}] Ready, waiting for other workers...")
    ready_barrier.wait()
    
    # 3. Wait for start signal
    _LOGGER.debug(f"[Worker-{worker_id}] Waiting for execution signal...")
    start_barrier.wait()
    
    # 4. Process tasks
    while True:
        item = task_queue.get()
        
        if item == SHUTDOWN_SIGNAL:
            task_queue.task_done()
            _LOGGER.debug(f"[Worker-{worker_id}] Received shutdown signal")
            break
        
        task_index, task = item
        task_name = f'task{task_index + 1}' if task_index is not None else 'task_dynamic'
        
        try:
            _LOGGER.info(f"[Worker-{worker_id}] Start task: {task_name}")
            
            new_tasks = task_process(
                task, task_name, spider, initial, step_funcs,
                stage_name, plan_name, plan_config
            )
            
            if new_tasks:
                _LOGGER.info(f"[Worker-{worker_id}] Collected {len(new_tasks)} new tasks")
                for new_task in new_tasks:
                    task_queue.put((None, new_task))
            
            _LOGGER.info(f"[Worker-{worker_id}] Task completed: {task_name}")
            
        except Exception as e:
            _LOGGER.error(f"[Worker-{worker_id}] Task failed: {task_name}, error: {e}")
            original_task = task.get('task', task) if isinstance(task, dict) else task
            if stage_name == 'action' and plan_name:
                save_failed_task(task_name, original_task, str(e), stage_name, worker_id)
        finally:
            task_queue.task_done()


def worker_start(worker_id: int, task_queue, ready_barrier, start_barrier,
                 stage_name: str, step_names: List[str], spider_factory: Callable,
                 initial_factory: Callable, plan_name: str, plan_config,
                 worker_type: str) -> Thread | Process:
    """
    Start a worker as thread or process.
    
    Returns:
        Thread or Process instance
    """
    args = (worker_id, task_queue, ready_barrier, start_barrier,
            stage_name, step_names, spider_factory, initial_factory,
            plan_name, plan_config)
    
    if worker_type == 'process':
        worker = Process(target=worker_run_loop, args=args)
    else:
        worker = Thread(target=worker_run_loop, args=args)
    
    worker.start()
    return worker


def worker_ready_block(ready_barrier, start_barrier, max_workers: int,
                       timeout: float = WORKER_PREPARE_TIMEOUT):
    """
    Block until all workers are ready, then signal start.
    
    Args:
        ready_barrier: Barrier for preparation sync
        start_barrier: Barrier for execution start sync
        max_workers: Number of workers
        timeout: Timeout in seconds
        
    Raises:
        TimeoutError: If workers don't prepare within timeout
    """
    _LOGGER.info(f"Waiting for {max_workers} workers to prepare (timeout: {timeout}s)...")
    
    try:
        ready_barrier.wait(timeout=timeout)
    except Exception as e:
        raise TimeoutError(f"Workers failed to prepare within {timeout}s: {e}")
    
    _LOGGER.info("All workers ready, starting in 3...")
    for i in range(2, 0, -1):
        time.sleep(1)
        _LOGGER.info(f"Starting in {i}...")
    time.sleep(1)
    
    start_barrier.wait()


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
    Dispatch tasks to workers.
    
    Lifecycle:
        1. Start workers (each worker prepares resources in subprocess/thread)
        2. Wait for all workers ready with timeout
        3. Feed tasks to queue
        4. Wait for completion
    
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
    # 1. Create synchronization primitives
    ready_barrier = Barrier(max_workers + 1)
    start_barrier = Barrier(max_workers + 1)
    task_queue = JoinableQueue() if worker_type == 'process' else Queue()
    
    # 2. Start workers (prepare happens in subprocess/thread)
    workers = [
        worker_start(
            worker_id=worker_id,
            task_queue=task_queue,
            ready_barrier=ready_barrier,
            start_barrier=start_barrier,
            stage_name=stage_name,
            step_names=step_names,
            spider_factory=spider_factory,
            initial_factory=initial_factory,
            plan_name=plan_name,
            plan_config=plan_config,
            worker_type=worker_type
        )
        for worker_id in range(max_workers)
    ]
    
    _LOGGER.info(f"Started {max_workers} {worker_type}s")
    
    # 3. Wait for workers to prepare with timeout
    worker_ready_block(ready_barrier, start_barrier, max_workers)
    
    # 4. Feed tasks to queue
    feeder_thread = worker_task_feeder_initial(tasks, task_queue, rate_limit)
    
    if feeder_thread:
        _LOGGER.info("Waiting for task feeder to complete...")
        feeder_thread.join()
        _LOGGER.info("All tasks have been fed to queue")
    
    # 5. Wait for completion
    worker_shutdown(task_queue, workers, max_workers)
