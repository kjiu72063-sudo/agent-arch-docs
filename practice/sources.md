---
title: 事实源清单
---

# 事实源清单

本站正文里每一条【事实】标注，都应当能在本页找到对应的**可点击来源**。**本页是全书唯一的来源索引**——若你在某章看到"详见事实源"，指的就是这一页。

::: tip 怎么用这一页
1. **核验**：读到【事实】时，回到本页核对来源与"直读状态"——区分"逐字读过"与"据转述归纳"。
2. **深入**：表里的链接是**权威原文入口**；本站负责的是"坐标与入口"（见 [首页定位](/README)）。
3. **复核**：Track C 的 [统一对比矩阵](/practice/compare) 评分若被修订，以本页来源为准逐格复核。
:::

## 一、框架权威源（本站实例章的事实依据）

| # | 权威源 | 类型 | 覆盖章节 | 直读状态 | 链接 |
|---|---|---|---|---|---|
| S1 | openclaw-docs | 文档站 | [06 skill](/concepts/skill) · [OpenClaw 实例](/instances/openclaw) | 站点抓取 | [openclaw-docs.dx3n.cn](https://openclaw-docs.dx3n.cn/) |
| S2 | 《Loop Engineering 完全指南》 | 技术博客 | [04 loop](/concepts/loop) | 归纳（图表+案例） | [cnblogs.com/xiaobaiysf/p/21964451](https://www.cnblogs.com/xiaobaiysf/p/21964451) |
| S3 | Hermes 源码研究 | GitHub 仓库 | [Hermes 实例](/instances/hermes) · [05 graph](/concepts/graph) | 仓库（System Prompt 工程章） | [github.com/luyao618/Hermes-Source-Code-Study](https://github.com/luyao618/Hermes-Source-Code-Study) |
| S4 | deep-dive-claude-code | GitHub 仓库 | [Claude Code 实例](/instances/claude-code) | 仓库（源码剖析） | [github.com/sawzhang/deep-dive-claude-code](https://github.com/sawzhang/deep-dive-claude-code) |
| S5 | Codex 剖析 | 技术博客 | [Codex 实例](/instances/codex) · [03 harness](/concepts/harness) | 归纳 | [cnblogs.com/smartloli/p/20684447](https://www.cnblogs.com/smartloli/p/20684447) |
| S6 | DeepSeek Harness 解析 | CSDN 博客 | [DeepSeek Harness 实例](/instances/deepseek-harness) | 归纳 | [blog.csdn.net/ChesterXue/article/details/163745888](https://blog.csdn.net/ChesterXue/article/details/163745888) |
| S7 | DeepSeek Harness 源码深度解析 | 技术博客 | [02 context](/concepts/context) · [DeepSeek Harness 实例](/instances/deepseek-harness) | 归纳（context/spill/compaction 三件套） | [iceyao.com.cn/post/2026-08-13-…](https://www.iceyao.com.cn/post/2026-08-13-deepseek-harness%E6%BA%90%E7%A0%81%E6%B7%B1%E5%BA%A6%E8%A7%A3%E6%9E%90/) |
| S8 | harness-engineering | GitHub 仓库 | [03 harness](/concepts/harness) | 仓库 | [github.com/deusyu/harness-engineering](https://github.com/deusyu/harness-engineering) |
| S9 | 腾讯云开发者 · skill 文章 | 技术文章 | [06 skill](/concepts/skill) | 文章 | [cloud.tencent.com/developer/article/2646885](https://cloud.tencent.com/developer/article/2646885) |
| S10 | LangChain deepagents 实践 | CSDN 博客 | [DeepAgent 实例](/instances/deepagent) | 归纳 | [blog.csdn.net/weixin_44733966/article/details/156938858](https://blog.csdn.net/weixin_44733966/article/details/156938858) |

## 二、通用参考（跨框架的权威共识）

| # | 来源 | 类型 | 覆盖章节 | 直读状态 | 链接 |
|---|---|---|---|---|---|
| G1 | Anthropic《Building effective agents》 | 官方文章 | [01 prompt](/concepts/prompt) · [02 context](/concepts/context) | 引用其结论 | [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/engineering/building-effective-agents) |
| G2 | OpenAI 提示工程指南 | 官方文档 | [01 prompt](/concepts/prompt) | ⚠️ **未直读**（抓取被 403） | [platform.openai.com/docs/guides/prompt-engineering](https://platform.openai.com/docs/guides/prompt-engineering) |
| G3 | DeepLearning.AI 提示工程课程 | 课程 | [01 prompt](/concepts/prompt) | 参考 | [deeplearning.ai](https://www.deeplearning.ai/) |
| G4 | LangGraph 官方文档 | 官方文档 | [05 graph](/concepts/graph) | 引用 API 语义 | [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/) |

## 三、直读状态说明（重要）

本站对来源的"直读程度"分三档，**请据此判断可信度**：

| 状态 | 含义 | 本站对应写法 |
|---|---|---|
| **逐字直读** | 正文内容直接来自原文 | 可标注为【事实】并给出原文级细节 |
| **归纳** | 依据原文转述/结构化归纳（图表、案例、机制） | 标注【事实】，但细节以原文为准 |
| **未直读** | 抓取失败或仅据二次资料 | 必须显式声明（如 G2） |

> 凡本站代码块标 `【示意实现】` 者，均为**依据来源归纳的示意代码**，非原文逐字复制——照抄前请以官方文档为准（尤其配置项与 API 签名）。

### 「源码级」称号的准入规则

为避免标签与内容不符，本站规定：

| 称号 | 准入条件 | 当前满足者 |
|---|---|---|
| **源码级** | 小节内**含 ≥3 处 file-path 级引用**（`packages/…`、`src/…`、具体文件名） | 仅 [DeepSeek Harness](/instances/deepseek-harness) |
| **配置级 / 示例级** | 有可抄用配置或可运行示例，但**未给到路径级定位** | Codex、Claude Code、OpenClaw、DeepAgent |
| **导读级** | 只给检索锚点与阅读方向 | Hermes |

> 未能满足准入的章节**不得使用"源码级"字样**——这是本站的自律规则，也是 Track B 深度审查后的整改项。

## 四、引用格式约定

全书正文引用统一采用：

```text
> 来源：[作者/站名](URL)（覆盖：x-1 / x-2）
```

例如：
```text
> 来源：[iceyao](https://www.iceyao.com.cn/post/2026-08-13-…/)（覆盖：2-1 / 2-2）
```

这样做的目的：**让来源覆盖度可机器校验**（每条引用都带可点击 URL 与章节号），避免"只在文字里提来源名"。

> 上一页：[掌握自检](/practice/selfcheck) ｜ 下一页：[统一对比矩阵](/practice/compare)
