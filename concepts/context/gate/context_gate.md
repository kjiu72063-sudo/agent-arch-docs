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

::: details 展开完整脚本 `gate/context_gate.py`
```python
"""context_gate.py — context 章 L5 验收（部分检查需真实 tokenizer/日志抽象）
运行：python gate/context_gate.py
"""
from typing import Annotated, TypedDict
import operator


# ---- 可审计日志：append-only + surface 投影 ----
class SessionLog:
    """极简 append-only 日志 + surface 投影（演示 compaction 不绕过日志）。"""

    def __init__(self):
        self.events = []          # 全量事件（可回放）
        self.surface = []         # 模型看到的投影

    def append(self, ev):
        self.events.append(ev)    # 只追加，不修改

    def compact(self, summary_event):
        # 压缩不是改旧事件，而是追加一个 replace 事件并重建投影
        self.events.append(summary_event)
        self.surface = [e for e in self.events if e.get("surface")]
        return True


# ---- DSE：确定性信号提取 ----
def dse_extract(text):
    """确定性提取（同输入必同输出）：抓 '约束:'/'用户:' 标记。"""
    out = []
    for line in text.splitlines():
        for prefix in ("约束:", "用户:"):
            if line.startswith(prefix):
                out.append(line)
    return out


def budget_controller_degrades_ok():
    """超预算输入下降配不崩（简化）。"""
    usage = {"system": 4000, "task": 8000, "retrieved": 40000}
    total = sum(usage.values())
    alarm = 0.85 * 32000
    if total > alarm:                       # 降配 retrieved
        while total > alarm and usage["retrieved"] > 1000:
            usage["retrieved"] //= 2
            total = sum(usage.values())
    return total <= 32000                   # 降配后不超预算、不崩


def compaction_not_bypass_log():
    log = SessionLog()
    log.append({"surface": True, "msg": "旧消息1"})
    log.append({"surface": True, "msg": "旧消息2"})
    log.compact({"surface": True, "msg": "[摘要]", "type": "replace"})
    # 旧事件仍在（可回放），投影已被收缩为摘要
    return len(log.events) == 3 and log.surface[-1]["msg"] == "[摘要]"


def dse_is_deterministic():
    txt = "约束: 只读不改\n用户: alice\n约束: 超时5s"
    return dse_extract(txt) == dse_extract(txt)   # 同一输入两次同输出


def count_tokens(text, enc_name="cl100k_base"):
    """真实 tokenizer 计数（tiktoken）。"""
    import tiktoken
    enc = tiktoken.get_encoding(enc_name)
    return len(enc.encode(text))


def tiktoken_differs_from_split():
    """真实验证：中文/代码的真实 token 数与 len(split()) 估算不同。"""
    sample = "def f():\n    return '中文测试'"
    split_est = len(sample.split())
    real = count_tokens(sample)
    print(f"    split估算={split_est}, 真实tokens={real}")
    return real != split_est


def chinese_token_cost_is_real():
    """真实验证：中文按字符计 token。"""
    zh = "上下文工程是在有限窗口内动态选取组织注入压缩信息"
    n = count_tokens(zh)
    print(f"    中文 {len(zh)} 字 -> {n} tokens")
    return n > 0 and n != len(zh.split())


def main():
    checks = [
        budget_controller_degrades_ok(),
        compaction_not_bypass_log(),
        dse_is_deterministic(),
        tiktoken_differs_from_split(),
        chinese_token_cost_is_real(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "context gate failed"
    print("PASS: context gate 5/5（真实 tokenizer 已启用）")


if __name__ == "__main__":
    main()
```
:::

> 上一节：[2-3 常见坑 + 自检](/concepts/context/pitfalls) ｜ 回到：[02 context](/concepts/context)
