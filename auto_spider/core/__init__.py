"""
Core runtime module.

Provides action registry, scheduler, storage, and loader.
"""

from .registry import (
    step,
    action,
    active,
    parse,
    extract,
    register_step,
    get_step,
    get_all_steps,
    get_all_actions,
    get_all_parses,
    get_all_extracts,
)

from ..step import Task, generate_task_name, execute_steps
from .scheduler import (
    run_plan,
    run_plan_from_file,
    DEFAULT_MAX_WORKERS,
)

from .stage import (
    get_tasks_for_stage,
    save_stage_result,
)

from .worker import (
    start_workers,
)

from .storage import (
    create_output_dir,
    save_task_result,
    find_latest_output_dir,
    load_task_result,
    list_task_results,
)


__all__ = [
    # registry - decorators
    'step',
    'action',
    'active',
    'parse',
    'extract',
    
    # registry - unified API
    'register_step',
    'get_step',
    'get_all_steps',
    'get_all_actions',
    'get_all_parses',
    'get_all_extracts',
    'execute_steps',
    
    # step
    'Task',
    'run_plan',
    'run_plan_from_file',
    'get_tasks_for_stage',
    'save_stage_result',
    'DEFAULT_MAX_WORKERS',
    'start_workers',
    
    # storage
    'create_output_dir',
    'save_task_result',
    'find_latest_output_dir',
    'load_task_result',
    'list_task_results',
    
]
