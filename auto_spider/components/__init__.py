"""
Components module for auto_spider.

Contains Context system components implementations.
Components like spider, db, config, cache should be placed here.

These components are injected into Context and used by actions.
"""

from .base_spider import Spider
from .request_spider import RequestSpider
from .playwright_spider import PlaywrightSpider

__all__ = [
    'Spider',
    'RequestSpider',
    'PlaywrightSpider',
]
