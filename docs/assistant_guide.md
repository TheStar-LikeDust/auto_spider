# Auto Spider 助手指南

本文档指导AI助手如何使用框架完成爬取任务。

---

## 核心原则

**遇到新页面，先探索；一个 plan，一个目标。**

---

## 探索 Plan（侦查）

遇到任何新页面，先创建单文件探索plan获取HTML，分析页面结构后再决定下一步。

```bash
python -m auto_spider generate explore_xxx --single-file
```

修改 `initial_task()` 放入目标URL，在action中使用 `get_page_info()` 或 `clean_html()` 获取页面信息：

```python
@action()
def fetch_page(context: Context):
    content = context.spider.do_url(url)
    page_info = context.spider.get_page_info()  # 获取可交互元素
    context['content'] = content
    context['result'] = page_info
```

运行后查看 `output/action_*/` 下的文件，分析页面结构，确定数据位置和提取方式。

---

## Plan 设计

一个 plan 只做一件事，代表一次简单的人类操作：

| 场景 | Plan 拆分 |
|------|-----------|
| 目录页 → 详情页 | `plan_list` + `plan_detail` |
| 查询 → 结果 → 详情 | `plan_search` + `plan_result` + `plan_detail` |
| 登录 → 列表 → 详情 | `plan_login` + `plan_list` + `plan_detail` |

---

## 记录规范

每个 plan 创建对应的记录文档 `{plan_name}_crawl.md`：

```markdown
# {plan_name} 爬取记录

目标: [目标URL]
数据: [需要提取的数据描述]

---

## step1 - YYYYMMDD HH:MM

描述这一步做了什么，执行了什么命令，结果如何。用段落文字简洁描述，不需要拆分成多个子标题。

## step2 - YYYYMMDD HH:MM

下一步操作...
```

记录原则：简洁为主，用段落而不是大量列表；每步用 step1, step2 编号；记录关键结果和发现。

---

## 常见网页结构处理

### Toggle/折叠内容

页面使用 toggle 按钮控制内容展开，通常 HTML 中已包含所有内容（只是隐藏状态），可以直接用 XPath 提取：

```python
# 不需要点击展开，直接解析HTML
links = xpath_extract(content, '//div[@class="toggle-content"]//a/@href')
```

如果内容是动态加载的，需要先点击展开：

```python
page = context.spider.get_driver()
page.click('.toggle-button')
page.wait_for_selector('.toggle-content')
content = page.content()
```

### 分页

使用增量任务处理分页：

```python
@action()
def fetch_list(context: Context):
    url = context.task.get('url')
    page_num = context.task.get('page', 1)
    
    content = context.spider.do_url(f"{url}?page={page_num}")
    context['content'] = content
    
    if has_next_page(content) and page_num < 10:  # 限制最大页数
        context.tasks.append(Task(url=url, page=page_num + 1))
```

### 登录

在同一个 Spider 实例中先登录，再访问需要登录的页面：

```python
@action()
def login_and_fetch(context: Context):
    page = context.spider.get_driver()
    
    page.goto('https://example.com/login')
    page.fill('#username', 'user')
    page.fill('#password', 'pass')
    page.click('#submit')
    page.wait_for_url('**/dashboard')
    
    content = context.spider.do_url(context.task.get('url'))
    context['content'] = content
```

### 表单提交

```python
@action()
def submit_search(context: Context):
    page = context.spider.get_driver()
    page.goto(context.task.get('url'))
    
    page.fill('input[name="query"]', context.task.get('keyword'))
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    
    context['content'] = page.content()
```

### 懒加载

滚动页面触发懒加载：

```python
page = context.spider.get_driver()
page.goto(url)

for _ in range(5):  # 滚动5次
    page.evaluate('window.scrollBy(0, 1000)')
    page.wait_for_timeout(500)

content = page.content()
```

---

## 调试技巧

### Action 阶段

1. 查看 `.html` 文件确认内容正确
2. 搜索目标数据关键词确认存在
3. 检查 `_failed.json` 查看失败原因

### Parse 阶段

1. 查看 `_parse.json` 确认提取结果
2. 如果为空，在HTML中搜索关键词验证XPath
3. 对比文件数和任务数确认无遗漏

### XPath 验证

在浏览器开发者工具Console中测试：

```javascript
$x('//h1/text()')  // 测试XPath
```

---

## 常见问题

### 页面内容为空或不完整

可能是JS渲染未完成，添加等待：

```python
page = context.spider.get_driver()
page.goto(url)
page.wait_for_selector('.content')  # 等待关键元素
content = page.content()
```

### 元素找不到

1. 确认选择器正确（在浏览器中测试）
2. 检查是否在 iframe 中
3. 检查是否需要滚动到可见区域

### 被反爬拦截

1. 降低并发：减少 `MAX_WORKERS`
2. 增加延迟：设置 `RATE_LIMIT`
3. 使用 headless=False 观察页面状态

### Parse 阶段找不到数据

1. 确认 Action 阶段成功生成 `.html`
2. 确认 XPath/CSS 选择器正确
3. 检查HTML结构是否与预期一致

---

## 验证流程

1. **单页验证**：`initial_task()` 只放 1 个 URL，确认逻辑正确
2. **扩展验证**：增加到 3-5 个 URL，验证通用性
3. **完整运行**：全量 URL 执行
