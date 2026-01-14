---
name: iterate-next-step
description: Decide what to do next after verification (fix action/parse/extract, or move forward). Keywords: iterate, next step, decision tree, debug loop.
allowed-tools: Read, Grep, Glob, Bash
---

# Iterate Next Step

## When to Use
- After using `verify-step-output`
- Need to decide: fix current stage or move to next stage
- Need a simple debugging loop

## Decision Tree

1. Action output OK?
- No -> improve `action-step`, rerun action, re-verify
- Yes -> go next

2. Parse output OK?
- No -> improve `parse-step`, rerun parse, re-verify
- Yes -> go next

3. Extract side effects OK?
- No -> improve `extract-step`, rerun extract, re-verify
- Yes -> done

## Core Patterns

### If Action is wrong
- Add `wait_for_selector`
- Add scrolling for lazy loading
- Handle login

### If Parse is wrong
- Test XPath variants: `//h1/text()` vs `//h1//text()`
- Dump intermediate debug fields into `context['result']`

### If Extract is wrong
- Print received parse result
- Validate DB connection/config

## Related Skills
- `verify-step-output`
- `action-step`
- `parse-step`
- `extract-step`
