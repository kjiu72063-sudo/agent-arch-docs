---
title: 4-3 loop 常见坑 + 自检
---

# 4-3 · loop 常见坑 + 掌握自检

loop 最容易在"没设刹车 / 自我评估 / 上下文膨胀"上翻车。本节给四个常见坑 + 产物化三档。

## 常见坑

- **坑① 目标模糊**：Goal 写成"让代码更好"——程序无法判断，循环可能永远停不下来。**解法**：目标必须是可程序检验的布尔表达式（见 [4-1](/concepts/loop/mechanism)）。
- **坑② 无刹车烧钱**：不设迭代/成本/无进展上限，一晚上烧掉一个月预算（`MAX_COST_USD` 缺失）。**解法**：三刹车必设，尤其成本上限。
- **坑③ 自我评估**：让写代码的 Agent 审自己的代码 → "写得太好了"必然通过。**解法**：Generator/Verifier 分离 + 独立评估器。
- **坑④ 上下文膨胀**：多轮 loop 每轮塞结果，context 越来越满 → 触发 02 的 compaction，但若不压缩，长任务后段会失真/超限。**解法**：loop 与 compaction 联动，每 N 轮或超水位即压缩。

## 反模式对照（代码级）

### 坑① 目标模糊 —— 可程序检验的 Goal

```python
# ✕ 反模式：目标无法判定，循环只能靠"感觉"停
goal_is_met = lambda: "代码变好了"

# ✓ 正解：可执行、返回布尔的判据
import subprocess
def goal_is_met():
    tests = subprocess.run(["pytest", "-q"]).returncode == 0
    lint  = subprocess.run(["ruff", "check", "."]).returncode == 0
    return tests and lint            # 全绿才算达标
```

### 坑② 无刹车烧钱 —— 三刹车必设

```python
# ✕ 反模式：只有 while True，没有上限
while not goal_is_met():
    result = agent.run(task)          # 一晚上烧掉一个月预算

# ✓ 正解：迭代 / 成本 / 无进展，三刹车齐备
iterations = cost = stalled = 0
while not goal_is_met():
    result = agent.run(task); cost += result.cost; iterations += 1
    if iterations >= MAX_ITER or cost >= MAX_COST_USD:
        break                          # 刹车 1 & 2
    stalled = stalled + 1 if result.output == last else 0
    if stalled >= NO_PROGRESS_LIMIT:
        break                          # 刹车 3
    last = result.output
```

### 坑③ 自我评估 —— Maker 与 Checker 必须是两个主体

```python
# ✕ 反模式：同一个 agent 既写又评 → 必然"通过"
result = maker.run(task)
if maker.evaluate(result).passed:      # 自己给自己打分
    return result

# ✓ 正解：独立 Verifier，对照外部 rubric，且可用更便宜模型
result = maker.run(task)
report = checker.evaluate(result, rubric)   # 独立评估器（不同实例/模型）
if report.passed:
    return result
feed_back(report)                      # 不通过 → 把报告喂回进下一轮
```

## 产物化三档自检

| 档位 | 必须提交的产物 |
|---|---|
| **了解** | 说出 loop 五零件（Goal/Trigger/Prompter/Agent/Verifier）及各自职责 |
| **熟悉** | 画出一轮 loop 的时序，并实现一段带三刹车的最小循环脚本，能受控停止而非无限烧钱 |
| **精通** | 在 harness 内实现一个完整 loop：可检验 Goal + 四类 Trigger + 反馈式 Prompter + 独立 Verifier + 三刹车，并成功跑通一个"失败→重试→通过"的真实任务 |

::: tip 达标判断
"熟悉"档硬指标：去掉刹车你的脚本会失控，加上刹车它在超限/无进展时**必然停止**——这验证刹车真的生效。
:::

::: info 下一章承接
一个 loop 反复迭代解决一件事；但当任务变成**多步骤、多角色、带分支**，需要上面那层结构把它们编排起来——这就是 [05 graph engineering](/concepts/graph)。graph 的**每个节点可以是一个 loop**。
:::

> 上一节：[4-2 loop 设计决策 + 验证](/concepts/loop/design) ｜ 下一章：[05 graph engineering](/concepts/graph)