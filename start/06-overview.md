# 0-6 读懂总览图

前面 5 页铺垫了"零件"。现在把它们拼成全站 12 个知识点的**全貌图**——后面每一章，都是在放大这张图的某一个节点。

## 一句话概念

> 全站 12 个知识点 = **5 个概念主轴** + **1 个横切支柱** + **6 个落地实例**。  
> 三 Track（A 概念主轴 / B 实例专项 / C 复刻实战）就是按这条主线组织的。

## 12 知识点地图

| 类别 | 知识点 |
|---|---|
| **概念主轴（递进）** | 01 prompt → 02 context → 03 harness → 04 loop → 05 graph |
| **横切支柱** | 06 skill 体系架构 |
| **落地实例（6）** | Hermes · DeepAgent · OpenClaw · Claude Code · Codex · DeepSeek Harness |

## 图示：主轴 + 横切 + 实例

```mermaid
flowchart LR
  P["01 prompt\n指令层"] --> C["02 context\n增强LLM"]
  C --> H["03 harness\n外壳/约束"]
  H --> L["04 loop\n迭代循环"]
  L --> G["05 graph\n图编排"]
  S["06 skill\n横切支柱"] -. "贯穿中段" .-> H
  S -. .-> L
  H --> I1["Hermes"]
  H --> I2["OpenClaw"]
  L --> I3["DeepAgent"]
  L --> I4["Claude Code"]
  L --> I5["Codex"]
  L --> I6["DeepSeek Harness"]
  style P fill:#4f46e5,color:#fff
  style C fill:#4f46e5,color:#fff
  style H fill:#0d7d6e,color:#fff
  style L fill:#0d7d6e,color:#fff
  style G fill:#b45309,color:#fff
  style S fill:#b45309,color:#fff
```

## 怎么读这张图

- **从左到右是递进主轴**：从"模型看到什么"（prompt/context） → "用什么外壳承载 Agent"（harness） → "外壳里怎么循环"（loop） → "多循环怎么编排成复杂流程"（graph）。
- **skill 是横切**：它不在这条线上独立成点，而是能力复用的"插件"，贯穿 context↔harness↔loop。
- **6 个实例挂在主轴上**：每个实例都"凸显"某一层（如 OpenClaw 凸显 harness、DeepAgent 凸显 graph+loop），不是孤立的产品介绍。

::: warning 关于顺序的说明
**主轴"prompt→context→harness→loop→graph"这个顺序，是本站的结构化假设（【推断】）**，理由是从"输入内容"递进到"承载与编排"。它能被 6 个实例反向印证，但**并非官方唯一定义**——你可以用自己的心智模型替换它，只要前后自洽。
:::

## 小测验

::: details 点击展开题目与答案
**Q1（选择）**：skill 体系在图中是？  
A. 主轴上的一个端点　B. 横切支柱，贯穿中段　C. 一个独立实例  
✅ B。它是横切能力扩展，不是主轴端点。

**Q2（判断）**：6 个实例是平铺孤立的产品介绍。  
❌ 错。每个实例挂靠主轴某一层，是"体系落地的例子"。

**Q3（判断）**：主轴顺序 prompt→…→graph 是官方强制定义。  
❌ 错。这是本站的【推断】结构化假设，非官方唯一标准。
:::

::: tip 本页要点
全站 = 5 主轴 + 1 横切 + 6 实例。后面每一章都是放大这张图的一个节点；主轴顺序是本站的【推断】，你也可自建心智模型。
:::

> 上一步：[0-5 什么是 Agent](./05-agent) ｜ 回到：[Track 0 总入口](./)
