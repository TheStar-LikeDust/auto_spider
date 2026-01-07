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
    
    if stage == 'action':
        func.priority = priority
        _ACTION_REGISTRY[name] = func
    elif stage == 'parse':
        _PARSE_REGISTRY[name] = {'func': func, 'priority': priority}
    elif stage == 'extract':
        _EXTRACT_REGISTRY[name] = {'func': func, 'priority': priority}
    else:
        raise ValueError(f"Unknown stage: {stage}")


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


def action(priority: int = 500):
    """Decorator to register action step."""
    return step('action', priority)


def active(priority: int = 500):
    """Alias for action (backward compatibility)."""
    return action(priority)


def parse(priority: int = 500):
    """Decorator to register parse step."""
    return step('parse', priority)


def extract(priority: int = 500):
    """Decorator to register extract step."""
    return step('extract', priority)


def get_step(stage: str, name: str) -> Callable:
    """
    Get step function from registry.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        name: Step function name
        
    Returns:
        Step function
    """
    if stage == 'action':
        if name not in _ACTION_REGISTRY:
            raise KeyError(f"Action not found: {name}")
        return _ACTION_REGISTRY[name]
    elif stage == 'parse':
        parse_info = _PARSE_REGISTRY.get(name)
        if not parse_info:
            raise ValueError(f"Parse function '{name}' not registered")
        return parse_info['func']
    elif stage == 'extract':
        extract_info = _EXTRACT_REGISTRY.get(name)
        if not extract_info:
            raise ValueError(f"Extract function '{name}' not registered")
        return extract_info['func']
    else:
        raise ValueError(f"Unknown stage: {stage}")


def get_all_steps(stage: str) -> Dict[str, Callable]:
    """
    Get all registered step functions for a stage.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        
    Returns:
        Dict mapping step names to functions
    """
    if stage == 'action':
        return _ACTION_REGISTRY.copy()
    elif stage == 'parse':
        return {name: info['func'] for name, info in _PARSE_REGISTRY.items()}
    elif stage == 'extract':
        return {name: info['func'] for name, info in _EXTRACT_REGISTRY.items()}
    else:
        raise ValueError(f"Unknown stage: {stage}")


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
