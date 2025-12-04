# Auto Spider 功能指南

---

## 1. CLI 命令

### generate - 生成项目模板

```bash
python -m auto_spider generate <name> [--single-file] [-d <description>]
```

| 参数 | 说明 |
|------|------|
| `<name>` | 计划名称，生成 `plan_{name}.py` 和 `steps_{name}/` |
| `--single-file` | 生成单文件模板（内联steps） |
| `-d, --description` | 计划描述 |

### run - 运行指定阶段

```bash
python -m auto_spider run <plan_file> <steps> [-s <stage>] [-w <workers>] [--retry-failed]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<plan_file>` | plan文件路径 | 必填 |
| `<steps>` | 步骤名（逗号分隔） | 必填 |
| `-s, --stage` | 阶段：action/parse/extract | 自动检测 |
| `-w, --workers` | 并发数 | `4` |
| `--retry-failed` | 重试失败任务 | `False` |

**stage自动检测规则**：
- 步骤名包含 `parse` → parse阶段
- 步骤名包含 `extract` 或 `save` → extract阶段
- 其他 → action阶段

**多关键词情况**：按优先级 `parse` > `extract/save` > `action` 判断。例如 `parse_and_save` 会被识别为 parse 阶段。

**建议**：使用 `-s` 参数显式指定阶段，避免歧义。

### 直接运行

```bash
python plan_mysite.py
```

---

## 2. 项目结构

执行 `python -m auto_spider generate mysite` 后生成：

| 文件/目录 | 说明 |
|-----------|------|
| `plan_mysite.py` | 主入口文件，配置Spider、Task、运行参数 |
| `steps_mysite/` | 步骤包目录 |
| `steps_mysite/__init__.py` | 包初始化，自动导入action/parse/extract |
| `steps_mysite/action.py` | Action阶段步骤函数 |
| `steps_mysite/parse.py` | Parse阶段步骤函数 |
| `steps_mysite/extract.py` | Extract阶段步骤函数 |

### 单文件模式

探索阶段使用 `--single-file` 生成单文件 plan，所有代码在一个文件中：

```bash
python -m auto_spider generate explore_xxx --single-file
```

生成 `plan_explore_xxx.py`，包含：
- 配置、三大函数、steps 定义
- 直接运行 `python plan_explore_xxx.py`
- 输出目录：`output/`（当前目录下）

**适用场景**：
- 快速探索页面结构
- 验证爬取逻辑
- 不需要保存/复用 steps

**性能差异**：无差异。单文件和多文件仅是代码组织方式不同，执行机制相同。

**导入优先级**：框架优先搜索 `steps_{name}/` 目录，找不到时在 plan 文件中查找内联函数。

---

## 3. 三阶段说明

### 为什么这样划分

| 阶段 | 职责 | 分离原因 |
|------|------|----------|
| Action | 网络 IO | 慢、不稳定、需要重试，与解析逻辑分离 |
| Parse | CPU 计算 | 纯计算、确定性高、可重复执行 |
| Extract | 外部副作用 | 数据库/API调用，与解析逻辑解耦 |

**合并场景**：如果数据量小且逻辑简单，可以在 Action 中直接解析并保存。不需要三个阶段都用。

### Action 阶段

**职责**：网络请求，获取原始数据

| 项目 | 说明 |
|------|------|
| **执行方式** | 多进程 |
| **输入** | `context.task` - 任务字典（包含url等） |
| **操作** | 使用Spider发起HTTP请求或浏览器访问 |
| **输出** | `context['content']` - HTML内容（必须设置） |
| **保存** | `context['result']` - 保存为 `task_action.json` |
| **增量** | `context.tasks.append(Task(...))` - 添加新任务 |

### Parse 阶段

**职责**：解析HTML，提取结构化数据

| 项目 | 说明 |
|------|------|
| **执行方式** | 多线程 |
| **输入** | `context['content']` - HTML内容 |
| **输入** | `context.get('input')` - Action阶段的result |
| **操作** | 使用XPath/CSS选择器解析HTML |
| **输出** | `context['result']` - 保存为 `task_parse.json` |

### Extract 阶段

**职责**：数据持久化，执行副作用操作

| 项目 | 说明 |
|------|------|
| **执行方式** | 多线程 |
| **输入** | `context.get('input')` - Parse阶段的result |
| **操作** | 数据库写入、API调用、文件保存等 |
| **输出** | 无文件输出 |

---

## 4. 配置项（PlanConfig）

