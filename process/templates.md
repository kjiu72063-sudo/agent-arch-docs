---
title: D7 模板库
---

# D7 · 模板库（可直接抄用）

> **理论锚点**：T1 对应 [3-2 AGENTS.md 地图模式](/concepts/harness/design)；T4 对应 [3-2 错误信息即 Prompt](/concepts/harness/design)。
> 本页模板**语言无关**（示例给出 Python 版）。

| # | 模板 | 用在 |
|---|---|---|
| T1 | [AGENTS.md](#t1-agents-md-模板) | S0/S1 · Tier 1 活契约 |
| T2 | [设计/规格文档](#t2-设计规格文档模板) | S2 · G2 规格闸 |
| T3 | [feature_list.json](#t3-feature-list-json-模板) | S0/S3 · 持久化记忆 |
| T4 | [Linter 三要素](#t4-linter-三要素模板) | S2 · 约束层 |
| T5 | [CI 工作流](#t5-ci-工作流模板python) | S3 · 质量门 |
| T6 | [隔离验证脚本](#t6-隔离验证脚本模板) | S3/S4 · 受控验证 |
| T7 | [后台清理 Agent 任务](#t7-后台清理-agent-任务模板) | S5/持续 · 熵管理 |
| T8 | [阶段放行审查提示词](#t8-阶段放行审查提示词模板) | 每道门 |
| T9 | [用户追问话术](#t9-用户追问话术模板) | 每次交付 |
| T10 | [强制报告格式](#t10-每次交付的强制报告格式) | 每次交付 |

---

## T1 AGENTS.md 模板

```markdown
# AGENTS.md

## 项目简介
[一句话] 这是一个面向 X 的 Y 系统，基于 [栈]。

## 技术栈基线（不允许擅自升级）
- 运行时：[版本]，不可使用 [更高版本] 语法
- 框架：[版本]
- 数据库：[版本]
- 持久化：[方案]，不引入 [替代方案]

## 快速导航
| 你想做什么 | 去哪里看 |
|---|---|
| 了解系统架构 | docs/architecture/overview.md |
| 了解模块边界和依赖规则 | docs/architecture/boundaries.md |
| 了解编码规范 | docs/conventions/README.md |
| 了解当前迭代任务 | docs/plans/current-sprint.md |
| 了解 API 规范 | docs/reference/api-spec.yaml |
| 了解错误码 | docs/reference/error-codes.md |
| 了解测试规范 | docs/conventions/testing.md |
| 了解规则码含义 | docs/conventions/rule-codes.md |

## 硬性规则（必须遵守，CI 会验证）
1. 依赖方向：[下层] → … → [上层]
2. 禁止 [最易犯的坏习惯]，统一使用 [正确做法]
3. 单文件 ≤ 300 行；单函数 ≤ 50 行
4. 禁止 [裸调用]，统一通过 [抽象]
5. 新增代码必须有对应测试，行覆盖率 ≥ 80%
6. [项目特有的第 6 条]

## 提交规范
- feat: 新功能 / fix: 修复 / refactor: 重构 / docs: 文档 / test: 测试
```

> **每条硬性规则必须能回答"由哪个工具在哪一步强制"**——答不上来的不是硬性规则，是建议，移到 `docs/`。

---

## T2 设计/规格文档模板

```markdown
# Feature: [功能名称]

## Status: spec-draft | spec-approved | tickets-approved | ready-for-agent
## 风险等级: L0 | L1 | L2 | L3  （升级理由：）

## 目标
一句话描述这个功能要解决什么问题。
## 非目标
明确列出这次不做什么（防止范围膨胀）。
## 不承诺什么

## 技术方案
### 涉及的模块
### 数据模型变更（迁移脚本路径）
### API 变更

## 权限与安全要求
## 数据迁移和回滚要求
## 可观测性要求
## 测试策略
## 非功能要求（用可验证指标）

## 验收标准
* 标准 1：具体的、可验证的
* 测试覆盖率 ≥ 80%

## 循环预算
- 最大修复轮次：N    超限处置：升级人工

## 未决问题
## 明确不包含的内容
## 依赖
```

---

## T3 feature_list.json 模板

```json
{
  "version": 1,
  "updated_at": "2026-09-12",
  "risk_level": "L2",
  "features": [
    {
      "id": "F001",
      "name": "项目初始化与骨架",
      "status": "passing",
      "priority": 1,
      "risk_level": "L0",
      "dependencies": [],
      "acceptance": ["骨架可启动", "基础端到端测试通过"],
      "evidence": ["CI #123 全绿", "e2e 2/2"],
      "notes": ""
    }
  ]
}
```

> `status` 固定枚举：`todo | decision | prefactor | in_design | spec_approved | in_progress | verified | passing | blocked`
>
> **用 JSON 而非 Markdown** —— `[书 p8]` 结构化数据不易被 Agent 误改。

---

## T4 Linter 三要素模板

```text
❌ [什么错了]
✅ FIX: [怎么改，给出代码片段]
📖 See: [哪个文档有详细说明]
```

**实例（Checkstyle / Ruff 风格层）**：

```xml
<module name="RegexpSinglelineJava">
    <property name="format" value="System\.out\.println"/>
    <property name="message"
              value="❌ 禁止 System.out.println。
✅ FIX: private static final Logger log = LoggerFactory.getLogger(X.class);
📖 See: docs/conventions/logging.md"/>
</module>
```

> ⚠️ Python 侧 Ruff 不支持自定义文本 → 走 [D6 A.2 两层策略](/process/mechanisms)（架构层自定义 + 风格层规则码映射表）。

---

## T5 CI 工作流模板（Python）

```yaml
# .github/workflows/harness-checks.yml
name: Harness Checks
on: [pull_request]

jobs:
  quality-gates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install
        run: pip install -e ".[dev]"
      - name: Lint + Format
        run: ruff check . && ruff format --check .
      - name: Types
        run: mypy app
      - name: Architecture
        run: lint-imports && pytest tests/architecture -q
      - name: Tests + Coverage (>= 80%)
        run: pytest -q --cov=app --cov-fail-under=80
      - name: File size check
        shell: bash
        run: |
          find app -name '*.py' | while read f; do
            lines=$(wc -l < "$f")
            if [ "$lines" -gt 300 ]; then
              echo "❌ $f 有 $lines 行（上限 300）"
              echo "✅ FIX: 拆分为更小的模块，辅助函数移至 helpers/ 或 infrastructure/"
              echo "📖 See: docs/conventions/file-size.md"
              exit 1
            fi
          done
      - name: Doc freshness
        shell: bash
        run: |
          find docs/design -name '*.md' | while read f; do
            last_mod=$(git log -1 --format=%ct "$f")
            now=$(date +%s)
            days_old=$(( (now - last_mod) / 86400 ))
            if [ "$days_old" -gt 60 ]; then
              echo "⚠ $f 已 ${days_old} 天未更新，可能已过期"
            fi
          done
```

> 注意 `File size check` 的失败输出**本身就是三要素**——CI 输出也是 Prompt。

---

## T6 隔离验证脚本模板

```bash
#!/usr/bin/env bash
set -euo pipefail
BRANCH="${1:?usage: verify.sh <branch>}"
WORKTREE_DIR="/tmp/agent-verify-$(date +%s)"

echo "🔧 创建 worktree: $WORKTREE_DIR"
git worktree add "$WORKTREE_DIR" "$BRANCH"
cd "$WORKTREE_DIR"

echo "🔍 校验工具链版本..."
python -V | grep -q '3\.11' || { echo "❌ 必须使用 Python 3.11"; exit 1; }

echo "📦 全量校验（ruff + mypy + import-linter + pytest + coverage）..."
make verify || { echo "❌ verify 失败"; exit 1; }

echo "🚀 启动服务做健康检查..."
uvicorn app.main:app --port 8080 > /tmp/app.log 2>&1 &
APP_PID=$!

for _ in $(seq 1 30); do
  sleep 2
  if curl -sf http://localhost:8080/health | grep -q '"status":"ok"'; then
    echo "✅ 健康检查通过"
    kill $APP_PID 2>/dev/null || true
    cd - >/dev/null
    git worktree remove "$WORKTREE_DIR"
    echo "✅ 所有验证通过"
    exit 0
  fi
done

echo "❌ 应用启动失败，最近日志："
tail -n 50 /tmp/app.log
kill $APP_PID 2>/dev/null || true
exit 1
```

> 三个要点：**隔离分支**（不污染工作区）、**先校验工具链版本**（防版本漂移）、**健康检查失败即退出**（fail-closed）。

---

## T7 后台清理 Agent 任务模板

```markdown
# 任务：代码库卫生清理

请执行以下检查，对每个发现的问题生成独立的修复 PR：

## 检查清单
1. **超长文件**：找出超过 300 行的源文件，拆分为更小的模块
2. **缺失测试**：找出没有对应 test_*.py 的模块，补充基础测试
3. **未使用的 import**：清理所有未使用 import
4. **TODO/FIXME**：列出所有 TODO/FIXME，超过 30 天未处理则生成清理 PR
5. **重复代码**：找出高度相似的代码段（>10 行），提取为共享工具模块
6. **过时文档**：检查 docs/design 中 status=Draft 但已超过 30 天的文档
7. **历史告警**：清理全量校验中累积的非阻塞告警

## 约束
- 每个修复作为独立 PR，不要混在一起
- 每个 PR 修改后必须确保全量校验通过
- PR 标题格式：chore(cleanup): [具体描述]
- 不允许升级运行时主版本（保持 3.11.x）
- 如果不确定某个修改是否安全，跳过并在 PR 中标注原因
```

> ⚠️ 按 [D2 §2.8](/process/control-model)：**单人项目默认不开**（API 支出 + 审查负担大概率负 ROI），改为每周手动收尾 30 分钟。

---

## T8 阶段放行审查提示词模板

```text
现在执行本阶段的独立放行审查。

你必须先完成完整校验，再输出阶段结论。禁止先给结论，再补充问题。
禁止使用「基本完成」「应该可以」「后续再补」「可以先进入下一阶段」等模糊表述。
你当前是第三方评审官，不是本阶段执行者。

审查原则：
1. 没有明确证据证明完成的事项，一律按未完成处理
2. 推测、默认值和理论可行性不能算完成证据
3. 任何未验证的异常、边界、依赖、风险或交付物都必须列出
4. 如果发现一个阻塞项，不能输出「完全达标」
5. 不得隐瞒剩余问题
6. 不得把「可以后续处理」当作当前阶段通过理由
7. 阶段结论必须与校验结果逐项一致
8. 不得修改代码来掩盖校验失败
9. 输入信息或验收标准不足时，先指出缺失，不得猜测
10. 结论只能使用规定的三级结论之一

输出必须包含：
- 已运行命令与原始输出
- 逐项校验结果
- 未验证事项
- 剩余风险与不可逆后果
- 允许进入 / 禁止进入
- 三级结论（A / B / C）
- 若为 C：阻塞项 → 事实证据 → 最小补救动作 → 重新验证命令
```

---

## T9 用户追问话术模板

```text
不要重复总结你做了什么。请只回答：

1. 你声称已完成的每一项对应什么实际证据？
2. 哪些事项只是推测、默认或静态阅读，尚未运行验证？
3. 当前所有未完成项和剩余风险是什么？
4. 哪些问题会阻塞下一阶段？为什么？
5. 哪些问题不能进入「后续再补」？
6. 如果现在放行，最可能在哪个环节失败？
7. 请重新给出三级结论，并逐项引用证据。
```

> **如果 AI 不能回答，就不要批准进入下一阶段。**

---

## T10 每次交付的强制报告格式

```markdown
## 结果
[这次交付了什么，一句话]

## 依据
[依据哪份规格 / 哪张票 / 哪个决策]

## 范围
[做了什么 + 明确不做什么]

## 契约与风险
[冻结契约 / 已知风险 / 不可逆点]

## 验证
[已运行命令 + 原始输出 + 逐项结果]

## 剩余风险
[未验证事项 / 阻塞项 / 最坏后果]
```

> 这套格式是**证据包的轻量版**——用于每次交付；**Gate Record** 是它在每道门的正式版（见 [D6 B.3](/process/mechanisms)）。

## 本节的流程输出

| 你需要 | 用哪个模板 |
|---|---|
| 开一个新项目 | T1 + T3 |
| 写一份规格 | T2 |
| 配置约束 | T4 + T5 |
| 跑一次受控验证 | T6 |
| 让 Agent 自己清理 | T7（单人慎用） |
| 每到一道门 | T8 + T10 |
| 每次 AI 说"做完了" | T9 |

> 上一节：[D6 贯穿机制](/process/mechanisms) ｜ 下一节：[D8 工具·清单·反模式·附录](/process/tooling)
