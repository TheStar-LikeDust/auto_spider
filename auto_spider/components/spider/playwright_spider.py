"""
Playwright-based spider implementation with CDP support.

## Current Implementation

This module provides a simplified, production-ready browser automation solution:

- **Core Approach**: Uses CDP native methods (DOM.querySelectorAll, DOM.getBoxModel) for element extraction
- **Design Principle**: KISS - Keep It Simple, delegate CDP operations to cdp_tools module
- **Code Size**: ~410 lines (spider logic only, CDP operations in cdp_tools)

## Key Features

1. **Element Extraction**: Via `get_page_info()` using native CDP DOM methods
2. **Element Interaction**: Via `select_element()` and `select_by_index()` using Playwright API
3. **Screenshot Capture**: Full page and element screenshots via CDP
4. **Browser Management**: Standard attach/detach lifecycle with automatic CDP initialization

## API Usage

```python
spider = PlaywrightSpider(enable_cdp=True)
spider.attach()
spider.do_url('https://example.com')

# Get all interactive elements using CDP native methods
page_info = spider.get_page_info()
# Returns: {
#   'elements': [{'index': 1, 'tag': 'button', 'attributes': {...}, 'position': {...}, 'css': '...', 'xpath': '...'}],
#   'analysis_info': {'method': 'cdp_native', ...}
# }

# Capture screenshots
full_page = spider.capture_screenshot()
element_img = spider.capture_element_screenshot(index=1, padding=10)

# Interact with element by index
spider.select_by_index(1, 'click')

spider.detach()
```

## Design Decisions

### What We Kept
- CDP native methods: Direct DOM queries via CDP, no JavaScript execution
- Minimal data structure: Only essential fields (tag, attributes, position, selectors)
- Single code path: No fallbacks, no backward compatibility bloat
- Modular design: CDP operations delegated to cdp_tools module

### What We Removed (900+ lines)
- Complex CDP DOM Snapshot parsing
- Occlusion detection (paint order, z-index, opacity analysis)
- Accessibility tree processing
- Element type/action classification
- Human-readable descriptions generation
- Multiple fallback mechanisms
- All CDP management logic (moved to cdp_tools)

### Why CDP Native Methods
- **Accurate**: Direct box model calculations, no rendering approximations
- **Modular**: CDP logic isolated in cdp_tools module
- **Maintainable**: Spider only handles business logic
- **Extensible**: Easy to add new CDP features in cdp_tools

## Current Features

### CDP Tools Integration
1. **Screenshot capture**: Full page and element screenshots via CDP Page.captureScreenshot
2. **Element visibility**: Native CDP box model detection
3. **Dimension calculation**: Accurate element position and size

## Future Development

### Potential Enhancements (Only If Needed)
1. **Advanced selectors**: More sophisticated CSS/XPath generation in cdp_tools
2. **Element filtering**: Filter by visibility, interaction state in cdp_tools

### What NOT to Add
- Multiple element extraction methods (keep one simple solution)
- Complex visibility/occlusion algorithms (JavaScript handles basic cases)
- Human-readable descriptions (let AI interpret raw data)
- Backward compatibility layers (clean break is better)
- Network monitoring, console logs, performance metrics (not critical for LLM)

### Refactoring Guidelines
- **Before adding features**: Ask "Is this really needed?" (YAGNI principle)
- **Keep it under 500 lines**: If growing too large, remove complexity first
- **One way to do things**: Avoid "flexible" solutions with multiple options
- **Fail fast**: No defensive programming, let errors surface early

## Technical Notes

### CDP Connection
- Only works with Chromium-based browsers
- Managed by `cdp_tools.init_cdp_client()` and `cdp_tools.close_cdp_client()`
- Spider only stores cdp_client reference

### Element Selector Strategy
- Priority: id > className > tagName
- XPath: Simplified version for id or basic tag matching
- Selector generation in cdp_tools module

### Error Handling
- Minimal try-catch blocks (let it fail principle)
- CDP operations fail fast in cdp_tools
- Raise RuntimeError for critical issues (CDP not enabled, page not attached)
"""

import time
from typing import Optional, Dict, Any, List

from .base_spider import Spider
from . import cdp


