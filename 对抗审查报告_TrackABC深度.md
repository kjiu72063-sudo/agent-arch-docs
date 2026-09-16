# 理论精讲 · Track A/B/C 三阶段对抗审查报告

审查对象：`agent-arch-docs`（VitePress 教学站，v0.4，Track 0/A/B/C 全部页面）
对标权威源：openclaw-docs / cnblogs loop / LangGraph Graph API / Hermes 源码研读 / Claude Code 深潜 / Codex 剖析 / DeepSeek Harness(iceyao) / deusyu harness-engineering / 腾讯云 skill
审查方式：反方论证 → 支持方（客观成立条件）→ 中立裁判（修改指令）
日期：2026-09-16

---

## 阶段一 · 反方论证（完全站在最强反方立场）

### 核心判断
**站点是「概念地图 / 思维导图」，不是「知识体系」。** 标题每章都承诺 "engineering"，实际交付的是「名词释义卡 + 一张图 + 三道选择题」。每一章停在"认识"档，而 selfcheck 却承诺读者可到"精通"档——**能力承诺未兑现，这是最致命的问题**。

### 炮点 A · 内容量：一章撑不起 "engineering"
以 `concepts/loop.md`（约 110 行）对照 cnblogs 全文：
- **Goal**：站点只说"定义目标"。权威源要求"Goal 必须是**可程序检验的布尔表达式**"，并给实例（`npm test 全绿且 tsc --noEmit 无报错`、`覆盖率 72%→80%`）。
- **Trigger**：站点"事件/定时/上轮完成"。权威源给**四类表**（Heartbeat 定时 / Cron / 事件 Hook / Goal 驱动），且点明"没有触发器的循环要你手动启动，那你还在循环里"。
- **Prompter**：站点"组装 prompt+context"。权威源核心机制是**反馈式**——"根据上轮验证结果调整下一轮指令、把失败信息融入新 prompt、不让 Agent 从零理解上下文"。
- **Verifier**：站点"判断是否达标"。权威源最重要的原则——**"Generator 绝对不能给自己的产出打分"、"写代码的 Agent 和审代码的 Agent 必须是两个 Agent"、"Verifier 可以用更便宜的模型"**。站点完全缺失，而这恰恰是 loop 最有价值、最反直觉的一点。
- **Open / Closed loop** 两种形态及其成本/灵活性权衡：缺失。
- **三个刹车伪代码**（`MAX_ITERATIONS/MAX_COST_USD/NO_PROGRESS_LIMIT`）：站点只有三行文字，无任何实现。
- **实战案例**（夜间修 bug / web scraping / opencode-loop，含 `git worktree` 并行）：缺失。

结论：把一篇含代码、实例、权衡的文章压成"一张图 + 名词表"，是**内容掉包**。

### 炮点 B · 深度：graph 章连"会用"都不到
`concepts/graph.md` 只有 StateGraph 五个名词（Node/Edge/ConditionalEdge/State/Reducer）。对照真实 LangGraph Graph API：
- 无 `add_node` / `add_edge` / `add_conditional_edges` / `compile()` 任何 API。
- 无 State 类型定义、`Annotated` 注解、`operator.add` reducer 语义——站点把 reducer 写成"覆盖/追加/取最大"一句带过，而实际是 **Channel/Reducer 机制**（如 `MESSAGES` 用 `operator.add` 追加）。
- 无 checkpoint / persistence / thread（状态持久化与多会话续跑，是 graph 相对 loop 的关键增量）。
- **无一行可运行代码。**
- 而 selfcheck 精通档写"能为真实多 agent 任务选型"——一个连 StateGraph 代码都没见过的人凭什么精通？**这是虚假的能力承诺。**

### 炮点 C · 标注了【事实】却讲错 / 讲浅：DeepSeek Harness 章
- 站点画的"三阶段工具流水线" = 声明/注册 → 组装/绑定 → 执行/回填。iceyao 源码里的真实三阶段是 `tools/pre-execute`（waterfall 审批把关）→ `execute`（fuse 信号）→ `tools/post-execute`（spill 把超大结果替换成 locator）。**站点自创的"三阶段"与实际实现不符，却贴着【事实】标签。**
- 站点只说 Context/Service/Event/Effect 四个名词，权威源含：三类事件域（session 持久 / agent 实时 / 能力 seam）、三种派发（waterfall/serial/emit）、profile/bundle/patch 分层叠加的可操作性、`ReactLoopAgent.kick()` 源码、session 事件溯源 + `deriveMessages` 投影、"模型可见即已记录"不变量、context/spill/compaction 三件套。**全部缺失。**
- 更严重：站点写"ReactLoopAgent 等实现细节以官方文档核对为准"——**权威源（iceyao 源码解析）就在手边却主动放弃深挖，这是懒于考证**，等于承认没读过源码就下了定义。

