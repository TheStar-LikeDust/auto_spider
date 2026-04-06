"""Plan core: orchestrate stage execution and dispatch workers."""

from typing import Callable
from .stage import (
    prepare_action_stage_class, prepare_action_stage_task_components, prepare_action_stage_function,
    prepare_parse_stage_class, prepare_parse_stage_task_components, prepare_parse_stage_function,
    prepare_extract_stage_class, prepare_extract_stage_task_components, prepare_extract_stage_function,
    execute_action_task, execute_parse_task, execute_extract_task,
)
from .worker_core import dispatch_workers
from .plan_config import PlanConfig, load_plan_module
from ..storage import setup_storage
from ..tools.logger import build_logger

_LOGGER = build_logger('scheduler')

DEFAULT_MAX_WORKERS = 4


def run_plan(
        initial_spider: Callable,
        initial_task: Callable,
        initial_plan: Callable,
        plan_config: PlanConfig,
        action: bool = False,
        parse: bool = False,
        extract: bool = False,
        retry_failed: bool = False,
        task_params: dict = None,
        init_params: dict = None,
        tasks: list = None,
):
    """
    Run plan by executing tasks in specified stage.

    Args:
        initial_spider: Spider factory
        initial_task: Task factory
        initial_plan: Plan factory
        plan_config: PlanConfig instance
        action: Run action stage
        parse: Run parse stage
        extract: Run extract stage
        retry_failed: Retry failed tasks (action stage only)

    Example:
        run_plan(initial_spider, initial_task, initial_plan, PLAN_CONFIG,
                 action=True)
    """
    save_result = getattr(plan_config, 'SAVE_RESULT', True)
    backends = getattr(plan_config, 'BACKENDS', ['file'])
    _save_callback = setup_storage(backends, plan_config)
    process_result_callback = _save_callback if save_result else lambda result: None

    collected_result_mapper = dict()

    if action:
        worker_class, barrier_class = prepare_action_stage_class(plan_config)
        task_pending_queue, task_result_queue = prepare_action_stage_task_components(
            plan_config, initial_task, retry_failed, task_params, init_params, tasks
        )
        prepare_worker_function = prepare_action_stage_function(plan_config, initial_spider, initial_plan)
        result = dispatch_workers(
            execute_action_task, process_result_callback, prepare_worker_function,
            task_pending_queue, task_result_queue,
            worker_class, barrier_class, plan_config
        )
        collected_result_mapper['action'] = result

    if parse:
        worker_class, barrier_class = prepare_parse_stage_class()
        task_pending_queue, task_result_queue = prepare_parse_stage_task_components(
            plan_config
        )
        prepare_worker_function = prepare_parse_stage_function(plan_config, initial_plan)
        result = dispatch_workers(
            execute_parse_task, process_result_callback, prepare_worker_function,
            task_pending_queue, task_result_queue,
            worker_class, barrier_class, plan_config
        )
        collected_result_mapper['parse'] = result

    if extract:
        worker_class, barrier_class = prepare_extract_stage_class()
        task_pending_queue, task_result_queue = prepare_extract_stage_task_components(
            plan_config
        )
        prepare_worker_function = prepare_extract_stage_function(plan_config, initial_plan)
        result = dispatch_workers(
            execute_extract_task, process_result_callback, prepare_worker_function,
            task_pending_queue, task_result_queue,
            worker_class, barrier_class, plan_config
        )
        collected_result_mapper['extract'] = result

    return collected_result_mapper


def run_plan_with_file(
        plan_file: str,
        action: bool = False,
        parse: bool = False,
        extract: bool = False,
        retry_failed: bool = False,
        task_params: dict = None,
        init_params: dict = None,
        tasks: list = None,
):
    """Run plan by loading from plan file.    """
    plan_params = load_plan_module(plan_file)
    return run_plan(plan_params['initial_spider'], plan_params['initial_task'], plan_params['initial_plan'],
                   plan_params['plan_config'], action, parse, extract, retry_failed, task_params, init_params, tasks)
