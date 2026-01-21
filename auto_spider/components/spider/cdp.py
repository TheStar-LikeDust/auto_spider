"""
CDP (Chrome DevTools Protocol) pure functions.

No classes, no state. Functions operate on client objects directly.
Client can be Playwright CDPSession or raw WebSocket.

Example:
    # From Playwright
    client = cdp_connect_playwright(page)
    
    # From existing browser
    client = cdp_connect_websocket('ws://localhost:9222/devtools/page/xxx')
    
    # Use functions
    elements = cdp_get_interactive_elements(client)
    screenshot = cdp_capture_screenshot(client)
    
    cdp_close(client)
"""

import json
import logging
from typing import Dict, Any, Optional, List

_LOGGER = logging.getLogger(__name__)


# ============== Connection ==============

def cdp_connect_playwright(page):
    """
    Get CDP session from Playwright page.
    
    Returns Playwright CDPSession object.
    """
    client = page.context.new_cdp_session(page)
    _cdp_enable_domains(client)
    _LOGGER.info("CDP connected via Playwright")
    return client


def cdp_connect_websocket(ws_url: str, timeout: float = 10.0):
    """
    Connect to existing browser via WebSocket.
    
    Returns raw websocket.WebSocket with _cdp_msg_id attached.
    
    Example:
        # Start Chrome: chrome --remote-debugging-port=9222
        # Get ws_url from: http://localhost:9222/json
        client = cdp_connect_websocket('ws://localhost:9222/devtools/page/xxx')
    """
    try:
        import websocket
    except ImportError:
        raise ImportError("websocket-client required: pip install websocket-client")
    
    ws = websocket.create_connection(ws_url, timeout=timeout)
    ws._cdp_msg_id = 0  # Attach message counter
    _cdp_enable_domains(ws)
    _LOGGER.info(f"CDP connected via WebSocket: {ws_url}")
    return ws


def cdp_close(client):
    """Close CDP connection."""
    if client is None:
        return
    try:
        if hasattr(client, 'detach'):  # Playwright session
            client.detach()
        elif hasattr(client, 'close'):  # WebSocket
            client.close()
    except Exception:
        pass


# ============== Core Send ==============

def cdp_send(client, method: str, params: Dict = None) -> Dict:
    """
    Send CDP command. Works with both Playwright session and WebSocket.
    """
    if hasattr(client, 'detach'):  # Playwright CDPSession
        return client.send(method, params or {})
    else:  # WebSocket
        return _ws_send(client, method, params or {})


def _ws_send(ws, method: str, params: Dict) -> Dict:
    """Send CDP command via WebSocket."""
    ws._cdp_msg_id += 1
    message = {'id': ws._cdp_msg_id, 'method': method, 'params': params}
    ws.send(json.dumps(message))
    
    while True:
        response = json.loads(ws.recv())
        if response.get('id') == ws._cdp_msg_id:
            if 'error' in response:
                raise RuntimeError(f"CDP error: {response['error']}")
            return response.get('result', {})


def _cdp_enable_domains(client):
    """Enable essential CDP domains."""
    cdp_send(client, 'Page.enable', {})
    cdp_send(client, 'Runtime.enable', {})
    cdp_send(client, 'DOM.enable', {})
    cdp_send(client, 'Accessibility.enable', {})


# ============== DOM Operations ==============

def cdp_get_document_root(client) -> int:
    """Get document root node ID."""
    result = cdp_send(client, 'DOM.getDocument', {'depth': -1})
    return result['root']['nodeId']


def cdp_query_selector_all(client, node_id: int, selector: str) -> List[int]:
    """Query elements using CSS selector."""
    result = cdp_send(client, 'DOM.querySelectorAll', {
        'nodeId': node_id,
        'selector': selector
    })
    return result.get('nodeIds', [])


def cdp_get_box_model(client, node_id: int = None, backend_node_id: int = None) -> Optional[Dict[str, Any]]:
    """Get element box model (position, size)."""
    try:
        params = {}
        if backend_node_id:
            params['backendNodeId'] = backend_node_id
        elif node_id:
            params['nodeId'] = node_id
        else:
            return None
        
        result = cdp_send(client, 'DOM.getBoxModel', params)
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
    except Exception:
        return None


def cdp_describe_node(client, node_id: int = None, backend_node_id: int = None) -> Dict[str, Any]:
    """Get detailed node information."""
    params = {}
    if backend_node_id:
        params['backendNodeId'] = backend_node_id
    elif node_id:
        params['nodeId'] = node_id
    
    result = cdp_send(client, 'DOM.describeNode', params)
    return result.get('node', {})


def cdp_get_attributes(client, node_id: int) -> Dict[str, str]:
    """Get element attributes as dict."""
    result = cdp_send(client, 'DOM.getAttributes', {'nodeId': node_id})
    attrs = result.get('attributes', [])
    return {attrs[i]: attrs[i + 1] for i in range(0, len(attrs), 2)}


