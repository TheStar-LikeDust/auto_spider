---
name: extract-step
description: Write extract steps to persist parsed data to DB/files/APIs. Keywords: extract step, save to db, csv, json, persistence.
allowed-tools: Read, Grep, Glob, Bash
---

# Extract Step

## When to Use
- Persist parse results to database/files
- Send data to external APIs
- Do side-effect operations (downloads, writes)

## File Location

After `python -m auto_spider generate myplan`:
- Multi-file: `steps_myplan/extract.py`
- Single-file: `plan_myplan.py` (inline `@extract()` function)

## Core Patterns

### Default Template (generated)
```python
from auto_spider import extract, Context

@extract()
def save_data(context: Context):
    parse_result = context.get('input', {})
    save_to_database(parse_result)
```

### Save JSON File
```python
import json
from pathlib import Path

@extract()
def save_to_json(context: Context):
    parse_result = context.get('input', {})
    task_name = context.task.get('name', 'task')

    output_file = Path('data') / f"{task_name}.json"
    output_file.parent.mkdir(exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parse_result, f, ensure_ascii=False, indent=2)
```

### Append CSV
```python
import csv
from pathlib import Path

@extract()
def save_to_csv(context: Context):
    parse_result = context.get('input', {})
    items = parse_result.get('items', [])

    csv_file = Path('data') / 'output.csv'
    csv_file.parent.mkdir(exist_ok=True)

    file_exists = csv_file.exists()
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        if items:
            writer = csv.DictWriter(f, fieldnames=items[0].keys())
            if not file_exists:
                writer.writeheader()
            writer.writerows(items)
```

## Related Skills
- `verify-step-output`
- `iterate-next-step`
- `config-and-run`
