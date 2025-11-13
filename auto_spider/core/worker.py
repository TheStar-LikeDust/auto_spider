"""
Task worker for executing steps.

Single worker execution logic for all stages.
    
"""

from pathlib import Path
from typing import Callable, List
from ..step import Context, generate_task_name, execute_steps
from .registry import get_step
from .stage import save_stage_result, setup_context_for_stage
from .dispatcher import dispatch_tasks
from ..logger import build_logger

_LOGGER = build_logger('worker')


def start_workers(
    tasks: List,
    steps: List[str],
    spider_factory: Callable,
    initial_factory: Callable,
    output_folder: Path,
    stage: str,
    max_workers: int
):
    """
    Start workers for any stage.
    
    Uses Process for action stage, Thread for parse/extract stages.
    Workers fetch tasks from Queue until empty.
    
    Args:
        tasks: List of tasks
        steps: List of step function names
        spider_factory: Spider factory function (None for parse/extract)
        initial_factory: Plan factory function
        output_folder: Output directory path
        stage: Stage name ('action', 'parse', 'extract')
        max_workers: Number of concurrent workers
    """
    worker_type = 'process' if stage == 'action' else 'thread'
    
    dispatch_tasks(
        tasks=tasks,
        worker_func=run_worker,
        worker_type=worker_type,
        max_workers=max_workers,
        steps=steps,
        spider_factory=spider_factory,
        initial_factory=initial_factory,
        output_folder=output_folder,
        stage=stage
    )


def run_worker(worker_id, task_queue, ready_barrier, start_barrier, steps, spider_factory, initial_factory, output_folder, stage):
    """
    Worker function that fetches tasks from queue until receives None signal.
    
    Args:
        worker_id: Worker ID
        task_queue: JoinableQueue containing tasks
        ready_barrier: Barrier for preparation sync
        start_barrier: Barrier for execution start sync
        steps: List of step function names
        spider_factory: Spider factory function (None for parse/extract)
        initial_factory: Plan factory function
        output_folder: Output directory path
        stage: Stage name ('action', 'parse', 'extract')
    """
    # preparation phase: initialize spider and resources
    spider = None
    if spider_factory:
        spider = spider_factory()
        spider.attach()
        _LOGGER.debug(f"[Worker-{worker_id}] Spider initialized: {type(spider).__name__}")
    
    initial = initial_factory()
    if not isinstance(initial, dict):
        initial = {'resources': initial}
    
    step_funcs = [get_step(stage, name) for name in steps]
    
    _LOGGER.debug(f"[Worker-{worker_id}] Preparation completed, waiting for other workers...")
    
    # wait for all workers to complete preparation
    ready_barrier.wait()
    
    # wait for main process countdown to complete
    _LOGGER.debug(f"[Worker-{worker_id}] Waiting for execution signal...")
    start_barrier.wait()
    
    # process tasks from queue until receives None
    while True:
        # get task from queue (blocking)
        item = task_queue.get()
        
        # None is stop signal
        if item is None:
            task_queue.task_done()
            _LOGGER.debug(f"[Worker-{worker_id}] Received stop signal")
            break
        
        task_index, task = item
        # use simple task naming: task1, task2, task3...
        task_name = f'task{task_index + 1}'
        
        try:
            _LOGGER.info(f"[Worker-{worker_id}] Start task: {task_name}")
            
            # create context with original task
            # context.task is always the original Task in all stages
            original_task = task.get('task', task) if isinstance(task, dict) else task
            context = Context(spider=spider, task=original_task, initial=initial)
            
            # setup context keys based on stage (unified logic in stage.py)
            setup_context_for_stage(stage, context, task)
            
            # execute steps
            execute_steps(step_funcs, context)
            
            # save result (only for action and parse stages)
            if output_folder:
                save_stage_result(stage, context, output_folder, task_name)
            
            # add collected tasks to queue
            if context.tasks:
                _LOGGER.info(f"[Worker-{worker_id}] Collected {len(context.tasks)} new tasks")
                for new_task in context.tasks:
                    task_queue.put((None, new_task))
            
            # log completion
            _LOGGER.info(f"[Worker-{worker_id}] Task completed: {task_name}")
            
        except Exception as e:
            _LOGGER.error(f"[Worker-{worker_id}] Task failed: {task_name}, error: {e}")
        finally:
            # mark task as done
            task_queue.task_done()
    
    # cleanup spider once per worker
    if spider:
        spider.detach()
        _LOGGER.debug(f"[Worker-{worker_id}] Spider cleaned up")
