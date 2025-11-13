"""
Playwright-based spider implementation with CDP support.

## Current Implementation

This module provides a simplified, production-ready browser automation solution:

- **Core Approach**: Uses CDP (Chrome DevTools Protocol) to execute JavaScript for element extraction
- **Design Principle**: KISS - Keep It Simple, one clear solution instead of multiple fallback options
- **Code Size**: ~320 lines (reduced from 1200+ lines of over-engineered code)

## Key Features

1. **Element Extraction**: Via `get_page_info()` using CDP Runtime.evaluate with JavaScript
2. **Element Interaction**: Via `select_element()` and `select_by_index()` using Playwright API
3. **Browser Management**: Standard attach/detach lifecycle with automatic CDP initialization

## API Usage

```python
spider = PlaywrightSpider(enable_cdp=True)
spider.attach()
spider.do_url('https://example.com')

# Get all interactive elements
page_info = spider.get_page_info()
# Returns: {
#   'elements': [{'index': 1, 'tag': 'button', 'attributes': {...}, 'position': {...}, 'css': '...', 'xpath': '...'}],
#   'analysis_info': {'method': 'cdp_javascript', ...}
# }

# Interact with element by index
spider.select_by_index(1, 'click')

spider.detach()
```

## Design Decisions

### What We Kept
- CDP + JavaScript: Simple, reliable, standard DOM API
- Minimal data structure: Only essential fields (tag, attributes, position, selectors)
- Single code path: No fallbacks, no backward compatibility bloat

### What We Removed (900+ lines)
- Complex CDP DOM Snapshot parsing
- Occlusion detection (paint order, z-index, opacity analysis)
- Accessibility tree processing
- Element type/action classification
- Human-readable descriptions generation
- Multiple fallback mechanisms

### Why JavaScript Instead of Native CDP
- **Simpler**: One script vs. complex snapshot parsing
- **Reliable**: Standard DOM API, no CDP format dependency
- **Maintainable**: Modify logic by changing JavaScript only
- **Sufficient**: Performance is good enough for our use case

## Future Development

### Potential Enhancements (Only If Needed)
1. **Screenshot integration**: Capture element screenshots using CDP Page.captureScreenshot
2. **Network monitoring**: Use CDP Network domain for request/response tracking
3. **Performance metrics**: Use CDP Performance domain for page load analysis
4. **Console logs**: Capture browser console via CDP Runtime.consoleAPICalled

### What NOT to Add
- Multiple element extraction methods (keep one simple solution)
- Complex visibility/occlusion algorithms (JavaScript handles basic cases)
- Human-readable descriptions (let AI interpret raw data)
- Backward compatibility layers (clean break is better)

### Refactoring Guidelines
- **Before adding features**: Ask "Is this really needed?" (YAGNI principle)
- **Keep it under 500 lines**: If growing too large, remove complexity first
- **One way to do things**: Avoid "flexible" solutions with multiple options
- **Fail fast**: No defensive programming, let errors surface early

## Technical Notes

### CDP Connection
- Only works with Chromium-based browsers
- Auto-initialized in `_do_attach()` when `enable_cdp=True`
- Uses Playwright's built-in CDP session (`page.context.new_cdp_session()`)

### Element Selector Strategy
- Priority: id > className > tagName
- XPath: Simplified version for id or basic tag matching
- No complex selector generation (keep it simple)

### Error Handling
- Minimal try-catch blocks (let it fail principle)
- Silent failures only for optional features (e.g., CDP domain enablement)
- Raise RuntimeError for critical issues (CDP not enabled, page not attached)
"""

import time
from typing import Optional, Dict, Any, List