def cdp_scroll_into_view(client, node_id: int):
    """Scroll element into view."""
    cdp_send(client, 'DOM.scrollIntoViewIfNeeded', {'nodeId': node_id})


# ============== Screenshot ==============

def capture_screenshot(client, format: str = 'png', quality: int = 100,
                       clip: Optional[Dict[str, float]] = None) -> str:
    """
    Capture page screenshot.
    
    Returns:
        Base64 encoded image string
    """
    params = {'format': format}
    if format == 'jpeg':
        params['quality'] = quality
    if clip:
        params['clip'] = clip
    
    result = cdp_send(client, 'Page.captureScreenshot', params)
    return result.get('data', '')


def capture_element_screenshot(client, node_id: int = None, backend_node_id: int = None,
                                format: str = 'png', quality: int = 100, 
                                padding: int = 0) -> Optional[str]:
    """Capture screenshot of specific element."""
    box = cdp_get_box_model(client, node_id=node_id, backend_node_id=backend_node_id)
    if not box:
        return None
    
    clip = {
        'x': max(0, box['x'] - padding),
        'y': max(0, box['y'] - padding),
        'width': box['width'] + 2 * padding,
        'height': box['height'] + 2 * padding,
        'scale': 1
    }
    return capture_screenshot(client, format, quality, clip)


# ============== Element Filters ==============

def filter_in_viewport(element: Dict, ctx: Dict) -> bool:
    """Filter: element is in viewport."""
    pos = element['position']
    vp = ctx['viewport']
    
    # Element center is in viewport
    return (0 <= pos['center_x'] <= vp['width'] and 
            0 <= pos['center_y'] <= vp['height'])


def filter_not_occluded(element: Dict, ctx: Dict) -> bool:
    """Filter: element center is not occluded by other elements."""
    pos = element['position']
    client = ctx['client']
    
    try:
        result = cdp_send(client, 'DOM.getNodeForLocation', {
            'x': int(pos['center_x']),
            'y': int(pos['center_y'])
        })
        top_backend_id = result.get('backendNodeId')
        return top_backend_id == element.get('backend_node_id')
    except Exception:
        return True  # Assume not occluded if detection fails


def filter_by_level(level: int):
    """Filter factory: return filter for specific visibility level."""
    def _filter(element: Dict, ctx: Dict) -> bool:
        return element.get('visibility_level') == level
    return _filter


def filter_level_at_most(level: int):
    """Filter factory: level <= threshold (1=foreground, 2=visible, 3=hidden)."""
    def _filter(element: Dict, ctx: Dict) -> bool:
        return element.get('visibility_level', 3) <= level
    return _filter


# Predefined filter registry
ELEMENT_FILTERS = {
    'all': lambda e, ctx: True,
    'viewport': filter_in_viewport,
    'not_occluded': filter_not_occluded,
    'foreground': filter_level_at_most(1),
    'visible': filter_level_at_most(2),
}


def _compute_visibility_level(element: Dict, ctx: Dict) -> int:
    """
    Compute visibility level:
        1 = foreground (in viewport, not occluded)
        2 = visible (in viewport, but occluded)
        3 = hidden (outside viewport)
    """
    if not filter_in_viewport(element, ctx):
        return 3
    if not filter_not_occluded(element, ctx):
        return 2
    return 1


# ============== Accessibility Tree ==============

INTERACTIVE_ROLES = {
    'button', 'link', 'textbox', 'combobox', 'checkbox', 'radio',
    'menuitem', 'menuitemcheckbox', 'menuitemradio', 'tab', 'switch',
    'searchbox', 'spinbutton', 'slider', 'listbox', 'option',
}


def get_interactive_elements(
    client,
    viewport: bool = True,
    not_occluded: bool = False,
    compute_level: bool = False
) -> List[Dict[str, Any]]:
    """
    Get interactive elements with optional filtering.
    
    Args:
        client: CDP client
        viewport: Only elements in viewport (default True)
        not_occluded: Only elements not covered by others (default False, adds CDP calls)
        compute_level: Add visibility_level field (default False, adds CDP calls)
    
    Returns:
        List of element dicts with index, role, name, position, selectors
    """
    # Build context
    vp = get_viewport_size(client)
    ctx = {'client': client, 'viewport': vp}
    
    # Get raw elements
    raw_elements = _get_raw_interactive_elements(client)
    
    # Compute level if requested
    if compute_level:
        for elem in raw_elements:
            elem['visibility_level'] = _compute_visibility_level(elem, ctx)
    
    # Apply filters
    elements = raw_elements
    if viewport:
        elements = [e for e in elements if filter_in_viewport(e, ctx)]
    if not_occluded:
        elements = [e for e in elements if filter_not_occluded(e, ctx)]
    
    # Re-index after filtering
    for i, elem in enumerate(elements):
        elem['index'] = i + 1
    
    return elements


