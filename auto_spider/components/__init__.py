"""
Components module.

Provides spider components and base classes.

Third-party libraries (requests, playwright) are imported 
inside methods to avoid dependency errors.
"""

from .spider import BaseSpider, RequestSpider, PlaywrightSpider

# Alias for backward compatibility
Spider = BaseSpider

__all__ = [
    'Spider',
    'BaseSpider',
    'RequestSpider',
    'PlaywrightSpider',
]
