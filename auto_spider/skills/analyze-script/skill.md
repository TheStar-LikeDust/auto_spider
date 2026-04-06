---
name: analyze-script
description: When analysis requires complex Python operations, create a standalone script file instead of inline code.
---

# Analyze Script

> 复杂分析操作应该拆出来作为独立脚本，而不是写在 plan 或 skill 中。

## When to Use
- 分析逻辑超过 10 行
- 需要复杂的数据处理（pandas/numpy）
- 需要可复用的分析代码
- 调试复杂的 XPath/正则

---

## 核心原则

**独立脚本的优势**：

| Plan 内联 | 独立脚本 |
|----------|----------|
| 难以调试 | 可单独运行调试 |
| 与流程耦合 | 可复用于不同项目 |
| 难以测试 | 可单元测试 |
| 分散在各处 | 集中管理 |

---

## 何时拆分为独立脚本

```
分析代码 > 10 行？
   ↓
YES → 创建独立 .py 文件
   ↓
NO  → 内联在 plan 或命令行中
```

---

## 独立脚本结构

```python
# scripts/analyze_xxx.py
"""
分析 XXX 数据

用法: python scripts/analyze_xxx.py
"""

from pathlib import Path

# 输入: scout 输出文件
INPUT_DIR = Path('output')

# 主要分析逻辑
def analyze():
    # 你的分析代码
    pass

if __name__ == '__main__':
    analyze()
```

---

## 示例场景

### 复杂 XPath 调试

```python
# scripts/debug_xpath.py
"""调试复杂 XPath 选择器"""

from pathlib import Path
from auto_spider.tools.xpath import xpath_extract

def test_xpath(html, xpath, desc):
    results = xpath_extract(html, xpath)
    print(f'{desc}: {len(results)} matches')
    for r in results[:3]:
        print(f'  {r[:50]}...' if len(str(r)) > 50 else f'  {r}')
    return results

if __name__ == '__main__':
    html = sorted(Path('output').glob('action_*/task1.html'))[-1].read_text(encoding='utf-8')
    
    # 测试多个 XPath
    test_xpath(html, '//div[@class="toggle-content"]//a/@href', '专业链接')
    test_xpath(html, '//div[@class="toggle-content"]//a/text()', '专业名称')
```

### 数据清洗和转换

```python
# scripts/clean_data.py
"""清洗和转换抓取的数据"""

import json
from pathlib import Path

def clean_major_data(raw_data):
    # 复杂的清洗逻辑
    cleaned = []
    for item in raw_data:
        # ... 20+ 行清洗代码
        cleaned.append(item)
    return cleaned

if __name__ == '__main__':
    data = json.loads(Path('output/parse_*/task1_parse.json').read_text())
    result = clean_major_data(data)
    Path('output/cleaned_data.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
```

---

## 文件组织建议

```
project/
├── myplan.py            # 主 plan
├── scripts/              # 独立分析脚本
│   ├── analyze_links.py
│   ├── debug_xpath.py
│   └── clean_data.py
└── output/               # 输出数据
```

---

## Related Skills
- `sense-scout` - 侦察页面
- `sense-clean-html` - 分析 HTML 结构
- `write-parse` - 编写 parse
