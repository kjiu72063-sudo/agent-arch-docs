"""gate_20_zero_per_card.py — ZeRO-1/2/3 的每卡显存（与既有 gate_09 交叉复用）

对应页面：9-10 并行切分

与 gate_09 的关系：gate_09 验的是既有讲义口径的 **16 B/参数** 静态账；
本 gate 验的是 9-10 正文给出的 **7B 全参每卡静态合计四档表**（84 / 35 / 22.75 / 10.5 GB），
两者用**不同的参数口径**描述同一族现象，因此必须**同时存在且互不矛盾**。

验证什么：
  1. 9-10 的四档每卡表（84 / 35 / 10.5 / 22.75 GB）逐项可复算
  2. 每卡值随 ZeRO 阶段单调下降（ZeRO-1 > ZeRO-2 > ZeRO-3）
  3. ZeRO-1 只切优化器状态，就足以把 84 GB 压到 35 GB —— 因为优化器状态本来就是最大项
  4. 与 gate_09 的口径差可解释（12 B/参数静态账 vs 84 GB 的分解口径）
  5. 纯 DP 不省显存（每卡权重与优化器状态都 ×1）

为什么确定：纯算术，无实测成分。
运行：python training/gate/gate_20_zero_per_card.py
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")

GB = 1e9

# 7B 全参（阿里云 12 B/参数口径）的分项，单位 GB
W_7B = 14.0        # 权重
G_7B = 14.0        # 梯度
O_7B = 56.0        # AdamW 优化器状态（8 B/参数）


def per_card(zero, dp):
    """每卡静态合计（GB）。ZeRO-1 切优化器；2 加切梯度；3 加切权重。"""
    w = W_7B / dp if zero >= 3 else W_7B
    g = G_7B / dp if zero >= 2 else G_7B
    o = O_7B / dp if zero >= 1 else O_7B
    return w, g, o, w + g + o


def check1_four_configs_recompute():
    """9-10 的四档表逐项可复算。"""
    cases = [
        ("1 × A100-80G", 1, (14.0, 14.0, 56.0, 84.0)),
        ("8 卡 DP + ZeRO-1", 8, (14.0, 14.0, 7.0, 35.0)),
        ("8 卡 DP + ZeRO-2", 8, (14.0, 1.75, 7.0, 22.75)),
        ("8 卡 DP + ZeRO-3", 8, (1.75, 1.75, 7.0, 10.5)),
    ]
    ok = True
    for name, dp, expect in cases:
        zero = {"1 × A100-80G": 0, "8 卡 DP + ZeRO-1": 1,
                "8 卡 DP + ZeRO-2": 2, "8 卡 DP + ZeRO-3": 3}[name]
        got = per_card(zero, dp)
        same = all(abs(a - b) < 0.01 for a, b in zip(got, expect))
        ok = ok and same
        print(f"    {name:<18} 权重 {got[0]:>5.2f} + 梯度 {got[1]:>5.2f}"
              f" + 优化器 {got[2]:>5.2f} = {got[3]:>6.2f} GB"
              f"   {'OK' if same else 'DIFF(期望 %s)' % str(expect)}")
    return ok


def check2_monotonic_across_zero_stages():
    """每卡值随 ZeRO 阶段单调下降。"""
    vals = [per_card(z, 8)[3] for z in (0, 1, 2, 3)]
    ok = vals[0] > vals[1] > vals[2] > vals[3]
    print(f"    ZeRO-0/1/2/3 @8卡: " + " > ".join(f"{v:.2f}" for v in vals) + " GB")
    return ok


def check3_zero1_targets_the_largest_item():
    """★ ZeRO-1 只切优化器状态，就足以把 84 GB 压到 35 GB。"""
    before = per_card(0, 8)[3]
    after = per_card(1, 8)[3]
    saved = before - after
    ok = abs(saved - O_7B * 7 / 8) < 0.01 and after < 40.0
    # 优化器状态是三项中最大的一项
    ok = ok and O_7B > W_7B and O_7B > G_7B
    print(f"    优化器状态 {O_7B} GB 是最大项（权重 {W_7B} / 梯度 {G_7B}）")
    print(f"    ZeRO-1 只切它：{before:.1f} → {after:.1f} GB（省 {saved:.1f} GB = 84 GB 的 {saved / before * 100:.0f}%）")
    return ok


def check4_crosscheck_with_gate09():
    """与 gate_09 的口径差可解释：16 B/参数 vs 12 B/参数的分解。"""
    # gate_09 用 16 B/参数（含 fp32 主权重）；本 gate 用阿里云 12 B/参数的 GB 分解
    p = 7e9
    by_16 = p * 16 / GB                  # 112 GB
    by_12 = W_7B + G_7B + O_7B           # 84 GB
    ok = abs(by_12 - 84.0) < 0.01 and abs(by_16 - 112.0) < 0.01
    # 两者差的正是 fp32 主权重 4 B/参数
    diff_bytes = (by_16 - by_12) * GB / p
    ok = ok and abs(diff_bytes - 4.0) < 1e-6
    print(f"    gate_09 口径（16 B/参数） = {by_16:.0f} GB")
    print(f"    本 gate 口径（12 B/参数） = {by_12:.0f} GB")
    print(f"    差 = {diff_bytes:.0f} B/参数 = fp32 主权重  →  口径差可解释")
    return ok


def check5_pure_dp_saves_nothing():
    """纯 DP（ZeRO-0）：每卡权重与优化器状态都是 ×1。"""
    w1, g1, o1, t1 = per_card(0, 1)
    w8, g8, o8, t8 = per_card(0, 8)
    ok = (w1 == w8 and g1 == g8 and o1 == o8 and t1 == t8)
    print(f"    纯 DP 1 卡 → {t1:.1f} GB   8 卡 → {t8:.1f} GB   ← 完全相同（复制，不切分）")
    return ok


def check6_docs_carry_the_table():
    """9-10 正文必须载有四档表与"DP 不省显存"的结论。"""
    txt = io.open(os.path.join(P9, "10-parallel-split.md"), encoding="utf-8").read()
    need = ["84 GB", "35 GB", "10.5 GB", "22.75 GB", "DP 本身不省显存", "ZeRO-3"]
    missing = [n for n in need if n not in txt]
    ok = not missing
    print(f"    9-10 关键词命中 {len(need) - len(missing)}/{len(need)}"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    return ok


def main():
    checks = [
        check1_four_configs_recompute(),
        check2_monotonic_across_zero_stages(),
        check3_zero1_targets_the_largest_item(),
        check4_crosscheck_with_gate09(),
        check5_pure_dp_saves_nothing(),
        check6_docs_carry_the_table(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_20 failed"
    print("PASS: gate_20 ZeRO 每卡显存 6/6（四档复算 + 单调 + ZeRO1切最大项 + 与gate_09口径可解释 + DP不省 + 正文）")


if __name__ == "__main__":
    main()
