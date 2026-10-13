---
title: 9-4 模型权重（下）：用公式反推模型
---

# 9-4 · 模型权重（下）：用公式反推模型

::: info 难度分层 · 本页 = L3（可算层）
L3 能用代码把 `V×h + L×(4h²+3hf)` 算出来，并会做**参数集自洽性检查**。★★★
:::

## 定位

[9-3](/training/p9/03-weights-params) 给了公式，本页把它变成**能跑的代码**，并用它做一件很实用的事：
**检验一个模型配置里的两组数字是否自洽**——`总参数量` 与 `层数/维度/头数/词表/FFN`。

## (1) 公式回顾与代码

```
Φ = V×h  +  L × (4h² + 3hf)
     ↑          ↑      ↑
  Embedding   注意力   FFN(SwiGLU)
```

```python
#!/usr/bin/env python3
"""参数量反推 + 配置自洽性检查。零第三方依赖。"""

def param_count(vocab, hidden, layers, ffn, tied_embedding=True):
    """按 V×h + L×(4h²+3hf) 反推总参数量。

    tied_embedding=True 表示输入/输出 embedding 共享权重，只计一次。
    """
    embedding = vocab * hidden
    attn_per_layer = 4 * hidden * hidden
    ffn_per_layer = 3 * hidden * ffn
    body = layers * (attn_per_layer + ffn_per_layer)
    return embedding + body


def breakdown(vocab, hidden, layers, ffn):
    embedding = vocab * hidden
    attn = 4 * hidden * hidden
    ffn_p = 3 * hidden * ffn
    per_layer = attn + ffn_p
    return {
        "embedding": embedding,
        "attn_per_layer": attn,
        "ffn_per_layer": ffn_p,
        "per_layer": per_layer,
        "body": layers * per_layer,
        "total": embedding + layers * per_layer,
    }


def consistency_check(vocab, hidden, layers, ffn, claim_b, tol=0.05):
    """自洽性检查：界面/文档标注的总参数量 vs 架构字段反推值。

    返回 (是否自洽, 反推值B, 偏差百分比)
    """
    derived = param_count(vocab, hidden, layers, ffn) / 1e9
    dev = (derived - claim_b) / claim_b
    return abs(dev) <= tol, derived, dev * 100


if __name__ == "__main__":
    # 计算器「自定义模型参数配置」的一组真实字段（录屏 OCR）
    FIELDS = dict(vocab=152064, hidden=3072, layers=32, ffn=18944)
    CLAIM_B = 3.0          # 界面「总参数量」标签

    b = breakdown(**FIELDS)
    print("=== 逐项拆解 ===")
    for k, v in b.items():
        print(f"  {k:16s} = {v:>18,}  ({v/1e9:.4f} B)")
    print()
    ok, derived, dev = consistency_check(**FIELDS, claim_b=CLAIM_B)
    print(f"架构字段反推      = {derived:.2f} B")
    print(f"界面标注总参数量  = {CLAIM_B:.2f} B")
    print(f"偏差              = {dev:+.1f}%")
    print(f"自洽性            = {'✅ 通过' if ok else '❌ 不通过（两组数字来自不同来源，必须先对齐）'}")
    print()
    # 反推：若要恰好 3B，FFN 中间层维度应是多少？
    target_body = 3e9 - FIELDS["vocab"] * FIELDS["hidden"]
    per_layer = target_body / FIELDS["layers"]
    need_ffn = (per_layer - 4 * FIELDS["hidden"] ** 2) / (3 * FIELDS["hidden"])
    print(f"若总参恰为 3B，在 L=32 / h=3072 下 FFN 需 ≈ {need_ffn:,.0f}")
    print(f"（界面填的是 {FIELDS['ffn']:,} —— 相差 {FIELDS['ffn']/need_ffn:.1f} 倍）")
```

::: tip 运行
```bash
python training/gate/gate_13_param_reverse.py
```
本页代码与 [gate_13](/training/gate/README) 同源；直接跑 gate 还会顺带校验 `h / n_q = d_head` 整除性。
:::

## (2) 实跑结果

```
=== 逐项拆解 ===
  embedding        =        467,140,608  (0.4671 B)
  attn_per_layer   =         37,748,736  (0.0377 B)
  ffn_per_layer    =        174,587,904  (0.1746 B)
  per_layer        =        212,336,640  (0.2123 B)
  body             =      6,794,772,480  (6.7948 B)
  total            =      7,261,913,088  (7.2619 B)

架构字段反推      = 7.26 B
界面标注总参数量  = 3.00 B
偏差              = +142.1%
自洽性            = ❌ 不通过（两组数字来自不同来源，必须先对齐）

若总参恰为 3B，在 L=32 / h=3072 下 FFN 需 ≈ 4,493
（界面填的是 18,944 —— 相差 4.2 倍）
```

