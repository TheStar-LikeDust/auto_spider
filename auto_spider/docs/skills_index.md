# Skills Index

本文档是 `skills/` 目录的简要目录。

> **核心规范**: 请先阅读 `docs/ai-assistant-guide.md`

---

## 分组结构

```
plan-*      规划类：生成计划
sense-*     感知类：侦察页面、分析数据
write-*     编写类：编写 action/parse/extract
exec-*      执行类：运行和验证
log-*       日志类：任务记录
```

---

## plan-* 规划类

| Skill | 职责 |
|-------|------|
| **plan-generate** | 生成 plan 模板文件 |

---

## sense-* 感知类

| Skill | 职责 | 触发时机 |
|-------|------|----------|
| **sense-scout** | 侦察页面，获取选择器和结构 | 新页面 |
| **sense-page-info** | 分析 page_info，理解交互元素 | scout/action 后 |
| **sense-clean-html** | 分析 clean_html，理解 DOM 结构 | action 后 |

---

## write-* 编写类

| Skill | 职责 | 输出 |
|-------|------|------|
| **write-action** | 编写下载 HTML 代码 | `context['content']` |
| **write-parse** | 编写提取数据代码 | `context['result']` |
| **write-extract** | 编写持久化代码 | 副作用 |

---

## exec-* 执行类

| Skill | 职责 | 流程 |
|-------|------|------|
| **exec-run-verify** | 运行阶段、验证输出、决策迭代 | 运行 → 检查 → 修复/继续 |

---

## log-* 日志类

| Skill | 职责 | 模式 |
|-------|------|------|
| **log-task** | 创建和更新任务日志 | 追加模式 |

---

## 层级关系

```
Level 1: 规划
    plan-generate      生成计划
    sense-scout        侦察页面
        ├── sense-page-info     分析交互元素
        └── sense-clean-html    分析 HTML 结构
            ↓
Level 2: 编写
    write-action       编写 action
    write-parse        编写 parse
    write-extract      编写 extract
            ↓
Level 3: 执行
    exec-run-verify    运行 → 验证 → 迭代
            ↓
    log-task           记录每步结果
```

---

## 设计原则

**一个 Plan 干一件事**: 每个 plan 只完成一个明确的目标。复杂任务拆分为多个 plan。

示例：
- `plan_scout_shop` - 侦察商品页面
- `plan_list` - 抓取列表页
- `plan_detail` - 抓取详情页
