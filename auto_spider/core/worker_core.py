"""
Worker core: task processing, worker lifecycle, and dispatch orchestration.

Architecture:
    initial tasks -> task_pending_queue (JoinableQueue) <- incremental tasks from workers
                          |
                    N workers (rate limit via shared Lock, _index via shared Value)
                          |
                    task_result_queue -> collector thread -> storage
"""
import time
import queue as thread_queue
from typing import Callable, List
from multiprocessing import Process, Queue, JoinableQueue, Barrier as ProcessBarrier, Lock as ProcessLock, Value
from ..step import Result
from threading import Thread, Barrier as ThreadBarrier
from .worker_support import (
    SHUTDOWN_SIGNAL,
    launch_collector,
)
from .plan_config import PlanConfig
from ..tools.logger import build_logger

_LOGGER = build_logger('worker')


# ── task processing ──

def _process_task(task, spider, initial, step_funcs: List,
                  execute_task_function: Callable, plan_config: PlanConfig) -> Result:
    """Execute all steps for one task and return a serializable Result."""
    task_index = task.get('_index')
    result = execute_task_function(task, task_index, spider, initial, plan_config, step_funcs)
    return result


def _process_result(worker_id: int, result: Result, task_pending_process_queue,
                    task_result_process_queue):
    """Dispatch new tasks (before task_done), send result to collector, mark done."""
    new_tasks = result.get('new_tasks') or []
    for new_task in new_tasks:
        task_pending_process_queue.put(new_task)
    task_result_process_queue.put(result)
    task_pending_process_queue.task_done()
    _LOGGER.info(f"[Worker-{worker_id}] Task completed: task{result.index}")


def _process_failed_result(worker_id: int, task, task_index: int,
                           error: Exception, stage: str,
                           task_pending_process_queue, task_result_process_queue):
    """Build error Result, send to collector, mark done."""
    original_task = task.get('task', task) if isinstance(task, dict) else task
    task_result_process_queue.put(Result(
        index=task_index,
        task=original_task,
        stage=stage,
        error=str(error),
    ))
    task_pending_process_queue.task_done()
    _LOGGER.error(f"[Worker-{worker_id}] Task failed: task{task_index}, error: {error}")


# ── worker lifecycle ──

def _worker_loop(worker_id: int, task_pending_process_queue, task_result_process_queue,
                 worker_barrier, plan_config: PlanConfig,
                 prepare_worker_function: Callable, execute_task_function: Callable,
                 rate_lock, task_counter, counter_lock):
    """Worker main loop: prepare -> start -> process until shutdown."""
    rate_limit = float(getattr(plan_config, 'RATE_LIMIT', 0) or 0)

    spider, initial, step_funcs = prepare_worker_function(worker_id)
    worker_barrier.wait(timeout=30)

    while True:
        item = task_pending_process_queue.get()

        if item == SHUTDOWN_SIGNAL:
            if spider:
                spider.detach()
            break

        task = item

        if rate_lock is not None:
            with rate_lock:
                time.sleep(rate_limit)

        with counter_lock:
            task_counter.value += 1
            task['_index'] = task_counter.value

        task_index = task['_index']

        stage = execute_task_function.__name__.split('_')[1]

        try:
            result = _process_task(
                task, spider, initial, step_funcs,
                execute_task_function, plan_config
            )
            _process_result(worker_id, result, task_pending_process_queue,
                            task_result_process_queue)

        except Exception as e:
            _process_failed_result(worker_id, task, task_index, e, stage,
                                   task_pending_process_queue, task_result_process_queue)


# ── worker management ──

def start_workers(max_workers: int, worker_class, worker_barrier,
                  task_pending_process_queue, task_result_process_queue,
                  plan_config: PlanConfig, prepare_worker_function: Callable, execute_task_function: Callable,
                  rate_lock, task_counter, counter_lock):
    """Start worker threads/processes."""
    workers = []
    for worker_id in range(max_workers):
        w = worker_class(target=_worker_loop, args=(
            worker_id, task_pending_process_queue, task_result_process_queue,
            worker_barrier, plan_config,
            prepare_worker_function, execute_task_function,
            rate_lock, task_counter, counter_lock
        ))
        w.start()
        workers.append(w)
    _LOGGER.info(f"Started {max_workers} {'thread' if worker_class.__name__ == 'Thread' else 'process'} workers")
    return workers


# ── worker orchestration ──

def dispatch_workers(
        execute_task_function: Callable,
        process_result_callback: Callable,
        prepare_worker_function: Callable,
        task_pending_queue,
        task_result_queue,
        worker_class,
        barrier_class,
        plan_config: PlanConfig,
):
    """
    Start workers and collector, block until all tasks done, then shut down.

    Exit: task_pending_queue.join() (JoinableQueue) - unblocks when every
    task_done() has been called, including for incremental tasks.
    """
    # 0. config and shared state
    max_workers = plan_config.MAX_WORKERS
    rate_limit = float(getattr(plan_config, 'RATE_LIMIT', 0) or 0)
    collected = []
    worker_barrier = barrier_class(max_workers + 1)
    rate_lock = ProcessLock() if rate_limit else None
    task_counter = Value('i', 0)
    counter_lock = ProcessLock()

    # 1. start workers (init runs in parallel with steps 2-3)
    workers = start_workers(
        max_workers, worker_class, worker_barrier,
        task_pending_queue, task_result_queue,
        plan_config, prepare_worker_function, execute_task_function,
        rate_lock, task_counter, counter_lock
    )

    # 2. start collector
    collector = launch_collector(task_result_queue, process_result_callback, collected)

    # 3. countdown, then release workers
    [_LOGGER.info(f"Starting in {i}...") or time.sleep(1) for i in range(plan_config.START_DELAY, 0, -1)]
    worker_barrier.wait(timeout=30)

    # 4. wait for all tasks (including incremental) to complete
    task_pending_queue.join()

    # 5. stop collector (all results are in queue before join() returned)
    task_result_queue.put(SHUTDOWN_SIGNAL)
    collector.join()

    # 6. shut down workers
    _LOGGER.info(f"Sending SHUTDOWN_SIGNAL to {max_workers} workers...")
    for _ in range(max_workers):
        task_pending_queue.put(SHUTDOWN_SIGNAL)
    for w in workers:
        w.join()

    return collected
