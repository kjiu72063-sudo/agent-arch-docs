---
title: 1-2 system prompt 机制
---

# 1-2 · system prompt 是如何决定 agent 行为的

system prompt 是"常驻说明书"，与每轮对话的临时内容分离；它决定了 agent 的**人设、能力边界、纪律**。

## 一次请求里装了什么

指令（system prompt，常驻） + 额外上下文（user 输入、项目规则、检索） + 工具（函数说明、调用历史） = **增强的 LLM**，每次请求都打包送给模型。

::: tip 关键点
"增强的 LLM = 指令 + 额外上下文 + 工具" 出自 Anthropic《Building effective agents》。system prompt 只是其中"指令"那一块。
:::

## 四个角色分工

| 角色 | 作用 | 特点 |
|---|---|---|
| **system** | 常驻说明书：人设、规则、输出纪律、边界 | 每一轮都带着；一次设定、长期生效 |
| **user** | 这一轮的请求 | 临时；每次不同 |
| **assistant** | 模型自己上一轮的回复 | 进入历史；供继续接话 |
| **tool result** | 模型调用工具后，工具返回的执行结果 | 回灌进下一轮请求（loop 的种子） |

## 从"一句话"到"一套"

真实 agent 的 system prompt 通常**分段拼装**，核心是"分块 + 按需 + 渐进披露"：

1. 分段 `PromptSection` 按 order 排序拼接（DeepSeek Harness）
2. 渐进式披露：入口是"地图"，细节按需展开
3. 规则文件（`AGENTS.md` / `CLAUDE.md`）注入
4. 模型每次请求带着这套指令执行

::: tip 要点
system prompt 决定 agent "是什么样的人 + 守什么规矩"；user 和工具结果决定它"这次干什么"。前者求稳，后者求准。
:::

::: info 【事实】
"分段 / 渐进披露"分别示例自 DeepSeek Harness（PromptSection 按 order 分段）与 harness engineering 的"地图而非手册"。详见 [事实源](/practice/compare)。
:::
