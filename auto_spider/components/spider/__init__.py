"""
Spider components.

Third-party dependencies imported inside methods.
"""

from .base_spider import BaseSpider, Spider
from .request_spider import RequestSpider
from .playwright_spider import PlaywrightSpider
from .cdp_spider import CDPSpider

__all__ = [
    'Spider',
    'BaseSpider',
    'RequestSpider',
    'PlaywrightSpider',
    'CDPSpider',
]
