# AI Assistant Guide for Auto Spider

> **核心规范文档 - AI 助手在使用 Auto Spider 前必读**
>
> 本文档是你使用 Auto Spider 框架的唯一入口。所有 skills 和详细文档通过 `auto-spider init` 已复制到项目中。

## 文档索引

项目初始化后（`auto-spider init`），文档结构如下：

```
docs/
├── ai/
│   ├── ai-assistant-guide.md   ← 你正在看的文档（总入口）
│   ├── skills_index.md         ← Skills 目录和分组
│   └── project_structure.md    ← 项目架构和模块说明
├── guide.md                    ← 使用指南（从简单到复杂）
├── api.md                      ← API 参考
└── build.md                    ← 构建发布

.claude/skills/                 ← Skills 定义（详细操作指引）
├── sense-scout/skill.md        ← 侦察页面（第一步）
├── sense-page-info/skill.md    ← 分析交互元素
├── sense-clean-html/skill.md   ← 分析 HTML 结构
├── plan-generate/SKILL.md      ← 生成 plan 模板
├── write-action/SKILL.md       ← 编写 action 步骤
├── write-parse/SKILL.md        ← 编写 parse 步骤
├── write-extract/SKILL.md      ← 编写 extract 步骤
├── exec-run-verify/SKILL.md    ← 运行和验证
└── analyze-script/skill.md     ← 复杂分析用独立脚本
```

---

## 禁止事项

### 不要写独立爬虫脚本
```python
# ❌ 错误 - 不要这样写
from bs4 import BeautifulSoup
import requests

def scrape_page():
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
```

**原因**: 忽略框架、不可维护、浪费时间

### 不要使用 requirements.txt 之外的依赖
```python
# ❌ 错误
from bs4 import BeautifulSoup  # 不在 requirements.txt
import scrapy                   # 不在 requirements.txt
```

### 不要跳过侦察
新页面必须先用 `sense-scout` 侦察，不要凭猜测写代码。

### 数据文件读取优先级
```
1. 先用 sense-scout 侦察页面，获取 markdown / cleaned_html / page_info
2. 用 analyze-script 生成分析脚本检查数据
3. 最后才考虑直接读取文件（作为最后手段）
```

**原因**: 数据文件可能很大，直接读取会超出 token 限制

---

## CLI 命令

```bash
# 初始化项目（复制 skills 和 docs 到当前目录）
auto-spider init

# 生成 plan 模板（默认单文件）
auto-spider generate <name>              # 生成 {name}.py
auto-spider generate <name> --module     # 生成 {name}.py + steps_{name}/

# 运行 plan（.py 扩展名可选）
auto-spider run <name> --action
auto-spider run <name> --parse
auto-spider run <name> --extract
auto-spider run <name> --action --retry-failed
```

默认生成**单文件 plan**，包含 action/parse/extract 步骤内联在同一个文件中。

---

## 默认 Plan 模板说明

`auto-spider generate <name>` 生成的单文件 plan 已经内置了完整的**侦察功能**：

```python
@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)

    # 自动收集三种数据
    markdown = html_to_markdown(content)           # 页面内容概览
    cleaned_html = clean_html(content).get('body', '')  # 干净 HTML
    page_info = context.spider.get_page_info()     # 交互元素列表

    context['content'] = content
    context['result'] = {
        'markdown': markdown,
        'cleaned_html': cleaned_html,
        'page_info': page_info,
    }
```

运行 `--action` 后，输出目录包含：
- `task1.html` — 原始 HTML
- `task1_action.json` — 包含 `markdown`、`cleaned_html`、`page_info`
- `task1_task.json` — 原始任务参数

---

## 可用工具

### Spider 类型
```python
# 静态页面 (快)
from auto_spider.components import RequestSpider

# 动态页面 (JS 渲染)
from auto_spider.components import PlaywrightSpider
```

### 解析工具
```python
from auto_spider.tools.xpath import xpath_extract
from auto_spider.tools.html_cleaner import clean_html
from auto_spider.tools.html_to_markdown import html_to_markdown
```

### 页面信息 (仅 PlaywrightSpider)
```python
page_info = context.spider.get_page_info()
```

---

## 决策流程

```
用户分配爬虫任务
      ↓
1. 侦察页面 (sense-scout skill)
   auto-spider generate scout_xxx
   修改 initial_task() 填入目标 URL
   auto-spider run scout_xxx --action
      ↓
2. 分析侦察结果
   - 查看 page_info → 了解交互元素 (sense-page-info skill)
   - 查看 cleaned_html → 了解 DOM 结构 (sense-clean-html skill)
   - 查看 markdown → 了解页面内容概览
      ↓
3. 制定采集策略（见下方"策略制定"）
      ↓
4. 生成正式 plan (plan-generate skill)
   auto-spider generate myplan
      ↓
5. 实现 action/parse/extract (write-* skills)
      ↓
6. 运行并验证 (exec-run-verify skill)
      ↓
7. 失败？分析原因，调整代码，重试
   成功？进入下一阶段
```

