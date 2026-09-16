---
title: 3-3 harness 设计决策与验证
---

# 3-3 · harness 设计决策与验证

3-1 给了机制与可运行门禁，本节把深度推到**设计者级**——基于 deusyu/harness-engineering 与 OpenAI《Harness Engineering》的真实结论，回答"harness 到底怎么搭、怎么让少数人扛起高吞吐"。

::: tip 承接 3-1 / 3-2
3-1 有 AGENTS.md/权限/门禁/fail-closed，3-2 讲坑。本节是它们的**方法论层**：目录式 AGENTS.md 怎么设计、门禁怎么让 agent 自纠、熵怎么扫、吞吐量下怎么决定重跑还是等人。
:::

## 决策一：AGENTS.md 是「地图」，不是「手册」

deusyu 六大核心概念之一（【事实】）：**AGENTS.md 是一个约 100 行的目录页，不是百科全书**。它渐进式披露：智能体从小入口点开始，被指导下一步该看什么。

巨型指令文件的三个死因（deusyu，【事实】）：
1. **挤占上下文**——每条规则都占 token，越长越稀释；
2. **无法维护**——长文档改一处要通读全文；
3. **无法机械验证**——自然语言规则机器没法断言。

**正确示范**（3-1 里我把 AGENTS.md 写得太像手册了，这里是目录式版本）：

```markdown
# AGENTS.md —— 导航入口（约 100 行，不展开细节）

## 我是谁
本仓库的资深工程师；负责交付可维护、可测试的代码。

## 先读这些（渐进披露）
- 架构与命名 → `docs/architecture.md`
- 提交流程与禁止项 → `AGENTS_commit.md`
- 质量标准与 gate → `docs/quality.md`

## 硬性纪律（机器可验证的才写这）
- 技术栈：Python 3.12 / uv / pytest / ruff。
- 任何改动必须通过 `gate.py`（机械断言，非口头约定）。
- 禁止提交 node_modules / dist / *.log / symlink。

## 工具权限速查
| 工具 | 权限 |
|---|---|
| read | 全库 |
| write | src/, tests/（需审批） |
| run | pytest/ruff/uv 白名单 |
| push | 人工显式授权 |
```
> 设计原则：**AGENTS.md 只放"机器能验的纪律 + 指向深层文档的指针"**；长篇细节放被它指引的文档里。

## 决策二：机械化执行要形成「agent 可自纠」闭环

deusyu 机械化执行（【事实】）：**文档会腐烂，lint 规则不会**；更关键的是——**lint 错误信息里内嵌修复指令**，智能体读取后能自我纠正。

所以门禁不能只返回 PASS/FAIL，而是返回**可被 agent 读的修复指令**（这正好把 01 的"失败信息喂回"、04 的 Prompter 反馈式闭环到这里）：

```python
# gate.py —— 输出含修复指令，agent 可自纠
def lint_gate(paths):
    r = subprocess.run(["ruff", "check", *paths], capture_output=True, text=True)
    if r.returncode != 0:
        return {
            "pass": False,
            "message": "lint 失败。修复指令：按 ruff 报告逐条修正；"
                       "常见：删未用 import、补齐空行、缩进 4 空格。"
                       "修完重跑：ruff check " + " ".join(paths),
        }
    return {"pass": True}
```
> 这把"门禁"从"拦截器"变成"教练"——agent 失败后知道怎么改，而不是卡死。

## 决策三：熵管理 = 垃圾回收 + 质量评分

deusyu 熵管理（【事实】）：**技术债是高息贷款**；智能体会复现仓库已有模式（**包括坏模式**）。所以熵管理不止"压缩/归档"，而是：

1. 把"黄金规则"编码进仓库；
2. 后台任务定期扫描偏差；
3. 更新质量评分；
4. 发起重构 PR。

```mermaid
flowchart LR
  R["黄金规则\n编码进仓库"] --> S["后台扫描\n扫描偏差"]
  S --> Q["质量评分\n更新"]
  Q --> P["重构 PR\n自动发起"]
  P --> R
  style S fill:#b45309,color:#fff
```

## 决策四：吞吐量改变合并理念

deusyu 关键组织结论（【事实】）：**纠错成本低，等待成本高**。在智能体吞吐量远超人类注意力的系统里：

| 情形 | 决策 | 理由 |
|---|---|---|
| 测试偶发失败 | **重跑** | 纠错成本低 |
| 确定性失败 | 人工介入 | 重跑也无意义 |
| 等待人工审查 | 尽量并行/后台 | 等待成本 > 纠错成本 |

> 这解释了 deusyu 的指标：3→7 人、~100 万行、~1500 PR、人均日 3.5 PR。**吞吐量体系不是"更多人盯代码"，而是"让 agent 高吞吐 + 机械兜底 + 人做闸门"。**

## 验收 gate：机械断言 harness

```python
# gate/harness_gate.py —— 3-3 验收
def run():
    checks = []
    # ① AGENTS.md 是地图式：≤ ~120 行，含深层文档指针
    checks.append(is_map_style_agents("AGENTS.md"))
    # ② 门禁输出含修复指令（agent 可自纠）
    checks.append(gate_output_has_fix_instruction())
    # ③ 熵扫描能发现一处故意注入的坏模式
    checks.append(entropy_scan_finds_bad_pattern())
    # ④ 权限矩阵：越权动作被确定性拦截
    checks.append(deny_out_of_scope_action())
    for i, ok in enumerate(checks, 1):
        assert ok, f"check {i} failed"
    print("PASS: harness gate 4/4")
```

## 三档自检（3-3 版）

| 档位 | 必须提交的产物 |
|---|---|
| 熟悉 | 把 AGENTS.md 写成目录式（≤~120 行 + 深层指针），门禁输出含修复指令 |
| 精通 | 为一个 3–7 人 agent 团队搭 harness：地图式 AGENTS + 自纠门禁 + 熵扫描 + 吞吐量合并策略 |

> 上一节：[3-2 常见坑 + 自检](/concepts/harness/pitfalls) ｜ 下一章：[04 loop engineering](/concepts/loop)