"""
Daemon mode for continuous task execution.

Provides a background manager that accepts plan submissions via socket.
"""

from .manager import DaemonManager
from .client import DaemonClient
from .protocol import DaemonCommand

__all__ = [
    'DaemonManager',
    'DaemonClient',
    'DaemonCommand',
]
