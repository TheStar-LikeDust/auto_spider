"""
Stage manager for different execution stages.

Prepare stage (storage + tasks), build context, save results.
"""

import functools
import queue as thread_queue
from multiprocessing import Process, Queue, JoinableQueue, Barrier as ProcessBarrier
from threading import Thread, Barrier as ThreadBarrier
from typing import Callable, List, Tuple
from ..storage._file_storage_backend import (load_action_result, load_parse_result, load_failed_tasks)
from ..step import Context, Result, execute_steps
from .step_registry import get_stage_steps
from .operations import initialize_spider, initialize_resources
from ..tools.logger import build_logger

_LOGGER = build_logger('stage')


# ── resource preparation ──

def prepare_action_resources(worker_id: int, spider_factory: Callable, initial_factory: Callable, plan_config) -> Tuple:
    """
    Prepare resources for action stage worker.
    
    Returns:
        (spider, initial, step_funcs)
    """
    if not spider_factory:
        raise ValueError("spider_factory is required for action stage")
    if not initial_factory:
        raise ValueError("initial_factory is required")
    
    spider = initialize_spider(spider_factory)
    initial = initialize_resources(initial_factory)
    
    step_names = getattr(plan_config, '_action_steps', None) or None
    step_funcs = get_stage_steps('action', step_names)
    
    _LOGGER.debug(f"[Worker-{worker_id}] Action resources prepared")
    return spider, initial, step_funcs


def prepare_parse_resources(worker_id: int, spider_factory: Callable, initial_factory: Callable, plan_config) -> Tuple:
    """
    Prepare resources for parse stage worker.
    
    Returns:
        (spider, initial, step_funcs)
    """
    if not initial_factory:
        raise ValueError("initial_factory is required")
    
    spider = None
    initial = initialize_resources(initial_factory)
    
    step_names = getattr(plan_config, '_parse_steps', None) or None
    step_funcs = get_stage_steps('parse', step_names)
    
    _LOGGER.debug(f"[Worker-{worker_id}] Parse resources prepared")
    return spider, initial, step_funcs


def prepare_extract_resources(worker_id: int, spider_factory: Callable, initial_factory: Callable, plan_config) -> Tuple:
    """
    Prepare resources for extract stage worker.
    
    Returns:
        (spider, initial, step_funcs)
    """
    if not initial_factory:
        raise ValueError("initial_factory is required")
    
    spider = None
    initial = initialize_resources(initial_factory)
    
    step_names = getattr(plan_config, '_extract_steps', None) or None
    step_funcs = get_stage_steps('extract', step_names)
    
    _LOGGER.debug(f"[Worker-{worker_id}] Extract resources prepared")
    return spider, initial, step_funcs


# ── task execution ──

def execute_action_task(task, task_index: int, spider, initial, plan_config, step_funcs: List[Callable]) -> Result:
    """
    Action stage complete execution: build context -> execute steps -> build result.
    """
    original_task = task.get('task', task) if isinstance(task, dict) else task
    task_name = f'task{task_index}' if task_index is not None else None
    
    context = Context(spider=spider, task=original_task, initial=initial,
                      config=plan_config, task_name=task_name)
    context['input'] = task
    
    execute_steps(step_funcs, context)
    
    return Result(
        index=task_index,
        task=dict(context.task),
        stage='action',
        new_tasks=context.append_tasks if context.append_tasks else None,
        result=context.get('result', {}),
        content=context.get('content', '')
    )


def execute_parse_task(task, task_index: int, spider, initial, plan_config, step_funcs: List[Callable]) -> Result:
    """
    Parse stage complete execution: build context -> execute steps -> build result.
    """
    original_task = task.get('task', task) if isinstance(task, dict) else task
    task_name = f'task{task_index}' if task_index is not None else None
    
    context = Context(spider=spider, task=original_task, initial=initial,
                      config=plan_config, task_name=task_name)
    context['input'] = task.get('input', {})
    context['content'] = task.get('content', '')
    context['action_result'] = task.get('action_result', {})
    
    execute_steps(step_funcs, context)
    
    return Result(
        index=task_index,
        task=dict(context.task),
        stage='parse',
        new_tasks=context.append_tasks if context.append_tasks else None,
        action_result=context.get('action_result', {}),
        result=context.get('result', {}),
        content=context.get('content', '')
    )


