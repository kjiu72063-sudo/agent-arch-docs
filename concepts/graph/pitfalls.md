---
title: 5-2 graph 常见坑 + 自检
---

# 5-2 · graph 常见坑 + 掌握自检

graph 最容易在"滥用图 / reducer 理解错 / 缺 checkpoint"上翻车。本节给四个常见坑 + 产物化三档。

## 常见坑

- **坑① 滥用图**：单线性任务也上 StateGraph → 复杂度白增。**解法**：先问"需要分支/并行/多角色吗？"不需要就用单 loop（见 [04](/concepts/loop)）。
- **坑② reducer 理解错**：以为带 reducer 的字段是"最后一次覆盖"，实际是**合并**（如 `operator.add` 累加消息）。**解法**：用 `Annotated` + reducer 明确每个字段的合并语义（见 [5-1](/concepts/graph/mechanism)）。
- **坑③ 条件边路由函数返回值与映射表不符**：`route()` 返回的值不在 `{...}` 映射里 → 运行时找不到目标节点报错。**解法**：返回值和映射 key 严格一致。
- **坑④ 缺 checkpoint**：长任务/多线程会话不落 checkpoint → 中断即丢，无法续跑。**解法**：`compile(checkpointer=...)` + 设 `thread_id`。

## 产物化三档自检

| 档位 | 必须提交的产物 |
|---|---|
| **了解** | 区分 workflow 与 agent/graph，说出 Node/Edge/State/Reducer 各自是什么 |
| **熟悉** | 用 LangGraph 搭一个**含条件边 + reducer** 的 3 节点 StateGraph，`compile()` 后 `invoke()` 跑通，并说明 reducer 如何合并 |
| **精通** | 为真实多 agent 任务选型（routing / parallel / orchestrator-worker），实现带 checkpoint/persistence 的图，并判断它能否降级为单 loop |

::: tip 达标判断
"熟悉"档硬指标：你能让 `messages` 在多个节点追加后**看到累加结果**（reducer 生效），并让条件边按 `approved` 真/假走不同分支——这验证了 reducer 与条件边真的跑起来了。
:::

::: info 下一章承接
图的节点可以是一个 loop，loop 里可以调用一个"能力单元"。这种可复用、按需注入的能力，就是横切主轴的 [06 skill 体系架构](/concepts/skill)。
:::

> 上一节：[5-1 graph 机制详解](/concepts/graph/mechanism) ｜ 下一章：[06 skill 体系架构](/concepts/skill)