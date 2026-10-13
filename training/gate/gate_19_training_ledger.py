"""gate_19_training_ledger.py — 微调账本：QLoRA 的量级校验与"激活主导"结论

对应页面：9-14 端到端实战 / 9-13 训练调参手册

验证什么：
  1. QLoRA（4-bit 基座）的权重 = 1.5 GB（3B × 0.5 B/参数）
  2. LoRA 参数量两档可复算且比值正确（仅注意力 / 全线性层 → 差约 3.7 倍）
  3. 5 项加总 ≈ 界面读数 31.2 GB（容差 5%）
  4. ★ **激活值占账本 85% 以上、前三项合计不足 6%** —— QLoRA 的真相
  5. 三条可行化路径的算术（降序列 / 梯度检查点 / 两者同开）
  6. 单卡（DP=1）时 ZeRO 除以 1 —— 等于没开

为什么确定：纯算术 + 占比判定，无实测成分。
运行：python training/gate/gate_19_training_ledger.py
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")
sys.path.insert(0, os.path.join(P9, "_calc"))

import calc as K  # noqa: E402

GB = 1e9

L, h, ffn = 32, 3072, 18944
RANK = 16
UI_TOTAL_GB = 31.2          # 界面读数（97.5% → 非常高）
TOL = 0.05                  # 容差 5%


def build(scope="attn"):
    return K.ledger_train(
        params_b=3, mode="QLoRA", opt="AdamW",
        L=L, h=h, ffn=ffn, n_q=48, n_kv=48, d_c=512 + 64,
        s=4096, b=1, C=1, attn="MLA", r=RANK, scope=scope,
    )


def check1_qloro_weight_is_1p5gb():
    """QLoRA 4-bit 基座：3B × 0.5 B = 1.5 GB。"""
    items, _ = build()
    w = items["模型权重"] / GB
    ok = abs(w - 1.5) < 0.001
    print(f"    权重 3B × 0.5 B/参数 = {w:.3f} GB")
    return ok


def check2_lora_param_counts():
    """LoRA 参数量两档：仅注意力 12.58 M / 全线性层 46.40 M，比值 ≈ 3.69。"""
    attn = K.lora_params(L, h, ffn, RANK, "attn")
    full = K.lora_params(L, h, ffn, RANK, "full")
    ratio = full / attn
    ok = abs(attn / 1e6 - 12.58) < 0.01 and abs(full / 1e6 - 46.40) < 0.01
    ok = ok and abs(ratio - 3.69) < 0.01
    print(f"    仅注意力 q/k/v/o            = {attn / 1e6:.2f} M")
    print(f"    全线性层(含 gate/up/down)   = {full / 1e6:.2f} M   比值 {ratio:.2f}x")
    return ok


def check3_total_matches_ui():
    """5 项加总与界面 31.2 GB 同量级（容差 5%）。"""
    ok_all = True
    for scope in ("attn", "full"):
        items, total = build(scope)
        dev = abs(total / (UI_TOTAL_GB * GB) - 1)
        ok = dev < TOL
        ok_all = ok_all and ok
        print(f"    [{scope}] 合计 {total / GB:.3f} GB  vs 界面 {UI_TOTAL_GB} GB"
              f"   偏差 {dev * 100:.2f}%")
    return ok_all


def check4_activation_dominates():
    """★ 激活值占比 ≥ 85%；前三项（权重+梯度+优化器）占比 ≤ 6%。"""
    items, total = build("attn")
    act_share = items["激活值"] / total
    top3 = (items["模型权重"] + items["梯度"] + items["优化器状态"]) / total
    ok = act_share >= 0.85 and top3 <= 0.06
    for k, v in items.items():
        print(f"    {k:<10} {v / GB:>8.3f} GB   {v / total * 100:>5.1f}%")
    print(f"    → 激活值占 {act_share * 100:.1f}%，前三项仅占 {top3 * 100:.1f}%")
    return ok


def check5_feasible_paths():
    """三条可行化路径的算术：s=2048 / 梯度检查点 / 两者同开。"""
    items, _ = build()
    w = items["模型权重"]
    frame = items["框架开销"]
    base = 34 * 4096 * 1 * h * 2 * L          # 激活（34 单位式）
    s2048 = 34 * 2048 * 1 * h * 2 * L
    ckpt = base / (L ** 0.5)
    both = s2048 / (L ** 0.5)

    tot_now = (w + base + frame) / GB
    t1 = (w + s2048 + frame) / GB
    t2 = (w + ckpt + frame) / GB
    t3 = (w + both + frame) / GB
    ok = (abs(tot_now - 29.89) < 0.05 and abs(t1 - 16.20) < 0.05
          and abs(t2 - 7.35) < 0.05 and abs(t3 - 4.93) < 0.05)
    assert tot_now > t1 > t2 > t3, (tot_now, t1, t2, t3)
    print(f"    现状 s=4096,无优化      → {tot_now:>6.2f} GB  ({tot_now / UI_TOTAL_GB * 100:.1f}%)")
    print(f"    ① 序列 4096→2048        → {t1:>6.2f} GB  ({t1 / UI_TOTAL_GB * 100:.1f}%)")
    print(f"    ② s=4096 + 梯度检查点    → {t2:>6.2f} GB  ({t2 / UI_TOTAL_GB * 100:.1f}%)")
    print(f"    ③ 两者同开               → {t3:>6.2f} GB  ({t3 / UI_TOTAL_GB * 100:.1f}%)")
    return ok


def check6_zero_no_effect_when_dp_is_1():
    """★ 单卡（DP=1）时 ZeRO-1/2/3 的每卡值完全相同 —— 等于没开。"""
    items, _ = build()
    results = []
    for z in (0, 1, 2, 3):
        per, dp = K.per_card(items, tp=1, pp=1, gpus=1, zero=z)
        results.append((z, dp, sum(per.values())))
    totals = [r[2] for r in results]
    ok = all(abs(t - totals[0]) < 1e-6 for t in totals) and all(r[1] == 1 for r in results)
    print("    " + "  ".join(f"ZeRO-{z}(DP={dp})={t / GB:.2f} GB" for z, dp, t in results))
    print("    → 全部相同：DP=1 时 ZeRO 除以 1")
    return ok


def check7_docs_carry_the_numbers():
    """9-14 / 9-13 正文必须载有这些判定值。"""
    txt = ""
    for name in ("15-end-to-end.md", "14-training-tuning.md"):
        txt += io.open(os.path.join(P9, name), encoding="utf-8").read()
    need = ["31.2 GB", "12.58 M", "46.40 M", "88%", "1.5", "15.8%", "DP = 1"]
    missing = [n for n in need if n not in txt]
    ok = not missing
    print(f"    正文命中 {len(need) - len(missing)}/{len(need)}"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    return ok


def main():
    checks = [
        check1_qloro_weight_is_1p5gb(),
        check2_lora_param_counts(),
        check3_total_matches_ui(),
        check4_activation_dominates(),
        check5_feasible_paths(),
        check6_zero_no_effect_when_dp_is_1(),
        check7_docs_carry_the_numbers(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_19 failed"
    print("PASS: gate_19 微调账本 7/7（4bit权重 + LoRA两档 + 合计同量级 + 激活主导 + 三路径 + ZeRO@DP=1 + 正文）")


if __name__ == "__main__":
    main()