from .base_spider import Spider


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

        # CDP related
        self.cdp_client = None
        self.message_id = 0

        super().__init__()

    def _do_attach(self):
        """Launch browser and create page."""
        # Lazy import to avoid dependency error
        from playwright.sync_api import sync_playwright

        launch_args = {}
        browser_args = []

        if self.enable_cdp and self.browser_type == 'chromium':
            if self.debug_port:
                browser_args.extend([f'--remote-debugging-port={self.debug_port}'])
            else:
                browser_args.extend(['--remote-debugging-port=0'])  # Auto-assign port

            launch_args['args'] = browser_args

        self.playwright = sync_playwright().start()

        browser_launcher = getattr(self.playwright, self.browser_type)
        self.browser = browser_launcher.launch(headless=self.headless, **launch_args)

        self.page = self.browser.new_page(viewport=self.viewport)
        self.page.set_default_timeout(self.timeout)

        # Enable CDP if requested
        if self.enable_cdp:
            self._enable_cdp()

    def _do_detach(self):
        """Close browser and cleanup."""
        # Close CDP connection
        if self.cdp_client:
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

    def _enable_cdp(self):
        """Enable CDP connection using Playwright's context."""
        if self.browser_type != 'chromium':
            return

        try:
            self.cdp_client = self.page.context.new_cdp_session(self.page)

            # Enable essential domains
            self._cdp_send_no_response('Page.enable')
            self._cdp_send_no_response('Runtime.enable')
            self._cdp_send_no_response('DOM.enable')
            self._cdp_send_no_response('Accessibility.enable')
        except Exception:
            self.enable_cdp = False

    def _cdp_send_no_response(self, method: str, params: Optional[Dict] = None):
        """Send CDP command without waiting for response."""
        if not self.cdp_client:
            return

        try:
            self.cdp_client.send(method, params or {})
        except Exception:
            pass  # Silently handle for production

    def _cdp_send(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Send CDP command and wait for response."""
        if not self.cdp_client:
            raise RuntimeError("CDP not enabled")

        try:
            result = self.cdp_client.send(method, params or {})
            if isinstance(result, dict):
                return result
            elif hasattr(result, 'result'):
                return {'result': result.result}
            else:
                return {'raw_response': str(result)}
        except Exception as e:
            raise RuntimeError(f"CDP command error: {e}")

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

    def get_page_info(self) -> Dict[str, Any]:
        """
        Get page information for AI navigation decision making.

        Returns:
            Dict with page title, URL, and actionable elements with selectors
        """
        if not self.page:
            raise RuntimeError("Spider not attached")

        if not self.enable_cdp or not self.cdp_client:
            raise RuntimeError("CDP not enabled")

        return self._get_enhanced_page_info_cdp()
        
    def _get_enhanced_page_info_cdp(self) -> Dict[str, Any]:
        """
        Enhanced page analysis using CDP features.
        
        Use JavaScript with CDP for simpler, more reliable element extraction.
        """
        if not self.cdp_client:
            raise RuntimeError("CDP not enabled")

        start_time = time.time()

        # Use JavaScript to extract elements - simple and reliable
        script = """
        (function() {
            const elements = [];
            const interactive_tags = ['a', 'button', 'input', 'select', 'textarea'];
            const interactive_selectors = interactive_tags.join(',') + ',[onclick],[role="button"],[role="link"]';
            
            document.querySelectorAll(interactive_selectors).forEach((el, idx) => {
                const rect = el.getBoundingClientRect();
                const computed = window.getComputedStyle(el);
                
                // Skip invisible elements
                if (rect.width === 0 || rect.height === 0 || 
                    computed.display === 'none' || 
                    computed.visibility === 'hidden' ||
                    parseFloat(computed.opacity) === 0) {
                    return;
                }
                
                // Extract attributes
                const attrs = {};
                for (let attr of el.attributes) {
                    attrs[attr.name] = attr.value;
                }
                
                elements.push({
                    index: elements.length + 1,
                    tag: el.tagName.toLowerCase(),
                    attributes: attrs,
                    position: {
                        x: Math.round(rect.left + window.scrollX),
                        y: Math.round(rect.top + window.scrollY),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        center_x: Math.round(rect.left + window.scrollX + rect.width / 2),
                        center_y: Math.round(rect.top + window.scrollY + rect.height / 2)
                    },
                    css: (() => {
                        if (el.id) return '#' + el.id;
                        if (el.className) {
                            const classes = el.className.split(' ').filter(c => c);
                            if (classes.length) return el.tagName.toLowerCase() + '.' + classes.join('.');
                        }
                        return el.tagName.toLowerCase();
                    })(),
                    xpath: el.id ? `//*[@id="${el.id}"]` : `//${el.tagName.toLowerCase()}`
                });
            });
            
            return elements;
        })()
        """

        result = self._cdp_send('Runtime.evaluate', {
            'expression': script,
            'returnByValue': True
        })

        elements = result.get('result', {}).get('value', [])
        processing_time = time.time() - start_time

        return {
            'title': self.page.title(),
            'url': self.page.url,
            'elements': elements,
            'analysis_info': {
                'method': 'cdp_javascript',
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
