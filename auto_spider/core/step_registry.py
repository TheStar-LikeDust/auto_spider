"""
Stage registry and executor.

Global registry for actions, parses, and extracts.
Unified execution logic for different stages.
"""

import sys
import importlib
from typing import Dict, Callable, List, Any, Union, Set
from ..step import Context
from ..tools.logger import build_logger

_LOGGER = build_logger('registry')

# global stage registries
_ACTION_REGISTRY: Dict[str, Callable] = {}
_PARSE_REGISTRY: Dict[str, Callable] = {}
_EXTRACT_REGISTRY: Dict[str, Callable] = {}

# module tracking for hot reload
_TRACKED_MODULES: Set[str] = set()


# ----------
# decorators

def action(priority: int = 500):
    """Decorator to register action step."""
    return step('action', priority)


def parse(priority: int = 500):
    """Decorator to register parse step."""
    return step('parse', priority)


def extract(priority: int = 500):
    """Decorator to register extract step."""
    return step('extract', priority)


def active(priority: int = 500):
    """Alias for action (backward compatibility)."""
    return action(priority)


# ----------
# functions

def _get_registry(stage: str) -> Dict[str, Callable]:
    """Get registry dict for a stage."""
    if stage == 'action':
        return _ACTION_REGISTRY
    elif stage == 'parse':
        return _PARSE_REGISTRY
    elif stage == 'extract':
        return _EXTRACT_REGISTRY
    raise ValueError(f"Unknown stage: {stage}")


def register_step(stage: str, name: str, func: Callable, priority: int = 500):
    """
    Register step function to global registry.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        name: Step function name
        func: Step function
        priority: Step priority
    """
    # track module for hot reload
    if hasattr(func, '__module__'):
        _TRACKED_MODULES.add(func.__module__)

    func.priority = priority
    _get_registry(stage)[name] = func


def step(stage: str = 'action', priority: int = 500):
    """
    Unified decorator to register step function.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        priority: Execution priority for display (default 500)
        
    Example:
        @step('action')
        def fetch_page(context: Context):
            return context.spider.do_url(url)
            
        @step('parse')
        def parse_html(context: Context):
            return extract_title(context['result'])
    """

    def decorator(func: Callable) -> Callable:
        register_step(stage, func.__name__, func, priority)
        return func

    return decorator


def get_step(stage: str, name: str) -> Callable:
    """
    Get step function from registry.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        name: Step function name
        
    Returns:
        Step function
    """
    registry = _get_registry(stage)
    if name not in registry:
        raise KeyError(f"Step not found: {stage}/{name}")
    return registry[name]


def get_all_steps(stage: str) -> Dict[str, Callable]:
    """
    Get all registered step functions for a stage.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        
    Returns:
        Dict mapping step names to functions
    """
    return _get_registry(stage).copy()


def get_stage_steps(stage: str, step_names: List[str] = None) -> List[Callable]:
    """
    Get step functions for a stage.
    
    If step_names is provided, return steps in that order.
    Otherwise, return all registered steps sorted by priority (ascending).
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        step_names: Optional list of step names to get in order
        
    Returns:
        List of step functions
    """
    if step_names:
        return [get_step(stage, name) for name in step_names]

    registry = _get_registry(stage)
    items = sorted(registry.values(), key=lambda f: getattr(f, 'priority', 500))
    return items


def get_stage_step_names(stage: str, step_names: List[str] = None) -> List[str]:
    """
    Get step function names for a stage.
    
    If step_names is provided, return as-is.
    Otherwise, return all registered step names sorted by priority (ascending).
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        step_names: Optional list of step names
        
    Returns:
        List of step function names
    """
    if step_names:
        return step_names

    registry = _get_registry(stage)
    items = sorted(registry.items(), key=lambda x: getattr(x[1], 'priority', 500))
    return [name for name, _ in items]


def get_all_actions() -> Dict[str, Callable]:
    """Get all registered actions (backward compatibility)."""
    return get_all_steps('action')


def get_all_parses() -> Dict[str, Callable]:
    """Get all registered parse functions (backward compatibility)."""
    return get_all_steps('parse')


def get_all_extracts() -> Dict[str, Callable]:
    """Get all registered extract functions (backward compatibility)."""
    return get_all_steps('extract')


def clear_all_steps():
    """
    Clear all registered steps.
    
    Used for hot reload to clear old registrations.
    """
    global _ACTION_REGISTRY, _PARSE_REGISTRY, _EXTRACT_REGISTRY
    _ACTION_REGISTRY.clear()
    _PARSE_REGISTRY.clear()
    _EXTRACT_REGISTRY.clear()
    _LOGGER.debug("All step registries cleared")


def reload_tracked_modules():
    """
    Reload all tracked modules that contain registered steps.
    
    This will trigger re-registration of all steps via decorators.
    Steps must be re-imported after this call.
    
    Returns:
        List of reloaded module names
    """
    reloaded = []

    for module_name in _TRACKED_MODULES:
        if module_name in sys.modules:
            try:
                module = sys.modules[module_name]
                importlib.reload(module)
                reloaded.append(module_name)
                _LOGGER.info(f"Reloaded module: {module_name}")
            except Exception as e:
                _LOGGER.error(f"Failed to reload module {module_name}: {e}")

    return reloaded


def get_tracked_modules() -> Set[str]:
    """
    Get all tracked module names.
    
    Returns:
        Set of module names that have registered steps
    """
    return _TRACKED_MODULES.copy()
