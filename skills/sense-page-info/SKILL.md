---
name: sense-page-info
description: Analyze page_info data to understand interactive elements. Use after scout or action to find buttons, links, selectors.
---

# Sense Page Info

> 分析 page_info 数据，理解页面交互元素。

## When to Use
- scout 或 action 后需要分析交互元素
- 需要找到按钮、链接、输入框的选择器
- 需要确定是否有动态加载按钮

---

## 获取 page_info

```python
# 在 action 步骤中
page_info = context.spider.get_page_info()
```

输出保存在: `output/xxx_action_*/task1_action.json`

```bash
cat output/xxx_action_*/task1_action.json
```

---

## 数据结构

```json
{
  "title": "Page Title",
  "url": "https://example.com",
  "elements": [
    {
      "index": 1,
      "role": "button",
      "name": "Load More",
      "tag": "button",
      "css": ".load-more-btn",
      "xpath": "//button[@class='load-more-btn']",
      "attributes": {"class": "load-more-btn", "id": "loadMore"},
      "position": {"x": 100, "y": 500, "width": 80, "height": 40}
    },
    {
      "index": 2,
      "role": "link",
      "name": "Product A",
      "tag": "a",
      "css": "a.product-link",
      "attributes": {"href": "/product/1", "class": "product-link"}
    }
  ]
}
```

---

## 分析清单

| 检查项 | 问题 | 决策 |
|--------|------|------|
| **元素数量** | 找到多少交互元素？ | 太少可能需要滚动 |
| **按钮类型** | 有 "Load More" / "Show All" 吗？ | 有 → action 需要点击 |
| **链接分布** | 产品/文章链接的选择器？ | 记录 css/xpath 给 parse 用 |
| **输入框** | 有搜索/筛选框吗？ | 有 → 可能需要表单交互 |
| **位置信息** | 元素在页面什么位置？ | 底部 → 需要滚动 |

---

## 决策输出

分析后输出以下结论：

```markdown
### page_info 分析结论

**发现的交互元素**: 25个
**关键元素**:
- Load More 按钮: `.load-more-btn` (position.y=1200)
- 产品链接: `a.product-link` (共 20 个)
- 搜索框: `#search-input`

**Action 需要**:
- [ ] 滚动到底部
- [x] 点击 Load More 按钮
- [ ] 填写搜索框

**Parse 可用选择器**:
- 产品链接: `a.product-link`
- 产品标题: 需要结合 sense-clean-html 确定
```

---

## 常见模式

### 懒加载检测
```json
{"role": "button", "name": "Load More", "css": ".load-more"}
{"role": "button", "name": "Show All", "css": "#showAll"}
```
→ action 需要点击此按钮

### 分页检测
```json
{"role": "link", "name": "Next", "css": ".pagination .next"}
{"role": "link", "name": "2", "css": ".page-number"}
```
→ 需要增量任务或循环点击

### 登录检测
```json
{"role": "textbox", "name": "Username", "css": "#username"}
{"role": "textbox", "name": "Password", "css": "#password"}
```
→ 需要登录步骤

---

## Related Skills
- `sense-scout` - 侦察页面（调用此 skill）
- `sense-clean-html` - 分析 HTML 结构
- `write-action` - 基于分析编写 action
