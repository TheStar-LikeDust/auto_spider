"""
Task data structure for action step.

Input for action step.
"""

from urllib.parse import urlparse


def generate_task_name(task: dict, index: int = None) -> str:
    """
    Generate task name from task dict.
    
    Args:
        task: Task dict
        index: Optional task index
        
    Returns:
        Generated task name
    """
    # use explicit name if provided
    if 'name' in task and task['name']:
        return str(task['name'])
    
    # generate from url
    if 'url' in task:
        url = str(task['url'])
        # extract domain or path
        parsed = urlparse(url)
        if parsed.netloc:
            # use domain as name
            name = parsed.netloc.replace('www.', '').replace('.', '_')
        elif parsed.path:
            # use path as name
            name = parsed.path.strip('/').replace('/', '_')
        else:
            name = 'task'
        
        # limit length
        if len(name) > 50:
            name = name[:50]
        
        return name
    
    # use index if available
    if index is not None:
        return f'task{index}'
    
    # fallback
    return 'task'


class Task(dict):
    """
    Task dict for action step.
    
    Name field is optional and auto-generated if not provided.
    
    Example:
        task = Task(url='https://baidu.com')
        task['url']  # access
        task.get('retry', 1)  # dict method
    """
    
    def __init__(self, **kwargs):
        """Initialize task with keyword arguments."""
        super().__init__(**kwargs)
    
    def __repr__(self):
        # generate name from url or first field
        name = self.get('name') or self.get('url', 'task')
        if isinstance(name, str) and len(name) > 30:
            name = name[:30] + '...'
        return f"Task({len(self)} fields, primary={name})"
