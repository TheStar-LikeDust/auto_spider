"""
Core runtime module.

Provides action registry, scheduler, storage, and loader.
"""

from .step_registry import (
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

from ..step import Task, Result, execute_steps
from .plan_core import (
    run_plan,
    run_plan_with_file,
    load_plan_module,
    DEFAULT_MAX_WORKERS,
)

from .stage import (
    prepare_action_stage_class, prepare_action_stage_task_components, prepare_action_stage_function,
    prepare_parse_stage_class, prepare_parse_stage_task_components, prepare_parse_stage_function,
    prepare_extract_stage_class, prepare_extract_stage_task_components, prepare_extract_stage_function,
    execute_action_task,
    execute_parse_task,
    execute_extract_task,
)

from .worker_core import (
    dispatch_workers,
)

from .worker_support import (
    SHUTDOWN_SIGNAL,
)

from .operations import (
    initialize_spider,
    cleanup_spider,
    initialize_resources,
)

from ..storage import setup_storage

from .plan_config import (
    PlanConfig,
    DEFAULT_CONFIG,
    DictAttributeMixin,
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
    
    # worker
    'SHUTDOWN_SIGNAL',
    'dispatch_workers',
    
    # operations
    'initialize_spider',
    'cleanup_spider',
    'initialize_resources',
    
    # step
    'Task',
    'Result',
    'run_plan',
    'run_plan_with_file',
    'load_plan_module',
    'DEFAULT_MAX_WORKERS',
    
    # stage
    'prepare_action_stage_class', 'prepare_action_stage_task_components', 'prepare_action_stage_function',
    'prepare_parse_stage_class', 'prepare_parse_stage_task_components', 'prepare_parse_stage_function',
    'prepare_extract_stage_class', 'prepare_extract_stage_task_components', 'prepare_extract_stage_function',
    'execute_action_task',
    'execute_parse_task',
    'execute_extract_task',
    
    # storage
    'setup_storage',
    
    # plan config
    'PlanConfig',
    'DEFAULT_CONFIG',
    'DictAttributeMixin',
]
