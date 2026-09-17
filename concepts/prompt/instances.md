---
title: 1-6 实例里的 prompt
---

# 1-6 · 在真实 agent 里看 prompt 怎么落地

::: info 难度分层 · 本页 = L0→L1（prompt 基础层）
L0 看懂概念与类比；L1 能照本页示例手写出可用 prompt。读完 1-1 ~ 1-7 即达成 Track A 的 L1 基线。
:::


把前面讲的抽象落进三个真实框架，看它们分别怎么组织"给模型看的字"。

## 三家对照

| 实例 | prompt 怎么组织 | 关键做法 |
|---|---|---|
| **Claude Code** | system prompt + 项目级 `CLAUDE.md` 注入 | "常驻说明书 + 项目规则"双轨，再叠加工具说明；权限/会话压缩影响内容进视图 |
| **Hermes** | System Prompt 工程模块（源码有专门章节） | 在框架里**显式管理** system prompt；与多模型适配、上下文管理并列为核心模块 |
| **DeepSeek Harness** | `PromptSection` 分段 + 变量插值 + 按 `order` 拼接 | 把 system prompt 拆成**可组合的段**，实现"地图而非手册"的渐进披露 |

## 三种组织形态（真实结构）

**① Claude Code：双轨注入**
```text
[常驻 system prompt]  身份 + 通用纪律 + 工具说明
        +
[项目 CLAUDE.md]     技术栈 / 测试命令 / 禁止事项 / 目录指针   ← 按目录层级加载
        ↓
每轮请求 = 上述两轨 + 本轮对话与工具结果
```
> 特点：**通用纪律与项目规则分离**——换项目只换 `CLAUDE.md`，system prompt 不动。

**② Hermes：把 prompt 当"工程模块"管**
```text
system_prompt/
├── base.md            # 基础人设
├── tools.md           # 工具说明段
└── policy.md          # 纪律与边界段
# 运行时按模型能力/场景选择性地拼装（多模型适配）
```
> 特点：**prompt 是一等公民**，有独立目录与拼装逻辑，可随模型/场景切换。

**③ DeepSeek Harness：分段 + 变量插值 + 排序**
```python
# 每段带 order 与变量，运行时插值后按序拼接
PromptSection(order=10, template="你是 {{role}}…", vars={"role": "工程师"})
PromptSection(order=20, template="{{project_rules}}")     # 注入 AGENTS.md
PromptSection(order=90, template="当前任务：{{task}}")     # 临时段放最后
```
> 特点：**可组合、可测试**——每段能单独改、单独断言，天然支持"渐进披露"。

## 一个共性公式

```text
给模型的整体指令
  = 常驻系统提示词（人设 + 纪律）
  + 项目规则注入（AGENTS.md / CLAUDE.md）
  + 按需分段（PromptSection / 渐进披露）
```

三者合起来要达到同一个目标：**清晰、可控、不臃肿**。

::: tip 启示
优秀 agent 的 prompt 都不是"一段话"，而是一套**分层、可组合、按需注入**的指令系统——这已是一只脚迈进 [harness engineering](/concepts/harness)：**把 prompt 当配置与代码来管理，而不是当作文来写**。
:::

## 小测验

::: details 点击展开题目与答案
**Q1（选择）**：Claude Code 把"通用纪律"与"项目规则"分离的好处是？  
A. 更短　B. 换项目只换 `CLAUDE.md`，system prompt 不动　C. 更省钱  
✅ B。

**Q2（判断）**：真实 agent 的 prompt 就是一大段文字。  
❌ 错。是分层、可组合、按需注入的指令系统。

**Q3（选择）**：DeepSeek Harness 用 `order` 字段的目的是？  
A. 好看　B. 决定各段拼接顺序（稳定段在前、临时段在后）　C. 加密  
✅ B。
:::

::: info 【事实】
> 来源：[sawzhang/deep-dive-claude-code](https://github.com/sawzhang/deep-dive-claude-code)（[S4](/practice/sources)）· [luyao618/Hermes-Source-Code-Study](https://github.com/luyao618/Hermes-Source-Code-Study)（[S3](/practice/sources)）· [iceyao](https://www.iceyao.com.cn/post/2026-08-13-deepseek-harness%E6%BA%90%E7%A0%81%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90/)（[S7](/practice/sources)）（覆盖：1-6）。上述结构为依据权威源的示意归纳。
:::

> 上一节：[1-5 策略④⑤⑥](/concepts/prompt/think-tools-test) ｜ 下一节：[1-7 常见坑 + 自检](/concepts/prompt/pitfalls)
