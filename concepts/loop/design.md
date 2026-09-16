---
title: 4-3 loop 设计决策与验证
---

# 4-3 · loop 设计决策与验证

4-1 给了五零件 + 三刹车，本节把深度推到**设计者级**：Open/Closed 怎么选、Maker-Checker 分离怎么做成实战、以及 Ralph 循环如何把 harness 与 loop 串成一套生产范式。

::: tip 承接 4-1 / 4-2
4-1 有 Goal 布尔判定 / Trigger 四类 / 反馈式 Prompter / Verifier 独立 / 三刹车脚本。本节回答"**什么时候用哪种 loop 形态**"并给两个实战闭环 + 验收 gate。
:::

## 决策一：Open vs Closed Loop（先探路，再固化）

cnblogs 给出两条形态与一条实践铁律（【事实】）：

| 形态 | 特点 | 适用 | 代价 |
|---|---|---|---|
| **Open Loop** | 不预设路径，自主探索 | 原型验证、未知领域调研 | **Token 成本不可预测** |
| **Closed Loop** | 预设步骤，逐步验证 | 修特定 bug、固定流程 | 灵活性差，遇新情况卡住 |

> 实践铁律：**先用 Open 探路验证可行性 → 把验证过的路径固化成 Closed 上生产**（cnblogs，【事实】）。这避免了"开放式裸跑烧钱"和"过早封闭卡住"。

## 决策二：Maker-Checker 分离的实战闭环

cnblogs 的核心工程原则（【事实】）：**写代码的 Agent 和审代码的 Agent 必须是两个 Agent**，且 Verifier 可用更便宜的模型。两个实战案例：

**案例 A · 夜间自动修 bug**（Claude Code 实现）：
1. Goal：修复昨日 CI 失败 + 处理 good-first-issue；
2. Trigger：每天 6:00 cron；
3. **隔离**：`git worktree` 为每个任务建独立工作目录（并行不干扰）；
4. **Writer Agent** 读 `SKILL.md` 修码、本地跑测试；
5. **Reviewer Agent（独立，可用便宜模型）** 检查规范 + 确认测试绿 + 对比 diff 与 issue；
6. 通过 → 自动建 PR + Slack 通知；失败 → Triage 等人工。

> 效果：每天 2–3 个 PR 等你 review。你从"写修复的人"变"审修复的人"，**杠杆 3–5 倍**（cnblogs 数据，【事实】）。

**案例 B · Web scraping 自我修复**：
1. 定义验证标准（Rubric）：必填字段 / 最小条数 / 填充率 ≥95% / 错误率 ≤5%；
2. **分离 Maker（爬虫）与 Checker（独立评估程序）**——Generator 看不到自己的评分；
3. 不达标 → 把评估报告喂回 Claude 修爬虫 → 重跑；
4. 实测网站改版后，字段填充率归零，**第一次修复即达标**（cnblogs，【事实】）。

> 共性：**Rubric/独立 Checker 是"补丁是否有效"唯一裁判**——不是让写代码的 Agent 自我感觉良好。

## 决策三：Ralph 循环 —— 把 harness 与 loop 串起来

deusyu/harness-engineering 收录的 Ralph 框架，六条信条与 harness 概念直接映射（【事实】）：

| Ralph 信条 | 对应 harness 概念 |
|---|---|
| Fresh Context Is Reliability | 智能体可读性（每次迭代重新读取） |
| Backpressure Over Prescription | 机械化执行（不规定怎么做，但门控拒绝坏结果） |
| The Plan Is Disposable | 熵管理（重新生成成本 = 一次 planning loop） |
| Disk Is State, Git Is Memory | 仓库即记录系统（文件是交接机制） |
| Steer With Signals, Not Scripts | 人类掌舵（加路标，不加脚本） |
| Let Ralph | 智能体执行（坐在循环上，不坐在循环里） |

> 一句话：Ralph 让"人坐循环上、agent 坐循环里"，正好把 03 harness 的约束与 04 loop 的迭代合成一套可运行的自主工作范式。

## 决策四：loop 可运行闭环（含 Open/Closed 切换 + 三刹车）

```python
# loop_design.py —— Open/Closed 可切换 + Maker/Checker + 三刹车（示意）
def run_loop(mode="closed", task=None, goal=lambda: False,
             max_iter=10, max_cost=5.0, no_progress=3):
    iterations = cost = stalled = 0
    last = None
    while not goal() and iterations < max_iter and cost < max_cost:
        result = maker.run(task, mode)         # 生成器
        cost += result.cost
        iterations += 1
        report = checker.evaluate(result)      # 独立检查器
        if report.passed:
            return result
        if result.output == last:
            stalled += 1
            if stalled >= no_progress:
                break                          # 刹车3：无进展
        else:
            stalled = 0
        last = result.output
    return None                                # 超限/无进展 → 失败返回
```

## 验收 gate（真实运行：`python gate/loop_gate.py`）

::: warning 验证范围（务必看清）
本 gate 只验证**不依赖模型**的**确定性控制流**：三刹车与 Goal 短路。它**不验证 LLM 产出质量**（那需要真实模型调用 + 评估集）。此前版本用 `FakeMaker/FakeChecker` 自证，已废弃。
:::

实际断言的 5 项（均为真实控制流，实测 PASS）：

| # | 验证内容 | 期望 |
|---|---|---|
| ① | 迭代上限刹车 | 永不达标时，恰好停在 `max_iter` 次 |
| ② | 成本上限刹车 | 超预算即停，不无限烧钱 |
| ③ | 无进展刹车 | 输出重复时，连续 N 次后停止（未到迭代上限也停） |
| ④ | Goal 短路 | Goal 一满足立即返回，不跑满上限 |
| ⑤ | 未达标继续 | Goal 未满足时循环继续，不是一次就退出 |

```python
# 真实循环控制流（gate/loop_gate.py 核心，已去除 Fake 组件）
def run_loop(step_fn, goal_fn, max_iter=10, max_cost=5.0, no_progress=3):
    iterations = cost = stalled = 0
    last = None
    while iterations < max_iter and cost < max_cost:
        result = step_fn(iterations)
        cost += result["cost"]; iterations += 1
        if goal_fn(result):                  # 满意才退出
            return {"iterations": iterations, "cost": cost, "met": True}
        if result["output"] == last:         # 无进展检测
            stalled += 1
            if stalled >= no_progress:
                break
        else:
            stalled = 0
        last = result["output"]
    return {"iterations": iterations, "cost": cost, "met": False}
```
> 运行输出：`PASS: loop gate 5/5（确定性控制流；不验证 LLM 质量）`

## 三档自检（4-3 版）

| 档位 | 必须提交的产物 |
|---|---|
| 熟悉 | 能说出 Open/Closed 何时选哪个，解释 Maker/Checker 分离为何必要 |
| 精通 | 实现一个 Open/Closed 可切换、Maker/Checker 分离、带三刹车的循环，并给出选型论证 |

> 上一节：[4-2 常见坑 + 自检](/concepts/loop/pitfalls) ｜ 下一章：[05 graph engineering](/concepts/graph)