在 `plan_mysite.py` 中设置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `PLAN_NAME` | 计划名称，用于输出目录命名 | 必填 |
| `OUTPUT_DIR` | 输出目录路径 | `None`（自动为`output`） |
| `MAX_WORKERS` | 并发Worker数量 | `4` |
| `RATE_LIMIT` | 任务间隔（秒） | `None`（无限制） |
| `STORAGE_TIMESTAMP` | 目录名是否带时间戳 | `True` |

**STORAGE_TIMESTAMP 策略说明**：

| 模式 | 目录示例 | 适用场景 |
|------|----------|----------|
| `True`（默认） | `action_20241127_140000/` | 需要保留历史记录、调试对比 |
| `False` | `action/` | 频繁调试、磁盘空间有限 |

**长期运行建议**：使用时间戳模式时，定期清理旧目录，避免磁盘占满。

---

## 5. run_plan 参数

```python
run_plan(initial_spider, initial_task, initial_plan,
         actions=[], parses=[], extracts=[],
         config=PLAN_CONFIG)
```

| 参数 | 说明 | 必填 |
|------|------|------|
| `initial_spider` | Spider工厂函数 | Action阶段必填 |
| `initial_task` | Task列表工厂函数 | 是（除非retry_failed） |
| `initial_plan` | 资源工厂函数 | 否 |
| `actions` | Action阶段函数名列表 | 三选一 |
| `parses` | Parse阶段函数名列表 | 三选一 |
| `extracts` | Extract阶段函数名列表 | 三选一 |
| `config` | PlanConfig实例 | 否 |
| `retry_failed` | 重试失败任务 | 否 |

---

## 6. Context API

### 属性

| 属性 | 阶段 | 说明 |
|------|------|------|
| `context.task` | 全部 | 原始Task字典，永不改变 |
| `context.spider` | Action | Spider实例 |
| `context.tasks` | Action | 增量任务列表 |
| `context.initial` | 全部 | `initial_plan()` 返回的资源字典 |

### 增量任务机制

**context.tasks.append() 执行时序**：

1. **当前任务执行完毕后**，Worker 检查 `context.tasks` 列表
2. **新任务加入当前批次队列尾部**，在本次 run_plan 中执行
3. **执行顺序**：先完成当前任务，再执行新增任务

**深度控制**：框架不限制深度，需要用户在代码中控制：

```python
@action()
def fetch_page(context: Context):
    depth = context.task.get('depth', 0)
    if depth >= 3:  # 最大深度3层
        return
    
    for link in extract_links(content):
        context.tasks.append(Task(url=link, depth=depth + 1))
```

### 键值

| 键 | 读/写 | 说明 |
|----|-------|------|
| `context['content']` | 读写 | HTML内容 |
| `context['result']` | 写 | 当前阶段输出，自动保存 |
| `context.get('input')` | 读 | 上一阶段的result |

---

## 7. Spider

两种Spider的 `do_url()` 都返回 `str`（HTML内容）。

### PlaywrightSpider（默认）

浏览器自动化，支持JS渲染。

| 方法 | 说明 |
|------|------|
| `do_url(url)` | 访问URL，返回HTML字符串 |
| `get_driver()` | 获取 `playwright.Page` 对象 |
| `get_page_info()` | 获取页面可交互元素列表 |

**初始化参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `headless` | 无头模式 | `True` |
| `enable_cdp` | 启用Chrome DevTools Protocol | `False` |
| `timeout` | 页面加载超时（秒） | `30` |

**enable_cdp 参数说明**：

- **用途**：启用 CDP 后，`get_page_info()` 通过 CDP Runtime.evaluate 执行 JavaScript 获取元素信息，比纯 Playwright API 更稳定
- **适用场景**：需要获取页面可交互元素列表时必须开启
- **性能影响**：首次调用有约 100ms 额外开销，后续调用无明显影响
- **不启用时**：`get_page_info()` 不可用，其他功能正常

**Page常用操作**：

| 操作 | 说明 |
|------|------|
| `page.click(selector)` | 点击元素 |
| `page.fill(selector, text)` | 填写输入框 |
| `page.wait_for_selector(selector)` | 等待元素出现 |
| `page.screenshot(path='x.png')` | 截图 |

**get_page_info() 返回数据结构**：

```python
{
    'title': '页面标题',
    'url': '当前URL',
    'elements': [
        {
            'index': 1,                    # 元素序号
            'tag': 'button',               # 标签名
            'text': 'Submit',              # 可见文本
            'attributes': {'id': 'btn1'},  # HTML属性
            'css': '#btn1',                # CSS选择器（不保证唯一）
            'xpath': '//*[@id="btn1"]',   # XPath选择器（不保证唯一）
            'position': {                  # 元素位置
                'x': 100,                  # 左上角x坐标
                'y': 200,                  # 左上角y坐标
                'width': 80,               # 宽度
                'height': 40,              # 高度
                'center_x': 140,           # 中心点x
                'center_y': 220            # 中心点y
            }
        }
    ]
}
```

