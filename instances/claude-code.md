---
title: Claude Code
---

# Claude Code

Track B 第四个实例：**Anthropic 的 CLI agent**。工程上极有代表性——用**六层权限**把"工具能被做什么"管得清清楚楚，正是 03 harness 权限系统的工业级范本。

::: tip 一句话
Claude Code 是把 harness 的"权限"做到六层级的代表：从"随便问"到"自动执行"再到"完全手控"，每一层都决定工具能否真的动手、改文件、跑命令。
:::

## 精确映射：本实例 × 主轴机制

Claude Code 最凸显的工程层是 **harness + loop**：

```mermaid
flowchart LR
  H["harness\n六层权限 + 工具管线"] --> L["loop\n对话-执行循环"]
  L --> C["context\n会话压缩"]
  H --> S["skill 技能"]
  H --> M["MCP 扩展"]
  style H fill:#0d7d6e,color:#fff
  style L fill:#0d7d6e,color:#fff
```

| 本实例的具体件 | 对应主轴机制 | 章节 |
|---|---|---|
| `CLAUDE.md` 项目宪法 | 常驻段注入 + 渐进披露（目录指针） | [2-1](/concepts/context/mechanism) |
| 长会话压缩摘要 | compaction（prune / summarize） | [2-2](/concepts/context/design) |
| `settings.json` `permissions.allow/deny` | 权限 allow/deny 矩阵 | [3-1](/concepts/harness/mechanism) |
| `defaultMode` 权限层级 | 权限取舍（越权越危险） | [3-2](/concepts/harness/design) |
| `PostToolUse` hook 跑 ruff + `exit 2` | 机械化门禁（声明 ≠ 执行） | [3-1](/concepts/harness/mechanism) |
| 对话-执行循环（读→改→验） | loop 五零件 | [4-1](/concepts/loop/mechanism) |
| Skill / MCP | 能力扩展（横切） | [06](/concepts/skill) |

## 六层权限 / 工具管线

```mermaid
flowchart TD
  P0["0 只读问答"] --> P1["1 工具+自动批准"]
  P1 --> P2["2 不读可编辑文件"]
  P2 --> P3["3 编辑文件+自动批准"]
  P3 --> P4["4 运行命令+自动批准"]
  P4 --> P5["5 完全自动执行"]
  style P5 fill:#b45309,color:#fff
```

| 层级 | 能力 | 典型权限 |
|---|---|---|
| 0 | 只读问答 | 不许动文件/命令 |
| 1 | 工具 + 自动批准 | 可调工具，逐个批准 |
| 2 | 不读可编辑文件 | 允许读，禁编辑 |
| 3 | 编辑文件 | 改文件，自动批准 |
| 4 | 运行命令 | 可跑命令，自动批准 |
| 5 | 完全自动 | 全自动执行 |

权限越高，越能办事，风险越大——**是 harness 权限取舍的直观缩影**。

## 会话压缩

长任务里 Claude Code 会对历史会话做**压缩摘要**，释放上下文窗口——正是 02 context 的"压缩/总结策略"落地。

## 真机配置：三份可直接抄用的真实文件

