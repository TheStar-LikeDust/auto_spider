"""
Storage module - unified interface for different backends.
"""

# Import interface functions (routes to backends)
from .interface import (
    configure,
    initial_storage,
    save_action_result,
    load_action_result,
    save_parse_result,
    load_parse_result,
    save_failed_task,
    load_failed_tasks,
)

__all__ = [
    'configure',
    'initial_storage',
    'save_action_result',
    'load_action_result',
    'save_parse_result',
    'load_parse_result',
    'save_failed_task',
    'load_failed_tasks',
]
