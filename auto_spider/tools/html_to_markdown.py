"""
HTML to Markdown converter.

Convert HTML to readable markdown using trafilatura.
"""

import trafilatura


def html_to_markdown(html: str) -> str:
    """
    Convert HTML to markdown.
    
    Args:
        html: Raw HTML content
        
    Returns:
        Markdown text, empty string if extraction fails
        
    Example:
        >>> md = html_to_markdown(raw_html)
        >>> print(md[:500])
    """
    if not html:
        return ''
    
    result = trafilatura.extract(html, output_format='markdown')
    return result or ''