**elements包含的可交互元素类型**：
- `a` - 链接
- `button` - 按钮
- `input` - 输入框（text/password/email/search等）
- `select` - 下拉框
- `textarea` - 多行文本框
- `[onclick]` - 带点击事件的元素
- `[role="button"]` - ARIA按钮角色元素

**注意**：`css` 和 `xpath` 选择器是基于元素属性生成的，**不保证唯一性**。如果需要精确定位，建议结合 `position` 坐标或手动检查页面结构。

### RequestSpider

HTTP请求，适合静态页面，更轻量。

| 方法 | 说明 |
|------|------|
| `do_url(url, retry=1)` | 发起HTTP请求，返回HTML字符串 |
| `get_driver()` | 获取 `requests.Session` 对象 |

---

## 8. 工具函数

### XPath提取

| 函数 | 说明 |
|------|------|
| `xpath_extract(html, xpath)` | 提取匹配XPath的内容列表 |

导入：`from auto_spider.tools.xpath import xpath_extract`

### HTML清洗

| 函数 | 说明 |
|------|------|
| `clean_html(html)` | 清洗HTML噪声，返回结构化结果 |

导入：`from auto_spider.tools.html_cleaner import clean_html`

**clean_html() 处理规则**：

| 操作 | 说明 |
|------|------|
| **移除标签** | `script`, `style`, `meta`, `link`, `noscript`, `svg`, `iframe`, `comment` |
| **移除属性** | 除 `id`, `class`, `href`, `src`, `alt`, `title`, `name`, `type`, `value`, `placeholder` 外的所有属性 |
| **保留结构** | 保留 DOM 树结构，可用于 XPath/CSS 选择器 |

**返回数据结构**：

```python
{
    'html': '<html>...</html>',  # 清洗后的完整HTML
    'body': '<div>...</div>',    # body内容
    'text': '纯文本内容...'       # 仅文本，无标签
}
```

---

## 9. 输出文件

### 目录结构

**STORAGE_TIMESTAMP=True**（默认，带时间戳）：
```
steps_mysite/output/
├── action_20241127_140000/
└── parse_20241127_140100/
```

**STORAGE_TIMESTAMP=False**（无时间戳，覆盖模式）：
```
steps_mysite/output/
├── action/
└── parse/
```

### 文件说明

| 文件 | 说明 |
|------|------|
| `task1.html` | HTML内容 |
| `task1_task.json` | 原始Task |
| `task1_action.json` | Action阶段result |
| `task1_parse.json` | Parse阶段result |
| `task1_failed.json` | 失败任务信息（如果有） |

### 失败任务处理

**生成 `_failed.json` 的情况**：
- 网络请求异常（超时、连接失败）
- Spider 执行异常
- 用户代码抛出未捕获异常

**文件内容**：
```json
{
    "task": {"url": "..."},
    "error": "异常信息",
    "traceback": "堆栈追踪"
}
```

**重试机制**：
- 使用 `--retry-failed` 参数重试失败任务
- 重试时创建**新的 Spider 实例**，不复用失败时的实例
- 重试次数由 Task 中的 `retry` 字段控制（Spider.do_url 层面）

---

## 10. 代码规范

### import语句

**必须放在文件顶部**，不要放在函数或条件块内。

```python
# 正确
import re
import json
from auto_spider import action, Context

@action()
def fetch_page(context: Context):
    text = re.sub(r'\s+', ' ', content)  # re可用
```

```python
# 错误 - 会导致 "cannot access local variable 're'"
@action()
def fetch_page(context: Context):
    if need_clean:
        import re  # 不要在条件块内import
        text = re.sub(r'\s+', ' ', content)
```

### URL处理

注意区分相对路径和完整URL：

```python
def normalize_url(uri: str, base_url: str) -> str:
    if uri.startswith('/'):
        return base_url + uri
    elif uri.startswith('http'):
        return uri
    else:
        return f"{base_url}/{uri}"
```

### 数据清洗

提取后清洗空白字符：

```python
def clean_text(text: str) -> str:
    if text:
        return ' '.join(text.split())
    return ''
```

---

## 11. 代码示例

### plan_mysite.py

