"""
Utility tools for auto_spider.

Plan template generation:
- generate_plan(): Generate plan script
- generate_steps(): Generate steps package

Utility modules (not auto-imported):
- dedup: Duplicate detection (create_duplicate_checker, is_duplicate)
- xpath: XPath parsing (xpath_extract)

Usage:
    from auto_spider.tools import generate_plan
    from auto_spider.tools.dedup import create_duplicate_checker, is_duplicate
    from auto_spider.tools.xpath import xpath_extract
"""

from ..template import generate_plan, generate_steps

__all__ = [
    'generate_plan',
    'generate_steps',
]
