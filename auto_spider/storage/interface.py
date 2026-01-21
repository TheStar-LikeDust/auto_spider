"""Storage interface - routes to different backends."""

from pathlib import Path
from typing import List

# Current backend configuration
_backend_type = 'file'
_backend_module = None


def configure(config=None, backend='file', stage_dir=None, stage=None, **options):
    """
    Configure storage backend.
    
    Args:
        config: PlanConfig instance
        backend: Backend type ('file', 'redis', 'sqlite')
        stage_dir: Stage directory path (for multiprocess workers)
        stage: Stage name (for multiprocess workers)
        **options: Backend-specific options
    """
    global _backend_type, _backend_module
    
    if config is not None:
        _backend_type = getattr(config, 'STORAGE_BACKEND', 'file')
    else:
        _backend_type = backend
    
    # Import and configure backend
    if _backend_type == 'file':
        from . import _file_storage_backend
        _backend_module = _file_storage_backend
        _file_storage_backend.configure(config, stage_dir=stage_dir, stage=stage, **options)
    elif _backend_type == 'redis':
        # from . import redis_backend
        # _backend_module = redis_backend
        # redis_backend.configure(config, **options)
        raise NotImplementedError('Redis backend not implemented')
    elif _backend_type == 'sqlite':
        # from . import sqlite_backend
        # _backend_module = sqlite_backend
        # sqlite_backend.configure(config, **options)
        raise NotImplementedError('SQLite backend not implemented')
    else:
        raise ValueError(f'Unknown backend: {_backend_type}')


def initial_storage(stage: str) -> Path:
    """Initialize storage for a stage."""
    if _backend_module is None:
        configure()  # Auto-configure with defaults
    return _backend_module.initial_storage(stage)


def save_action_result(task_name: str, task: dict, action: dict, content: str):
    """Save action result."""
    if _backend_module is None:
        configure()
    _backend_module.save_action_result(task_name, task, action, content)


def load_action_result() -> List[dict]:
    """Load action results."""
    if _backend_module is None:
        configure()
    return _backend_module.load_action_result()


def save_parse_result(task_name: str, task: dict, action: dict, parse: dict, content: str):
    """Save parse result."""
    if _backend_module is None:
        configure()
    _backend_module.save_parse_result(task_name, task, action, parse, content)


def load_parse_result() -> List[dict]:
    """Load parse results."""
    if _backend_module is None:
        configure()
    return _backend_module.load_parse_result()


def save_failed_task(task_name: str, task: dict, error: str, stage: str = 'action', worker_id: int = None):
    """Save failed task information."""
    if _backend_module is None:
        configure()
    _backend_module.save_failed_task(task_name, task, error, stage, worker_id)


def load_failed_tasks(stage: str = 'action') -> List[dict]:
    """Load all failed tasks for a stage."""
    if _backend_module is None:
        configure()
    return _backend_module.load_failed_tasks(stage)
