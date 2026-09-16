---
title: context 验收 gate
---

# context 验收 gate

对应 [2-2 design](/concepts/context/design) 的 L5 验收。脚本：`gate/context_gate.py`（本地可运行）。

运行：
```bash
python concepts/context/gate/context_gate.py
```

## 验证内容（5 项，均真实执行）

| # | 验证 | 方式 |
|---|---|---|
| ① | 预算超限降配不崩 | 真实降配循环，断言不超预算 |
| ② | 压缩不绕过日志（可审计） | `SessionLog` append-only + `replace` 落地，断言旧事件仍在 |
| ③ | DSE 确定性 | 同输入两次同输出 |
| ④ | 真实 tokenizer vs `split()` 差异 | **真 `tiktoken`** 计数 |
| ⑤ | 中文 token 成本 | 中文按字计，与空白切分不同 |

## 实测输出（真实 tiktoken）

```
split估算=4, 真实tokens=10     ← 空格切分低估 2.5 倍
中文 24 字 -> 27 tokens
check1..check5: PASS
PASS: context gate 5/5（真实 tokenizer 已启用）
```

> 依赖：`pip install tiktoken`。

> 上一节：[2-3 常见坑 + 自检](/concepts/context/pitfalls) ｜ 回到：[02 context](/concepts/context)
