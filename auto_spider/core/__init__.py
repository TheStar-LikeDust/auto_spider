"""
Core runtime module.

Provides action registry, scheduler, storage, and loader.
"""

from .registry import (
    active,
    action,
    parse,
    extract,
    set_active,
    register_action,
    register_parse,
    register_extract,
    get_action,
    get_parse,
    get_extract,
    get_all_actions,
    get_all_parses,
    get_all_extracts,
    clear_actions,
    clear_parses,
    clear_extracts,
    execute_plan,
    execute_parse,
    execute_extract,
)

from ..step import Task, generate_task_name
from .scheduler import (
    run_plan,
    run_plan_from_file,
    DEFAULT_MAX_WORKERS,
)

from .storage import (
    create_output_dir,
    save_task_result,
    find_latest_output_dir,
    load_task_result,
)

from .loader import (
    load_actions_from_file,
    load_actions_from_directory,
    load_actions_from_directories,
    auto_load_actions,
)

__all__ = [
    # registry - decorators
    'active',
    'action',
    'parse',
    'extract',
    'set_active',
    
    # registry - action
    'register_action',
    'get_action',
    'get_all_actions',
    'clear_actions',
    'execute_plan',
    
    # registry - parse
    'register_parse',
    'get_parse',
    'get_all_parses',
    'clear_parses',
    'execute_parse',
    
    # registry - extract
    'register_extract',
    'get_extract',
    'get_all_extracts',
    'clear_extracts',
    'execute_extract',
    
    # scheduler
    'Task',
    'run_plan',
    'run_plan_from_file',
    'DEFAULT_MAX_WORKERS',
    
    # storage
    'create_output_dir',
    'save_task_result',
    'find_latest_output_dir',
    'load_task_result',
    
    # loader
    'load_actions_from_file',
    'load_actions_from_directory',
    'load_actions_from_directories',
    'auto_load_actions',
]
