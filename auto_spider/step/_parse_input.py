"""
ParseInput class for parse step input.
"""

from typing import Any


class ParseInput(dict):
    """
    Parse stage input with action result data.

    Standard fields:
        action_input: ActionInput reference (Task)
        result: Action result dict (metadata, status, etc.)
        content: Raw HTML/text content

    Example:
        parse_input = ParseInput(
            action_input=Task(url='https://example.com'),
            result={'status': 200, 'item_id': 1001},
            content='<html>...</html>'
        )
        context['input'] = parse_input['result']
        context['content'] = parse_input['content']
    """

    def __init__(self, action_input: Any = None, result: Any = None, content: str = '', **kwargs):
        """
        Initialize ParseInput.

        Args:
            action_input: ActionInput reference (Task)
            result: Action result dict
            content: Raw HTML/text content
            **kwargs: Additional fields
        """
        super().__init__(**kwargs)
        if action_input is not None:
            self['action_input'] = action_input
        if result is not None:
            self['result'] = result
        if content:
            self['content'] = content

    def __repr__(self):
        has_action_input = 'action_input' in self
        has_result = 'result' in self
        has_content = 'content' in self
        return f"ParseInput(action_input={has_action_input}, result={has_result}, content={has_content})"
