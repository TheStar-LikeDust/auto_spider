"""
HTML cleaner utilities.

Clean HTML by removing noise tags and attributes.
"""

from typing import List, Dict
from lxml import etree
from lxml.html import tostring, HtmlElement


_DEFAULT_REMOVE_TAGS = ['script', 'style', 'meta', 'svg', 'link', 'noscript', 'iframe']
_DEFAULT_KEEP_ATTRS = ['id', 'class', 'href']


def _remove_elements(tree: HtmlElement, tags: List[str]) -> None:
    """Remove elements by tag name."""
    for tag in tags:
        for element in tree.xpath(f'//{tag}'):
            element.getparent().remove(element)


def _remove_comments(tree: HtmlElement) -> None:
    """Remove HTML comments."""
    for comment in tree.xpath('//comment()'):
        parent = comment.getparent()
        if parent is not None:
            parent.remove(comment)


def _filter_attrs(tree: HtmlElement, keep_attrs: List[str]) -> None:
    """Remove attributes not in keep list."""
    for element in tree.xpath('//*'):
        attrs_to_remove = [attr for attr in element.attrib if attr not in keep_attrs]
        for attr in attrs_to_remove:
            del element.attrib[attr]


def _get_body_content(tree: HtmlElement) -> str:
    """Extract body content."""
    body = tree.xpath('//body')
    if body:
        return tostring(body[0], encoding='unicode', method='html')
    return tostring(tree, encoding='unicode', method='html')


def _get_text_content(tree: HtmlElement) -> str:
    """Extract text content."""
    return ' '.join(tree.xpath('//body//text()') or tree.xpath('//text()'))


def clean_html(html: str,
               remove_tags: List[str] = None,
               keep_attrs: List[str] = None,
               remove_comments: bool = True) -> Dict[str, str]:
    """
    Clean HTML and return multiple formats.
    
    Default behavior:
    - Remove tags: script, style, meta, svg, link, noscript, iframe
    - Keep attrs: id, class, href
    - Remove comments: True
    
    Args:
        html: Raw HTML content
        remove_tags: Additional tags to remove (merged with defaults)
        keep_attrs: Attributes to keep (overrides defaults if provided)
        remove_comments: Whether to remove HTML comments
        
    Returns:
        {
            'html': cleaned HTML with structure,
            'text': text only content,
            'body': body content without html/head,
        }
        
    Example:
        >>> result = clean_html(raw_html)
        >>> clean = result['html']
        >>> text = result['text']
        
        >>> result = clean_html(raw_html, remove_tags=['nav', 'footer'])
        >>> result = clean_html(raw_html, keep_attrs=['id', 'class', 'href', 'src'])
    """
    if not html:
        return {'html': '', 'text': '', 'body': ''}
    
    try:
        tree = etree.HTML(html)
    except Exception:
        return {'html': html, 'text': '', 'body': html}
    
    # merge remove tags
    tags_to_remove = list(_DEFAULT_REMOVE_TAGS)
    if remove_tags:
        tags_to_remove.extend(remove_tags)
    
    # use provided keep_attrs or default
    attrs_to_keep = keep_attrs if keep_attrs is not None else list(_DEFAULT_KEEP_ATTRS)
    
    # remove tags
    _remove_elements(tree, tags_to_remove)
    
    # remove comments
    if remove_comments:
        _remove_comments(tree)
    
    # extract text before filtering attrs
    text = _get_text_content(tree)
    text = ' '.join(text.split())  # normalize whitespace
    
    # extract body before filtering attrs (for structure)
    body = _get_body_content(tree)
    
    # filter attributes
    _filter_attrs(tree, attrs_to_keep)
    
    # get final html
    cleaned_html = tostring(tree, encoding='unicode', method='html')
    
    # get body after attr filtering
    body_cleaned = _get_body_content(tree)
    
    return {
        'html': cleaned_html,
        'text': text,
        'body': body_cleaned,
    }
