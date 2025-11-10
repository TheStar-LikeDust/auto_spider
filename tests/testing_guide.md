# Testing Framework Guide

Simple three-layer TDD workflow: **Examples → Integrations → Unittests**

## Quick Reference

| Action | Path/Command |
|--------|-------------|
| Example file | `tests/examples/example_{feature}.py` |
| Function name | `{feature}_main()` |
| Input data | `tests/data_input/example_{feature}.json` |
| Local input | `tests/data_input_local/example_{feature}.json` |
| Output file | `tests/data_output/example_{feature}_{timestamp}.json` |
| Load input | `load()` |
| Load output | `load_output("example_feature")` |
| Save output | `save(data)` |

## TDD Development Flow

### Step 1: Write Example (Executable Demo)
Create runnable code in `examples/` that demonstrates the feature.

### Step 2: Integration Test (Verify Output)
Write integration tests to verify example outputs match expectations.

### Step 3: Unit Tests (Edge Cases)
Extract and test individual functions with boundary conditions.

---

## Naming Conventions

### File Names
- Example files: `example_{feature}.py`
- Function name: `{feature}_main()`
- Input data: `data_input/example_{feature}.json`
- Local input: `data_input_local/example_{feature}.json`
- Output: `data_output/example_{feature}_{timestamp}.json`

### Test Data
- Input files: `data_input/*.json` (git tracked, empty values)
- Local files: `data_input_local/*.json` (git ignored, actual values)
- All JSON use 2-space indentation
- Keep data minimal and focused
- No sensitive data in input files

---

## Directory Structure

```
tests/
├── data_input/                      # Git-tracked (default test data)
│   ├── example_feature.json
│   ├── studio/                      # Supports nested folders
│   │   └── example_studio_login.json
│   └── README.md
├── data_input_local/                # Git ignored (your data)
│   ├── example_feature.json
│   └── custom_folder/               # Files can be in any subdirectory
│       └── example_test.json
├── data_output/                     # Git ignored (auto-generated)
│   ├── example_feature_20251030_110530.json
│   └── example_feature_20251030_112015.json
├── examples/
│   ├── example_feature.py
│   └── example_step2.py
├── integrations/
│   └── test_example_feature.py
├── unittests/
│   └── test_feature.py
└── test_tools.py
```

### Recursive File Search

**Important:** The `load()` function recursively searches through all subdirectories in `data_input/` and `data_input_local/`. This means:

- Files can be organized in nested folders (e.g., `data_input/studio/example_login.json`)
- Files can be moved or renamed without breaking the search
- If multiple files with the same name exist, the most recently modified one is used
- The search only matches the filename, not the full path

### Git Configuration

Add to your `.gitignore`:

```gitignore
# Test data - local overrides and outputs
tests/data_input_local/
tests/data_output/
```

**Note:** `tests/data_input/*.json` files are tracked (default test data).

---

## Example Template

Minimal structure for `examples/example_feature.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.test_tools import load, save


def feature_main():
    input_data = load()
    
    # Step 1: Process data
    param1 = input_data.get('param1')
    param2 = input_data.get('param2')
    
    # Step 2: Generate output
    output_data = {
        "result": f"{param1}_{param2}",
        "status": "success"
    }
    
    save(output_data)


if __name__ == "__main__":
    feature_main()
```

### Input Data

Create `data_input/example_feature.json`:

```json
{
  "param1": "",
  "param2": ""
}
```

### Key Points
- **Function name matches module** - `example_feature.py` → `feature_main()`
- **No docstrings needed** - code speaks for itself
- **Use `load()` and `save()`** - handles paths automatically
- **Step comments** - mark logical sections
- **No logging** - keep examples simple and fast

---

## Test Tools (`test_tools.py`)

### Basic Functions

**`load(filename="data.json", input_data_path=None)`**
- Recursively searches in priority order:
  1. `data_input_local/**/{module}.json` (your overrides, any subdirectory)
  2. `data_input/**/{module}.json` (standard, any subdirectory)
  3. `--input-data` CLI argument (JSON string)
- Supports nested folders - files can be in any subdirectory
- If multiple matches found, uses the most recently modified file

**`save(data, filename=None, save_data_path=None)`**
- Auto-generates path: `data_output/{module}_{timestamp}.json`
- Uses `--output` CLI arg if provided, else module name

**`load_output(pattern=None, latest=True)`**
- Load previous output from `data_output/`
- Pattern defaults to caller module name
- Latest=True loads most recent file (by timestamp)

### Path Priority

```
Load Priority (Recursive Search):
  data_input_local/**/{module}.json  ← Your modifications (overrides, any folder)
        ↓
  data_input/**/{module}.json        ← Standard inputs (git tracked, any folder)
        ↓
  --input-data                       ← CLI JSON string (fallback)

Save Location:
  data_output/{module}_{timestamp}.json  ← Auto-generated with timestamp
```

**Note:** The `**` pattern means recursive search through all subdirectories. Files can be organized in folders like `studio/`, `api/`, etc.

### CLI Arguments

```bash
# Use JSON string input
python tests/examples/example_feature.py --input-data '{"key": "value"}'

# Custom output filename
python tests/examples/example_feature.py --output my_result

# Combined
python tests/examples/example_feature.py --input-data '{"test": 1}' --output result
```

### Setup Workflow

```bash
# 1. Copy to local
cp tests/data_input/example_feature.json tests/data_input_local/example_feature.json

# 2. Edit with actual values
vim tests/data_input_local/example_feature.json

# 3. Run example
python tests/examples/example_feature.py

# 4. Check output
ls tests/data_output/
```

### Pipeline Example

Chain multiple examples using `load_output()`:

```python
# example_step2.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.test_tools import load, load_output, save

def step2_main():
    input_data = load()
    step1_result = load_output("example_step1")
    
    # Step 1: Combine inputs
    combined_data = {
        "input": input_data,
        "previous": step1_result,
        "status": "processed"
    }
    
    save(combined_data)

if __name__ == "__main__":
    step2_main()
```

---

## Integration & Unit Tests

### Integration Tests
Verify examples produce expected outputs.

```python
# tests/integrations/test_example_feature.py
import subprocess
from tests.test_tools import load_output

def test_feature_output():
    # Run example
    result = subprocess.run(
        ["python", "tests/examples/example_feature.py",
         "--input-data", '{"param1":"test","param2":"value"}'],
        capture_output=True
    )
    
    # Load and check output
    output = load_output("example_feature")
    print(f"Output: {output}")
```

### Unit Tests
Test individual functions with edge cases.

```python
# tests/unittests/test_feature.py
def test_function_edge_case():
    result = process_data(None)
    print(f"Result: {result}")
```

Keep tests simple and focused.

---

## Troubleshooting

### FileNotFoundError: No input found

**Problem:** `load()` cannot find input file

**Solutions:**
1. Copy to local: `cp tests/data_input/example_feature.json tests/data_input_local/example_feature.json`
2. Use CLI: `--input-data '{"key":"value"}'`
3. Check file name matches module name

### No output files found

**Problem:** `load_output()` cannot find previous output

**Solutions:**
1. Run the example first to generate output
2. Check pattern matches module name exactly
3. Verify files exist: `ls tests/data_output/`

### Import errors

**Problem:** Cannot import project modules

**Solution:** Add path setup in example file:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

---

## Key Principles

1. **KISS** - Simple code over clever code
2. **Let it fail** - Don't over-validate, let natural errors show
3. **Modularity** - Small functions, clear purposes
4. **Determinism** - Reproducible results with seeds/mocks
