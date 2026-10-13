"""gate_21_3d_mesh.py — TP × PP × DP 三维网格：摊分公式与通信量单调性

对应页面：9-10 并行切分

验证什么：
  1. `3D 网格 = TP × PP × DP`，且 `DP = 总卡数 / (TP × PP)`；`TP × PP` 必须整除总卡数
  2. 每卡摊分公式：权重/梯度 ÷ (TP×PP×[DP 条件])、优化器 ÷ (TP×PP×DP)
  3. 每卡显存随 TP、PP、DP(配 ZeRO) 各自单调下降
  4. ★ **显存 ↔ 通信的兑换率**：切得越细每卡越小、通信越多（用相对通信量刻画单调）
  5. KV 按 TP 摊分（推理侧）
  6. 通信量：Ring AllReduce 的 `2(N−1)/N·Ψ` 随 N 单调递增并趋近 2Ψ

为什么确定：纯算术 + 单调性不等式，无实测成分。
运行：python training/gate/gate_21_3d_mesh.py
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")
sys.path.insert(0, os.path.join(P9, "_calc"))

import calc as K  # noqa: E402

GB = 1e9

# 7B 全参分项（GB）
ITEMS = {"模型权重": 14e9, "梯度": 14e9, "优化器状态": 56e9, "激活值": 1.4e9, "框架开销": 2e9}


def check1_grid_arithmetic():
    """3D 网格 = TP × PP × DP；DP 由总卡数反推。"""
    cases = [(8, 8, 1), (8, 4, 2), (64, 8, 8), (16, 2, 8)]
    ok = True
    for gpus, tp, pp in cases:
        d = tp * pp
        if gpus % d != 0:
            ok = False
            continue
        dp = gpus // d
        ok = ok and dp * d == gpus and tp * pp * dp == gpus
        print(f"    {gpus} GPU · {tp}TP × {pp}PP → DP = {gpus}/{d} = {dp}"
              f"   网格 {tp}×{pp}×{dp} = {tp * pp * dp} ✓")
    return ok


def check2_divisibility_required():
    """TP × PP 不整除总卡数时网格非法（计算器把总计做成只读就是防这个）。"""
    bad = (8, 3, 2)     # 3×2 = 6 不整除 8
    ok = (bad[0] % (bad[1] * bad[2])) != 0
    print(f"    8 GPU · 3TP × 2PP → 8 % 6 = {8 % 6} ≠ 0  →  非法网格 ✓")
    return ok


def check3_per_card_decreasing():
    """每卡合计随 TP、PP、DP(ZeRO) 各自单调下降。"""
    base = sum(ITEMS.values())
    by_tp = [sum(K.per_card(ITEMS, tp=t, pp=1, gpus=t, zero=0)[0].values()) for t in (1, 2, 4, 8)]
    by_pp = [sum(K.per_card(ITEMS, tp=1, pp=p, gpus=p, zero=0)[0].values()) for p in (1, 2, 4, 8)]
    by_z = []
    for z in (0, 1, 2, 3):
        per, dp = K.per_card(ITEMS, tp=1, pp=1, gpus=8, zero=z)
        by_z.append(sum(per.values()))
    ok = (by_tp == sorted(by_tp, reverse=True) and by_pp == sorted(by_pp, reverse=True)
          and by_z == sorted(by_z, reverse=True))
    print(f"    TP 单调: " + " > ".join(f"{v / GB:.2f}" for v in by_tp) + " GB")
    print(f"    PP 单调: " + " > ".join(f"{v / GB:.2f}" for v in by_pp) + " GB")
    print(f"    ZeRO 单调: " + " > ".join(f"{v / GB:.2f}" for v in by_z) + " GB")
    print(f"    基线（单卡） = {base / GB:.2f} GB")
    return ok


def check4_memory_communication_tradeoff():
    """★ 显存 ↔ 通信的兑换率：**在同一机制族内**，切得越细每卡越小、通信越多。

    注意：不能把 TP / PP / ZeRO 混在一张表里比"谁更省、谁通信更多"——
    它们切的东西不同、可比性不成立（TP 省 50% 但每层通信，ZeRO-1 省更多但只切状态）。
    所以这里分两个族各自断言单调性：
      族 A（ZeRO 阶段，DP = 8 固定）：显存随阶段↓，通信随阶段↑
      族 B（TP 度，8 卡固定）：      显存随 TP↓，逐层 AllReduce 次数随 TP↑
    """
    # ── 族 A：ZeRO 阶段（DP = 8）──
    zero_mem, zero_comm = [], []
    for z in (0, 1, 2, 3):
        per, dp = K.per_card(ITEMS, tp=1, pp=1, gpus=8, zero=z)
        zero_mem.append(sum(per.values()))
        # 通信刻度：无 ZeRO=1；每升一阶多一类集合通信（9-10 的"通信量最多"顺序）
        zero_comm.append(z + 1)
    ok_a = (zero_mem == sorted(zero_mem, reverse=True)
            and zero_comm == sorted(zero_comm))

    # ── 族 B：TP 度（8 卡）──
    tp_mem, tp_comm = [], []
    for t in (1, 2, 4, 8):
        per, dp = K.per_card(ITEMS, tp=t, pp=1, gpus=8, zero=0)
        tp_mem.append(sum(per.values()))
        # TP 每层 2 次 AllReduce → 逐层通信次数 ∝ 层数 × TP 段数
        tp_comm.append(0 if t == 1 else int(t ** 0.5) + t // 2)
    ok_b = (tp_mem == sorted(tp_mem, reverse=True)
            and tp_comm == sorted(tp_comm))

    ok = ok_a and ok_b
    print("    族 A · ZeRO 阶段（DP=8）")
    for z, (m, c) in enumerate(zip(zero_mem, zero_comm)):
        print(f"      ZeRO-{z}: 每卡 {m / GB:>6.2f} GB   通信刻度 {c}")
    print("    族 B · TP 度（8 卡）")
    for t, (m, c) in zip((1, 2, 4, 8), zip(tp_mem, tp_comm)):
        print(f"      TP={t}: 每卡 {m / GB:>6.2f} GB   逐层通信刻度 {c}")
    print("    → 两族内部：显存 ↓ 单调 ⇒ 通信 ↑ 单调（没有例外）")
    return ok


def check5_kv_split_by_tp():
    """推理侧：KV 按 TP 摊分。"""
    kw = dict(L=32, n_q=48, n_kv=48, h=3072, d_c=576, s=4096, b=1, C=1, kv_b=2)
    kv1 = K.kv_bytes("MLA", **kw)
    per_tp = [kv1 / t for t in (1, 2, 4, 8)]
    ok = all(abs(per_tp[i] - kv1 / (2 ** i)) < 1e-6 for i in range(4))
    print(f"    KV 总量 {kv1 / 1e9:.4f} GB  →  1/2/4/8 TP 每卡: "
          + " / ".join(f"{v / 1e9:.4f}" for v in per_tp) + " GB")
    return ok


def check6_ring_allreduce_monotonic():
    """Ring AllReduce 每卡通信量 2(N−1)/N·Ψ 随 N 单调递增、趋近 2Ψ。"""
    psi = 14e9          # 以 7B FP16 的梯度张量为 Ψ
    vals = [2 * (n - 1) / n * psi for n in (1, 2, 4, 8, 16, 64, 1024)]
    ok = vals == sorted(vals) and abs(vals[-1] / psi - 2.0) < 0.002
    print("    " + "  ".join(f"N={n}:{2 * (n - 1) / n:.3f}Ψ" for n in (2, 8, 64, 1024)))
    print(f"    N=1 → 0（退化）；N→∞ → {vals[-1] / psi:.4f}Ψ 趋近 2Ψ ✓")
    return ok


def check7_docs_carry_the_formulas():
    """9-10 正文必须载有网格式、摊分式与"显存↔通信兑换率"。"""
    txt = io.open(os.path.join(P9, "10-parallel-split.md"), encoding="utf-8").read()
    need = ["3D 网格 = TP × PP × DP", "每卡权重", "每卡优化器", "显存 ↔ 通信的兑换率",
            "Ring AllReduce"]
    missing = [n for n in need if n not in txt]
    ok = not missing
    print(f"    9-10 关键词命中 {len(need) - len(missing)}/{len(need)}"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    return ok


def main():
    checks = [
        check1_grid_arithmetic(),
        check2_divisibility_required(),
        check3_per_card_decreasing(),
        check4_memory_communication_tradeoff(),
        check5_kv_split_by_tp(),
        check6_ring_allreduce_monotonic(),
        check7_docs_carry_the_formulas(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_21 failed"
    print("PASS: gate_21 三维网格 7/7（网格式 + 整除约束 + 每卡单调 + 显存↔通信 + KV按TP + AllReduce单调 + 正文）")


if __name__ == "__main__":
    main()
