---
name: strategy
description: Define target and strategy before formal data collection. Progressive approach with fallback options.
---

# Strategy

> 记录对任务的思考和决策。目标、策略、反思。

## 与 Log 的区分

| 文档 | 文件名 | 内容 |
|------|--------|------|
| **Log** | `TASK_{name}_log.md` | 执行步骤记录（做了什么） |
| **Strategy** | `TASK_{name}_strategy.md` | 思考和决策记录（为什么这样做） |

**一致性要求**：
- 任务名称 `{name}` 必须相同
- 两个文档同步创建
- 递增式追加，不修改已有内容

## When to Use
- Sense 完成后，准备正式采集
- 需要明确采集目标和方法
- 需要制定失败后的备选方案

---

## 核心流程

```
1. 明确目标
      ↓
2. 制定策略（从简单开始）
      ↓
3. 执行并验证
      ↓
4. 失败？尝试下一个方案
      ↓
5. 成功？记录方案，继续下一步
```

---

## Step 1: 明确目标

在开始之前，明确要采集什么：

```markdown
### 采集目标

**页面**: UCI 专业目录
**URL**: https://example.com/courses/

**目标数据**:
- 专业名称
- 专业类型（B.A./B.S./Minor）
- 详情链接

**预期数量**: ~170 个专业
```

---

## Step 2: 制定策略

基于 sense 报告，制定策略（从简单到复杂）：

```markdown
### 采集策略

**方案 A（首选）**: RequestSpider + XPath
- 依据: sense 报告显示 HTML 已包含 396 个链接
- 步骤: 直接请求页面 → XPath 提取

**方案 B（备选）**: Playwright + XPath
- 触发条件: 方案 A 提取数据为空
- 步骤: 渲染页面 → XPath 提取

**方案 C（最后）**: Playwright + 点击展开
- 触发条件: 方案 B 数据不完整
- 步骤: 渲染页面 → 点击展开按钮 → XPath 提取
```

---

## Step 3: 执行并验证

每个方案执行后都要验证：

```python
# scripts/verify_result.py
"""验证采集结果"""
import json
from pathlib import Path

def verify(expected_count, expected_fields):
    f = sorted(Path('output').glob('parse_*/task1_parse.json'))[-1]
    data = json.loads(f.read_text(encoding='utf-8'))
    
    # check count
    actual_count = len(data) if isinstance(data, list) else 1
    print(f"Count: {actual_count} / {expected_count}")
    
    # check fields
    if isinstance(data, list) and data:
        sample = data[0]
        for field in expected_fields:
            has_field = field in sample
            print(f"Field '{field}': {'✓' if has_field else '✗'}")
    
    return actual_count >= expected_count * 0.9  # 90% threshold

if __name__ == '__main__':
    ok = verify(
        expected_count=170,
        expected_fields=['name', 'type', 'url']
    )
    print(f"\nResult: {'PASS' if ok else 'FAIL'}")
```

---

## Step 4: 失败处理

失败时的处理流程：

```
方案 A 失败
    ↓
分析原因（数据为空？格式错误？）
    ↓
尝试方案 B
    ↓
方案 B 失败
    ↓
分析原因
    ↓
尝试方案 C
    ↓
所有方案失败
    ↓
重新 sense，调整策略
```

---

## 策略文档模板

```markdown
# {name} 采集策略

- **创建时间**: YYYY-MM-DD HH:MM
- **最后更新**: YYYY-MM-DD HH:MM

## 目标
- **页面**: [URL]
- **目标数据**: [字段列表]
- **预期数量**: [N 条]

## Sense 结论
- 二级 URI: [数量]
- 目标字段: [存在情况]

## 策略

### 方案 A: [名称]
- **方法**: [具体步骤]
- **XPath**: [选择器]
- **验证**: [预期结果]

### 方案 B: [名称]
- **触发条件**: [何时使用]
- **方法**: [具体步骤]

---

## 更新记录

### Update 1: YYYY-MM-DD HH:MM
**原因**: [为什么更新]
**改动**: [改了什么]
**反思**: [学到了什么]

---

## 最终方案
[成功的方案及原因]
```

---

## 示例：UCI 专业采集

```markdown
# uci_majors 采集策略

- **创建时间**: 2024-01-15 10:30
- **最后更新**: 2024-01-15 11:45

## 目标
- **页面**: https://example.com/courses/
- **目标数据**: 专业名称、类型、链接
- **预期数量**: ~170 个

## Sense 结论
- HTML 中找到 396 个链接
- 包含 "major" 245 次, "B.A." 89 次

## 策略

### 方案 A: RequestSpider + XPath
- **方法**: 直接 GET 请求，XPath 提取
- **XPath**: `//div[@class='toggle-content']//a`
- **验证**: 提取数量 >= 150

### 方案 B: Playwright 渲染
- **触发条件**: 方案 A 提取为空
- **方法**: Playwright 渲染后提取

---

## 更新记录

### Update 1: 2024-01-15 11:00
**原因**: 方案 A 执行失败，提取数量为 0
**改动**: 检查发现 XPath 错误，应该是 `//div[contains(@class,'toggle')]//a`
**反思**: 需要先用 sense 确认实际 HTML 结构

### Update 2: 2024-01-15 11:45
**原因**: 修正 XPath 后重新执行
**改动**: 方案 A 成功
**反思**: 静态 HTML 已包含数据，无需 Playwright

---

## 最终方案
方案 A 成功。数据在静态 HTML 中已存在，无需 JS 渲染。
```

---

## Related Skills
- `sense` - 感知数据存在性
- `write-action` - 实现具体方案
- `write-parse` - 实现数据提取
- `log-task` - 记录执行过程
