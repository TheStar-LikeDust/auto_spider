---
name: sense
description: Sense webpage data to check if target data exists. Output is a data existence report, not decisions.
---

# Sense

> 感知网页数据，检查目标数据是否存在。输出是数据存在性报告，不做决策。

## When to Use
- Scout 完成后，需要了解页面包含什么数据
- 检查目标数据（二级 URI、列表项、详情字段等）是否存在
- 为后续的 action/parse 提供数据基础

---

## 核心原则

**sense 只做感知，不做决策**

| sense 输出 | 不输出 |
|-------------|----------|
| “找到 168 个链接” | “应该用 RequestSpider” |
| “HTML 中包含专业名称” | “不需要点击” |
| “发现 Load More 按钮” | “需要写点击代码” |

---

## 数据源

模板自动生成三种数据：

| Key | 内容 | 用途 |
|-----|------|------|
| `markdown` | trafilatura 提取的主要内容 | 快速查看页面结构 |
| `cleaned_html` | 清理后的 HTML | 推导 XPath 选择器 |
| `page_info` | CDP 获取的交互元素 | 查看按钮/表单等 |

---

## 感知操作

感知操作应生成独立脚本，配合 `analyze-script` skill 使用。

### 示例：检查二级 URI

```python
# scripts/sense_links.py
"""感知: 检查页面中的链接"""
import json
import re
from pathlib import Path

def sense_links(pattern=None):
    """Check links in page data."""
    f = sorted(Path('output').glob('action_*/task1_action.json'))[-1]
    data = json.loads(f.read_text(encoding='utf-8'))
    
    # from markdown
    md = data.get('markdown', '')
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', md)
    
    # from cleaned_html
    html = data.get('cleaned_html', '')
    html_links = re.findall(r'<a [^>]*href="([^"]+)"[^>]*>([^<]*)</a>', html)
    
    # filter by pattern
    if pattern:
        md_links = [(t, u) for t, u in md_links if pattern in u]
        html_links = [(u, t) for u, t in html_links if pattern in u]
    
    return {
        'markdown_links': len(md_links),
        'html_links': len(html_links),
        'samples': md_links[:5] or html_links[:5]
    }

if __name__ == '__main__':
    result = sense_links(pattern='/major/')  # 根据目标调整
    print(f"Markdown links: {result['markdown_links']}")
    print(f"HTML links: {result['html_links']}")
    print("Samples:")
    for item in result['samples']:
        print(f"  {item}")
```

### 示例：检查目标字段

```python
# scripts/sense_fields.py
"""感知: 检查目标字段是否存在"""
import json
from pathlib import Path

def sense_fields(keywords):
    """Check if target fields exist in page data."""
    f = sorted(Path('output').glob('action_*/task1_action.json'))[-1]
    data = json.loads(f.read_text(encoding='utf-8'))
    
    md = data.get('markdown', '')
    html = data.get('cleaned_html', '')
    
    result = {}
    for kw in keywords:
        result[kw] = {
            'in_markdown': md.lower().count(kw.lower()),
            'in_html': html.lower().count(kw.lower()),
        }
    return result

if __name__ == '__main__':
    # 根据目标调整关键字
    keywords = ['major', 'minor', 'B.A.', 'B.S.', 'degree']
    result = sense_fields(keywords)
    for kw, counts in result.items():
        print(f"{kw}: markdown={counts['in_markdown']}, html={counts['in_html']}")
```

---

## 感知报告模板

sense 的输出是数据存在性报告：

```markdown
### 感知报告

**目标**: 专业信息

**二级 URI**:
- markdown 中找到: 168 个
- HTML 中找到: 396 个
- 样本: `/major/computer-science`, `/minor/data-science`

**目标字段**:
- "major": 245 次
- "B.A.": 89 次
- "B.S.": 102 次

**交互元素**:
- 按钮: 12 个
- 表单: 0 个
```

---

## Related Skills
- `analyze-script` - 感知操作生成独立脚本
- `strategy` - 基于感知结果制定策略