class PlaywrightSpider(Spider):
    """
    Browser spider using Playwright with CDP support.

    Modern browser automation with full JavaScript support and Chrome DevTools Protocol.
    Supports Chromium, Firefox, and WebKit.

    Example:
        spider = PlaywrightSpider(headless=True, enable_cdp=True)
        spider.attach()

        content = spider.do_url('https://example.com')

        # Get page info using CDP
        page_info = spider.get_page_info()

        # Use get_driver for advanced operations
        page = spider.get_driver()
        page.click('button#submit')
        page.fill('input#username', 'user')

        spider.detach()
    """

    def __init__(
        self,
        browser_type: str = 'chromium',
        headless: bool = True,
        timeout: float = 30000,
        viewport: Optional[Dict[str, int]] = None,
        enable_cdp: bool = True,
        debug_port: Optional[int] = None
    ):
        """
        Initialize PlaywrightSpider.

        Args:
            browser_type: Browser type ('chromium', 'firefox', 'webkit')
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
            viewport: Viewport size {'width': 1280, 'height': 720}
            enable_cdp: Enable Chrome DevTools Protocol support (default True)
            debug_port: CDP debug port (auto-assigned if None)
        """
        self.browser_type = browser_type
        self.headless = headless
        self.timeout = timeout
        self.viewport = viewport or {'width': 1280, 'height': 720}
        self.enable_cdp = enable_cdp and browser_type == 'chromium'
        self.debug_port = debug_port

        self.playwright = None
        self.browser = None
        self.page = None
        self.cdp_client = None

        super().__init__()

    def _do_attach(self):
        """Launch browser and create page."""
        # Lazy import to avoid dependency error
        from playwright.sync_api import sync_playwright

        launch_args = {}
        browser_args = []

        if self.browser_type == 'chromium':
            browser_args.append('--disable-blink-features=AutomationControlled')

            if self.enable_cdp:
                if self.debug_port:
                    browser_args.append(f'--remote-debugging-port={self.debug_port}')
                else:
                    browser_args.append('--remote-debugging-port=0')  # Auto-assign port

            launch_args['args'] = browser_args

        self.playwright = sync_playwright().start()

        browser_launcher = getattr(self.playwright, self.browser_type)
        self.browser = browser_launcher.launch(headless=self.headless, **launch_args)

        self.page = self.browser.new_page(viewport=self.viewport)
        self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            from playwright_stealth import stealth_sync
            stealth_sync(self.page)
        except ImportError:
            pass

        self.page.set_default_timeout(self.timeout)

        if self.enable_cdp:
            self.cdp_client = cdp.cdp_connect_playwright(self.page)

    def _do_detach(self):
        """Close browser and cleanup."""
        cdp.cdp_close(self.cdp_client)
        self.cdp_client = None

        if self.page:
            self.page.close()
            self.page = None

        if self.browser:
            self.browser.close()
            self.browser = None

        if self.playwright:
            self.playwright.stop()
            self.playwright = None

    def _do_clear(self):
        """Clear browser context (cookies, storage)."""
        if self.page:
            self.page.context.clear_cookies()

    def get_driver(self):
        """Get Playwright page instance."""
        return self.page

    def do_url(self, url: str, wait_until: str = 'load', **kwargs) -> str:
        """
        Navigate to URL.

        Args:
            url: Target URL
            wait_until: Wait state ('load', 'domcontentloaded', 'networkidle')
            **kwargs: Additional navigation options

        Returns:
            Page content
        """
        self.page.goto(url, wait_until=wait_until)
        return self.page.content()

    def get_page_info(
        self,
        viewport: bool = True,
        not_occluded: bool = False,
        compute_level: bool = False
    ) -> Dict[str, Any]:
        """
        Get page information using CDP Accessibility Tree.
        
        Args:
            viewport: Only elements in viewport (default True)
            not_occluded: Only elements not covered by others (default False)
            compute_level: Add visibility_level 1/2/3 (default False)

        Returns:
            Dict with page title, URL, and actionable elements
        """
        if not self.page:
            raise RuntimeError("Spider not attached")

        if not self.cdp_client:
            raise RuntimeError("CDP not enabled")

        start_time = time.time()
        elements = cdp.get_interactive_elements(
            self.cdp_client,
            viewport=viewport,
            not_occluded=not_occluded,
            compute_level=compute_level
        )
        processing_time = time.time() - start_time

        return {
            'title': self.page.title(),
            'url': self.page.url,
            'elements': elements,
            'analysis_info': {
                'method': 'cdp_accessibility_tree',
                'viewport': viewport,
                'not_occluded': not_occluded,
                'compute_level': compute_level,
                'processing_time_ms': round(processing_time * 1000, 2),
                'interactive_elements_found': len(elements)
            }
        }

    def select_element(self, locator: str, action: str = 'click', text: str = None,
                   locator_type: str = 'css') -> bool:
        """
        Select and interact with element using multiple locator strategies.

        Args:
            selector: CSS selector for the element
            action: Action to perform ('click', 'type', 'focus', 'hover')
            text: Text to type (only for 'type' action)

        Returns:
            True if successful, False otherwise
        """
        if not self.page:
            raise RuntimeError("Spider not attached")

        try:
            # Build locator based on type
            if locator_type == 'css':
                element = self.page.locator(locator)
            elif locator_type == 'xpath':
                element = self.page.locator(f'xpath={locator}')
            elif locator_type == 'text':
                element = self.page.get_by_text(locator)
            elif locator_type == 'id':
                element = self.page.locator(f'#{locator}')
            elif locator_type == 'class':
                element = self.page.locator(f'.{locator}')
            elif locator_type == 'tag':
                element = self.page.locator(locator)
            else:
                raise ValueError(f"Unsupported locator type: {locator_type}")

            # Wait for element to be ready
            element.wait_for(timeout=5000, state='visible')

            if action == 'click':
                element.click()
            elif action == 'type':
                if not text:
                    raise ValueError("Text is required for 'type' action")
                element.fill('')
                element.type(text)
            elif action == 'fill':
                if not text:
                    raise ValueError("Text is required for 'fill' action")
                element.fill(text)
            elif action == 'focus':
                element.focus()
            elif action == 'hover':
                element.hover()
            elif action == 'select':
                if not text:
                    raise ValueError("Option text is required for 'select' action")
                element.select_option(text)
            else:
                raise ValueError(f"Unsupported action: {action}")

            return True

        except Exception:
            return False

    def select_by_index(self, index: int, action: str = 'click', text: str = None,
                   locator_type: str = 'css') -> bool:
        """
        Select element by index from get_page_info() result.

        Args:
            index: Element index from get_page_info() (1-based)
            action: Action to perform ('click', 'type', 'focus', 'hover', 'select', 'fill')
            text: Text to type or select option
            locator_type: Which locator to use ('css' or 'xpath')

        Returns:
            True if successful, False otherwise

        Example:
            page_info = spider.get_page_info()
            # AI decides to click element #3
            spider.select_by_index(3, 'click')
        """
        if not self.page:
            raise RuntimeError("Spider not attached")

        # Get current page elements
        page_info = self.get_page_info()

        if index < 1 or index > len(page_info['elements']):
            return False

        element = page_info['elements'][index - 1]

        if locator_type == 'xpath':
            locator = element['xpath']
        else:
            locator = element['css']

        return self.select_element(locator, action, text, locator_type)

    def capture_screenshot(self, format: str = 'png', quality: int = 100) -> Optional[str]:
        """
        Capture full page screenshot.
        
        Args:
            format: Image format ('png' or 'jpeg')
            quality: JPEG quality 0-100
            
        Returns:
            Base64 encoded image string
        """
        if not self.cdp_client:
            raise RuntimeError("CDP not enabled")
        
        return cdp.capture_screenshot(self.cdp_client, format, quality)

    def capture_element_screenshot(self, index: int, format: str = 'png', 
                                   quality: int = 100, padding: int = 5) -> Optional[str]:
        """
        Capture screenshot of specific element by index.
        
        Args:
            index: Element index from get_page_info() (1-based)
            format: Image format ('png' or 'jpeg')
            quality: JPEG quality 0-100
            padding: Extra padding around element
            
        Returns:
            Base64 encoded image string
        """
        if not self.cdp_client:
            raise RuntimeError("CDP not enabled")
        
        page_info = self.get_page_info()
        if index < 1 or index > len(page_info['elements']):
            return None
        
        element = page_info['elements'][index - 1]
        
        # Use CDP to find node and capture
        root_id = cdp.cdp_get_document_root(self.cdp_client)
        node_ids = cdp.cdp_query_selector_all(self.cdp_client, root_id, element['css'])
        
        if not node_ids:
            return None
        
        return cdp.capture_element_screenshot(self.cdp_client, node_id=node_ids[0], format=format, quality=quality, padding=padding)