```python
from auto_spider import Task, PlanConfig, run_plan
from auto_spider.components import PlaywrightSpider

import steps_mysite  # noqa: F401

PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'mysite'
PLAN_CONFIG.OUTPUT_DIR = 'steps_mysite/output'

def initial_spider():
    return PlaywrightSpider(headless=True)

def initial_task():
    return [Task(url='https://example.com')]

def initial_plan():
    return {}

if __name__ == '__main__':
    run_plan(
        initial_spider, initial_task, initial_plan,
        actions=['fetch_page'],      # action: fetch HTML
        # parses=['parse_data'],     # parse: extract data from HTML
        # extracts=['save_data'],    # extract: save to database
        config=PLAN_CONFIG
    )
```

### action.py

```python
from auto_spider import action, Context, Task

@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)
    context['content'] = content
    context['result'] = {'url': url}

# 增量爬取示例
@action()
def fetch_list(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)
    
    # 添加新任务
    for link in extract_links(content):
        context.tasks.append(Task(url=link))
    
    context['content'] = content
```

### parse.py

```python
from auto_spider import parse, Context
from auto_spider.tools.xpath import xpath_extract

@parse()
def parse_data(context: Context):
    content = context.get('content', '')
    data = {
        'title': xpath_extract(content, '//h1/text()'),
        'links': xpath_extract(content, '//a/@href'),
    }
    context['result'] = data
```

### extract.py

```python
from auto_spider import extract, Context

@extract()
def save_data(context: Context):
    parse_result = context.get('input', {})
    # 执行数据库写入等操作
```

### Spider初始化示例

```python
# PlaywrightSpider（默认，支持JS）
def initial_spider():
    return PlaywrightSpider(headless=True, enable_cdp=True)

# RequestSpider（轻量，静态页面）
def initial_spider():
    return RequestSpider(timeout=10)
```

---

## 12. 并发与资源管理

### 并发控制

| 阶段 | 执行方式 | Worker模型 |
|------|----------|------------|
| Action | 多进程 | 每个 Worker 独立的 Spider 实例 |
| Parse | 多线程 | 共享内存，无竞争（只读文件） |
| Extract | 多线程 | 共享内存，需用户处理数据库并发 |

**竞态避免**：
- Action 阶段：多进程天然隔离，无竞态问题
- Parse/Extract：任务独立，每个任务处理不同文件

**Rate Limit**：
- `RATE_LIMIT` 作用于任务分发层面，控制任务进入队列的间隔
- 各 Worker 并行执行，实际并发数 = `MAX_WORKERS`

### 资源生命周期

**Playwright 浏览器**：
- 创建：`initial_spider()` 中创建 PlaywrightSpider
- 关闭：Worker 处理完所有任务后自动关闭
- 异常退出：进程结束时由操作系统回收

**内存管理**：
- 每个任务的 `context` 在任务完成后释放
- HTML 内容写入文件后从内存移除
- 大文件场景建议减少 `MAX_WORKERS`

### 任务依赖

| 场景 | 行为 |
|------|------|
| Action 失败 | 不生成 `.html`，Parse 找不到输入文件，跳过该任务 |
| Parse 失败 | 生成 `_failed.json`，Extract 找不到输入，跳过 |

**数据一致性**：各阶段独立执行，不回滚。部分失败时，成功的任务结果仍然保存。

---

## 13. 常见场景

### 登录状态保持

```python
@action()
def login_and_fetch(context: Context):
    page = context.spider.get_driver()
    
    # 登录
    page.goto('https://example.com/login')
    page.fill('#username', 'user')
    page.fill('#password', 'pass')
    page.click('#submit')
    page.wait_for_url('**/dashboard')  # 等待跳转
    
    # 获取需要登录的页面
    content = context.spider.do_url(context.task.get('url'))
    context['content'] = content
```

**Cookie 生命周期**：同一 Spider 实例内保持，跨 Worker 不共享。

### 表单提交

```python
@action()
def submit_form(context: Context):
    page = context.spider.get_driver()
    page.goto(context.task.get('url'))
    
    page.fill('input[name="query"]', context.task.get('keyword'))
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    
    context['content'] = page.content()
```

### 分页处理

```python
@action()
def fetch_list(context: Context):
    url = context.task.get('url')
    page_num = context.task.get('page', 1)
    
    content = context.spider.do_url(f"{url}?page={page_num}")
    context['content'] = content
    
    # 添加下一页任务
    if has_next_page(content) and page_num < 10:  # 最多10页
        context.tasks.append(Task(url=url, page=page_num + 1))
```

### 二进制文件

```python
@action()
def download_file(context: Context):
    page = context.spider.get_driver()
    
    # 设置下载路径
    with page.expect_download() as download_info:
        page.click('a.download')
    download = download_info.value
    download.save_as(f"output/{download.suggested_filename}")
    
    context['content'] = f'Downloaded: {download.suggested_filename}'
```
