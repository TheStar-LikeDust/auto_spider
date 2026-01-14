---
name: verify-step-output
description: Verify output of action/parse/extract stages (HTML completeness, JSON structure, persistence). Keywords: verify output, check html, debug, missing fields.
allowed-tools: Read, Grep, Glob, Bash
---

# Verify Step Output

## When to Use
- After running action/parse/extract
- HTML is empty / missing target content
- Parsed fields are null/empty or structure is wrong
- Extract did not save data as expected

## Core Patterns

### Verify Action Output (HTML)
- Check `.html` exists and is not too small
- Search for target keywords

### Verify Parse Output (JSON)
- Check `*_parse.json` exists
- Confirm required keys exist and values look correct
- Confirm list lengths match expectations

### Verify Extract Output (side effects)
- Confirm database row count / files exist

## Examples

### Action: HTML too small
```bash
# if the file is very small, page likely not loaded
ls -lh output/myplan_action_*/task1.html
```

### Parse: fields are empty
```bash
cat output/myplan_parse_*/task1_parse.json
```

## Next Step
- If output is wrong -> use `iterate-next-step` to decide what to fix

## Related Skills
- `iterate-next-step`
- `action-step`
- `parse-step`
- `extract-step`
