# Auto Spider 执行逻辑

## 三阶段概述

| 阶段 | 职责 | 执行方式 | 输入 | 输出 |
|------|------|----------|------|------|
| Action | 网络请求，下载页面 | 多进程 | context.task | context['content'], context['result'] |
| Parse | 解析HTML，提取数据 | 多线程 | context['content'], context['input'] | context['result'] |
| Extract | 数据持久化，副作用操作 | 多线程 | context['input'] | 无文件输出 |

---

## Action 阶段

### 执行流程

1. Scheduler 从 `initial_task()` 获取任务列表
2. 任务分发到多进程 Worker 队列
3. 每个 Worker 创建独立的 Spider 实例（调用 `initial_spider()`）
4. Worker 执行 `@action()` 装饰的函数
5. 结果保存到 `output/action_{timestamp}/`

### 结果保存

每个任务生成以下文件：
- `task1.html` - HTML内容（来自 context['content']）
- `task1_task.json` - 原始Task
- `task1_action.json` - action结果（来自 context['result']）

### 增量任务

在action函数中可以动态添加新任务：

```python
@action()
def fetch_list(context: Context):
    content = context.spider.do_url(url)
    for link in extract_links(content):
        context.tasks.append(Task(url=link))
    context['content'] = content
```

新任务加入当前批次队列尾部，在本次 run_plan 中执行。框架不限制深度，需在代码中自行控制。

### 失败处理

任务失败时生成 `task1_failed.json`，包含错误信息和堆栈追踪。使用 `--retry-failed` 参数可重试失败任务，重试时会创建新的 Spider 实例。

---

## Parse 阶段

### 执行流程

1. Stage 自动加载最新 Action 阶段输出目录
2. 读取所有任务的 `.html` 和 `_action.json` 文件
3. 任务分发到多线程 Worker
4. Worker 执行 `@parse()` 装饰的函数
5. 结果保存到 `output/parse_{timestamp}/`

### 数据来源

- `context['content']` - 自动加载的HTML内容
- `context.get('input')` - Action阶段的result
- `context.task` - 原始Task

### 结果保存

每个任务生成以下文件：
- `task1.html` - HTML内容
- `task1_task.json` - 原始Task
- `task1_action.json` - action结果
- `task1_parse.json` - parse结果（来自 context['result']）

---

## Extract 阶段

### 执行流程

1. Stage 自动加载最新 Parse 阶段输出目录
2. 读取所有任务的 `_parse.json` 文件
3. 任务分发到多线程 Worker
4. Worker 执行 `@extract()` 装饰的函数
5. 不保存文件，只执行副作用操作

### 数据来源

- `context.get('input')` - Parse阶段的result
- `context.initial` - 共享资源（如数据库连接）

### 典型用途

- 数据库写入
- API调用
- 文件保存
- 发送通知

---

## 并发控制

| 阶段 | 并发方式 | 原因 |
|------|----------|------|
| Action | 多进程 | Spider需要独立进程，避免资源冲突 |
| Parse | 多线程 | 纯CPU计算，线程效率高 |
| Extract | 多线程 | IO密集型，线程即可 |

**竞态避免**：Action阶段多进程天然隔离；Parse/Extract每个任务处理不同文件，无竞态。

**Rate Limit**：`RATE_LIMIT` 控制任务进入队列的间隔，各Worker并行执行，实际并发数等于 `MAX_WORKERS`。

---

## 数据传递

```
initial_task()
    ↓
┌─────────────────────────────────────────────────────────┐
│ Action阶段                                               │
│   context.task = 原始Task                                │
│   context.spider = Spider实例                            │
│   → 设置 context['content'] = HTML                       │
│   → 设置 context['result'] = action结果                  │
└─────────────────────────────────────────────────────────┘
    ↓ 自动加载
┌─────────────────────────────────────────────────────────┐
│ Parse阶段                                                │
│   context.task = 原始Task                                │
│   context['content'] = HTML（自动加载）                   │
│   context['input'] = action结果（自动加载）               │
│   → 设置 context['result'] = parse结果                   │
└─────────────────────────────────────────────────────────┘
    ↓ 自动加载
┌─────────────────────────────────────────────────────────┐
│ Extract阶段                                              │
│   context.task = 原始Task                                │
│   context['input'] = parse结果（自动加载）                │
│   → 执行副作用操作                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 文件保存结构

```
output/
├── action_20241118_100000/
│   ├── task1.html
│   ├── task1_task.json
│   ├── task1_action.json
│   └── task1_failed.json      # 如果失败
│
└── parse_20241118_100100/
    ├── task1.html
    ├── task1_task.json
    ├── task1_action.json
    └── task1_parse.json
```

STORAGE_TIMESTAMP=False 时目录名不带时间戳，会覆盖之前的结果。

---

## 资源生命周期

**Spider**：在 Worker 中创建，处理完所有任务后自动关闭。异常退出时由操作系统回收。

**Context**：每个任务独立创建，任务完成后释放。

**Cookie/Session**：同一 Spider 实例内保持，跨 Worker 不共享。

---

## 任务依赖

| 场景 | 行为 |
|------|------|
| Action 失败 | 不生成 `.html`，Parse 找不到输入，跳过该任务 |
| Parse 失败 | 生成 `_failed.json`，Extract 找不到输入，跳过 |

各阶段独立执行，不回滚。部分失败时，成功的任务结果仍然保存。
