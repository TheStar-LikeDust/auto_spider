"""
Context class for action pipeline.

Provides both attribute access (with IDE hints) and dict flexibility.
"""

from typing import Any, Optional


class Context(dict):
    """
    Action pipeline context with system resources as attributes.
    
    System resources (fixed attributes):
        - spider: Spider component for web access
        - db: Database connection
        - config: Configuration object
        - cache: Cache component
    
    Business data (dict access):
        - Use dict methods for flexible business data
        - context['url'], context['prev_result'], etc.
    
    Example:
        context = Context(spider=my_spider, url='https://example.com')
        
        # attribute access (with IDE hints)
        content = context.spider.get(context['url'])
        
        # dict access (flexible)
        context['data'] = 'value'
        prev = context.get('prev_result')
    """
    
    def __init__(
        self,
        spider: Optional[Any] = None,
        db: Optional[Any] = None,
        config: Optional[Any] = None,
        cache: Optional[Any] = None,
        **kwargs
    ):
        """
        Initialize context with system resources and business data.
        
        Args:
            spider: Spider component for web access
            db: Database connection
            config: Configuration object
            cache: Cache component
            **kwargs: Business data as dict items
        """
        super().__init__(**kwargs)
        self.spider = spider
        self.db = db
        self.config = config
        self.cache = cache
    
    def __repr__(self):
        resources = []
        if self.spider:
            resources.append(f"spider={type(self.spider).__name__}")
        if self.db:
            resources.append(f"db={type(self.db).__name__}")
        if self.config:
            resources.append(f"config={type(self.config).__name__}")
        if self.cache:
            resources.append(f"cache={type(self.cache).__name__}")
        
        dict_items = dict(self)
        return f"Context({', '.join(resources)}, data={dict_items})"
