# Auto Spider 工作流程

本文档定义爬取任务的执行流程和设计原则。

---

## 核心原则

**遇到新页面，先探索；一个 plan，一个目标。**

---

## Plan 设计原则

### 一个 plan = 一次人类操作

Plan 代表一次简单的、独立的人类操作。每个 plan 只做一件事。

**示例**：

| 场景 | Plan 数量 | 说明 |
|------|-----------|------|
| 目录页 → 详情页 | 2 | `plan_list` 提取链接，`plan_detail` 提取数据 |
| 查询 → 结果 → 详情 | 3 | `plan_search` 提交查询，`plan_result` 解析结果，`plan_detail` 提取数据 |
| 登录 → 列表 → 详情 | 3 | `plan_login` 登录，`plan_list` 获取列表，`plan_detail` 提取数据 |

### 遇到新页面先探索

每遇到一种新页面，都需要先探索：
1. 用单文件 plan 获取 HTML
2. 分析页面结构
3. 确定需要提取的数据
4. 再创建正式 plan

---

## 执行流程

### Step 1: 探索页面

遇到任何新页面，先创建探索 plan：

```bash
python -m auto_spider generate explore_xxx --single-file
```

修改 `initial_task()` 放入目标 URL，运行获取 HTML。

在 action 中可以使用以下工具获取页面数据：

**1. get_page_info() - 获取可交互元素**

```python
@action()
def fetch_page(context: Context):
    content = context.spider.do_url(url)
    
    # 获取页面可交互元素（按钮、链接、输入框等）
    page_info = context.spider.get_page_info()
    # 返回: {title, url, elements: [{tag, text, css, xpath, position}]}
    
    context['content'] = content
    context['result'] = page_info
```

**2. clean_html() - 清洗 HTML 噪声**

```python
from auto_spider.tools.html_cleaner import clean_html

@action()
def fetch_page(context: Context):
    content = context.spider.do_url(url)
    
    # 清洗 HTML：移除 script/style/meta 等，只保留 id/class/href 属性
    result = clean_html(content)
    # 返回: {html: 清洗后HTML, text: 纯文本, body: body内容}
    
    context['content'] = content
    context['result'] = result
```

运行后查看 `output/action_*/` 下的文件，分析页面结构。

### Step 2: 分析并决策

根据探索结果决定下一步：

| 发现 | 行动 |
|------|------|
| 这是目录页，包含详情链接 | 创建 `plan_xxx_list`，提取链接 |
| 这是详情页，包含目标数据 | 创建 `plan_xxx_detail`，提取数据 |
| 需要登录/查询才能访问 | 创建对应的前置 plan |
| 链接指向新类型页面 | 回到 Step 1，探索新页面 |

### Step 3: 创建正式 Plan

确定目标后创建正式 plan：

```bash
python -m auto_spider generate xxx_list
```

### Step 4: 验证

1. **单页验证**：`initial_task()` 只放 1 个 URL，验证逻辑正确
2. **扩展验证**：增加到 3-5 个 URL，验证通用性
3. **完整运行**：全量 URL 执行

---

## 记录规范

**必须**：每个plan创建对应的记录文档 `{plan_name}_crawl.md`，与plan文件同级。

### 文档结构

```markdown
# {plan_name} 爬取记录

目标: [目标URL]
数据: [需要提取的数据描述]

---

## [Phase] - [YYYYMMDD HH:MM]

**操作**: 做了什么
**命令**: 执行的命令
**结果**: 成功/失败，关键数据
**输出**: 输出目录
**下一步**: 下一步行动
```

### 记录时机

- 创建plan后立即创建记录文档
- 每次执行命令后记录结果
- 遇到问题时记录问题和解决方案

---

## 执行结果说明

### Action 阶段

**成功标志**：生成 `output/action_*/task_name.html` 文件

**调试方法**：
1. 查看 `.html` 文件内容是否正常
2. 搜索目标数据关键词确认存在
3. 检查 `_failed.json` 文件查看失败原因

### Parse 阶段

**成功标志**：生成 `output/parse_*/task_name_parse.json` 文件

**调试方法**：
1. 查看 `_parse.json` 内容是否正确
2. 如果为空，在HTML中搜索关键词确认XPath是否正确
3. 对比文件数和任务数，确认是否有遗漏

### 失败任务

**重试方法**：使用 `--retry-failed` 参数重试失败任务

```bash
python -m auto_spider run plan_xxx.py fetch_page -s action --retry-failed
```

---

## 检查清单

- [ ] 探索：确认页面类型和数据位置
- [ ] 单页：action生成.html，parse生成.json
- [ ] 扩展：多页验证通过
- [ ] 记录：每步操作已记录
