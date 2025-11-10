"""
Base action module for auto_spider.

Simple function-based action system.
"""

from typing import Any, Union, Dict, List, Callable
from auto_spider.actions.context import Context


def execute_pipeline(
    actions: Union[Callable, List[Callable]],
    context: Union[Context, Dict[str, Any]] = None,
    **kwargs
) -> Any:
    """
    Execute action pipeline.
    
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
