---
title: 4-1 loop 机制详解
---

# 4-1 · loop engineering 机制详解

把 04 的"五零件"落地成**可实现的机制**：Goal 怎么可程序检验、Trigger 有哪四类、Prompter 如何反馈式重组、为什么 Generator/Verifier 必须分离、三刹车怎么写成脚本。读完能"写出来"。

::: tip 承接 01
01 的 `think-tools-test` 说过"先推理再动手是 loop 雏形"。本章把这个雏形做完整——并揭示 loop 最反直觉的一条铁律：**Verifier 必须独立于写代码的 Agent**。
:::

## 机制一：Goal —— 必须「可程序检验」

不能是"优化得更好"（程序无法判断），必须是能写成**布尔表达式**的目标。cnblogs 原文给了清晰对照：

| ❌ 不可检验 | ✅ 可检验 |
|---|---|
| "优化得更好" | `npm test` 全绿 且 `tsc --noEmit` 无报错 |
| "让代码更健壮" | 覆盖率从 72% 提升到 80% |
| "修一下 bug" | 修复 Issue #1234 且回归测试全过 |

> 判定标准：**"什么算完成"能写成一行返回 true/false 的代码**，这才是 Goal。

```python
def goal_is_met():
    return test_result == 0 and typecheck_result == 0   # 可程序检验
```

## 机制二：Trigger —— 四种触发源

没有触发器的循环要你手动启动——**那你还在循环里**。Trigger 四类：

| 类型 | 实现 | 场景 |
|---|---|---|
| 定时 Heartbeat | `cron` / 轮询间隔 | 盯 CI、定时检查 |
| Cron | 系统 cron / CI | 夜间批处理、每日报告 |
| 事件 Hook | Git hook / webhook | PR 创建即审查、CI 失败即修 |
| Goal 驱动 | `/goal` 命令 | 持续修到测试变绿 |

## 机制三：Prompter —— 反馈式重组（不是复读）

Prompter 不是"把同一段话反复发"，而是**根据上一轮验证结果调整下一轮指令**：

- 把失败信息（测试输出、lint 报错）**融入**新 prompt；
- 不让 Agent 每轮从零理解上下文；
- 让指令在一轮轮循环里**收敛**而不是原地打转。

```mermaid
sequenceDiagram
  participant V as Verifier
  participant P as Prompter
  participant A as Agent(LLM)
  participant T as 工具/环境
  V->>P: 失败报告（测试输出/lint 报错）
  P->>P: 把失败信息融入本轮指令
  P->>A: 组装 prompt + 上下文 + 失败反馈
  A->>T: 调用工具
  T-->>A: 返回结果
  A->>V: 产出本轮结果
  V->>V: 验证（达标？）
```

## 机制四：Verifier —— 独立评估（loop 最有价值的一条）

::: warning 铁律
**Generator 绝对不能给自己的产出打分。** 写代码的 Agent 和审代码的 Agent 必须是两个 Agent。
:::

因为同一个 Agent 给自己打分，结果永远是"写得太好了"。Anthropic 工程团队发现：**调教一个独立的评估器让它保持怀疑，比让生成器对自己苛刻可行得多**（cnblogs/Anthropic，【事实】）。

附带收益：**Verifier 可以用更便宜的模型**——审代码要的不是"写出更好的代码"，而是"检查是否满足标准"，便宜模型足够。

```python
# 分离 Maker / Checker（cnblogs web-scraping 案例的思想）
def run_loop():
    attempt = 1
    while attempt <= MAX_ATTEMPTS:
        maker_result = maker.run(task)          # 生成器：写代码/爬数据
        report = checker.evaluate(maker_result) # 独立评估器：对照 rubric 打分
        if report.passed:
            return maker_result
        # 失败 → 把 report 喂回 maker 重试（prompter 反馈式）
        attempt += 1
```

## 机制五：Open vs Closed Loop

| 形态 | 特点 | 适用 |
|---|---|---|
| **Open Loop（开放）** | 不预设完整路径，给大方向自主探索 | 原型验证、未知领域调研；成本不可预测 |
| **Closed Loop（封闭）** | 预设完整步骤，每步验证通过才进入下一步 | 修特定 bug、固定流程；成本可控可预测 |

> 实践建议：先用 Open 探路，验证可行后固化成 Closed 上生产（【建议】）。

## 机制六：三个刹车（可运行）

没有刹车的循环 = Token 焚烧炉。三个必须设置的刹车（cnblogs 伪代码，转 Python）：

```python
# loop_with_brakes.py —— 带三刹车的最小 loop（示意）
MAX_ITERATIONS = 10      # 刹车1：最多跑 N 轮
MAX_COST_USD = 5         # 刹车2：最多花 X 美元
NO_PROGRESS_LIMIT = 3    # 刹车3：连续 N 轮无实质进展就停

def has_progress(new, old) -> bool:
    return new != old      # 示意：结果有变化算有进展

iterations = cost = no_progress = 0
last = None
while not goal_is_met() and iterations < MAX_ITERATIONS and cost < MAX_COST_USD:
    result = agent.run(task)
    cost += result.cost
    iterations += 1
    if not has_progress(result.output, last):
        no_progress += 1
        if no_progress >= NO_PROGRESS_LIMIT:
            print("[BRAKE] 连续无进展，停止")
            break
    else:
        no_progress = 0
    last = result.output
print(f"done: iterations={iterations}, cost={cost}, goal_met={goal_is_met()}")
```

## 机制七：失败重试 + 韧性

单步工具失败**不整轮崩溃**——重试或降级（如失败后改用更稳的备用工具/更简单的方案），并更新上下文后继续。

## 小测验

::: details 点击展开题目与答案
**Q1（选择）**：下列哪个是"可程序检验"的 Goal？  
A. "让代码更好"　B. "npm test 全绿且 tsc --noEmit 无报错"　C. "尽量优化一下"  
✅ B。

**Q2（判断）**：让生成代码的 Agent 同时审自己的代码，是高效做法。  
❌ 错。Generator 不能给自家产出打分；Verifier 必须独立，且可用更便宜模型。

**Q3（选择）**：三刹车不包括以下哪项？  
A. 迭代上限　B. 成本上限　C. 提高模型温度　D. 无进展检测  
✅ C。
:::

> 上一节：[04 loop 总入口](/concepts/loop) ｜ 下一节：[4-2 常见坑 + 自检](/concepts/loop/pitfalls)