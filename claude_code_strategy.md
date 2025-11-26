# Auto Spider 爬取策略

## 核心原则

**侦察兵先行，逐步验证，记录过程。**

每一步：执行 → 查看输出 → 更新文档 → 决定下一步

---

## 文档记录

每个爬取项目创建 `docs/网站名_crawl.md`，按时间顺序记录：

```
[网站名] 爬取记录

目标: https://xxx.com
数据: 需要提取的内容描述

---
2024-11-20 14:30
目标: 侦察目标页面
行为: 创建plan_recon.py, 运行获取HTML
结果: 成功, HTML 52KB, 数据在HTML中
输出: steps_xxx/output/recon_action_20241120/

---
2024-11-20 14:45
目标: 分析页面结构
行为: 搜索关键词, 定位数据标签
结果: 数据在 //div[@class="item"] 下, 共3个字段
决定: 用RequestSpider + XPath

---
2024-11-20 15:00
目标: 单页验证
行为: 创建plan_xxx.py, 1个URL测试
结果: action成功, parse提取12条数据, 正确
输出: steps_xxx/output/action_20241120/

---
2024-11-20 15:30
目标: 扩展验证
行为: 增加到5个URL
结果: 5/5成功, 共提取58条数据
问题: 无

---
完成
总数据: 58条
输出: steps_xxx/output/parse_20241120/
```

每完成一步追加记录。

---

## Phase 1: 侦察

创建 `plan_recon.py`，只做一件事：获取目标URL的HTML。

```python
# action只需要：
response = context.spider.do_url(url)
context['content'] = response.text
```

运行后查看 `steps_项目名/output/recon_action_*/target.html`

**验证**：
- HTML正常获取？
- 目标数据在HTML中？（搜索关键词验证）
- 如果数据不在 → 可能需要PlaywrightSpider

---

## Phase 2: 分析

在HTML中搜索目标数据，确定：
- 数据所在的HTML标签
- XPath或CSS选择器

**决策表**：
| 情况 | 方案 |
|------|------|
| 数据在HTML中 | RequestSpider + XPath |
| 需要JS渲染 | PlaywrightSpider |
| 有分页 | 增量任务处理 |
| 列表页+详情页 | 两阶段爬取 |

---

## Phase 3: 单页验证

创建正式plan，`initial_task()` 只放1个URL。

先只跑action：
```bash
python plan_xxx.py
```
查看 `steps_xxx/output/action_*/` 确认HTML正确。

再跑parse，查看 `*_parse.json` 确认数据提取正确。

**验证**：提取的数据数量、内容是否符合预期

---

## Phase 4: 扩展

`initial_task()` 增加更多URL（3-5个），运行验证：
- 所有页面都成功
- 提取逻辑对不同页面都有效

---

## Phase 5: 增量爬取（如需要）

在action中发现新链接时添加任务：
```python
context.tasks.append(Task(name='detail_1', url=new_url))
```

运行后检查是否发现了新任务。

---

## 错误排查

| 问题 | 检查 | 可能原因 |
|------|------|----------|
| HTML为空 | 查看status_code | JS渲染/登录/反爬 |
| Parse为空 | grep搜索HTML | XPath错误 |
| 部分失败 | 对比文件数和任务数 | 超时/限速 |

---

## 检查清单

- [ ] Phase 1: HTML获取成功，数据在其中
- [ ] Phase 2: 确定XPath，选择Spider类型
- [ ] Phase 3: 单页action+parse验证通过
- [ ] Phase 4: 多页验证通过
- [ ] Phase 5: 增量任务正确（如适用）
