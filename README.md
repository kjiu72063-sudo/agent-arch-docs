# Agent 架构知识体系 · 文档教学站

> 从「会用」到「会造」Agent —— **概念主轴 + 实例专项 + 复刻实战** 一体化的 VitePress 教学文档站。

本仓库对标优秀的开源 Agent 文档站（如 openclaw-docs），用 **「图多字少 · 关系图即导航」** 的设计法则，把 Agent 架构知识梳理成一条可递进、可自检的主线。

---

## ⚠️ 定位与边界（请先读）

这是一份 **Agent 架构「概念地图 + 权威源导航 + 部分可运行验证」**，**不是**完整的产品文档，也**暂不宣称"完备知识体系"**。预期如下：

- **广度完整**：12 个知识点（5 主轴 + skill + 6 实例）均有页面与关系图。
- **深度分层**：每章分 `机制 → 设计决策 → 坑与自检`。设计决策层引入权威源的决策表与代码，但**内容量仍是权威原文的一部分**（如 loop 章 ≈ cnblogs 原文 2/3，部分实例章 ≈ 权威源码解析 1/6）。
- **验证边界**：`concepts/*/gate/` 脚本可本地运行，但范围有限——
  - `graph_gate`：真实验证（真 LangGraph）；`context_gate`：真实验证（真 tiktoken）；
  - `harness_gate` / `skill_gate`：对 fixtures 真实文件断言；
  - `loop_gate`：**只验证确定性控制流（三刹车/Goal 短路），不验证 LLM 产出质量**。
- **深入请读原文**：每章标注【事实】出处；**全部来源集中在 [事实源清单](practice/sources.md)**（含 URL、覆盖章节、直读状态），正文引用统一格式 `> 来源：[作者](URL)（覆盖：x-1）`。

## ✅ 验收口径（可机器校验）

本站的质量标准不是"字符数"，而是**可检查的四项硬指标**（防止用模板灌水掩盖真实差距）：

| 指标 | 阈值 | 检查方式 |
|---|---|---|
| 权威源落地率 | 用户给定的权威源 **100%** 出现在 `practice/sources.md` 且带 URL | 全仓 grep vs sources 表 |
| 死链 | 指向"事实源"的链接 **0 个**指向非来源页 | 链接目标检查 |
| Track 体量比 | Track A : Track C **≤ 6 : 1** | 字符统计 |
| 实例章真实代码块 | **每章 ≥ 3 个**（不含 mermaid） | 代码块语言统计 |
| 引用完整性 | 引用块 **100% 带可点击 URL** | 格式检查 |

> 已达成：来源 100% 落地（S1–S10）；Track A:C ≈ 3.8:1；6 个实例章各 3 个真实代码块（此前均值 1.5）。

---

## ✨ 特性

- **图多字少**：主干用 Mermaid 关系图讲清楚，文字只补齐无法画出来的关键点。
- **三层递进**：每章 `机制详解 → 设计决策 → 坑与自检`，难度从"会用"到"会设计"递进。
- **可运行 gate**：`concepts/*/gate/` 下有可本地运行的验收脚本（范围见上）。
- **三级标注**：事实来源、结构化推断、工程建议严格区分，避免把假设当定论。
- **小测验**：每页带折叠式随堂测验，即学即测。
- **明暗主题**：自动跟随系统，Mermaid 图同步切换明暗。

## 🗺️ 内容结构（12 个知识点）

| Track | 内容 |
|---|---|
| **Track 0 · 新手前置** | LLM / token / 对话角色 / 工具调用 / 什么是 Agent / 读懂总览图 |
| **Track A · 概念主轴** | prompt（7 子页） + context / harness / loop / graph / skill（各 `机制·设计决策·坑与自检` 三子页 + gate） |
| **Track B · 实例专项** | Hermes · DeepAgent · OpenClaw · Claude Code · Codex · DeepSeek Harness |
| **Track C · 复刻实战** | 统一对比矩阵 · 学习路径 · 掌握自检 · 自研 harness |
| **Track D · 生产级流程** | 导读 / 第一性原理 / **控制模型** / 生命周期 S0–S5+G0–G5 / 阶段细则 / 贯穿机制 / 模板库 / 工具·清单·反模式·附录（依据项目内 SOP v2.2.1） |

> ℹ️ 主轴顺序 `prompt→context→harness→loop→graph` 为本站结构化假设（【推断】），可自建心智模型，只要前后自洽。

## 🧱 技术栈

- [VitePress](https://vitepress.vuejs.org/) v1.6 — 静态站点生成器
- [vitepress-plugin-mermaid](https://www.npmjs.com/package/vitepress-plugin-mermaid) + mermaid v11 — 关系图
- Vue / Vite（VitePress 内置）

## 🚀 快速开始

```bash
# 安装依赖
npm install

# 本地开发
npm run dev

# 生产构建
npm run build

# 本地预览构建产物（默认 http://localhost:4173/）
npm run preview
```

### ⚠️ 构建注意事项

- 若在异环境（AI 助手沙箱等）构建遇 `.temp`/dist 清理报 EPERM，先执行 `export NODE_OPTIONS=""` 再 `npm run build`。
- npm 安装如遇缓存锁（`.npmcache` 索引被锁），换全新缓存目录重试：`npm install --cache "$PWD/.npmcacheN"`。

## 📁 目录结构

```
agent-arch-docs/
├─ .vitepress/
│  ├─ config.mjs        # 站点配置 + Mermaid + 侧栏导航
│  └─ theme/            # 主题样式
├─ start/               # Track 0 新手前置（7 页）
├─ concepts/            # Track A 概念主轴（prompt 子章节 + 5 章）
├─ instances/           # Track B 六实例
├─ practice/            # Track C 四实战
└─ index.md             # 首页
```

## 📜 来源与分级标注

文中每处关键论断均按以下三档标注，保证可追溯：

- **【事实】** 有明确权威出处（Anthropic / OpenAI / LangGraph / 腾讯云社区 等）
- **【推断】** 本站的结构化假设（如主轴顺序），非官方定论
- **【建议】** 工程落地取舍，可按项目裁剪

## 📄 License

本项目文档内容遵循 MIT 许可证，详见各来源页标注。