### 炮点 D · 衔接：主轴之间没有因果链
- prompt→context→harness→loop→graph 只是"并列概念卡"堆叠，没有"上一层的产物如何成为下一层的输入"：
  - harness 章没讲 AGENTS.md **本身就是 context 的来源之一**（由 harness 管理、由 context 注入）。
  - loop 章说"每轮读写 context"，但没讲多轮 loop 会**耗尽 context 预算 → 触发 compaction**。
  - graph 章没说"**节点本身可以是一个 loop**"（loop 是 graph 的原子），二者唯一连接是"loop 之上的编排层"一句带过。
- 权威源（Addy Osmani 四次进化表：prompt→context→harness→loop，每层"解决上一层的瓶颈"）是现成的因果锚，站点没引用。
- 结果：读者看完五章，**拼不出一个 agent 从 prompt 到 graph 的全链路数据流**。

### 炮点 E · 难度过渡：没有标准梯度
- Track 0 讲"什么是 LLM"（零基础），Track A 第一章 prompt 直接跳到工程策略——**断层，无斜坡**。
- 五章之间难度几乎无差，全部停在"认识"档。真正的梯度应是"概念→实现→设计"，但没有任何一章给到"实现"。

### 炮点 F · 实例章是"贴标签"，不是"读源码"
- 六个实例章 = "XX 最凸显 harness+loop" + 一张映射图，**没有一处来自源码的真实机制**。
- Codex 说 AGENTS.md+sandbox，但无真实 AGENTS.md 样例、无 sandbox 机制；Hermes 说工具注册表，但无注册片段。
- 用户提供的权威源（deep-dive-claude-code 25 章深潜、Codex 剖析、Hermes 源码研读）被降级成"产品简介"。

### 炮点 G · 定位错位
- 对标的 openclaw-docs 是**可用的产品文档**（真实 API/配置/命令）；站点是**概念科普**。用"科普的深度"填充"文档的框架"，两头不靠。README 自封"知识体系"——**名不副实**。

---

## 阶段二 · 支持方（客观成立条件，非吹捧）

1. **主题覆盖完整**：12 知识点（5 主轴 + skill + 6 实例）覆盖了全部权威源的最高层主题，广度无遗漏。
2. **事实标注机制真实存在**：【事实】/【推断】/【建议】三级标注 + 来源链接，是**可验证的诚实机制**，且 06-overview 承认主轴顺序为【推断】，未把假设伪装成定论。
3. **图多字少落地**：每页均含 Mermaid 图，符合认知负荷原则，便于快速浏览。
4. **教学闭环骨架存在**：随堂测验 + 三档自检 + 学习路径 + 对比矩阵，构成学习闭环的框架。
5. **技术链路可用**：站点可构建（exit 0）、32 页全部 200、已部署私有仓库，交付可运行。
6. **权威源引用方向正确**：所引 10 个源确为该领域最高质量来源，选择无误。

---

## 阶段三 · 中立裁判：此刻如何修改

**总判**：站点不是"改"，是"**补深度**"——每一章从"认识"档至少抬到"会用"档。三档自检必须落到可运行代码。按优先级执行。

### P0（必修，否则不配叫"知识体系"）
1. **loop 章重写**（对照 cnblogs 全文）：补 Goal 可程序检验（给布尔表达式实例）、Trigger 四类表、Prompter 反馈式调整、**Verifier 独立评估原则（Generator 不能给自家打分 + 更便宜模型）**、Open/Closed loop，并给一段可运行的 Python/bash loop 骨架（含三刹车）。
2. **graph 章重写**（对照真实 LangGraph）：给 StateGraph **完整可运行代码**（State 类型 + `Annotated` + `operator.add` reducer + `add_node` + `add_conditional_edges` + `compile`），纠正 reducer 语义（Channel 而非"覆盖/追加"），补 checkpoint/persistence。
3. **DeepSeek Harness 章**（对照 iceyao）：把"三阶段工具流水线"修正为真实的 `pre-execute/execute/post-execute`，补 turn/step 精确定义 + 事件溯源 + context/spill/compaction。**删掉"以官方核对为准"这句逃避话**，直接引用源码机制。

### P1（衔接与可信）
4. 每章开头加"承接 / 输出"段，讲清因果链：context←harness（AGENTS.md 由 harness 管理、context 注入）；loop 耗尽 context 预算→compaction；graph 节点可为一个 loop。用四次进化表作主轴因果锚。
5. 每个实例章补**一个来自真实源码的可运行片段**：Codex 给 AGENTS.md 样例、Hermes 给工具注册片段、DeepSeek 给 Cordis 插件骨架。
6. **修正 selfcheck 精通档**——只有真正给了读者可运行实现，才能写"精通=能实现"；否则降档为"熟悉"。

### P2（定位诚实）
7. 改首页/README 定位：明确"概念引导 + 权威源导航"，而非"完整知识体系"。**要么降低承诺，要么补深度后再称体系**。
8. 难度过渡：Track A 每章标注难度（认识/会用/设计），或每章补"进阶机制"一节，形成梯度。

---

*以上为中立裁判结论，依据站点文件真实内容与所给权威源全文逐条比对得出，无主观吹捧。*
