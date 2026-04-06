# Context

`Context` 是贯穿所有 step 的执行上下文，继承自 `dict`，分两层：系统资源（属性访问）和业务数据（字典访问）。

---

## 系统资源（属性）

| 属性 | 类型 | 说明 |
|------|------|------|
| `context.spider` | Spider | Spider 实例，用于网络请求 |
| `context.task` | dict | 当前任务的原始数据，三个阶段都不变 |
| `context.initial` | Any | `initial_plan()` 返回的资源（db、cache 等） |
| `context.config` | PlanConfig | 计划配置，如 MAX_WORKERS、RATE_LIMIT |
| `context.task_name` | str | 当前任务名，如 `task1`，用于日志 |
| `context.append_tasks` | list | 增量任务列表，见下文 |

---

## 业务数据（字典）

通过 `context['key']` 读写，框架约定了以下 key：

| Key | 阶段 | 说明 |
|-----|------|------|
| `context['input']` | action/parse/extract | 当前阶段的输入（action=原始task，parse=action结果，extract=parse结果） |
| `context['content']` | action/parse | HTML 原始内容，框架自动保存为 `.html` 文件 |
| `context['result']` | action/parse | 当前阶段的输出，框架自动保存为 `_action.json` / `_parse.json` |
| `context['action_result']` | parse/extract | action 阶段的结果，框架自动注入 |

---

## Step 返回值与 Step Result

每个 step 函数的 **return 值**会被框架存入 `context._step_results`，供**同阶段后续 step** 读取，与跨阶段传递无关。

```python
# step A
@action()
def fetch_page(context: Context):
    content = context.spider.do_url(url)
    context['content'] = content
    return content  # 存入 context['fetch_page'] 和 context[-1]


# step B（同一 action 阶段）
@action()
def process_page(context: Context):
    prev_content = context['fetch_page']  # 按函数名取
    prev_content = context[-1]            # 取上一个 step 的返回值
    first_result = context[0]             # 取第一个 step 的返回值
```

> 如果只有一个 step，return 值可以不写，没有副作用。

---

## 增量爬取（append_tasks）

在 step 中动态追加新任务，框架会自动将这些任务加入 pending_queue 继续处理。

```python
@action()
def fetch_list_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)

    # 从列表页提取详情页 URL，追加为新任务
    detail_urls = extract_links(content)
    for detail_url in detail_urls:
        context.append_tasks.append({'url': detail_url})

    context['content'] = content
    context['result'] = {'url': url}
```

`context.append_tasks` 中的每个元素格式与初始 `Task` 相同（普通 dict）。框架在 `_process_result` 中将它们放回 `task_pending_queue`，`JoinableQueue.join()` 会等待所有增量任务也完成后才退出。

---

## 数据流（三阶段）

```
initial_task() → [Task, Task, ...]
                     ↓
            ┌─── Action Stage ───┐
            │  context['input']  = 原始 task        │
            │  context['content'] = HTML             │
            │  context['result']  = action 结果      │
            │  保存: task1.html, task1_task.json,    │
            │        task1_action.json               │
            └────────────────────┘
                     ↓ (自动加载)
            ┌─── Parse Stage ────┐
            │  context['input']       = action 结果  │
            │  context['action_result']= action 结果  │
            │  context['content']     = HTML          │
            │  context['result']      = parse 结果    │
            │  保存: task1.html, task1_task.json,     │
            │        task1_action.json, task1_parse.json │
            └────────────────────┘
                     ↓ (自动加载)
            ┌─── Extract Stage ──┐
            │  context['input']       = parse 结果   │
            │  context['action_result']= action 结果  │
            │  context['parse_result'] = parse 结果   │
            │  不保存文件，只做副作用（写库等）        │
            └────────────────────┘
```

---

## 完整用法示例

```python
from auto_spider import action, parse, extract, Context


@action()
def fetch_page(context: Context):
    url = context.task.get('url')
    content = context.spider.do_url(url)

    context['content'] = content
    context['result'] = {'url': url, 'status': 200}


@parse()
def parse_data(context: Context):
    action_result = context.get('input', {})
    content = context.get('content', '')

    data = {'url': action_result.get('url'), 'items': []}
    context['result'] = data


@extract()
def save_data(context: Context):
    parse_result = context.get('input', {})
    db = context.initial.get('db')
    db.save(parse_result)
```
