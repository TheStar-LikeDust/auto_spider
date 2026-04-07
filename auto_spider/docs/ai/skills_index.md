# Skills Index

本文档是 `skills/` 目录的简要目录。

> **核心规范**: 请先阅读 `docs/ai/ai-assistant-guide.md`

---

## 分组结构

```
sense-*     感知类：侦察页面、分析数据（第一步）
plan-*      规划类：生成计划
write-*     编写类：编写 action/parse/extract
exec-*      执行类：运行和验证
analyze-*   分析类：复杂分析用独立脚本
```

---

## sense-* 感知类

| Skill | 目录 | 职责 | 触发时机 |
|-------|------|------|----------|
| **sense-scout** | `sense-scout/skill.md` | 侦察页面，获取选择器和结构 | **第一步**，新页面 |
| **sense-page-info** | `sense-page-info/skill.md` | 分析 page_info，理解交互元素 | scout 后 |
| **sense-clean-html** | `sense-clean-html/skill.md` | 分析 cleaned_html，理解 DOM 结构 | scout 后 |

---

## plan-* 规划类

| Skill | 目录 | 职责 |
|-------|------|------|
| **plan-generate** | `plan-generate/SKILL.md` | 生成 plan 模板文件（默认单文件） |

---

## write-* 编写类

| Skill | 目录 | 职责 | 输出 |
|-------|------|------|------|
| **write-action** | `write-action/SKILL.md` | 编写下载 HTML 代码 | `context['content']` |
| **write-parse** | `write-parse/SKILL.md` | 编写提取数据代码 | `context['result']` |
| **write-extract** | `write-extract/SKILL.md` | 编写持久化代码 | 副作用 |

---

## exec-* 执行类

| Skill | 目录 | 职责 | 流程 |
|-------|------|------|------|
| **exec-run-verify** | `exec-run-verify/SKILL.md` | 运行阶段、验证输出、决策迭代 | 运行 → 检查 → 修复/继续 |

---

## analyze-* 分析类

| Skill | 目录 | 职责 |
|-------|------|------|
| **analyze-script** | `analyze-script/skill.md` | 复杂分析拆为独立脚本 |

---

## 层级关系

```
Level 1: 侦察
    sense-scout        侦察页面（always first）
        ├── sense-page-info     分析交互元素
        └── sense-clean-html    分析 HTML 结构
            ↓
Level 2: 规划 + 编写
    plan-generate      生成 plan 模板
    write-action       编写 action
    write-parse        编写 parse
    write-extract      编写 extract
            ↓
Level 3: 执行
    exec-run-verify    运行 → 验证 → 迭代
```

辅助工具（任意阶段可用）：
- `analyze-script` — 复杂分析拆为独立脚本

---

## 设计原则

**一个 Plan 干一件事**: 每个 plan 只完成一个明确的目标。复杂任务拆分为多个 plan。

示例：
- `scout_shop` — 侦察商品页面
- `shop_list` — 抓取列表页
- `shop_detail` — 抓取详情页
