"""
Playwright-based spider implementation.

Modern browser automation using Playwright.
"""

from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, Browser, Page, Playwright

from auto_spider.components.base_spider import Spider


class PlaywrightSpider(Spider):
    """
    Browser spider using Playwright.
    
    Modern browser automation with full JavaScript support.
    Supports Chromium, Firefox, and WebKit.
    
    Example:
        spider = PlaywrightSpider(headless=True)
        spider.attach()
        
        content = spider.do_url('https://example.com')
        
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
        viewport: Optional[Dict[str, int]] = None
    ):
        """
        Initialize PlaywrightSpider.
        
        Args:
            browser_type: Browser type ('chromium', 'firefox', 'webkit')
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
            viewport: Viewport size {'width': 1280, 'height': 720}
        """
        self.browser_type = browser_type
        self.headless = headless
        self.timeout = timeout
        self.viewport = viewport or {'width': 1280, 'height': 720}
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
        super().__init__()
    
    def _do_attach(self):
        """Launch browser and create page."""
        self.playwright = sync_playwright().start()
        
        browser_launcher = getattr(self.playwright, self.browser_type)
        self.browser = browser_launcher.launch(headless=self.headless)
        
        self.page = self.browser.new_page(viewport=self.viewport)
        self.page.set_default_timeout(self.timeout)
    
    def _do_detach(self):
        """Close browser and cleanup."""
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
    
    def get_driver(self) -> Page:
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