def _get_raw_interactive_elements(client) -> List[Dict[str, Any]]:
    """Get all interactive elements without filtering."""
    elements = []
    
    ax_result = cdp_send(client, 'Accessibility.getFullAXTree', {})
    ax_nodes = ax_result.get('nodes', [])
    
    for ax_node in ax_nodes:
        role_obj = ax_node.get('role', {})
        role = role_obj.get('value', '') if isinstance(role_obj, dict) else ''
        
        if role not in INTERACTIVE_ROLES:
            continue
        
        backend_node_id = ax_node.get('backendDOMNodeId')
        if not backend_node_id:
            continue
        
        box = cdp_get_box_model(client, backend_node_id=backend_node_id)
        if not box:
            continue
        
        name_obj = ax_node.get('name', {})
        name = name_obj.get('value', '') if isinstance(name_obj, dict) else ''
        
        node_info = _get_node_info(client, backend_node_id)
        
        elements.append({
            'index': len(elements) + 1,
            'role': role,
            'name': name,
            'tag': node_info.get('tag', ''),
            'attributes': node_info.get('attributes', {}),
            'backend_node_id': backend_node_id,
            'position': {
                'x': int(box['x']),
                'y': int(box['y']),
                'width': int(box['width']),
                'height': int(box['height']),
                'center_x': int(box['center_x']),
                'center_y': int(box['center_y'])
            },
            'css': node_info.get('css', ''),
            'xpath': node_info.get('xpath', '')
        })
    
    return elements


def _get_node_info(client, backend_node_id: int) -> Dict[str, Any]:
    """Get DOM node info (tag, attributes, selectors)."""
    try:
        node = cdp_describe_node(client, backend_node_id=backend_node_id)
        
        tag = node.get('nodeName', '').lower()
        attrs = {}
        
        attr_list = node.get('attributes', [])
        for i in range(0, len(attr_list), 2):
            attrs[attr_list[i]] = attr_list[i + 1]
        
        if 'id' in attrs:
            css = f'#{attrs["id"]}'
            xpath = f'//*[@id="{attrs["id"]}"]'
        elif 'class' in attrs:
            classes = attrs['class'].split()
            css = f'{tag}.{".".join(classes)}' if classes else tag
            xpath = f'//{tag}'
        else:
            css = tag
            xpath = f'//{tag}'
        
        return {'tag': tag, 'attributes': attrs, 'css': css, 'xpath': xpath}
    except Exception:
        return {'tag': '', 'attributes': {}, 'css': '', 'xpath': ''}


# ============== Utilities ==============

def get_viewport_size(client) -> Dict[str, int]:
    """Get current viewport size."""
    result = cdp_send(client, 'Page.getLayoutMetrics', {})
    viewport = result.get('visualViewport', {})
    return {
        'width': viewport.get('clientWidth', 0),
        'height': viewport.get('clientHeight', 0)
    }


def navigate(client, url: str):
    """Navigate to URL."""
    cdp_send(client, 'Page.navigate', {'url': url})


def get_page_content(client) -> str:
    """Get page HTML content."""
    result = cdp_send(client, 'Runtime.evaluate', {
        'expression': 'document.documentElement.outerHTML'
    })
    return result.get('result', {}).get('value', '')


def get_page_title(client) -> str:
    """Get page title."""
    result = cdp_send(client, 'Runtime.evaluate', {
        'expression': 'document.title'
    })
    return result.get('result', {}).get('value', '')


def get_page_url(client) -> str:
    """Get current page URL."""
    result = cdp_send(client, 'Runtime.evaluate', {
        'expression': 'window.location.href'
    })
    return result.get('result', {}).get('value', '')


def click_element(client, backend_node_id: int):
    """Click element using CDP Input."""
    box = cdp_get_box_model(client, backend_node_id=backend_node_id)
    if not box:
        raise RuntimeError("Element not visible")
    
    x, y = box['center_x'], box['center_y']
    
    cdp_send(client, 'Input.dispatchMouseEvent', {
        'type': 'mousePressed',
        'x': x, 'y': y,
        'button': 'left',
        'clickCount': 1
    })
    cdp_send(client, 'Input.dispatchMouseEvent', {
        'type': 'mouseReleased',
        'x': x, 'y': y,
        'button': 'left',
        'clickCount': 1
    })


def type_text(client, text: str):
    """Type text using CDP Input."""
    for char in text:
        cdp_send(client, 'Input.dispatchKeyEvent', {
            'type': 'keyDown',
            'text': char
        })
        cdp_send(client, 'Input.dispatchKeyEvent', {
            'type': 'keyUp',
            'text': char
        })
