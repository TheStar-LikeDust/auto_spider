"""
HTML cleaner utilities.

Clean HTML by removing noise tags and attributes.
"""

from typing import List, Dict, Optional
from lxml import etree
from lxml.html import tostring, HtmlElement


_DEFAULT_REMOVE_TAGS = ['script', 'style', 'meta', 'svg', 'link', 'noscript', 'iframe']
_DEFAULT_KEEP_ATTRS = ['id', 'class', 'href', 'src', 'alt', 'title', 'name', 'type', 'value', 'placeholder']
_DEFAULT_UNWRAP_TAGS = ['div', 'span']


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


def _is_blank_text(text: Optional[str]) -> bool:
    return text is None or text.strip() == ''


def _compact_wrappers(tree: HtmlElement, unwrap_tags: List[str], max_passes: int = 5) -> None:
    for _ in range(max_passes):
        changed = False
        elements = list(tree.xpath('//*'))
        elements.reverse()

        for element in elements:
            if element.tag not in unwrap_tags:
                continue
            if element.attrib:
                continue
            if not _is_blank_text(element.text):
                continue

            parent = element.getparent()
            if parent is None:
                continue

            if len(element) == 0:
                if _is_blank_text(element.tail):
                    parent.remove(element)
                    changed = True
                continue

            if len(element) != 1:
                continue

            child = element[0]
            if not _is_blank_text(child.tail):
                continue

            tail = element.tail
            parent.replace(element, child)
            if tail:
                child.tail = (child.tail or '') + tail
            changed = True

        if not changed:
            break


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

    html_stripped = html.lstrip()
    if '<' not in html_stripped:
        return {'html': html, 'text': '', 'body': html}
    
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

    _compact_wrappers(tree, list(_DEFAULT_UNWRAP_TAGS))
    
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
