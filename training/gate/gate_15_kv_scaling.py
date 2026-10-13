"""gate_15_kv_scaling.py — KV 的标度律：随 s / b / C 线性，SWA 把 O(s) 压到 O(W)

对应页面：9-6 KV Cache（下）

验证什么：
  1. KV 随序列长度 s **严格线性**（K = KV(s)/s 为常数）
  2. KV 随批量 b **严格线性**、随并发 C **严格线性**，且 b×C 等价
     （`并发8×批1` 与 `并发1×批8` 在 KV 上完全相同）—— 本模块的隐形炸点
  3. SWA 把 `O(s)` 压到 `O(W)`：s > W 时 KV 与 s 无关；s ≤ W 时与 MHA 一致
  4. 每 1K token 的 KV 是常数（9-C §3 那张表的依据）

为什么确定：纯算术，无实测成分。
运行：python training/gate/gate_15_kv_scaling.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")
sys.path.insert(0, os.path.join(P9, "_calc"))

import calc as K  # noqa: E402

# Llama-3.1-8B 的 GQA 配置（9-C §3 用的就是它）
LLAMA = dict(L=32, n_q=32, n_kv=8, h=4096, d_c=0, kv_b=2)


def kv(s, b=1, C=1, attn="GQA", win=None):
    return K.kv_bytes(attn, s=s, b=b, C=C, win=win, **LLAMA)


def check1_linear_in_seq_len():
    """KV(s) / s 为常数 → 严格线性。"""
    rates = [kv(s) / s for s in (2048, 4096, 8192, 16384, 32768)]
    ok = max(rates) - min(rates) < 1e-6
    print(f"    每 token KV = {rates[0]:,.1f} B   （五个长度上完全相同）")
    print(f"    每 1K token = {rates[0] * 1000 / 1e9:.4f} GB")
    print(f"    实际: 2048→{kv(2048) / 1e9:.4f}  4096→{kv(4096) / 1e9:.4f}"
          f"  8192→{kv(8192) / 1e9:.4f}  32768→{kv(32768) / 1e9:.4f} GB")
    return ok


def check2_linear_in_batch_and_concurrency():
    """KV 随 b 与 C 各自线性，且与 MHA 通式里的位置一致。"""
    base = kv(4096)
    ok = all(abs(kv(4096, b=n) / base - n) < 1e-9 for n in (1, 2, 4, 6, 8))
    ok = ok and all(abs(kv(4096, C=n) / base - n) < 1e-9 for n in (1, 2, 4, 8, 16))
    print(f"    b 线性: 1→{kv(4096, b=1) / 1e9:.4f}  4→{kv(4096, b=4) / 1e9:.4f}"
          f"  8→{kv(4096, b=8) / 1e9:.4f} GB")
    print(f"    C 线性: 1→{kv(4096, C=1) / 1e9:.4f}  4→{kv(4096, C=4) / 1e9:.4f}"
          f"  16→{kv(4096, C=16) / 1e9:.4f} GB")
    return ok


def check3_batch_concurrency_equivalence():
    """★ b 与 C 在 KV 上等价：并发8×批1 == 并发1×批8。"""
    a = kv(4096, b=1, C=8)
    b_ = kv(4096, b=8, C=1)
    ok = abs(a - b_) < 1e-6
    print(f"    并发8 × 批1 = {a / 1e9:.4f} GB")
    print(f"    并发1 × 批8 = {b_ / 1e9:.4f} GB   ← 完全相同（KV 只认乘积 b×C）")
    return ok


def check4_swa_caps_at_window():
    """SWA：s ≤ W 时与 MHA 一致；s > W 时恒为 W 处的值。"""
    W = 4096
    at_window = kv(W, win=W, attn="SWA")
    below = kv(2048, win=W, attn="SWA")
    above_a = kv(8192, win=W, attn="SWA")
    above_b = kv(131072, win=W, attn="SWA")
    ok = (abs(above_a - at_window) < 1e-6
          and abs(above_b - at_window) < 1e-6
          and abs(below - kv(2048, win=W, attn="GQA")) < 1e-6)
    print(f"    s=2048  (≤W) {below / 1e9:.4f} GB  ← 与 GQA 同（未触发窗口）")
    print(f"    s=4096  (=W) {at_window / 1e9:.4f} GB")
    print(f"    s=8192  (>W) {above_a / 1e9:.4f} GB")
    print(f"    s=131072(>W) {above_b / 1e9:.4f} GB  ← 与 s=8192 相同（饱和）")
    return ok


def check5_swa_saving_grows_with_length():
    """SWA 相对 MHA 的节省倍数随 s 单调增长（9-C §2 那张表）。"""
    ratios = []
    for s in (4096, 8192, 32768, 131072):
        ratios.append(kv(s, attn="MHA") / kv(s, win=4096, attn="SWA"))
    ok = ratios == sorted(ratios) and len(set(ratios)) == len(ratios)
    expect = [4.0, 8.0, 32.0, 128.0]
    ok = ok and all(abs(a - b) < 1e-6 for a, b in zip(ratios, expect))
    print(f"    节省倍数: " + "  ".join(f"s={s}→{r:.1f}x"
                                       for s, r in zip((4096, 8192, 32768, 131072), ratios)))
    return ok


def main():
    checks = [
        check1_linear_in_seq_len(),
        check2_linear_in_batch_and_concurrency(),
        check3_batch_concurrency_equivalence(),
        check4_swa_caps_at_window(),
        check5_swa_saving_grows_with_length(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_15 failed"
    print("PASS: gate_15 KV 标度律 5/5（s线性 + b/C线性 + b×C等价 + SWA饱和 + 节省倍数单调）")


if __name__ == "__main__":
    main()
