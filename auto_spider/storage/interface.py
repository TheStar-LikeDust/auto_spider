"""Storage interface - setup_storage returns a unified process_result callable."""

import functools
from typing import Callable

_backend_modules = []


def setup_storage(backends: list, plan_config) -> Callable:
    """
    Setup all backends and return a unified process_result function.

    Args:
        backends: List of backend names, e.g. ['file'] or ['file', 'mongo']
        plan_config: PlanConfig instance passed to each backend's setup()

    Returns:
        process_result(result) callable that fans out to all backends
    """
    global _backend_modules
    _backend_modules = []

    for backend in backends:
        if backend == 'file':
            from . import _file_storage_backend
            _file_storage_backend.setup(plan_config)
            _backend_modules.append(_file_storage_backend)
        else:
            raise ValueError(f'Unknown backend: {backend}')

    return functools.partial(_dispatch_to_backends, list(_backend_modules))


def _dispatch_to_backends(backend_modules: list, result: dict):
    """Fan out result to all configured backends with error isolation."""
    for module in backend_modules:
        try:
            module.process_result(result)
        except Exception as e:
            from ..tools.logger import build_logger
            build_logger('storage').error(f"Backend '{module.__name__}' process_result failed: {e}")