> **【示意实现】**：以下三份为依据源码剖析归纳的**格式示意**（键名与结构以 [官方文档](https://docs.anthropic.com/en/docs/claude-code) 为准），可直接作为模板起手，但照抄前请对照你安装版本的官方字段。

下面三份配置是 Claude Code harness 的**核心可运行资产**（格式依据 sawzhang《deep-dive-claude-code》与 Anthropic 官方设置，【事实】；具体键名以你安装的版本为准）。

### ① 项目级 `CLAUDE.md`（等价 AGENTS.md，由 harness 注入 context）

```markdown
# CLAUDE.md

## 项目
- 类型：FastAPI + React；包管理 uv / pnpm。
- 测试：`uv run pytest`；lint：`uv run ruff check .`

## 纪律（只写机器可验证的）
- 改动必须通过 pytest + ruff，否则不得提交。
- 禁止直接修改 lockfile 与 .env。
- 提交信息用 Conventional Commits。

## 目录指针（渐进披露，不展开全文）
- 架构 → docs/architecture.md
- 接口约定 → docs/api.md
```

### ② 权限配置 `settings.json`（六层权限的工程落点）

```json
{
  "permissions": {
    "allow": [
      "Read(**)",
      "Bash(uv run pytest:*)",
      "Bash(uv run ruff:*)",
      "Bash(git diff:*)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(curl:*)",
      "Write(.env)",
      "Write(**/*.lock)"
    ],
    "defaultMode": "acceptEdits"
  }
}
```
> `defaultMode` 对应权限层级：只读 → 接受编辑 → 完全自动执行。越往上越能办事、风险越大（呼应 [03 harness](/concepts/harness) 的权限取舍）。

### ③ Hook：机械化守护（改文件即跑门禁）

```json
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash",
        "hooks": [{ "type": "command",
                    "command": "test \"$CLAUDE_TOOL_INPUT\" != \"rm -rf /\" || exit 2" }] }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "uv run ruff check . || exit 2" }] }
    ]
  }
}
```
> Hook 让"机械化执行"落地：`PostToolUse` 在每次改文件后**自动跑 ruff**，不合规 `exit 2` 阻断——把可靠性从"模型自觉"变成"工程保证"。这正是 [3-1 门禁](/concepts/harness/mechanism) 的真实范例。

**上手顺序**：① 建 `CLAUDE.md` → ② 配 `settings.json` 权限 → ③ 挂 hook 门禁 → ④ 按需加 Skill / MCP。

::: info 【事实】
> 来源：[sawzhang/deep-dive-claude-code](https://github.com/sawzhang/deep-dive-claude-code)（[S4](/practice/sources)，multi-part 结构已确认，25 章 + 2 附录；许可证按 MIT 处理）；配置格式另参 [Anthropic 官方文档](https://docs.anthropic.com/en/docs/claude-code)（覆盖：Claude Code 实例 · 1-6）。上述配置为**依据来源归纳的示意实现**；"凸显 harness+loop"是本体系的结构化定位（【推断】）。
:::

## 局限与不适用场景

| 局限 | 说明 | 何时别用 |
|---|---|---|
| 商用闭源 | 无法自托管、无法改内核；六层权限与 hook 只能"用"，不能"换实现" | 需要完全自托管 / 离线部署时 |
| 模型绑定 | 能力与成本绑定 Anthropic 模型，无法替换为本地/其他 Provider | 有私有化模型要求时 |
| 强依赖官方运行时 | 配置键名与 hook 事件随版本演进，升级需跟随 | 需要长期冻结接口时 |

**替代方案**：需要可自托管 + 可换模型 → [OpenClaw](/instances/openclaw) / [Hermes](/instances/hermes) / [DeepSeek Harness](/instances/deepseek-harness)。

## 常见坑与反模式

- **坑① 把 `CLAUDE.md` 写成手册**：塞进全部规范会**稀释指令**、抬高每轮预算。正解是"地图 + 目录指针"，细则放 `docs/` 按需读取。
- **坑② hook 里做重活**：`PostToolUse` **每次改文件都会触发**，把 `pytest` 全量跑塞进去会拖垮整个循环。应跑"快检查"（lint / 单测子集），全量留给提交前。
- **坑③ 权限开太宽**：`allow` 里写 `Bash(*)` 等于**放弃六层权限的意义**；应按最小必要授权，危险动作留在 `deny` 或审批层。
- **坑④ 把"会话压缩"当免费**：压缩会丢信息，必须保证不可再生的约束/决策**不进入摘要**（见 [2-2 compaction](/concepts/context/design)）。

## 小测验

::: details 点击展开题目与答案
**Q1（选择）**：Claude Code 的六层权限，核心管控的是？  
A. 模型参数　B. 工具/文件/命令能被执行到什么程度　C. 界面主题  
✅ B。它管"工具能真的动手到什么层级"。

**Q2（判断）**：层级越高，agent 越安全。  
❌ 错。层级越高越能办事，风险越大，需要按任务取舍。

**Q3（选择）**：项目根的 CLAUDE.md 属于主轴哪一层的落地？  
A. graph　B. harness（常驻上下文注入）　C. 仅 prompt 层  
✅ B。它是 harness 把"项目宪法"注入常驻上下文的实现。
:::

## 三档自检

| 档位 | 你能做到 |
|---|---|
| 了解 | 说出 Claude Code 凸显 harness+loop，有六层权限与会话压缩 |
| 熟悉 | 能画六层权限递进图，并说明会话压缩对应 context 哪一策略 |
| 精通 | 能在真实项目配好 CLAUDE.md + hook + skill + MCP，并按风险调权限层级 |

> 上一实例：[OpenClaw](./openclaw) ｜ 相关概念：[03 harness](/concepts/harness) · [04 loop](/concepts/loop) · [06 skill](/concepts/skill) ｜ 下一实例：[Codex](./codex)