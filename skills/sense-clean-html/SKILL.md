---
name: sense-clean-html
description: Analyze cleaned HTML to understand DOM structure. Use after action to find XPath patterns for parse step.
---

# Sense Clean HTML

> 分析清洗后的 HTML，理解 DOM 结构，推导 XPath。

## When to Use
- action 后需要分析页面结构
- 需要确定 XPath/CSS 选择器给 parse 用
- page_info 不足以确定数据位置

---

## 获取 clean_html

```python
from auto_spider.tools.html_cleaner import clean_html

# 读取 action 输出的 HTML
with open('output/xxx_action_*/task1.html') as f:
    raw_html = f.read()

result = clean_html(raw_html)

# 返回字典
result['html']   # 清洗后的完整 HTML
result['body']   # 只有 body 内容（推荐分析用）
result['text']   # 纯文本内容
```

---

## 清洗规则

**默认移除**:
- script, style, meta, svg, link, noscript, iframe
- HTML 注释
- 空的 div/span 包装器

**保留属性**:
- id, class, href, src, alt, title, name, type, value, placeholder

---

## 分析方法

### Step 1: 查看 body 结构

```python
print(result['body'][:2000])  # 前 2000 字符
```

### Step 2: 找到重复模式

列表页通常有重复的容器：

```html
<div class="product-card">
  <h2 class="title">Product A</h2>
  <span class="price">$99</span>
  <a href="/product/1">View</a>
</div>
<div class="product-card">
  <h2 class="title">Product B</h2>
  <span class="price">$149</span>
  <a href="/product/2">View</a>
</div>
```

### Step 3: 推导 XPath

| 目标数据 | XPath |
|---------|-------|
| 所有产品容器 | `//div[@class='product-card']` |
| 产品标题 | `//div[@class='product-card']//h2/text()` |
| 产品价格 | `//div[@class='product-card']//span[@class='price']/text()` |
| 产品链接 | `//div[@class='product-card']//a/@href` |

---

## 分析清单

| 检查项 | 问题 | 输出 |
|--------|------|------|
| **容器标签** | 列表项用什么标签包裹？ | div/li/article |
| **容器选择器** | 容器的 class/id？ | `.product-card` |
| **数据字段** | 需要提取哪些字段？ | title, price, url |
| **字段位置** | 每个字段在容器内的路径？ | XPath 表达式 |
| **嵌套层级** | 数据嵌套多深？ | 影响 XPath 复杂度 |

---

## 决策输出

分析后输出以下结论：

```markdown
### clean_html 分析结论

**页面类型**: 产品列表页
**列表容器**: `div.product-list`
**列表项**: `div.product-card` (共 20 个)

**XPath 选择器**:
| 字段 | XPath | 示例值 |
|------|-------|--------|
| 标题 | `//div[@class='product-card']//h2/text()` | "Product A" |
| 价格 | `//div[@class='product-card']//span[@class='price']/text()` | "$99" |
| 链接 | `//div[@class='product-card']//a/@href` | "/product/1" |

**需要清洗**: 价格字段需要去除 "$" 符号
```

---

## XPath 技巧

### 文本提取变体
```python
# 直接子文本
//h2/text()

# 包含嵌套标签的所有文本
//h2//text()

# 获取整个元素（用于后续处理）
//h2
```

### 属性提取
```python
# 链接地址
//a/@href

# 图片地址
//img/@src

# 任意属性
//div/@data-id
```

### 条件过滤
```python
# 包含特定 class
//div[contains(@class, 'product')]

# 包含特定文本
//a[contains(text(), 'More')]

# 排除某些元素
//div[@class='product'][not(contains(@class, 'ad'))]
```

---

## Related Skills
- `sense-scout` - 侦察页面（调用此 skill）
- `sense-page-info` - 分析交互元素
- `write-parse` - 基于分析编写 parse