::: danger ⚠ 这是本页最重要的一条发现
把计算器「自定义模型参数配置」里那 14 个字段**原样**代入标准公式，得到的是 **≈ 7.26 B**，
而界面「总参数量」标签写的是 **3 B**——**差 2.4 倍**。

**说明界面上挂着两条互不校验的数据链**：

| 数据链 | 字段 | 喂给谁 |
|---|---|---|
| ① 总参数量 | `总参数量`（3 B，手填档位） | **权重项** `Φ × 位宽` |
| ② 架构字段 | `层数 / 隐藏维度 / 头数 / 词表 / FFN` | **KV Cache 项**、**激活项** |

两条链各自可信，但**不会互相验算**。所以：
> **"算得对"的前提是这两组数字自洽。** 随手选个「3B」标签、却保留 7B 级架构字段，算出来的账是错的——
> 权重项按 3B 算（偏小 2.4 倍），KV 项按 32 层/3072 维算（偏大）。**分母和分子口径不一致，结论就没意义。**
:::

## (3) 自洽性检查器：三条断言

在你自己的配置上跑一遍，任何一条不通过都要先修参数再算显存。

| # | 断言 | 不通过意味着 |
|---|---|---|
| 1 | `隐藏维度 % Query头数 == 0` | `d_head` 不整除 → KV 公式失效 |
| 2 | `KV头数 <= Query头数` | 头数配置非法（MQA 时 `KV头数 = 1`） |
| 3 | 反推参数量与标注值偏差 `≤ 5%` | **两组数字不同源**，先对齐再算 |

```python
def assert_config(vocab, hidden, layers, ffn, n_q, n_kv, claim_b):
    assert hidden % n_q == 0, f"隐藏维度 {hidden} 不能被 Query 头数 {n_q} 整除"
    assert 1 <= n_kv <= n_q, f"KV 头数 {n_kv} 非法（应在 1..n_q）"
    ok, derived, dev = consistency_check(vocab, hidden, layers, ffn, claim_b)
    assert ok, f"参数量不自洽：反推 {derived:.2f}B vs 标注 {claim_b}B（{dev:+.1f}%）"
    return True
```

## (4) 算完参数量，权重显存一步到位

```
权重显存 = Φ × 每参数字节
```

以反推出的 **7.26 B** 为例：

| 位宽 | 字节/参数 | 权重显存 |
|---|---|---|
| FP32 | 4 | 27.06 GiB |
| FP16 / BF16 | 2 | **13.53 GiB** |
| FP8 / INT8 | 1 | 6.77 GiB |
| INT4 | 0.5 | 3.38 GiB |

> 对比：32 GB 卡上，FP16 权重就占掉 **42%**——这才是 [9-5](/training/p9/05-kv-classic) 要算 KV 之前必须先看清的底数。

## 决策表：反推出的数比标注大时怎么办

| 情况 | 处理 |
|---|---|
| 你用**自己的模型** | 以**架构字段反推值**为准，标注值多半是抄的系列名 |
| 你用**开源模型** | 以**官方标注参数量**为准，架构字段只用来算 KV / 激活 |
| 两者差 > 5% | **停下来先对齐**，不要带着不一致的口径往下算 |
| 只想知道量级 | 记住懒人记法：**每 10 亿参数，FP32 约 4 GB、FP16 约 2 GB、INT8 约 1 GB、INT4 约 0.5 GB** |

## 坑与自检

> ✕ 拿界面上「总参数量」的档位当作架构字段的推导结果。

> ✓ 两者是**两条独立数据链**，必须人工对齐；本页 gate 就是查这个。

> ✕ 觉得"差 2.4 倍无所谓，反正都是量级估算"。

> ✓ 权重项会**偏小**、KV 项会**偏大**，误差方向相反 → 加总后的总账**可能凑巧看着合理**，但每一分项都是错的。

> ✕ 忽略 `隐藏维度 % Query头数` 的整除性。

> ✓ 不整除时 `d_head` 无定义，KV 公式直接失效。

**自检清单**：

- [ ] 我能手算 `V×h` 与 `L×(4h²+3hf)` 两项
- [ ] 我知道计算器默认字段反推是 **≈7.26 B**，与标签 **3 B** 不自洽
- [ ] 我知道原因是**两条数据链互不校验**
- [ ] 我会跑三条自洽性断言（整除 / 头数 / 参数量偏差）
- [ ] 我能背懒人记法：每 10 亿参数 → FP32 4G / FP16 2G / INT8 1G / INT4 0.5G

---

> 上一节：[9-3 模型权重（上）：参数量从哪来](/training/p9/03-weights-params) ｜ 下一节：[9-5 KV Cache（上）：公式与前 4 档注意力结构](/training/p9/05-kv-classic)
