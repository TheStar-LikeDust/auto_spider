"""
Core action registry and executor.

Global registry for loaded actions.
"""

from typing import Dict, Callable, List, Any, Optional
from auto_spider.actions import Context, execute_pipeline

# global action registry
_ACTION_REGISTRY: Dict[str, Callable] = {}


def register_action(name: str, action: Callable, priority: int = 500):
    """
    Register action to global registry.
    
    Args:
        name: Action name
        action: Action function
        priority: Action priority
    """
    action.priority = priority
    _ACTION_REGISTRY[name] = action


def active(priority: int = 500):
    """
    Decorator to activate and auto-register action.
    
    Args:
        priority: Action priority for display/management (default 500)
                 Does NOT affect execution order - plan list order is used
        
    Returns:
        Decorator function
        
    Example:
        @active()
        def my_action(context): pass
        
        @active(priority=100)
        def high_priority_action(context): pass
    """
    def decorator(func: Callable) -> Callable:
        func.active = True
        func.name = func.__name__
        func.priority = priority
        register_action(func.__name__, func, priority)
        return func
    return decorator


def set_active(func: Callable, priority: int = 500):
    """
    Manually activate and register action.
    
    Args:
        func: Action function
        priority: Action priority
    """
    func.active = True
    func.priority = priority
    register_action(func.__name__, func, priority)


def get_action(name: str) -> Callable:
    """
    Get action from registry.
    
    Args:
        name: Action name
        
    Returns:
        Action function
    """
    if name not in _ACTION_REGISTRY:
        raise KeyError(f"Action not found: {name}")
    return _ACTION_REGISTRY[name]


def get_all_actions() -> Dict[str, Callable]:
    """Get all registered actions."""
    return _ACTION_REGISTRY.copy()


def clear_actions():
    """Clear all registered actions."""
    _ACTION_REGISTRY.clear()


def execute_plan(action_names: List[str], context: Context = None, **kwargs) -> Any:
    """
    Execute plan (list of action names) in order.
    
    Args:
        action_names: List of action names (execution order)
        context: Context object
        **kwargs: Context initialization args
        
    Returns:
        Final result
        
    Note:
        Actions executed in plan list order, not by priority.
    """
    if not action_names:
        raise ValueError("Plan is empty")
    
    # get actions from registry in plan order
    actions = [get_action(name) for name in action_names]
    
    # execute in order
    result = execute_pipeline(actions, context=context, **kwargs)
    return result
