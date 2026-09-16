---
title: 6-3 skill 常见坑 + 自检
---

# 6-3 · skill 常见坑 + 掌握自检

skill 体系最容易在"全量注入 / skill 写太薄 / 无版本评审"上翻车。本节给四个常见坑 + 产物化三档。

## 常见坑

- **坑① 全量注入撑爆上下文**：把所有 skill 一次性塞进 context → 窗口爆、注意力稀释。**解法**：按需 discovery + 命中才注入（见 [6-1](/concepts/skill/mechanism)）。
- **坑② skill 写太薄**：SKILL.md 只有一句话"帮我做 X"→ 模型无从执行。**解法**：补 `触发条件 / 执行步骤 / 输出格式 / 边界约束 / 失败处理`。
- **坑③ 边界不清**：把"确定函数"当 skill、或把 skill 当 context → 执行责任混乱。**解法**：明确 tool（执行）/ context（信息）/ skill（能力说明）三者边界。
- **坑④ 无版本评审**：skill 改坏依赖它的 agent 无感知。**解法**：版本号 + 变更记录 + 评审流程；用装饰器做横切，不动原逻辑。

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