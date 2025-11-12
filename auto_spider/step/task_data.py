"""
TaskData data structure for extract step.

Input for extract step - represents parsed data to be extracted/saved.
"""


class TaskData(dict):
    """
    TaskData dict for extract step.
    
    Represents the parsed data from parse step that needs to be extracted/saved.
    Automatically loaded from latest parse output directory.
    
    Example:
        # Automatically created by scheduler when loading parse results
        data = TaskData(
            task_name='example_com',
            parsed_data={'title': 'Example', 'links': [...]},
            source_dir='output/plan_parse_20241112_100100'
        )
        
        # In extract step
        @extract()
        def save_to_db(context: Context):
            data = context['result']  # TaskData content
            # save to database...
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
