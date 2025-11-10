"""
Plan execution module.

Define and execute action plans.
"""

from typing import List, Any
from auto_spider import Context
from auto_spider.core import execute_plan as _execute_plan
from auto_spider.logger import build_logger

logger = build_logger('plan')


class Plan:
    """
    Action execution plan.
    
    Example:
        plan = Plan([
            'fetch_page',
            'parse_content',
            'save_data'
        ])
        
        result = plan.execute(scraper=my_scraper, url='...')
    """
    
    def __init__(self, actions: List[str]):
        """
        Initialize plan.
        
        Args:
            actions: List of action names
        """
        self.actions = actions
    
    def execute(self, context: Context = None, **kwargs) -> Any:
        """
        Execute plan.
        
        Args:
            context: Context object
            **kwargs: Context initialization args
            
        Returns:
            Final result
        """
        return _execute_plan(self.actions, context=context, **kwargs)
    
    def __repr__(self):
        return f"Plan({self.actions})"


def create_plan(actions: List[str]) -> Plan:
    """
    Create a plan.
    
    Args:
        actions: List of action names
        
    Returns:
        Plan object
    """
    return Plan(actions)


def execute_plan_list(actions: List[str], context: Context = None, **kwargs) -> Any:
    """
    Execute plan from action list.
    
    Args:
        actions: List of action names
        context: Context object
        **kwargs: Context initialization args
        
    Returns:
        Final result
    """
    return _execute_plan(actions, context=context, **kwargs)
