"""
Components module for auto_spider.

Exports component base classes and utilities for scraper components.
"""

from auto_spider.components._base_component import (
    Component,
    ComponentMeta,
    active,
    set_active,
    logger
)

__all__ = [
    'Component',
    'ComponentMeta',
    'active',
    'set_active',
    'logger'
]
