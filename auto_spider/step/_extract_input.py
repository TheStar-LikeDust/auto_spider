"""
ExtractInput class for extract step input.
"""

from typing import Any


class ExtractInput(dict):
    """
    Extract stage input with parse result data.

    Standard fields:
        parse_input: ParseInput reference
        result: Parse result dict (parsed structured data)

    Example:
        extract_input = ExtractInput(
            parse_input=ParseInput(...),
            result={'title': 'Example', 'links': [...]}
        )
        context['input'] = extract_input['result']
    """

    def __init__(self, parse_input: Any = None, result: Any = None, **kwargs):
        """
        Initialize ExtractInput.

        Args:
            parse_input: ParseInput reference
            result: Parse result dict
            **kwargs: Additional fields
        """
        super().__init__(**kwargs)
        if parse_input is not None:
            self['parse_input'] = parse_input
        if result is not None:
            self['result'] = result

    def __repr__(self):
        has_parse_input = 'parse_input' in self
        has_result = 'result' in self
        return f"ExtractInput(parse_input={has_parse_input}, result={has_result})"
