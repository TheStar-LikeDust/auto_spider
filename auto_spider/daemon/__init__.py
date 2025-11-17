"""
Daemon mode for continuous task execution.

Provides a background manager that accepts plan submissions via socket.
"""

from .manager import DaemonManager
from .client import add_plan, reload, shutdown
from .config import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_MAX_WORKERS

__all__ = [
    'DaemonManager',
    'add_plan',
    'reload',
    'shutdown',
    'DEFAULT_HOST',
    'DEFAULT_PORT',
    'DEFAULT_MAX_WORKERS',
]
