---
layout: home

hero:
  name: Agent 架构知识体系
  text: 从「会用」到「会造」Agent
  tagline: 一条概念主轴（prompt → context → harness → loop → graph）＋ 一根横切支柱（skill 体系）＋ 六个真实框架落地。
  actions:
    - theme: brand
      text: 进入 prompt 章节
      link: /concepts/prompt
    - theme: alt
      text: 新手前置
      link: /start/

features:
  - icon: 🧠
    title: Track A · 概念主轴
    details: prompt / context / harness / loop / graph + skill 横切。从"模型看到什么"到"复杂流程怎么编排"。
  - icon: 🏗️
    title: Track B · 框架实例专项
    details: Hermes / DeepAgent / OpenClaw / Claude Code / Codex / DeepSeek Harness，看真实框架怎么落地。
  - icon: 🧩
    title: Track C · 复刻实战
    details: 7 维对比矩阵、两段式学习路径、掌握自检、自研 harness。
  - icon: 🗺️
    title: 图多字少 · 关系图即导航
    details: 每个知识点讲清在体系中的位置；硬断言标注【事实】/【推断】来源。
---

## 推荐阅读路径（从 0 到 1）

1. **第一步**：读「新手前置」，搞懂 LLM / token / 工具调用 / 什么是 Agent。
2. **第二步**：沿概念主轴走 `prompt → context → harness → loop → graph`。
3. **第三步**：进 Track B 看六个真实框架如何落地。
4. **最后**：用 Track C 的对比矩阵选型，并尝试自研。

## 你将学到什么

面向「要动手实现」的读者，而非只看概念。你会系统理解 Agent 的指令层、上下文、外壳、循环与图编排，并能对照六个真实框架反向印证。

::: warning 本站定位（务必先读，避免误会）
这是一份 **Agent 架构「概念地图 + 权威源导航 + 部分可运行验证」**，**不是**完整的产品文档，也暂不宣称"完备知识体系"。请按如下预期使用：

- **覆盖广度完整**：12 个知识点（5 主轴 + skill + 6 实例）均有页面与关系图；
- **深度分层**：每章分 `机制 → 设计决策 → 坑与自检` 三层。多数内容为「概念/机制级」；**设计决策层**引入了权威源的决策表与代码，但**内容量仍只是权威原文的一部分**（如 loop 章 ≈ cnblogs 原文的 2/3，部分实例章 ≈ 权威源码解析的 1/6）；
- **验证边界**：`concepts/*/gate/` 下的脚本可本地运行，但**验证范围有限**——
  - `graph_gate`：真实验证（真 LangGraph：条件边/reducer/checkpoint/Send）；
  - `context_gate`：真实验证（真 tiktoken 计数）；
  - `harness_gate` / `skill_gate`：对 fixtures **真实文件**断言；
  - `loop_gate`：只验证**确定性控制流**（三刹车/Goal 短路），**不验证 LLM 产出质量**。
- **权威源**：每章标注【事实】出处（Anthropic / OpenAI / LangGraph / 腾讯云 / iceyao 等）。要深入请**直接读原文**，本站负责的是"坐标与入口"。
:::

## 内容现状（v0.7）

| Track | 状态 | 说明 |
|---|---|---|
| Track 0 新手前置 | ✅ 完成 | 7 页（含 Track 0→A 难度阶梯说明） |
| Track A 概念主轴 | ✅ 完成 | prompt(7 子页) + 02–06 各 `机制/设计决策/坑与自检` 三子页 + gate |
| Track B 框架实例 | ⚠️ 部分源码级 | deepagent / claude-code / deepseek-harness / hermes 已有真实代码或配置；其余偏概念映射 |
| Track C 复刻实战 | ✅ 完成 | 对比矩阵 / 学习路径 / 掌握自检 / 自研 harness |

## 常见问题

**这套体系是什么？**
一条"概念主轴 + 横切支柱 + 六个落地实例"：从"模型看到什么"递进到"复杂流程如何编排"，再用六个真实框架反向印证。

**为什么先学 prompt？**
prompt 是整条主轴的基座——后面所有工程（上下文、工具、循环）最终都要通过一段文字送到模型面前。连 prompt 都写不对，后面再花哨也白搭。

**学完能做什么？**
阶段 A **评用**：能选型、能搭可跑工程；阶段 B **自研**：能设计 harness + loop + graph + skill 体系，画出整体架构。

**和某个产品的官方文档是什么关系？**
不是任何一家产品的官方文档，而是把多个框架放到同一套概念坐标系下对比、归纳出的"元知识"。
