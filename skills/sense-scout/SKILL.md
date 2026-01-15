---
name: sense-scout
description: Scout a new webpage to get selectors and structure. Use before writing action/parse steps.
---

# Sense Scout

> 侦察新页面，获取选择器和结构。编写 action/parse 前必须先侦察。

## When to Use
- 新页面需要抓取
- 需要 CSS/XPath 选择器
- 调试页面为什么为空

---

## 快速流程

```
1. 生成 scout plan
      ↓
2. 运行获取页面信息
      ↓
3. 分析 page_info (交互元素)
      ↓
4. 分析 clean_html (页面结构)
      ↓
5. 确定选择器和加载方式
```

---

## Step 1: 生成 Scout Plan

```bash
python -m auto_spider generate scout --single-file
```

## Step 2: 修改并运行

```python
@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    page = context.spider.get_driver()

    page.goto(url)
    page.wait_for_load_state('networkidle')

    # 获取页面信息
    page_info = context.spider.get_page_info()
    page.screenshot(path='output/scout_screenshot.png', full_page=True)

    context['content'] = page.content()
    context['result'] = {
        'url': url,
        'title': page_info.get('title'),
        'elements': page_info.get('elements', []),
    }
```

```bash
python plan_scout.py
```

---

## Step 3: 分析 page_info

### 什么是 page_info

`get_page_info()` 通过 CDP 获取页面所有交互元素（按钮、链接、输入框等）。

### 输出结构

```json
{
  "title": "Page Title",
  "elements": [
    {
      "index": 1,
      "role": "button",
      "name": "Load More",
      "tag": "button",
      "css": ".load-more-btn",
      "xpath": "//button[@class='load-more-btn']",
      "position": {"x": 100, "y": 500, "width": 80, "height": 40}
    },
    {
      "index": 2,
      "role": "link",
      "name": "Product A",
      "tag": "a",
      "css": "a.product-link",
      "attributes": {"href": "/product/1"}
    }
  ]
}
```

### 分析要点

| 检查项 | 关注点 |
|--------|--------|
| **元素数量** | 找到多少交互元素？ |
| **元素类型** | button/link/textbox 分布？ |
| **选择器质量** | css/xpath 是否足够具体？ |
| **动态加载** | 有 "Load More" 按钮吗？ |

### 决策输出

- 找到 "Load More" 按钮 → action 需要点击
- 找到产品链接 `.product-link` → parse 使用此选择器
- 元素位置在底部 → action 需要滚动

---

## Step 4: 分析 clean_html

### 什么是 clean_html

清洗 HTML，去除 script/style/注释等噪音，保留核心结构。

### 使用方法

```python
from auto_spider.tools.html_cleaner import clean_html

result = clean_html(raw_html)

# 返回字典
result['html']   # 清洗后的完整 HTML
result['body']   # 只有 body 内容
result['text']   # 纯文本内容
```

### 分析要点

| 检查项 | 关注点 |
|--------|--------|
| **DOM 结构** | 列表项的容器标签是什么？ |
| **嵌套层级** | 目标数据在哪个层级？ |
| **重复模式** | 哪些元素重复出现？ |

### XPath 推导

根据 clean_html 结构推导 XPath：

```python
# 产品列表
//div[@class='product-card']

# 产品标题
//div[@class='product-card']//h2/text()

# 产品链接
//div[@class='product-card']//a/@href
```

---

## Step 5: 查看原始 HTML（可选）

当 page_info 和 clean_html 不足以确定选择器时：

```bash
# 查看原始 HTML
cat output/scout_action_*/task1.html

# 搜索关键字
grep -n "product" output/scout_action_*/task1.html
```

---

## 变体：懒加载页面

```python
@action()
def scout_page(context: Context):
    page = context.spider.get_driver()
    page.goto(context.task['url'])

    # 滚动触发懒加载
    for _ in range(5):
        page.evaluate('window.scrollBy(0, 1000)')
        page.wait_for_timeout(500)

    page_info = context.spider.get_page_info()
    context['content'] = page.content()
    context['result'] = {'elements': page_info.get('elements', [])}
```

## 变体：需要登录

```python
@action()
def scout_page(context: Context):
    page = context.spider.get_driver()

    # 先登录
    page.goto('https://example.com/login')
    page.fill('#username', 'user')
    page.fill('#password', 'pass')
    page.click('#submit')
    page.wait_for_url('**/dashboard')

    # 再侦察
    page.goto(context.task['url'])
    page_info = context.spider.get_page_info()
    context['content'] = page.content()
    context['result'] = {'elements': page_info.get('elements', [])}
```

---

## Related Skills
- `sense-page-info` - 分析交互元素
- `sense-clean-html` - 分析 HTML 结构
- `write-action` - 基于侦察结果编写 action
- `write-parse` - 使用侦察得到的选择器
- `log-task` - 记录侦察结果
