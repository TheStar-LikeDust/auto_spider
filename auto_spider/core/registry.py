"""
Stage registry and executor.

Global registry for actions, parses, and extracts.
Unified execution logic for different stages.
"""

from typing import Dict, Callable, List, Any, Union
from ..step import Context
from ..logger import build_logger

_LOGGER = build_logger('registry')

# global stage registries
_ACTION_REGISTRY: Dict[str, Callable] = {}
_PARSE_REGISTRY: Dict[str, Callable] = {}
_EXTRACT_REGISTRY: Dict[str, Callable] = {}


def register_step(stage: str, name: str, func: Callable, priority: int = 500):
    """
    Register step function to global registry.
    
    Args:
        stage: Stage type ('action', 'parse', 'extract')
        name: Step function name
        func: Step function
        priority: Step priority
    """
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