def execute_extract_task(task, task_index: int, spider, initial, plan_config, step_funcs: List[Callable]):
    """
    Extract stage complete execution: build context -> execute steps (side effects only).
    """
    original_task = task.get('task', task) if isinstance(task, dict) else task
    task_name = f'task{task_index}' if task_index is not None else None
    
    context = Context(spider=spider, task=original_task, initial=initial,
                      config=plan_config, task_name=task_name)
    context['input'] = task.get('input', {})
    context['content'] = task.get('content', '')
    context['action_result'] = task.get('action_result', {})
    context['parse_result'] = task.get('parse_result', {})
    
    execute_steps(step_funcs, context)
    
    return None



# ── action stage preparation ──

def prepare_action_stage_class(plan_config) -> Tuple:
    """Determine worker and barrier class for action stage."""
    use_thread = getattr(plan_config, 'USE_THREAD_WORKERS', False)
    worker_class = Thread if use_thread else Process
    barrier_class = ThreadBarrier if use_thread else ProcessBarrier
    return worker_class, barrier_class


def prepare_action_stage_task_components(plan_config, initial_task: Callable = None,
                                         retry_failed: bool = False,
                                         task_params: dict = None,
                                         init_params: dict = None,
                                         tasks: list = None) -> Tuple:
    """Create output dir, queues, load and seed tasks for action stage."""
    use_thread = getattr(plan_config, 'USE_THREAD_WORKERS', False)
    if use_thread:
        task_pending_queue = thread_queue.Queue()
        task_result_queue = thread_queue.Queue()
    else:
        task_pending_queue = JoinableQueue()
        task_result_queue = Queue()

    if retry_failed:
        failed_tasks = load_failed_tasks('action')
        tasks = [item['task'] for item in failed_tasks]
        if not tasks:
            _LOGGER.info("No failed tasks found, action stage will be skipped")
        else:
            _LOGGER.info(f"Retrying {len(tasks)} failed tasks")
    elif tasks is not None:
        _LOGGER.info(f"Using {len(tasks)} tasks from --tasks argument")
    else:
        if not initial_task:
            raise ValueError("initial_task is required for action stage (unless retry_failed=True or --tasks provided)")
        tasks = initial_task(init_params) if init_params else initial_task()

    if task_params:
        tasks = [{**task, **task_params} for task in tasks]

    for task in tasks:
        task_pending_queue.put(task)
    _LOGGER.info(f"Seeded {len(tasks)} tasks for action stage")

    return task_pending_queue, task_result_queue


def prepare_action_stage_function(plan_config, spider_factory: Callable,
                                  initial_factory: Callable) -> Callable:
    """Create worker prepare function for action stage."""
    return functools.partial(
        prepare_action_resources,
        spider_factory=spider_factory,
        initial_factory=initial_factory,
        plan_config=plan_config
    )


# ── parse stage preparation ──

def prepare_parse_stage_class() -> Tuple:
    """Determine worker and barrier class for parse stage (always thread)."""
    return Thread, ThreadBarrier


def prepare_parse_stage_task_components(plan_config) -> Tuple:
    """Create output dir, queues, load and seed tasks for parse stage."""
    task_pending_queue = thread_queue.Queue()
    task_result_queue = thread_queue.Queue()

    tasks = [{
        'task': loaded['task'],
        'input': loaded['action'],
        'content': loaded['content'],
        'action_result': loaded['action'],
    } for loaded in load_action_result()]

    for task in tasks:
        task_pending_queue.put(task)
    _LOGGER.info(f"Seeded {len(tasks)} tasks for parse stage")

    return task_pending_queue, task_result_queue


def prepare_parse_stage_function(plan_config, initial_factory: Callable) -> Callable:
    """Create worker prepare function for parse stage."""
    return functools.partial(
        prepare_parse_resources,
        initial_factory=initial_factory,
        plan_config=plan_config
    )


# ── extract stage preparation ──

def prepare_extract_stage_class() -> Tuple:
    """Determine worker and barrier class for extract stage (always thread)."""
    return Thread, ThreadBarrier


def prepare_extract_stage_task_components(plan_config) -> Tuple:
    """Create output dir, queues, load and seed tasks for extract stage."""
    task_pending_queue = thread_queue.Queue()
    task_result_queue = thread_queue.Queue()

    tasks = [{
        'task': loaded['task'],
        'input': loaded['parse'],
        'content': loaded['content'],
        'action_result': loaded['action'],
        'parse_result': loaded['parse'],
    } for loaded in load_parse_result()]

    for task in tasks:
        task_pending_queue.put(task)
    _LOGGER.info(f"Seeded {len(tasks)} tasks for extract stage")

    return task_pending_queue, task_result_queue


def prepare_extract_stage_function(plan_config, initial_factory: Callable) -> Callable:
    """Create worker prepare function for extract stage."""
    return functools.partial(
        prepare_extract_resources,
        initial_factory=initial_factory,
        plan_config=plan_config
    )
