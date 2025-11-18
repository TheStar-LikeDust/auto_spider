"""
Storage module for task results.

Provides directory management and file I/O for task results.
"""

from .manager import (
    ensure_output_dir,
    ensure_plan_dir,
    create_stage_dir,
    save_task_result,
    find_latest_stage_dir,
    load_directory,
    DEFAULT_OUTPUT_DIR,
)

__all__ = [
    'ensure_output_dir',
    'ensure_plan_dir',
    'create_stage_dir',
    'save_task_result',
    'find_latest_stage_dir',
    'load_directory',
    'DEFAULT_OUTPUT_DIR',
]
