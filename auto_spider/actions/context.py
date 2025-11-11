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
        - task: Task data dict for current scraping task
        - db: Database connection
        - config: Configuration object
        - cache: Cache component
    
    Dict fields are for business data.
    
    Example:
        task = {'name': 'fetch_baidu', 'url': 'https://baidu.com'}
        initial = {'db': db, 'cache': cache}
        context = Context(spider=my_spider, task=task, initial=initial)
        
        # attribute access (with IDE hints)
        url = context.task['url']
        content = context.spider.do_url(url)
        
        # dict access (flexible)
        context['html'] = content
    """
    
    def __init__(
        self,
        spider: Optional[Any] = None,
        task: Optional[dict] = None,
        initial: Optional[Any] = None,
        db: Optional[Any] = None,
        config: Optional[Any] = None,
        cache: Optional[Any] = None,
        **kwargs
    ):
        """
        Initialize context with system resources and business data.
        
        Args:
            spider: Spider instance
            task: Task dict
            initial: Initial resources object from initial_plan
            db: Database instance (deprecated)
            config: Config instance (deprecated)
            cache: Cache instance (deprecated)
            **kwargs: Business data
        """
        super().__init__(**kwargs)
        self.spider = spider
        self.task = task or {}
        self.initial = initial
        self.db = db
        self.config = config
        self.cache = cache
    
    def save_result(self, result: Any = None):
        """
        Save result to output directory.
        
        Args:
            result: Result to save (default: context['result'])
            
        Example:
            context['result'] = {'title': 'Example'}
            context.save_result()  # saves to output/task_name.json
        """
        if not self.initial or 'save_result' not in self.initial:
            raise RuntimeError("save_result not available in context.initial")
        
        if result is None:
            result = self.get('result')
        
        task_name = self.task.get('name', 'unnamed')
        self.initial['save_result'](task_name, result)
    
    def __repr__(self):
        resources = []
        if self.spider:
            resources.append(f"spider={type(self.spider).__name__}")
        if self.task:
            resources.append(f"task={self.task.get('name', 'unnamed')}")
        if self.db:
            resources.append(f"db={type(self.db).__name__}")
        if self.config:
            resources.append(f"config={type(self.config).__name__}")
        if self.cache:
            resources.append(f"cache={type(self.cache).__name__}")
        
        dict_items = dict(self)
        return f"Context({', '.join(resources)}, data={dict_items})"
