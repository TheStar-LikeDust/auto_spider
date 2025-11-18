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
    clear_all_steps,
    reload_tracked_modules,
    get_tracked_modules,
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

from .scheduler import (
    start_workers,
)

from .worker import (
    SHUTDOWN_SIGNAL,
    RELOAD_SIGNAL,
)

from ..storage import (
    ensure_output_dir,
    ensure_plan_dir,
    create_stage_dir,
    save_task_result,
    find_latest_stage_dir,
    load_directory,
)

from .plan_config import (
    PlanConfig,
    DEFAULT_CONFIG,
    merge_config,
    load_config_from_module,
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
    
    # registry - reload
    'clear_all_steps',
    'reload_tracked_modules',
    'get_tracked_modules',
    
    # worker signals
    'SHUTDOWN_SIGNAL',
    'RELOAD_SIGNAL',
    
    # step
    'Task',
    'run_plan',
    'run_plan_from_file',
    'get_tasks_for_stage',
    'save_stage_result',
    'DEFAULT_MAX_WORKERS',
    'start_workers',
    
    # storage
    'ensure_output_dir',
    'ensure_plan_dir',
    'create_stage_dir',
    'save_task_result',
    'find_latest_stage_dir',
    'load_directory',
    
    # plan config
    'PlanConfig',
    'DEFAULT_CONFIG',
    'merge_config',
    'load_config_from_module',
]
