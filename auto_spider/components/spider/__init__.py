"""
Spider components.

Third-party dependencies imported inside methods.
"""

from .base_spider import BaseSpider, Spider
from .request_spider import RequestSpider
from .playwright_spider import PlaywrightSpider

__all__ = [
    'Spider',
    'BaseSpider',
    'RequestSpider',
    'PlaywrightSpider',
]