---

## Skills 列表

| Skill | 用途 | 何时使用 |
|-------|------|----------|
| `sense-scout` | 侦察新页面 | **第一步**，了解页面结构 |
| `sense-page-info` | 分析交互元素 | 侦察后，查看按钮/链接/表单 |
| `sense-clean-html` | 分析 HTML 结构 | 侦察后，推导 XPath 选择器 |
| `plan-generate` | 生成 plan 模板 | 准备写正式爬虫代码 |
| `write-action` | 写 action 步骤 | 下载 HTML |
| `write-parse` | 写 parse 步骤 | 提取数据 |
| `write-extract` | 写 extract 步骤 | 保存数据 |
| `exec-run-verify` | 运行和验证 | 执行并检查结果 |
| `analyze-script` | 复杂分析用独立脚本 | 需要复杂 Python 操作 |

详细 skill 文档见: `docs/ai/skills_index.md`

---

## 核心原则

1. **先侦察后编码**: 新页面先用 `sense-scout` 获取数据，不要凭猜测写代码
2. **从简单开始**: RequestSpider + XPath 优先，失败再升级到 Playwright
3. **默认单文件 plan**: 使用 `auto-spider generate <name>` 生成单文件，简单直接
4. **一个 Plan 干一件事**: 每个 plan 只完成一个明确目标，复杂任务拆分多个 plan
5. **CSS 隐藏 ≠ JS 加载**: 看到折叠/隐藏元素不代表需要交互，先检查 HTML 是否已包含数据

---

## 策略制定

侦察完成后，基于数据制定采集策略。**从简单到复杂，逐步升级**：

### 方案选择

```
静态 HTML 已包含目标数据？
  YES → 方案 A: RequestSpider + XPath（最简单）
  NO  ↓
页面需要 JS 渲染？
  YES → 方案 B: PlaywrightSpider + XPath
  NO  ↓
需要交互（点击/滚动/登录）？
  YES → 方案 C: PlaywrightSpider + 交互操作
```

### 策略思维检查列表

写代码前问自己：

- [ ] **静态数据检查**: cleaned_html 是否已包含目标数据？
- [ ] **最简方案**: RequestSpider 是否足够？
- [ ] **必要性**: 真的需要 Playwright 吗？
- [ ] **数量验证**: 数据条数是否符合预期？

### 失败处理

```
方案 A 失败 → 分析原因（数据为空？格式错误？）→ 尝试方案 B
方案 B 失败 → 分析原因 → 尝试方案 C
所有方案失败 → 重新侦察，检查假设是否正确
```

建议在 plan 文件顶部注释中记录当前使用的策略方案，便于回溯。

---

## 日志记录建议

复杂任务建议记录执行过程，帮助回溯和调试。

### 推荐格式

在项目根目录创建 `TASK_<name>_log.md`：

```markdown
# 任务: {任务描述}

- **目标**: {详细目标}
- **状态**: 进行中 / 已完成 / 失败

## 侦察结论
- HTML 链接数: xxx
- 目标字段: xxx 存在 / 不存在
- 交互元素: 按钮 x 个, 表单 x 个

## 采集策略
方案 A: RequestSpider + XPath（首选）

## 执行记录

### Step 1: 侦察
- 运行: `auto-spider run scout_xxx --action`
- 结果: 成功，找到 xxx 条数据

### Step 2: 正式采集
- 运行: `auto-spider run myplan --action`
- 结果: 成功 / 失败（原因: xxx）
```

**注意**: 日志记录是建议而非强制。简单任务可以不记录，复杂任务建议记录关键步骤。

---

## 三阶段架构

```
Task → action step → 原始数据(.html)
                         ↓
                    TaskResult → parse step → 解析数据(.json)
                                                  ↓
                                             TaskData → extract step → 持久化
```

### Context 数据传递

| Key | 说明 |
|-----|------|
| `context.task` | 原始 Task 字典，永不改变 |
| `context['content']` | HTML 内容，Action 阶段必须设置 |
| `context['result']` | 当前阶段输出，自动保存为 json |
| `context.get('input')` | 上一阶段的 result |
| `context.spider` | Spider 实例（仅 Action 阶段） |
| `context.tasks` | 增量任务列表（仅 Action 阶段） |
| `context.initial` | `initial_plan()` 返回的资源字典 |

### 代码示例

```python
from auto_spider import action, parse, extract, Context

@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)
    context['content'] = content
    context['result'] = {'url': url}

@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    context['result'] = {'title': 'extracted data'}

@extract()
def save_data(context: Context):
    data = context.get('input', {})
    # save to database / file
```

更多示例见: `docs/guide.md` 和 `docs/api.md`