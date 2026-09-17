---
title: 6-3 skill 常见坑 + 自检
---

# 6-3 · skill 常见坑 + 掌握自检

::: tip 难度分层 · 本页 = 全档自检（L0–L2）
用下方**三档表**先定位自己在哪一级；「常见坑」与难度无关，任何档都该看。
:::


skill 体系最容易在"全量注入 / skill 写太薄 / 无版本评审"上翻车。本节给四个常见坑 + 产物化三档。

## 常见坑

- **坑① 全量注入撑爆上下文**：把所有 skill 一次性塞进 context → 窗口爆、注意力稀释。**解法**：按需 discovery + 命中才注入（见 [6-1](/concepts/skill/mechanism)）。
- **坑② skill 写太薄**：SKILL.md 只有一句话"帮我做 X"→ 模型无从执行。**解法**：补 `触发条件 / 执行步骤 / 输出格式 / 边界约束 / 失败处理`。
- **坑③ 边界不清**：把"确定函数"当 skill、或把 skill 当 context → 执行责任混乱。**解法**：明确 tool（执行）/ context（信息）/ skill（能力说明）三者边界。
- **坑④ 无版本评审**：skill 改坏依赖它的 agent 无感知。**解法**：版本号 + 变更记录 + 评审流程；用装饰器做横切，不动原逻辑。

## 反模式对照（配置/代码级）

### 坑① 全量注入 —— 按需 discovery，命中才注入

```python
# ✕ 反模式：把 30 个 skill 的正文全塞进 system prompt
system = base + "\n".join(skill.body for skill in ALL_SKILLS)   # 窗口爆、注意力稀释

# ✓ 正解：只常驻"目录"（name+description），命中后再注入正文
catalog = "\n".join(f"- {s.name}: {s.description}" for s in ALL_SKILLS)
# 模型按目录选中 skill → 才把该 skill 正文注入
if hit := match_skill(user_intent):
    context += hit.body
```

### 坑② skill 写太薄 —— 五个必备段落

```markdown
<!-- ✕ 反模式 -->
# code-review
帮我审查代码。

<!-- ✓ 正解：触发 / 步骤 / 输出格式 / 边界 / 失败处理 -->
# code-review
## 触发条件
当用户要求 review 代码或提供 diff 时使用。
## 执行步骤
1. 读取 diff；2. 按 P0/P1/P2 分级检查；3. 输出问题清单。
## 输出格式
JSON：{issues:[{level,file,line,desc}], verdict}
## 边界与约束
只读审查，不改文件；发现敏感操作标为 P0 并停止。
## 失败处理
无法定位问题时提问，不猜测。
```

### 坑③ 边界不清 —— tool / context / skill 分工

| 类型 | 职责 | 反例 |
|---|---|---|
| **tool** | 真的执行动作（读文件、发请求） | 把"读文件"写成 skill → 模型拿到说明书却没有执行能力 |
| **context** | 提供信息（资料、规则） | 把长规范塞进 skill → 每次注入都占预算 |
| **skill** | 说明"这类任务该怎么做" | 把 skill 当工具 → 期待它自己执行 |

### 坑④ 无版本评审 —— 版本号 + 装饰器横切

```python
# ✕ 反模式：改动直接改原函数，依赖方无感知、无法回滚
def review(code):
    ...  # 直接改这里，所有调用方一起受影响

# ✓ 正解：语义化版本 + 变更记录；横切用装饰器，不动原逻辑
SKILL_VERSION = "1.2.0"          # 配合 CHANGELOG 与评审
def with_logging(fn):            # 装饰器：加日志/缓存，不侵入原实现
    def wrapper(*a, **k):
        log("start"); r = fn(*a, **k); log("end"); return r
    return wrapper

@with_logging
def review(code): ...
```

## 产物化三档自检

| 档位 | 必须提交的产物 |
|---|---|
| **了解** | 说清 skill 与 tool/context/plugin 的边界，知道它"横切"主轴 |
| **熟悉** | 写一个结构完整的 `SKILL.md`（触发/步骤/输出/边界/失败），并跑通"被 discovery 命中 → 注入 → agent 用它完成一个任务" |
| **精通** | 为团队设计 skill 库：分层（应用/组合/执行/基础）+ 组合/策略/装饰器模式 + 版本评审流程，让 skill 可发现、可注入、可版本化 |

::: tip 达标判断
"熟悉"档硬指标：你写的 SKILL.md 能被另一个 agent **仅凭 description 正确命中并照着做完**——这验证了"能力说明"真的够用，而不只是好看。
:::

::: info 进入实例
到这里概念主轴（01–06）讲完了。接下来在 [Track B · 框架实例专项](/instances/hermes) 里，看 Hermes / DeepAgent / Claude Code / DeepSeek Harness 等真实框架，分别怎么实现这套 harness / loop / graph / skill。
:::

> 上一节：[6-2 skill 设计决策 + 验证](/concepts/skill/design) ｜ 进入实例：见 [Track B · 框架实例专项](/instances/hermes)