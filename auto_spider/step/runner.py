"""
Step runner for different stages.

Execute step functions based on stage type.
"""

from typing import List, Callable
from .types import Context
from ..tools.logger import build_logger

_LOGGER = build_logger('runner')


def execute_steps(step_funcs: List[Callable], context: Context):
    """
    Execute step functions in order.
    
    Each step result is saved to context and can be accessed by:
    - context.get_step_result('step_name')  # by name
    - context.get_step_result(-1)  # last step result
    - context.get_step_result(0)   # first step result
    
    Args:
        step_funcs: List of step functions to execute
        context: Context object
    """
    if not step_funcs:
        _LOGGER.warning("No steps to execute")
        return
    
    _LOGGER.info(f"Executing {len(step_funcs)} steps")
    
    for i, step_func in enumerate(step_funcs, 1):
        func_name = step_func.__name__
        _LOGGER.debug(f"Step {i}/{len(step_funcs)}: Executing '{func_name}'")
        
        try:
            result = step_func(context)
            context.save_step_result(func_name, result)
            _LOGGER.debug(f"Step '{func_name}' completed successfully")
        except Exception as e:
            _LOGGER.error(f"Step '{func_name}' failed: {e}")
            raise
    
    _LOGGER.info(f"All {len(step_funcs)} steps completed successfully")
