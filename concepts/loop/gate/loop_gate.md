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

> 上一节：[4-3 常见坑 + 自检](/concepts/loop/pitfalls) ｜ 回到：[04 loop](/concepts/loop)
