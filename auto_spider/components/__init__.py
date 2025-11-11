"""
Components module for auto_spider.

Contains Context system components implementations.
Components like spider, db, config, cache should be placed here.

These components are injected into Context and used by actions.
"""

from auto_spider.components.base_spider import Spider
from auto_spider.components.request_spider import RequestSpider
from auto_spider.components.playwright_spider import PlaywrightSpider

__all__ = [
    'Spider',
    'RequestSpider',
    'PlaywrightSpider',
]
