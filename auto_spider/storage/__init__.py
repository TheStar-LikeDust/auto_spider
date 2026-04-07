"""
Storage module - unified interface for different backends.
"""

from .interface import setup_storage
from ._file_storage_backend import (
    load_action_result,
    load_parse_result,
    load_failed_tasks,
)

__all__ = [
    'setup_storage',
    'load_action_result',
    'load_parse_result',
    'load_failed_tasks',
]
