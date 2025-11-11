"""
Spider base class for web data access.

Spider is the core component for sensing and operating web data.
Provides unified lifecycle management: attach -> use -> detach.
"""

from abc import ABC, abstractmethod
from typing import Any


class Spider(ABC):
    """
    Base class for all spider implementations.
    
    Lifecycle:
        1. attach: Initialize and connect
        2. use: Get/post data
        3. detach: Clean up and disconnect
    
    Example:
        spider = RequestSpider()
        spider.attach()
        response = spider.do_url('https://example.com')
        spider.detach()
    """
    
    def __init__(self):
        """Initialize spider."""
        self._attached = False
    
    @property
    def attached(self) -> bool:
        """Check if spider is attached."""
        return self._attached
    
    def attach(self) -> 'Spider':
        """
        Attach spider and create connection.
        
        Returns:
            Self for chaining
        """
        if not self._attached:
            self._do_attach()
            self._attached = True
        return self
    
    def detach(self) -> 'Spider':
        """
        Detach spider and close connection.
        
        Returns:
            Self for chaining
        """
        if self._attached:
            self._do_detach()
            self._attached = False
        return self
    
    def restart(self) -> 'Spider':
        """
        Restart spider by detach then attach.
        
        Returns:
            Self for chaining
        """
        return self.detach().attach()
    
    def clear(self) -> 'Spider':
        """
        Clear spider session (cookies, cache, etc).
        
        Returns:
            Self for chaining
        """
        self._do_clear()
        return self
    
    @abstractmethod
    def _do_attach(self):
        """Create connection. Implement in subclass."""
        pass
    
    @abstractmethod
    def _do_detach(self):
        """Close connection. Implement in subclass."""
        pass
    
    @abstractmethod
    def _do_clear(self):
        """Clear session. Implement in subclass."""
        pass
    
    @abstractmethod
    def get_driver(self) -> Any:
        """Get underlying driver instance. Implement in subclass."""
        pass
    
    def do_url(self, url: str, **kwargs) -> Any:
        """
        Universal URL operation method.
        
        Optional method for spiders that work with URLs.
        Subclasses can implement with retry, HTTP methods, auto_raise, etc.
        
        Args:
            url: Target URL
            **kwargs: Implementation-specific parameters
                     (e.g., http_method, retry, auto_raise)
            
        Returns:
            Implementation-specific response or None
        """
        return None
