"""
Development tools for auto_spider.

Backward compatibility wrapper for plan_template.
"""

from ..core.plan_template import generate_plan, generate_steps

__all__ = [
    'generate_plan',
    'generate_steps',
]
