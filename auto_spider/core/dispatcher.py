"""
Task dispatcher for worker pool.

Simple MPQueue-based task dispatcher.
"""

import time
from multiprocessing import Process, JoinableQueue, Barrier
from threading import Thread, Barrier as ThreadBarrier
from queue import Queue
from typing import List, Callable, Optional
from ..logger import build_logger
from .signals import WorkerSignal

_LOGGER = build_logger('dispatcher')


def dispatch_tasks(
    tasks: List,
    worker_func: Callable,
    worker_type: str = 'process',
    max_workers: int = 4,
    rate_limit: Optional[float] = None,
    **worker_kwargs
):
    """
    Dispatch tasks to workers using JoinableQueue.
    
    Uses barriers and task_done for synchronization:
    1. Ready barrier: all workers complete preparation
    2. Start barrier: main process countdown complete, workers start execution
    3. Queue.join(): wait for all tasks (including dynamically added) to complete
    
    Supports incremental crawling where tasks can generate new tasks.
    Rate limiting is achieved by a dedicated feeder thread that controls task feeding speed.
    
    Args:
        tasks: Task list
        worker_func: Worker function to execute each task
        worker_type: 'process' or 'thread'
        max_workers: Number of concurrent workers
        rate_limit: Delay between tasks in seconds (None = no limit, e.g., 1.0 = 1 task/sec, 0.5 = 2 tasks/sec)
        **worker_kwargs: Additional arguments passed to worker_func
    """
    if worker_type == 'process':
        worker_class = Process
        ready_barrier = Barrier(max_workers + 1)
        start_barrier = Barrier(max_workers + 1)
        task_queue = JoinableQueue()
    elif worker_type == 'thread':
        worker_class = Thread
        ready_barrier = ThreadBarrier(max_workers + 1)
        start_barrier = ThreadBarrier(max_workers + 1)
        task_queue = Queue()
    else:
        raise ValueError(f"Unknown worker_type: {worker_type}")
    
    # feeder thread for rate-limited task feeding
    feeder_thread = None
    if rate_limit:
        task_buffer = [(i, task) for i, task in enumerate(tasks)]
        
        def feed_tasks():
            """Feed tasks to queue at controlled rate"""
            for i, task_item in enumerate(task_buffer):
                task_queue.put(task_item)
                if i < len(task_buffer) - 1:
                    time.sleep(rate_limit)
            _LOGGER.debug(f"Feeder completed: {len(task_buffer)} tasks fed")
        
        feeder_thread = Thread(target=feed_tasks)
        feeder_thread.start()
        _LOGGER.info(f"Rate limiter enabled: {rate_limit}s delay between tasks")
    else:
        # no rate limit: put all tasks immediately
        for i, task in enumerate(tasks):
            task_queue.put((i, task))
    
    # start workers
    workers = [
        worker_class(target=worker_func, args=(worker_id, task_queue, ready_barrier, start_barrier), kwargs=worker_kwargs)
        for worker_id in range(max_workers)
    ]
    
    for worker in workers:
        worker.start()
    
    # wait for all workers to complete preparation
    _LOGGER.info(f"Waiting for {max_workers} workers to complete preparation...")
    ready_barrier.wait()
    
    # countdown in main process
    _LOGGER.info("All workers ready!")
    _LOGGER.info("")
    for i in range(2, 0, -1):
        _LOGGER.info(f"Starting execution in {i}...")
        time.sleep(1)
    _LOGGER.info("Workers executing!")
    
    # release start barrier, workers begin execution
    start_barrier.wait()
    
    # wait for feeder to complete (if rate limiting enabled)
    if feeder_thread:
        _LOGGER.info("Waiting for task feeder to complete...")
        feeder_thread.join()
        _LOGGER.info("All tasks have been fed to queue")
    
    # wait for all tasks to complete (including dynamically added tasks)
    _LOGGER.info("Waiting for all tasks to complete...")
    task_queue.join()
    _LOGGER.info("All tasks completed! ready to exit...")
    time.sleep(1)
    
    # send stop signal to workers
    for _ in range(max_workers):
        task_queue.put(WorkerSignal.SHUTDOWN)
    
    for worker in workers:
        worker.join()
    
    _LOGGER.debug(f"All workers exited: {max_workers} {worker_type}s")
