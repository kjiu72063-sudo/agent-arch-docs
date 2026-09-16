---
title: 1-6 实例里的 prompt
---

# 1-6 · 在真实 agent 里看 prompt 怎么落地

把前面讲的抽象落进三个真实框架，看它们分别怎么组织"给模型看的字"。

## 三家对照

| 实例 | prompt 怎么组织 | 关键做法 |
|---|---|---|
| **Claude Code** | system prompt + 项目级 `CLAUDE.md` 注入 | "常驻说明书 + 项目规则"双轨，再叠加工具说明；权限/会话压缩影响内容进视图（经源码剖析） |
| **Hermes** | System Prompt 工程模块（源码有专门章节） | 在 agent 框架里显式管理系统 prompt；与多模型适配、上下文管理一起作为核心模块设计 |
| **DeepSeek Harness** | `PromptSection` 分段、变量插值、按 order 排序拼接 | 把 system prompt 拆成可组合的"段"，用表达式拼装；实现"地图而非手册"的渐进披露 |

::: info 【事实】
来源：sawzhang《深入理解 Claude Code 源码》；Hermes 源码分析（System Prompt 工程章节）；iceyao《DeepSeek Harness 源码深度解析》。
:::

## 一个共性

常驻系统提示词（人设 + 纪律） ＋ 项目规则注入（`AGENTS.md` / `CLAUDE.md`） ＋ 按需分段（`PromptSection` / 渐进披露） ＝ 给模型的整体指令（清晰、可控、不臃肿）。

::: tip 启示
优秀 agent 的 prompt 都不是"一段话"，而是一套**分层、可组合、按需注入**的指令系统——这已是一只脚迈进 `harness engineering`。
:::
