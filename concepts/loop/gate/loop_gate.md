---
title: loop 验收 gate
---

# loop 验收 gate

对应 [4-2 design](/concepts/loop/design) 的 L5 验收。脚本：`gate/loop_gate.py`（本地可运行）。

运行：
```bash
python concepts/loop/gate/loop_gate.py
```

::: warning 验证范围（重要）
本 gate **只验证不依赖模型**的**确定性控制流**：三刹车与 Goal 短路。它**不验证 LLM 产出质量**——那需要真实模型调用 + 评估集，不在本 gate 范围。此前版本用 `FakeMaker/FakeChecker` 自证，已废弃。
:::

## 验证内容（5 项，真实控制流）

| # | 验证 | 期望 |
|---|---|---|
| ① | 迭代上限刹车 | 永不达标时恰好停在 `max_iter` 次 |
| ② | 成本上限刹车 | 超预算即停 |
| ③ | 无进展刹车 | 输出重复时连续 N 次后停止 |
| ④ | Goal 短路 | Goal 一满足立即返回 |
| ⑤ | 未达标继续 | Goal 未满足时循环继续 |

## 实测输出

```
iterations=3 (期望=3), met=False
cost=3.0 (预算=2.5), iterations=3
iterations=4 (期望=4), met=False
met=True, iterations=3 (期望=3)
调用次数=5, met=True
check1..check5: PASS
PASS: loop gate 5/5（确定性控制流；不验证 LLM 质量）
```

::: details 展开完整脚本 `gate/loop_gate.py`
```python
"""loop_gate.py — loop 章验收：**确定性控制流部分**（不验证 LLM 输出质量）
运行：python gate/loop_gate.py

范围声明（重要）：
  本 gate 只验证**不依赖模型**的循环控制流：三刹车（迭代/成本/无进展）、
  Goal 布尔判定的短路、以及"满意才退出"的语义。
  它**不**验证 LLM 产出质量——那需要真实模型调用与评估集，不在本 gate 范围。
"""

def run_loop(step_fn, goal_fn, max_iter=10, max_cost=5.0, no_progress=3):
    """真实的循环控制流：三刹车 + goal 短路。step_fn 由调用方注入。"""
    iterations = cost = stalled = 0
    last = None
    history = []
    while iterations < max_iter and cost < max_cost:
        result = step_fn(iterations)
        cost += result["cost"]
        iterations += 1
        history.append(result["output"])
        if goal_fn(result):                       # Goal 判定：满意才退出
            return {"output": result["output"], "iterations": iterations,
                    "cost": cost, "met": True, "history": history}
        if result["output"] == last:              # 无进展检测
            stalled += 1
            if stalled >= no_progress:
                break
        else:
            stalled = 0
        last = result["output"]
    return {"output": None, "iterations": iterations, "cost": cost,
            "met": False, "history": history}


def brake_max_iterations():
    """真实验证：迭代上限生效 —— 永不达标的 step 必须在 max_iter 次后停止。"""
    def step(i):
        return {"output": f"attempt-{i}", "cost": 0.1}

    r = run_loop(step, goal_fn=lambda x: False, max_iter=3)
    print(f"    iterations={r['iterations']} (期望=3), met={r['met']}")
    return r["iterations"] == 3 and r["met"] is False


def brake_max_cost():
    """真实验证：成本上限生效 —— 单次成本高时提前停，不超过预算太多。"""
    def step(i):
        return {"output": f"attempt-{i}", "cost": 1.0}

    r = run_loop(step, goal_fn=lambda x: False, max_iter=100, max_cost=2.5)
    print(f"    cost={r['cost']} (预算=2.5), iterations={r['iterations']}")
    return r["cost"] <= 3.5 and r["met"] is False      # 允许最后一次越界即停


def brake_no_progress():
    """真实验证：连续无进展（输出重复）触发停止，即使远未到迭代上限。"""
    def step(i):
        return {"output": "same-output", "cost": 0.1}   # 恒定输出 = 无进展

    r = run_loop(step, goal_fn=lambda x: False, max_iter=100, no_progress=3)
    print(f"    iterations={r['iterations']} (期望=4), met={r['met']}")
    return r["iterations"] == 4 and r["met"] is False


def goal_short_circuit():
    """真实验证：Goal 一旦满足立即退出，不跑满上限。"""
    def step(i):
        return {"output": f"attempt-{i}", "cost": 0.1}

    r = run_loop(step, goal_fn=lambda x: x["output"] == "attempt-2", max_iter=100)
    print(f"    met={r['met']}, iterations={r['iterations']} (期望=3)")
    return r["met"] is True and r["iterations"] == 3


def loop_continues_until_goal_or_brakes():
    """真实验证：未达标时循环继续（不是一次就退出）。"""
    calls = []

    def step(i):
        calls.append(i)
        return {"output": f"attempt-{i}", "cost": 0.1}

    r = run_loop(step, goal_fn=lambda x: x["output"] == "attempt-4", max_iter=10)
    print(f"    调用次数={len(calls)}, met={r['met']}")
    return len(calls) == 5 and r["met"] is True


def main():
    checks = [
        brake_max_iterations(),
        brake_max_cost(),
        brake_no_progress(),
        goal_short_circuit(),
        loop_continues_until_goal_or_brakes(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "loop gate failed"
    print("PASS: loop gate 5/5（确定性控制流；不验证 LLM 质量）")


if __name__ == "__main__":
    main()
```
:::

> 上一节：[4-3 常见坑 + 自检](/concepts/loop/pitfalls) ｜ 回到：[04 loop](/concepts/loop)
