"""
Task class for step input.
"""


class Task(dict):
    """
    Task dict for step input. Hashable for deduplication.

    Example:
        task = Task(url='https://baidu.com', retry=3)
        hash(task)
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __hash__(self):
        items = tuple(sorted(self.items()))
        return hash(items)

    def __eq__(self, other):
        if not isinstance(other, (Task, dict)):
            return False
        return dict(self) == dict(other)

    def __repr__(self):
        name = self.get('name') or self.get('url', 'task')
        if isinstance(name, str) and len(name) > 30:
            name = name[:30] + '...'
        return f"Task({len(self)} fields, primary={name})"


ActionInput = Task
