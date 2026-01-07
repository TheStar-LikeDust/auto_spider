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
from .plan_scheduler import (
    run_plan,
    DEFAULT_MAX_WORKERS,
)

from .stage import (
    get_tasks_for_stage,
    save_stage_result,
)

from .plan_scheduler import (
    start_workers,
)

from .plan_worker import (
    SHUTDOWN_SIGNAL,
    run_worker,
    dispatch_workers,
)

from .operations import (
    setup_storage,
    create_stage_storage,
    initialize_spider,
    cleanup_spider,
    initialize_resources,
    setup_worker_storage,
)

from ..storage import (
    configure,
    initial_storage,
    save_action_result,
    load_action_result,
    save_parse_result,
    load_parse_result,
)

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
    'run_worker',
    'dispatch_workers',
    
    # operations
    'setup_storage',
    'create_stage_storage',
    'initialize_spider',
    'cleanup_spider',
    'initialize_resources',
    'setup_worker_storage',
    
    # step
    'Task',
    'run_plan',
    'get_tasks_for_stage',
    'save_stage_result',
    'DEFAULT_MAX_WORKERS',
    'start_workers',
    
    # storage
    'configure',
    'initial_storage',
    'save_action_result',
    'load_action_result',
    'save_parse_result',
    'load_parse_result',
    
    # plan config
    'PlanConfig',
    'DEFAULT_CONFIG',
    'DictAttributeMixin',
]
