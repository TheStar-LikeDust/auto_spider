# 测试框架指南

简洁的三层 TDD 工作流：**Examples → Integrations → Unittests**

## 快速参考

| 操作 | 路径/命令 |
|--------|-------------|
| 示例文件 | `tests/examples/example_{feature}.py` |
| 函数名 | `{feature}_main()` |
| 输入数据 | `tests/data_input/example_{feature}.json` |
| 本地输入 | `tests/data_input_local/example_{feature}.json` |
| 输出文件 | `tests/data_output/example_{feature}_{timestamp}.json` |
| 加载输入 | `load()` |
| 加载输出 | `load_output("example_feature")` |
| 保存输出 | `save(data)` |

## TDD 开发流程

### 步骤 1: 编写示例（可执行演示）
在 `examples/` 中创建可运行的代码来演示功能。

### 步骤 2: 集成测试（验证输出）
编写集成测试来验证示例输出是否符合预期。

### 步骤 3: 单元测试（边界情况）
提取并测试单个函数的边界条件。

---

## 命名规范

### 文件名
- 示例文件：`example_{feature}.py`
- 函数名：`{feature}_main()`
- 输入数据：`data_input/example_{feature}.json`
- 本地输入：`data_input_local/example_{feature}.json`
- 输出文件：`data_output/example_{feature}_{timestamp}.json`

### 测试数据
- 输入文件：`data_input/*.json`（git 跟踪，空值）
- 本地文件：`data_input_local/*.json`（git 忽略，实际值）
- 所有 JSON 使用 2 空格缩进
- 保持数据最小化和聚焦
- 输入文件中不含敏感数据

---

## 目录结构

```
tests/
├── data_input/                      # Git 跟踪（默认测试数据）
│   ├── example_feature.json
│   ├── studio/                      # 支持嵌套文件夹
│   │   └── example_studio_login.json
│   └── README.md
├── data_input_local/                # Git 忽略（你的数据）
│   ├── example_feature.json
│   └── custom_folder/               # 文件可以在任意子目录中
│       └── example_test.json
├── data_output/                     # Git 忽略（自动生成）
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

### 递归文件搜索

**重要：** `load()` 函数会递归搜索 `data_input/` 和 `data_input_local/` 下的所有子目录。这意味着：

- 文件可以组织在嵌套的文件夹中（例如 `data_input/studio/example_login.json`）
- 文件可以移动或重命名而不会破坏搜索
- 如果存在多个同名文件，使用最近修改的那个
- 搜索只匹配文件名，不匹配完整路径

### Git 配置

添加到你的 `.gitignore`：

```gitignore
# Test data - local overrides and outputs
tests/data_input_local/
tests/data_output/
```

**注意：** `tests/data_input/*.json` 文件会被跟踪（项目默认测试数据）。

---

## 示例模板

`examples/example_feature.py` 的最小结构：

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

### 输入数据

创建 `data_input/example_feature.json`：

```json
{
  "param1": "",
  "param2": ""
}
```

### 关键点
- **函数名匹配模块名** - `example_feature.py` → `feature_main()`
- **不需要 docstring** - 代码本身说明一切
- **使用 `load()` 和 `save()`** - 自动处理路径
- **步骤注释** - 标记逻辑部分
- **无日志** - 保持示例简单快速

---

## 测试工具 (`test_tools.py`)

### 基本函数

**`load(filename="data.json", input_data_path=None)`**
- 递归搜索，按优先级：
  1. `data_input_local/**/{module}.json` （你的覆盖，任意子目录）
  2. `data_input/**/{module}.json` （标准，任意子目录）
  3. `--input-data` CLI 参数（JSON 字符串）
- 支持嵌套文件夹 - 文件可以在任意子目录中
- 如果找到多个匹配文件，使用最近修改的文件

**`save(data, filename=None, save_data_path=None)`**
- 自动生成路径：`data_output/{module}_{timestamp}.json`
- 如果提供 `--output` CLI 参数则使用，否则使用模块名

**`load_output(pattern=None, latest=True)`**
- 加载之前的输出，从 `data_output/` 目录
- Pattern 默认为调用者模块名
- Latest=True 加载最新文件（按时间戳）

### 路径优先级

```
加载优先级（递归搜索）：
  data_input_local/**/{module}.json  ← 你的修改（覆盖所有，任意文件夹）
        ↓
  data_input/**/{module}.json        ← 标准输入（git 跟踪，任意文件夹）
        ↓
  --input-data                       ← CLI JSON 字符串（回退）

保存位置：
  data_output/{module}_{timestamp}.json  ← 自动生成带时间戳
```

**注意：** `**` 模式表示递归搜索所有子目录。文件可以组织在 `studio/`、`api/` 等文件夹中。

### CLI 参数

```bash
# 使用 JSON 字符串输入
python tests/examples/example_feature.py --input-data '{"key": "value"}'

# 自定义输出文件名
python tests/examples/example_feature.py --output my_result

# 组合使用
python tests/examples/example_feature.py --input-data '{"test": 1}' --output result
```

### 设置工作流

```bash
# 1. 复制到本地
cp tests/data_input/example_feature.json tests/data_input_local/example_feature.json

# 2. 编辑填入实际值
vim tests/data_input_local/example_feature.json

# 3. 运行示例
python tests/examples/example_feature.py

# 4. 检查输出
ls tests/data_output/
```

### 流水线示例

使用 `load_output()` 串联多个示例：

```python
# example_step2.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.test_tools import load, load_output, save

def step2_main():
    input_data = load()
    step1_result = load_output("example_step1")
    
    # Step 1: 合并输入
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

## 集成测试与单元测试

### 集成测试
验证示例产生预期的输出。

```python
# tests/integrations/test_example_feature.py
import subprocess
from tests.test_tools import load_output

def test_feature_output():
    # 运行示例
    result = subprocess.run(
        ["python", "tests/examples/example_feature.py",
         "--input-data", '{"param1":"test","param2":"value"}'],
        capture_output=True
    )
    
    # 加载并检查输出
    output = load_output("example_feature")
    print(f"Output: {output}")
```

### 单元测试
测试带有边界情况的单个函数。

```python
# tests/unittests/test_feature.py
def test_function_edge_case():
    result = process_data(None)
    print(f"Result: {result}")
```

保持测试简单且聚焦。

---

## 常见问题

### FileNotFoundError: No input found

**问题：** `load()` 找不到输入文件

**解决方法：**
1. 复制到本地：`cp tests/data_input/example_feature.json tests/data_input_local/example_feature.json`
2. 使用 CLI：`--input-data '{"key":"value"}'`
3. 检查文件名是否匹配模块名

### No output files found

**问题：** `load_output()` 找不到之前的输出

**解决方法：**
1. 先运行示例生成输出
2. 检查 pattern 是否完全匹配模块名
3. 验证文件存在：`ls tests/data_output/`

### Import errors

**问题：** 无法导入项目模块

**解决方法：** 在示例文件中添加路径设置：
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

---

## 核心原则

1. **KISS** - 简单代码胜过聪明代码
2. **Let it fail** - 不要过度验证，让自然错误显现
3. **Modularity** - 小函数，清晰目的
4. **Determinism** - 通过种子/模拟实现可重现结果
