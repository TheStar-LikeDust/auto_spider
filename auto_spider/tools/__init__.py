"""
Utility tools for auto_spider.

Plan template generation:
- generate_plan(): Generate plan script
- generate_steps(): Generate steps package

Logger:
- build_logger(): Build logger instance

Utility modules (not auto-imported):
- dedup: Duplicate detection (create_duplicate_checker, is_duplicate)
- xpath: XPath parsing (xpath_extract)
- html_cleaner: HTML cleaning (clean_html)

Usage:
    from auto_spider.tools import generate_plan, build_logger
    from auto_spider.tools.dedup import create_duplicate_checker, is_duplicate
    from auto_spider.tools.xpath import xpath_extract
"""

from ..template import generate_plan, generate_steps
from .logger import build_logger

__all__ = [
    'generate_plan',
    'generate_steps',
    'build_logger',
]
