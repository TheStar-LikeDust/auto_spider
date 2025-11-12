"""
Context class for step pipeline.

Provides both attribute access (with IDE hints) and dict flexibility.
"""

from typing import Any, Optional


class Context(dict):
    """
    Step pipeline context with system resources as attributes.
    
    System resources (fixed attributes):
        - spider: Spider component for web access
        - task: Task data dict for current scraping task
        - db: Database connection
        - config: Configuration object
        - cache: Cache component
    
    Dict fields are for business data.
    
    Example:
        task = {'url': 'https://baidu.com'}
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
        
        # internal step results storage
        self._step_results = {}  # {step_name: result}
        self._step_history = []  # [result1, result2, ...]
    
    def save_step_result(self, step_name: str, result: Any):
        """
        Save step result for later access.
        
        Args:
            step_name: Step function name
            result: Step result
        """
        self._step_results[step_name] = result
        self._step_history.append(result)
    
    def __getitem__(self, key):
        """
        Get item from context.
        
        Supports:
        - context['data']: normal dict access
        - context['step_name']: access step result by name (priority over dict)
        - context[-1]: access last step result
        - context[0]: access first step result
        
        Note: Integer keys are reserved for step history access.
        
        Args:
            key: Dict key (str) or step index (int)
            
        Returns:
            Value from dict or step result
        """
        if isinstance(key, int):
            # integer index: access step history
            if -len(self._step_history) <= key < len(self._step_history):
                return self._step_history[key]
            raise IndexError(f"Step index out of range: {key}")
        elif isinstance(key, str) and key in self._step_results:
            # string key: check step results first
            return self._step_results[key]
        else:
            # normal dict access (string key only)
            return super().__getitem__(key)
    
    def __contains__(self, key):
        """
        Check if key exists in context or step results.
        
        Args:
            key: Dict key or step name
            
        Returns:
            True if key exists
        """
        if isinstance(key, str) and key in self._step_results:
            return True
        return super().__contains__(key)
    
    def __repr__(self):
        return f"Context(steps={len(self._step_history)}, data_keys={list(self.keys())})"
