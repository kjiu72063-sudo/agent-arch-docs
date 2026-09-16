# Agent 架构知识体系 · 文档教学站

> 从「会用」到「会造」Agent —— **概念主轴 + 实例专项 + 复刻实战** 一体化的 VitePress 教学文档站。

本仓库对标优秀的开源 Agent 文档站（如 openclaw-docs），用 **「图多字少 · 关系图即导航」** 的设计法则，把 Agent 架构知识梳理成一条可递进、可自检的主线。

---

## ✨ 特性

- **图多字少**：主干用 Mermaid 关系图讲清楚，文字只补齐无法画出来的关键点。
- **三档分级**：每章末尾带「了解 / 熟悉 / 精通」自检表，学习目标可验证。
- **三级标注**：事实来源、结构化推断、工程建议严格区分，避免把假设当定论。
- **小测验**：每页带折叠式随堂测验，即学即测。
- **明暗主题**：自动跟随系统，Mermaid 图同步切换明暗。

## 🗺️ 内容结构（12 个知识点）

| Track | 内容 |
|---|---|
| **Track 0 · 新手前置** | LLM / token / 对话角色 / 工具调用 / 什么是 Agent / 读懂总览图 |
| **Track A · 概念主轴** | prompt → context → harness → loop → graph（+ skill 横切支柱） |
| **Track B · 实例专项** | Hermes · DeepAgent · OpenClaw · Claude Code · Codex · DeepSeek Harness |
| **Track C · 复刻实战** | 统一对比矩阵 · 学习路径 · 掌握自检 · 自研 harness |

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