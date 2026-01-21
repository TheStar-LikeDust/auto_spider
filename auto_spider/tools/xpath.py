"""
XPath parser utilities.

Simple XPath extraction function.
"""

from typing import List
from lxml import html


def _extract_text(elements: List) -> List[str]:
    """Extract text from elements using xpath('string()')."""
    if not elements:
        return []
    
    if isinstance(elements[0], str):
        return [str(e) for e in elements]
    
    results = []
    for e in elements:
        text = e.xpath('string()').strip()
        if text:
            results.append(text)
    return results


def xpath_extract(html_content: str, xpath_expr: str) -> List[str]:
    """
    Extract data from HTML using XPath.
    
    Args:
        html: HTML content
        xpath: XPath expression
        
    Returns:
        List of extracted strings, empty list if no match
        
    Example:
        # extract text
        texts = xpath_extract(html, '//a/text()')
        # ['Link1', 'Link2']
        
        # extract attribute
        hrefs = xpath_extract(html, '//a/@href')
        # ['/page1', '/page2']
        
        # extract element text
        titles = xpath_extract(html, '//h1')
        # ['Title']
    """
    if not html_content or not xpath_expr:
        return []
    
    try:
        tree = html.fromstring(html_content)
        elements = tree.xpath(xpath_expr)
        
        if not elements:
            return []
        
        # xpath returns attributes or text directly
        if isinstance(elements[0], str):
            return [str(e) for e in elements if e]
        
        # xpath returns element nodes, extract text
        return _extract_text(elements)
    
    except Exception:
        return []
