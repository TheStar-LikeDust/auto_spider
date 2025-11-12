"""
TaskResult data structure for parse step.

Input for parse step - represents action step output to be parsed.
"""


class TaskResult(dict):
    """
    TaskResult dict for parse step.
    
    Represents the result from action step that needs to be parsed.
    Automatically loaded from latest action output directory.
    
    Example:
        # Automatically created by scheduler when loading action results
        result = TaskResult(
            task_name='example_com',
            content='<html>...</html>',
            source_dir='output/plan_action_20241112_100000'
        )
        
        # In parse step
        @parse()
        def parse_html(context: Context):
            html = context['result']  # TaskResult content
            # parse logic...
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
