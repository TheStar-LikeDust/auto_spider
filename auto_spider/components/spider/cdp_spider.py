"""
CDP Spider - Connect to existing browser via WebSocket.

Use this when you want to control an already running browser instance.
Useful for debugging, manual intervention, or avoiding detection.

Example:
    # 1. Start Chrome with debugging port:
    #    chrome --remote-debugging-port=9222
    
    # 2. Get WebSocket URL from http://localhost:9222/json
    
    # 3. Connect and use:
    spider = CDPSpider('ws://localhost:9222/devtools/page/xxx')
    spider.attach()
    
    spider.do_url('https://example.com')
    page_info = spider.get_page_info()
    
    spider.detach()
"""

import time
from typing import Optional, Dict, Any, List

from .base_spider import Spider
from . import cdp


class CDPSpider(Spider):
    """
    Spider that connects to existing browser via CDP WebSocket.
    
    Does not launch browser - connects to already running instance.
    """
    
    def __init__(self, ws_url: str = None, debug_port: int = 9222, timeout: float = 10.0):
        """
        Initialize CDPSpider.
        
        Args:
            ws_url: Full WebSocket URL (e.g., ws://localhost:9222/devtools/page/xxx)
                   If None, will try to discover from debug_port
            debug_port: Chrome debugging port (used if ws_url is None)
            timeout: Connection timeout in seconds
        """
        self.ws_url = ws_url
        self.debug_port = debug_port
        self.timeout = timeout
        self.client = None
        
        super().__init__()
    
    def _do_attach(self):
        """Connect to existing browser."""
        ws_url = self.ws_url or self._discover_ws_url()
        self.client = cdp.cdp_connect_websocket(ws_url, self.timeout)
    
    def _do_detach(self):
        """Close CDP connection."""
        cdp.cdp_close(self.client)
        self.client = None
    
    def _do_clear(self):
        """Clear is not supported for existing browser."""
        pass
    
    def _discover_ws_url(self) -> str:
        """Discover WebSocket URL from debug port."""
        import urllib.request
        import json
        
        url = f'http://localhost:{self.debug_port}/json'
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                targets = json.loads(response.read().decode())
                
            # Find first page target
            for target in targets:
                if target.get('type') == 'page':
                    return target['webSocketDebuggerUrl']
            
            raise RuntimeError(f"No page target found at port {self.debug_port}")
        except Exception as e:
            raise RuntimeError(f"Cannot discover browser at port {self.debug_port}: {e}")
    
    def get_driver(self):
        """Get CDP client."""
        return self.client
    
    def do_url(self, url: str, wait_until: str = 'load', **kwargs) -> str:
        """
        Navigate to URL.
        
        Args:
            url: Target URL
            wait_until: Not used (for API compatibility)
            
        Returns:
            Page content
        """
        if not self.client:
            raise RuntimeError("Spider not attached")
        
        cdp.navigate(self.client, url)
        
        # Simple wait for page load
        time.sleep(1)
        
        return cdp.get_page_content(self.client)
    
    def get_page_info(
        self,
        viewport: bool = True,
        not_occluded: bool = False,
        compute_level: bool = False
    ) -> Dict[str, Any]:
        """
        Get page information with interactive elements.
        
        Args:
            viewport: Only elements in viewport (default True)
            not_occluded: Only elements not covered by others (default False)
            compute_level: Add visibility_level 1/2/3 (default False)
        
        Returns:
            Dict with title, url, elements, and analysis info
        """
        if not self.client:
            raise RuntimeError("Spider not attached")
        
        start_time = time.time()
        elements = cdp.get_interactive_elements(
            self.client,
            viewport=viewport,
            not_occluded=not_occluded,
            compute_level=compute_level
        )
        processing_time = time.time() - start_time
        
        return {
            'title': cdp.get_page_title(self.client),
            'url': cdp.get_page_url(self.client),
            'elements': elements,
            'analysis_info': {
                'method': 'cdp_websocket',
                'viewport': viewport,
                'not_occluded': not_occluded,
                'compute_level': compute_level,
                'processing_time_ms': round(processing_time * 1000, 2),
                'interactive_elements_found': len(elements)
            }
        }
    
    def select_by_index(self, index: int, action: str = 'click', text: str = None) -> bool:
        """
        Select element by index from get_page_info() result.
        
        Args:
            index: Element index (1-based)
            action: Action to perform ('click', 'type')
            text: Text to type (for 'type' action)
            
        Returns:
            True if successful
        """
        if not self.client:
            raise RuntimeError("Spider not attached")
        
        page_info = self.get_page_info()
        
        if index < 1 or index > len(page_info['elements']):
            return False
        
        element = page_info['elements'][index - 1]
        
        # Get backend node id from element
        # Need to query by selector since we don't store backend_node_id
        root_id = cdp.cdp_get_document_root(self.client)
        node_ids = cdp.cdp_query_selector_all(self.client, root_id, element['css'])
        
        if not node_ids:
            return False
        
        node = cdp.cdp_describe_node(self.client, node_id=node_ids[0])
        backend_node_id = node.get('backendNodeId')
        
        if not backend_node_id:
            return False
        
        try:
            if action == 'click':
                cdp.click_element(self.client, backend_node_id)
            elif action == 'type':
                if not text:
                    raise ValueError("Text required for 'type' action")
                cdp.click_element(self.client, backend_node_id)
                cdp.type_text(self.client, text)
            else:
                raise ValueError(f"Unsupported action: {action}")
            
            return True
        except Exception:
            return False
    
    def capture_screenshot(self, format: str = 'png', quality: int = 100) -> str:
        """
        Capture full page screenshot.
        
        Returns:
            Base64 encoded image string
        """
        if not self.client:
            raise RuntimeError("Spider not attached")
        
        return cdp.capture_screenshot(self.client, format, quality)
    
    def capture_element_screenshot(self, index: int, format: str = 'png',
                                    quality: int = 100, padding: int = 5) -> Optional[str]:
        """
        Capture screenshot of specific element by index.
        
        Returns:
            Base64 encoded image string, or None if element not found
        """
        if not self.client:
            raise RuntimeError("Spider not attached")
        
        page_info = self.get_page_info()
        if index < 1 or index > len(page_info['elements']):
            return None
        
        element = page_info['elements'][index - 1]
        
        root_id = cdp.cdp_get_document_root(self.client)
        node_ids = cdp.cdp_query_selector_all(self.client, root_id, element['css'])
        
        if not node_ids:
            return None
        
        return cdp.capture_element_screenshot(
            self.client, node_id=node_ids[0],
            format=format, quality=quality, padding=padding
        )
