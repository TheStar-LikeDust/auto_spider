"""
Stage registry and executor.

Global registry for actions, parses, and extracts.
Unified execution logic for different stages.
"""

from typing import Dict, Callable, List, Any, Union
from ..actions import Context
from ..logger import build_logger

_LOGGER = build_logger('registry')

# global stage registries
_ACTION_REGISTRY: Dict[str, Callable] = {}
_PARSE_REGISTRY: Dict[str, Callable] = {}
_EXTRACT_REGISTRY: Dict[str, Callable] = {}


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
        
    Example:
        @action()
        def fetch_page(context: Context):
            return context.spider.do_url(url)
    """
    def decorator(func: Callable) -> Callable:
        register_action(func.__name__, func, priority)
        return func
    return decorator


def action(priority: int = 500):
    """
    Decorator to register action (download stage).
    
    Args:
        priority: Execution priority (higher = later)
        
    Example:
        @action()
        def fetch_page(context: Context):
            response = context.spider.do_url(url)
            context['result'] = {'html': response.text}
    """
    def decorator(func: Callable) -> Callable:
        register_action(func.__name__, func, priority)
        return func
    return decorator


def parse(priority: int = 500):
    """
    Decorator to register parse function (parse stage).
    
    Args:
        priority: Execution priority (higher = later)
        
    Example:
        @parse()
        def parse_html(context: Context):
            html = context['html']
            title = extract_title(html)
            context['result'] = {'title': title}
    """
    def decorator(func: Callable) -> Callable:
        register_parse(func.__name__, func, priority)
        return func
    return decorator


def extract(priority: int = 500):
    """
    Decorator to register extract function (extract stage).
    
    Args:
        priority: Execution priority (higher = later)
        
    Example:
        @extract()
        def save_to_db(context: Context):
            data = context['parsed_data']
            context.initial['db'].insert(data)
    """
    def decorator(func: Callable) -> Callable:
        register_extract(func.__name__, func, priority)
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
    global _ACTION_REGISTRY
    _ACTION_REGISTRY = {}


def register_parse(name: str, parse_func: Callable, priority: int = 500):
    """
    Register parse function to global registry.
    
    Args:
        name: Parse function name
        parse_func: Parse function
        priority: Priority for execution order
    """
    _PARSE_REGISTRY[name] = {'func': parse_func, 'priority': priority}


def get_parse(name: str) -> Callable:
    """Get parse function by name."""
    parse_info = _PARSE_REGISTRY.get(name)
    if not parse_info:
        raise ValueError(f"Parse function '{name}' not registered")
    return parse_info['func']


def get_all_parses() -> Dict[str, Callable]:
    """Get all registered parse functions."""
    return {name: info['func'] for name, info in _PARSE_REGISTRY.items()}


def clear_parses():
    """Clear all registered parse functions."""
    global _PARSE_REGISTRY
    _PARSE_REGISTRY = {}


def register_extract(name: str, extract_func: Callable, priority: int = 500):
    """
    Register extract function to global registry.
    
    Args:
        name: Extract function name
        extract_func: Extract function
        priority: Priority for execution order
    """
    _EXTRACT_REGISTRY[name] = {'func': extract_func, 'priority': priority}


def get_extract(name: str) -> Callable:
    """Get extract function by name."""
    extract_info = _EXTRACT_REGISTRY.get(name)
    if not extract_info:
        raise ValueError(f"Extract function '{name}' not registered")
    return extract_info['func']


def get_all_extracts() -> Dict[str, Callable]:
    """Get all registered extract functions."""
    return {name: info['func'] for name, info in _EXTRACT_REGISTRY.items()}


def clear_extracts():
    """Clear all registered extract functions."""
    global _EXTRACT_REGISTRY
    _EXTRACT_REGISTRY = {}


def _execute_actions(
    actions: Union[Callable, List[Callable]],
    context: Union[Context, Dict, None] = None,
    **kwargs
) -> Any:
    """
    Execute action functions sequentially.
    
    Args:
        actions: Single action or list of actions
        context: Context object or dict
        **kwargs: Context initialization args
        
    Returns:
        Final result
    """
    # convert to list
    if not isinstance(actions, list):
        actions = [actions]
    
    # create context
    if context is None:
        context = Context(**kwargs)
    elif isinstance(context, dict) and not isinstance(context, Context):
        context = Context(**context)
    
    # execute actions sequentially
    result = None
    for action in actions:
        result = action(context)
        context['prev_result'] = result
        context.setdefault('results', []).append(result)
    
    return result


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
        _LOGGER.warning("No actions to execute")
        return None
    
    _LOGGER.info(f"Executing action plan: {action_names}")
    
    result = None
    for i, action_name in enumerate(action_names, 1):
        _LOGGER.debug(f"Step {i}/{len(action_names)}: Executing action '{action_name}'")
        
        action_func = get_action(action_name)
        if action_func:
            try:
                result = action_func(context)
                _LOGGER.debug(f"Action '{action_name}' completed successfully")
            except Exception as e:
                _LOGGER.error(f"Action '{action_name}' failed: {e}")
                raise
        else:
            error_msg = f"Action not found: {action_name}"
            _LOGGER.error(error_msg)
            raise ValueError(error_msg)
    
    _LOGGER.info(f"Action plan completed successfully, {len(action_names)} actions executed")
    return result


def execute_parse(parse_names: List[str], context: Context = None, **kwargs) -> Any:
    """
    Execute parse plan (list of parse function names) in order.
    
    Args:
        parse_names: List of parse function names (execution order)
        context: Context object
        **kwargs: Context initialization args
        
    Returns:
        Final result
    """
    if not parse_names:
        raise ValueError("Parse plan is empty")
    
    # get parse functions from registry in plan order
    parse_funcs = [get_parse(name) for name in parse_names]
    
    # execute in order
    result = _execute_actions(parse_funcs, context=context, **kwargs)
    return result


def execute_extract(extracts: List[str], context=None):
    """
    Execute extract plan with given context.
    
    Args:
        extracts: List of extract names to execute
        context: Context object (optional)
        
    Returns:
        Result from last extract
    """
    if not extracts:
        _LOGGER.warning("No extracts to execute")
        return None
    
    _LOGGER.info(f"Executing extract plan: {extracts}")
    
    result = None
    for i, extract_name in enumerate(extracts, 1):
        _LOGGER.debug(f"Step {i}/{len(extracts)}: Executing extract '{extract_name}'")
        
        extract_func = get_extract(extract_name)
        if extract_func:
            try:
                result = extract_func(context)
                _LOGGER.debug(f"Extract '{extract_name}' completed successfully")
            except Exception as e:
                _LOGGER.error(f"Extract '{extract_name}' failed: {e}")
                raise
        else:
            error_msg = f"Extract not found: {extract_name}"
            _LOGGER.error(error_msg)
            raise ValueError(error_msg)
    
    _LOGGER.info(f"Extract plan completed successfully, {len(extracts)} extracts executed")
    return result
