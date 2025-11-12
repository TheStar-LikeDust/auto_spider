"""
Request-based spider implementation.

Simple HTTP spider using requests library.
"""

from typing import Dict, Optional, Union

from .base_spider import Spider


DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}


class RequestSpider(Spider):
    """
    HTTP spider using requests.Session.
    
    Simple and fast for static pages and API requests.
    
    Example:
        spider = RequestSpider()
        spider.attach()
        
        response = spider.do_url('https://example.com', http_method='GET', retry=3)
        html = response.text
        
        spider.detach()
    """
    
    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        timeout: Union[int, float] = 10,
        verify_ssl: bool = True,
        auto_raise: bool = True
    ):
        """
        Initialize RequestSpider.
        
        Args:
            headers: Custom HTTP headers
            timeout: Request timeout in seconds
            verify_ssl: Verify SSL certificates
            auto_raise: Raise exception on request failure
        """
        self.headers = headers or DEFAULT_HEADERS.copy()
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.auto_raise = auto_raise
        self.session = None
        self.last_response = None
        
        super().__init__()
    
    def _do_attach(self):
        """Create requests session."""
        # Lazy import to avoid dependency error
        from requests import Session
        
        self.session = Session()
        self.session.headers.update(self.headers)
    
    def _do_detach(self):
        """Close requests session."""
        if self.session:
            self.session.close()
            self.session = None
    
    def _do_clear(self):
        """Clear cookies."""
        if self.session:
            self.session.cookies.clear()
    
    def get_driver(self):
        """Get requests session instance."""
        return self.session
    
    def do_url(
        self,
        url: str,
        http_method: str = 'GET',
        retry: int = 1,
        timeout: Optional[Union[int, float]] = None,
        auto_raise: Optional[bool] = None,
        **kwargs
    ):
        """
        Universal URL request method with retry support.
        
        Args:
            url: Target URL
            http_method: HTTP method (GET, POST, PUT, DELETE, OPTIONS)
            retry: Retry count on failure
            timeout: Request timeout
            auto_raise: Raise exception on request failure
            **kwargs: Additional requests arguments (params, data, json, etc.)
            
        Returns:
            Response object
        """
        timeout = timeout or self.timeout
        http_method = http_method.upper()
        auto_raise = auto_raise if auto_raise is not None else self.auto_raise
        
        count = 0
        exception = None
        response = None
        
        while count < retry:
            try:
                if http_method == 'GET':
                    response = self.session.get(url, timeout=timeout, verify=self.verify_ssl, **kwargs)
                elif http_method == 'POST':
                    response = self.session.post(url, timeout=timeout, verify=self.verify_ssl, **kwargs)
                elif http_method == 'DELETE':
                    response = self.session.delete(url, timeout=timeout, verify=self.verify_ssl, **kwargs)
                elif http_method == 'PUT':
                    response = self.session.put(url, timeout=timeout, verify=self.verify_ssl, **kwargs)
                elif http_method == 'OPTIONS':
                    response = self.session.options(url, timeout=timeout, verify=self.verify_ssl, **kwargs)
                else:
                    raise ValueError(f'Unsupported HTTP method: {http_method}')
                
                self.last_response = response
                response.raise_for_status()
                return response
                
            except Exception as e:
                count += 1
                exception = e
        
        if exception and auto_raise:
            raise exception
        
        return response
