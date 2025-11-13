"""
CDP utility functions for browser automation.

Focused on essential operations: screenshots, visibility detection, 
element dimensions, and selector generation.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

_LOGGER = logging.getLogger(__name__)


def init_cdp_client(page):
    """
    Initialize CDP client and enable essential domains.
    
    Args:
        page: Playwright page instance
        
    Returns:
        CDP client instance
    """
    try:
        cdp_client = page.context.new_cdp_session(page)
        
        cdp_client.send('Page.enable', {})
        cdp_client.send('Runtime.enable', {})
        cdp_client.send('DOM.enable', {})
        
        _LOGGER.info("CDP client initialized")
        return cdp_client
    except Exception as e:
        _LOGGER.error(f"Failed to initialize CDP client: {e}")
        return None


def close_cdp_client(cdp_client):
    """Close CDP client connection."""
    if cdp_client:
        try:
            cdp_client.detach()
        except Exception:
            pass


def get_document_root(cdp_client) -> int:
    """Get document root node ID."""
    result = cdp_client.send('DOM.getDocument', {'depth': -1})
    return result['root']['nodeId']


def query_selector_all(cdp_client, node_id: int, selector: str) -> List[int]:
    """
    Query elements using CSS selector via CDP.
    
    Returns:
        List of node IDs
    """
    result = cdp_client.send('DOM.querySelectorAll', {
        'nodeId': node_id,
        'selector': selector
    })
    return result.get('nodeIds', [])


def get_node_box_model(cdp_client, node_id: int) -> Optional[Dict[str, Any]]:
    """
    Get element box model (position, size, borders, padding).
    
    Returns:
        Box model dict with x, y, width, height
        Returns None if element not visible/rendered
    """
    try:
        result = cdp_client.send('DOM.getBoxModel', {'nodeId': node_id})
        model = result.get('model', {})
        
        content = model.get('content', [])
        if len(content) >= 4:
            x_coords = [content[i] for i in range(0, len(content), 2)]
            y_coords = [content[i] for i in range(1, len(content), 2)]
            
            return {
                'x': min(x_coords),
                'y': min(y_coords),
                'width': max(x_coords) - min(x_coords),
                'height': max(y_coords) - min(y_coords),
                'center_x': sum(x_coords) / len(x_coords),
                'center_y': sum(y_coords) / len(y_coords)
            }
        return None
    except Exception as e:
        _LOGGER.debug(f"Failed to get box model for node {node_id}: {e}")
        return None


def is_element_visible(cdp_client, node_id: int) -> bool:
    """Check if element is visible using CDP box model."""
    box_model = get_node_box_model(cdp_client, node_id)
    if not box_model:
        return False
    
    return box_model['width'] > 0 and box_model['height'] > 0


def get_element_attributes(cdp_client, node_id: int) -> Dict[str, str]:
    """
    Get all attributes of an element.
    
    Returns:
        Dict of attribute name-value pairs
    """
    result = cdp_client.send('DOM.getAttributes', {'nodeId': node_id})
    attrs = result.get('attributes', [])
    
    return {attrs[i]: attrs[i + 1] for i in range(0, len(attrs), 2)}


def describe_node(cdp_client, node_id: int) -> Dict[str, Any]:
    """Get detailed node information."""
    result = cdp_client.send('DOM.describeNode', {'nodeId': node_id})
    return result.get('node', {})


def generate_xpath(cdp_client, node_id: int) -> str:
    """
    Generate XPath for element using CDP.
    
    Returns:
        XPath string (simplified version)
    """
    try:
        node = describe_node(cdp_client, node_id)
        node_name = node.get('nodeName', '').lower()
        
        attrs = get_element_attributes(cdp_client, node_id)
        if 'id' in attrs:
            return f'//*[@id="{attrs["id"]}"]'
        
        return f'//{node_name}'
    except Exception as e:
        _LOGGER.debug(f"Failed to generate XPath for node {node_id}: {e}")
        return ''


def capture_screenshot(cdp_client, format: str = 'png', quality: int = 100, 
                      clip: Optional[Dict[str, float]] = None) -> Optional[str]:
    """
    Capture page or element screenshot.
    
    Args:
        format: Image format ('png' or 'jpeg')
        quality: JPEG quality 0-100 (ignored for PNG)
        clip: Optional clip region {'x': 0, 'y': 0, 'width': 100, 'height': 100, 'scale': 1}
        
    Returns:
        Base64 encoded image string, None on error
    """
    params = {'format': format}
    
    if format == 'jpeg':
        params['quality'] = quality
    
    if clip:
        params['clip'] = clip
    
    try:
        result = cdp_client.send('Page.captureScreenshot', params)
        return result.get('data')
    except Exception as e:
        _LOGGER.error(f"Failed to capture screenshot: {e}")
        return None


def capture_element_screenshot(cdp_client, node_id: int, format: str = 'png', 
                               quality: int = 100, padding: int = 0) -> Optional[str]:
    """
    Capture screenshot of specific element.
    
    Args:
        node_id: Target node ID
        format: Image format ('png' or 'jpeg')
        quality: JPEG quality 0-100
        padding: Extra padding around element in pixels
        
    Returns:
        Base64 encoded image string, None on error
    """
    box_model = get_node_box_model(cdp_client, node_id)
    if not box_model:
        _LOGGER.warning(f"Cannot capture screenshot for invisible element {node_id}")
        return None
    
    clip = {
        'x': max(0, box_model['x'] - padding),
        'y': max(0, box_model['y'] - padding),
        'width': box_model['width'] + 2 * padding,
        'height': box_model['height'] + 2 * padding,
        'scale': 1
    }
    
    return capture_screenshot(cdp_client, format, quality, clip)


def get_viewport_size(cdp_client) -> Dict[str, int]:
    """
    Get current viewport size.
    
    Returns:
        Dict with 'width' and 'height'
    """
    result = cdp_client.send('Page.getLayoutMetrics', {})
    viewport = result.get('visualViewport', {})
    return {
        'width': viewport.get('clientWidth', 0),
        'height': viewport.get('clientHeight', 0)
    }


def scroll_into_view(cdp_client, node_id: int) -> bool:
    """
    Scroll element into view.
    
    Returns:
        True if successful
    """
    try:
        cdp_client.send('DOM.scrollIntoViewIfNeeded', {'nodeId': node_id})
        return True
    except Exception as e:
        _LOGGER.debug(f"Failed to scroll element {node_id} into view: {e}")
        return False


def get_interactive_elements(cdp_client) -> List[Dict[str, Any]]:
    """
    Get all interactive elements using native CDP methods.
    
    Returns:
        List of element dicts with index, tag, attributes, position, selectors
    """
    interactive_tags = ['a', 'button', 'input', 'select', 'textarea']
    elements = []
    
    root_id = get_document_root(cdp_client)
    
    for tag in interactive_tags:
        node_ids = query_selector_all(cdp_client, root_id, tag)
        
        for node_id in node_ids:
            box_model = get_node_box_model(cdp_client, node_id)
            if not box_model:
                continue
            
            attrs = get_element_attributes(cdp_client, node_id)
            
            # Build CSS selector
            if 'id' in attrs:
                css_selector = f'#{attrs["id"]}'
            elif 'class' in attrs:
                classes = attrs['class'].split()
                css_selector = f'{tag}.{".".join(classes)}' if classes else tag
            else:
                css_selector = tag
            
            elements.append({
                'index': len(elements) + 1,
                'tag': tag,
                'attributes': attrs,
                'position': {
                    'x': int(box_model['x']),
                    'y': int(box_model['y']),
                    'width': int(box_model['width']),
                    'height': int(box_model['height']),
                    'center_x': int(box_model['center_x']),
                    'center_y': int(box_model['center_y'])
                },
                'css': css_selector,
                'xpath': generate_xpath(cdp_client, node_id)
            })
    
    # Query elements with onclick and roles
    for selector in ['[onclick]', '[role="button"]', '[role="link"]']:
        node_ids = query_selector_all(cdp_client, root_id, selector)
        
        for node_id in node_ids:
            box_model = get_node_box_model(cdp_client, node_id)
            if not box_model:
                continue
            
            node = describe_node(cdp_client, node_id)
            tag = node.get('nodeName', '').lower()
            attrs = get_element_attributes(cdp_client, node_id)
            
            elements.append({
                'index': len(elements) + 1,
                'tag': tag,
                'attributes': attrs,
                'position': {
                    'x': int(box_model['x']),
                    'y': int(box_model['y']),
                    'width': int(box_model['width']),
                    'height': int(box_model['height']),
                    'center_x': int(box_model['center_x']),
                    'center_y': int(box_model['center_y'])
                },
                'css': attrs.get('id', tag),
                'xpath': generate_xpath(cdp_client, node_id)
            })
    
    return elements
