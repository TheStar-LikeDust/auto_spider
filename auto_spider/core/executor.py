"""
Executor for action/parse/extract stages.

Execute registered functions in sequence.
"""

from typing import Callable, List, Any, Union, Dict
from ..step import Context
from ..logger import build_logger

_LOGGER = build_logger('executor')


def execute_functions(
    functions: Union[Callable, List[Callable]],
    context: Union[Context, Dict, None] = None,
    **kwargs
) -> Any:
    """
    Execute functions sequentially.
    
    Args:
        functions: Single function or list of functions
        context: Context object or dict
        **kwargs: Context initialization args
        
    Returns:
        Final result
    """
    # convert to list
    if not isinstance(functions, list):
        functions = [functions]
    
    # create context
    if context is None:
        context = Context(**kwargs)
    elif isinstance(context, dict) and not isinstance(context, Context):
        context = Context(**context)
    
    # execute functions sequentially
    result = None
    for func in functions:
        result = func(context)
        context['prev_result'] = result
        context.setdefault('results', []).append(result)
    
    return result


def execute_plan(action_names: List[str], context: Context = None, get_func=None, **kwargs) -> Any:
    """
    Execute plan (list of function names) in order.
    
    Args:
        action_names: List of function names (execution order)
        context: Context object
        get_func: Function to get callable by name
        **kwargs: Context initialization args
        
    Returns:
        Final result
    """
    if not action_names:
        _LOGGER.warning("No functions to execute")
        return None
    
    _LOGGER.info(f"Executing plan: {action_names}")
    
    result = None
    for i, func_name in enumerate(action_names, 1):
        _LOGGER.debug(f"Step {i}/{len(action_names)}: Executing '{func_name}'")
        
        func = get_func(func_name)
        if func:
            try:
                result = func(context)
                _LOGGER.debug(f"Function '{func_name}' completed successfully")
            except Exception as e:
                _LOGGER.error(f"Function '{func_name}' failed: {e}")
                raise
        else:
            error_msg = f"Function not found: {func_name}"
            _LOGGER.error(error_msg)
            raise ValueError(error_msg)
    
    _LOGGER.info(f"Plan completed successfully, {len(action_names)} functions executed")
    return result
