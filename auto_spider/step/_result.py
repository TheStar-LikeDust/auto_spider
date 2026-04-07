"""
Result class for step execution output.
"""


class Result(dict):
    """
    Step execution result. Used by all stage types (action, parse, extract).

    Standard fields:
        index: Task sequence number
        task: Original task dict
        stage: Stage name ('action', 'parse', 'extract')
        error: Error message (only present on failure)

    Stage-specific fields:
        action: result, content
        parse: action_result, result, content

    Example:
        result = Result(index=1, task={'url': '...'}, stage='action',
                        result={'status': 200}, content='<html>...</html>')
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def index(self):
        return self.get('index')

    @property
    def task(self):
        return self.get('task', {})

    @property
    def stage(self):
        return self.get('stage')

    @property
    def is_success(self):
        return 'error' not in self

    @property
    def error(self):
        return self.get('error')

    def __repr__(self):
        status = 'ok' if self.is_success else f'error={self.error}'
        return f"Result(index={self.index}, stage={self.stage}, {status})"
