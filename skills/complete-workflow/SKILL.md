---
name: complete-workflow
description: End-to-end workflow: scout -> generate -> action -> verify -> iterate -> parse -> extract. Keywords: workflow, end-to-end, pipeline.
allowed-tools: Read, Grep, Glob, Bash
---

# Complete Workflow

## When to Use
- Need the full step-by-step workflow
- Want to onboard quickly to Auto Spider

## Workflow

### 1) Scout
Use `scout-webpage` to collect selectors and understand loading behavior.

### 2) Generate Plan
Use `generate-plan` to scaffold files.

### 3) Implement Action
Use `action-step` to download HTML and save `context['content']`.

### 4) Verify + Iterate
Use `verify-step-output` then `iterate-next-step`.

### 5) Implement Parse
Use `parse-step` to extract structured data into `context['result']`.

### 6) Implement Extract
Use `extract-step` to persist data.

### 7) Run
Use `config-and-run` to run stages.

## Related Skills
- `scout-webpage`
- `generate-plan`
- `action-step`
- `parse-step`
- `extract-step`
- `verify-step-output`
- `iterate-next-step`
- `config-and-run`
