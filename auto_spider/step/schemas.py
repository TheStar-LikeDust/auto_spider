"""
Data schemas for auto_spider pipeline.

Type hierarchy:
    Task (ActionInput)
      ↓
    ActionResult (ParseInput)  
      ↓
    ParseResult (ExtractInput)

Each stage's Result becomes next stage's Input.
"""

from urllib.parse import urlparse


# ============================================================================
# Task name generation utility
# ============================================================================

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


# ============================================================================
# Core pipeline classes
# ============================================================================

class Task(dict):
    """
    Task dict for action step input.
    
    Also serves as ActionInput in the pipeline.
    Name field is optional and auto-generated if not provided.
    Hashable for deduplication.
    
    Example:
        task = Task(url='https://baidu.com', retry=3)
        context['input'] = task
        context['task'] = task
        task['url']  # access
        hash(task)  # compute hash for deduplication
    """
    
    def __init__(self, **kwargs):
        """Initialize task with keyword arguments."""
        super().__init__(**kwargs)
    
    def __hash__(self):
        """Compute hash from sorted items for deduplication."""
        items = tuple(sorted(self.items()))
        return hash(items)
    
    def __eq__(self, other):
        """Check equality for deduplication."""
        if not isinstance(other, (Task, dict)):
            return False
        return dict(self) == dict(other)
    
    def __repr__(self):
        name = self.get('name') or self.get('url', 'task')
        if isinstance(name, str) and len(name) > 30:
            name = name[:30] + '...'
        return f"Task({len(self)} fields, primary={name})"


class ActionResult(dict):
    """
    Action stage result (also serves as ParseInput).
    
    Standard fields:
        result: Action result dict (metadata, status, etc.)
        content: Raw HTML/text content
    
    This is both:
        - Action stage output
        - Parse stage input (ParseInput = ActionResult)
    
    Example:
        # Action stage saves
        context['result'] = {'status': 200, 'item_id': 1001}
        context['content'] = '<html>...</html>'
        # → saves to: task.json (result) + task.html (content)
        
        # Parse stage loads as ParseInput
        action_result = ActionResult(
            result={'status': 200, 'item_id': 1001},
            content='<html>...</html>'
        )
        context['input'] = action_result['result']
        context['content'] = action_result['content']
    """
    
    def __repr__(self):
        has_result = 'result' in self
        has_content = 'content' in self
        return f"ActionResult(result={has_result}, content={has_content})"


class ParseResult(ActionResult):
    """
    Parse stage result (also serves as ExtractInput).
    
    Inherits from ActionResult, adds parse-specific fields.
    
    Standard fields:
        result: Parse result dict (parsed structured data)
        content: Raw HTML/text content (from action, read-only)
        action_input: Original action input (for tracing)
        
    This is both:
        - Parse stage output
        - Extract stage input (ExtractInput = ParseResult)
    
    Example:
        # Parse stage saves
        context['result'] = {'title': 'Example', 'links': [...]}
        # → saves to: task.json (result)
        
        # Extract stage loads as ExtractInput
        parse_result = ParseResult(
            result={'title': 'Example', 'links': [...]},
            content='<html>...</html>',
            action_input=Task(url='...')
        )
        context['input'] = parse_result['result']
        context['content'] = parse_result['content']
    """
    
    def __repr__(self):
        has_result = 'result' in self
        has_content = 'content' in self
        has_action_input = 'action_input' in self
        return f"ParseResult(result={has_result}, content={has_content}, action_input={has_action_input})"


# ============================================================================
# Type aliases for clarity
# ============================================================================

# Input aliases (for type hints and clarity)
ActionInput = Task          # Action stage input
ParseInput = ActionResult   # Parse stage input
ExtractInput = ParseResult  # Extract stage input


# ============================================================================
# Backward compatibility classes (deprecated)
# ============================================================================

class TaskResult(dict):
    """
    TaskResult dict for parse step (deprecated, use ActionResult).
    
    Kept for backward compatibility only.
    
    Example:
        result = TaskResult(
            task_name='example_com',
            content='<html>...</html>',
            source_dir='output/plan_action_20241112_100000'
        )
    """
    
    def __init__(self, **kwargs):
        """
        Initialize TaskResult.
        
        Common fields:
            task_name: Name of the task
            content: Raw content from action step
            source_dir: Source output directory
            file_path: Source file path
        """
        super().__init__(**kwargs)
    
    def __repr__(self):
        task_name = self.get('task_name', 'unknown')
        content_len = len(str(self.get('content', '')))
        return f"TaskResult(task={task_name}, content_size={content_len} bytes)"


class TaskData(dict):
    """
    TaskData dict for extract step (deprecated, use ParseResult).
    
    Kept for backward compatibility only.
    
    Example:
        data = TaskData(
            task_name='example_com',
            parsed_data={'title': 'Example', 'links': [...]},
            source_dir='output/plan_parse_20241112_100100'
        )
    """
    
    def __init__(self, **kwargs):
        """
        Initialize TaskData.
        
        Common fields:
            task_name: Name of the task
            parsed_data: Structured data from parse step
            source_dir: Source output directory
            file_path: Source file path
        """
        super().__init__(**kwargs)
    
    def __repr__(self):
        task_name = self.get('task_name', 'unknown')
        data_keys = list(self.get('parsed_data', {}).keys()) if isinstance(self.get('parsed_data'), dict) else []
        return f"TaskData(task={task_name}, fields={data_keys})"
