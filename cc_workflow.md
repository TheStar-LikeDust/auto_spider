# Auto Spider 工作流程

本文档定义爬取任务的执行流程和记录规范。

---

## 核心原则

**先探索，后建设，每步记录。**

---

## Plan 创建原则

### 一个plan处理一种页面

- 目录页（列表页）：创建 `plan_xxx_list.py`，只提取详情页链接
- 详情页：创建 `plan_xxx_detail.py`，提取具体数据

### 何时创建plan

- 需要保存数据时才创建plan
- 探索阶段使用单文件plan（`--single-file`），不需保存

### 典型流程

```
目标网站 → 探索首页 → 发现目录页 → plan_xxx_list 提取链接
                                    ↓
                          发现详情页 → plan_xxx_detail 提取数据
```

---

## 执行流程

### Phase 1: 探索

目标：了解页面结构，确认数据位置。

1. 创建单文件探索plan：`python -m auto_spider generate explore_xxx --single-file`
2. 修改 `initial_task()` 放入目标URL
3. 运行：`python plan_explore_xxx.py`
4. 查看HTML，分析页面结构

**分析结果**：
- 这是目录页 → 创建 list plan，提取详情页链接
- 这是详情页 → 创建 detail plan，提取具体数据
- 需要JS渲染 → 使用 PlaywrightSpider（默认）

### Phase 2: 单页验证

1. 创建正式plan（带steps包）
2. `initial_task()` 只放1个URL
3. 运行action，检查HTML
4. 运行parse，检查提取结果

### Phase 3: 扩展验证

1. 增加到3-5个URL
2. 验证所有页面成功
3. 确认提取逻辑通用

### Phase 4: 完整运行

全量URL运行。

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
