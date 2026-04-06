# API 参考

## CLI 命令

```bash
# 生成项目模板
auto-spider generate <name>              # 默认生成单文件 {name}.py
auto-spider generate <name> --module     # 生成 {name}.py + steps_{name}/ 模块

# 运行计划（.py 扩展名可选）
auto-spider run <name> --action          # 支持 tp 或 tp.py
auto-spider run <name> --parse
auto-spider run <name> --extract
auto-spider run <name> --action --retry-failed
```

**阶段参数**：`--action` / `--parse` / `--extract`（三选一）

**步骤配置**：执行哪些 step 由 plan 文件中的 `ACTION_STEPS` / `PARSE_STEPS` / `EXTRACT_STEPS` 列表决定

## PlanConfig

```python
from auto_spider import PlanConfig

PLAN_CONFIG = PlanConfig()
PLAN_CONFIG.PLAN_NAME = 'myplan'           # 计划名称，作为输出子目录
PLAN_CONFIG.OUTPUT_DIR = 'output'          # 基础输出目录（最终: output/<PLAN_NAME>/action_xxx）
PLAN_CONFIG.MAX_WORKERS = 4                # 并发Worker数量
PLAN_CONFIG.RATE_LIMIT = 1.0               # 任务间隔秒数，None为无限制
PLAN_CONFIG.STORAGE_TIMESTAMP = True       # True: action_20241118_150000, False: action（覆盖模式）
PLAN_CONFIG.TASK_RETRY_COUNT = 3           # 任务重试次数（1次初始 + 2次重试）
PLAN_CONFIG.START_DELAY = 0               # Worker启动前的倒计时秒数（0=无倒计时）

ACTION_STEPS = ['fetch_page']              # action阶段执行的step列表
PARSE_STEPS = ['parse_data']               # parse阶段执行的step列表
EXTRACT_STEPS = ['save_data']              # extract阶段执行的step列表
```

## Context

### 属性

| 属性 | 阶段 | 说明 |
|------|------|------|
| `context.task` | 全部 | 原始Task字典 |
| `context.spider` | Action | Spider实例 |
| `context.tasks` | Action | 增量任务列表 |
| `context.initial` | 全部 | `initial_plan()` 返回的资源字典 |

### 键值

| 键 | 读/写 | 说明 |
|----|-------|------|
| `context['content']` | 读写 | HTML内容，Action阶段必须设置 |
| `context['result']` | 写 | 当前阶段输出，自动保存为json |
| `context.get('input')` | 读 | 上一阶段的result |

## 装饰器

```python
from auto_spider import action, parse, extract, Context

@action()
def fetch_page(context: Context):
    # Action阶段

@parse()
def parse_data(context: Context):
    # Parse阶段

@extract()
def save_data(context: Context):
    # Extract阶段
```

## Task

Task本质是dict，可传入任意参数：

```python
from auto_spider import Task

task = Task(url='https://example.com', page_type='list', retry=3)
# 在action中通过 context.task.get('url') 获取
```

## Spider

### PlaywrightSpider

浏览器自动化，支持JS渲染。

```python
from auto_spider.components import PlaywrightSpider

spider = PlaywrightSpider(headless=True, enable_cdp=True, timeout=30)
```

**方法**：

| 方法 | 说明 |
|------|------|
| `do_url(url)` | 访问URL，返回HTML字符串 |
| `get_driver()` | 获取 playwright.Page 对象 |
| `get_page_info()` | 获取页面可交互元素列表（需enable_cdp=True） |

**get_page_info() 返回**：`{title, url, elements: [{index, tag, text, css, xpath, position}]}`

**Page 常用操作**：
- `page.click(selector)` - 点击元素
- `page.fill(selector, text)` - 填写输入框
- `page.wait_for_selector(selector)` - 等待元素出现
- `page.wait_for_url(pattern)` - 等待URL匹配
- `page.screenshot(path='x.png')` - 截图

### RequestSpider

HTTP请求，适合静态页面。

```python
from auto_spider.components import RequestSpider

spider = RequestSpider(timeout=10)
```

**方法**：

| 方法 | 说明 |
|------|------|
| `do_url(url, retry=1)` | 发起HTTP请求，返回HTML字符串 |
| `get_driver()` | 获取 requests.Session 对象 |

## 工具函数

### XPath 提取

```python
from auto_spider.tools.xpath import xpath_extract

titles = xpath_extract(html, '//h1/text()')
links = xpath_extract(html, '//a/@href')
```

### HTML 清洗

```python
from auto_spider.tools.html_cleaner import clean_html

result = clean_html(html)
# 返回: {html: 清洗后HTML, body: body内容, text: 纯文本}
# 移除: script, style, meta, link, noscript, svg, iframe, comment
# 保留属性: id, class, href, src, alt, title, name, type, value, placeholder
```

### 任务去重

```python
from auto_spider.tools.dedup import create_duplicate_checker, is_duplicate
from auto_spider import Task

# 内存模式
checker = create_duplicate_checker()

# 持久化到文件
checker = create_duplicate_checker('seen.json')

task = Task(url='https://example.com')
if not is_duplicate(checker, task):
    context.tasks.append(task)
```
