"""
Signal definitions for worker control.

Defines special signals for worker lifecycle management.
"""


class WorkerSignal:
    """Worker control signals"""
    
    # shutdown signal for workers
    SHUTDOWN = '__SHUTDOWN__'
    
    # reload signal for hot module reload
    RELOAD = '__RELOAD__'


def is_shutdown_signal(item) -> bool:
    """Check if item is shutdown signal"""
    return item == WorkerSignal.SHUTDOWN


def is_reload_signal(item) -> bool:
    """Check if item is reload signal"""
    return item == WorkerSignal.RELOAD


def is_control_signal(item) -> bool:
    """Check if item is any control signal"""
    return is_shutdown_signal(item) or is_reload_signal(item)
