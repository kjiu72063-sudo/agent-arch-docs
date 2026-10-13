"""gate_18_inference_ledger.py — 推理账本 5 项加总与界面读数同量级

对应页面：9-2 显存账本总览 / 9-14 端到端实战

验证什么：
  1. 推理账本**恰为 5 项**，且名称与 9-2 一致
  2. 5 项加总 ≈ 界面读数 5.1 GB（容差 2%，且**声明容差**）
  3. 框架开销落在阿里云给出的 **1～2 GB** 区间内
  4. 反推出的激活系数落在 20~30% 档（不是 10% 档）—— 9-14 的核心判定
  5. 框架开销在总占用中的占比在界面读数的量级（约 19.6%）

为什么确定：纯算术 + 区间判定，无实测成分。
运行：python training/gate/gate_18_inference_ledger.py
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")
sys.path.insert(0, os.path.join(P9, "_calc"))

import calc as K  # noqa: E402

GB = 1e9

EXPECT_ITEMS = ("模型权重", "KV缓存", "激活值", "框架开销", "多GPU开销")
UI_TOTAL_GB = 5.1          # 界面读数
TOL = 0.02                 # 容差 2%
FRAMEWORK_GB = 1.01        # 计算器界面实测


def build():
    return K.ledger_infer(
        params_b=3, attn="MLA", L=32, h=3072, n_q=48, n_kv=48, d_c=512 + 64,
        s=4096, b=1, C=1, w_prec="INT8", kv_prec="FP16", win=4096,
        act_ratio=0.30, framework_gb=FRAMEWORK_GB,
    )


def check1_exactly_five_items():
    """账本恰 5 项，名称与 9-2 一致。"""
    items, _ = build()
    ok = tuple(items.keys()) == EXPECT_ITEMS
    print(f"    账本项: {list(items.keys())}")
    return ok


def check2_total_matches_ui():
    """5 项加总与界面 5.1 GB 同量级（容差 2%）。"""
    items, total = build()
    dev = abs(total / (UI_TOTAL_GB * GB) - 1)
    ok = dev < TOL
    for k, v in items.items():
        print(f"    {k:<10} {v / GB:>7.4f} GB")
    print(f"    {'合计':<10} {total / GB:>7.4f} GB   vs 界面 {UI_TOTAL_GB} GB"
          f"   偏差 {dev * 100:.2f}%  (容差 {TOL * 100:.0f}%)")
    return ok


def check3_framework_overhead_in_aliyun_range():
    """框架开销 ∈ [1, 2] GB（阿里云 PAI 区间）。"""
    items, _ = build()
    gb = items["框架开销"] / GB
    ok = 1.0 <= gb <= 2.0
    print(f"    框架开销 {gb:.2f} GB  ∈ 阿里云区间 [1.00, 2.00] GB")
    return ok


def check4_implied_activation_ratio():
    """★ 反推激活系数：残差 / 权重 应落在 20~30% 档（而非 10% 档）。"""
    items, total = build()
    w = items["模型权重"]
    resid = UI_TOTAL_GB * GB - w - items["KV缓存"] - items["框架开销"]
    ratio = resid / w
    ok = 0.20 <= ratio <= 0.35
    # 若取 10% 档，与界面偏差应 > 10%（证明不是 10% 档）
    t10 = w + items["KV缓存"] + 0.10 * w + items["框架开销"]
    dev10 = abs(t10 / (UI_TOTAL_GB * GB) - 1)
    ok = ok and dev10 > 0.10
    print(f"    残差 {resid / GB:.4f} GB ÷ 权重 {w / GB:.3f} GB = {ratio * 100:.1f}%"
          f"   →  落在 20~30% 档")
    print(f"    若取 10% 档：合计 {t10 / GB:.3f} GB，偏差 {dev10 * 100:.2f}%  →  排除")
    return ok


def check5_framework_share_matches_ui():
    """框架开销占比应与界面读数（约 19.6%）同量级。"""
    items, total = build()
    share = items["框架开销"] / total
    ok = 0.15 <= share <= 0.25
    # 且它应显著大于 KV 项（界面示例中"比 KV 还大 6 倍"）
    ratio = items["框架开销"] / items["KV缓存"]
    ok = ok and ratio >= 6.0
    print(f"    框架开销占比 {share * 100:.1f}%   （界面读数 19.6%）")
    print(f"    框架开销 / KV = {ratio:.1f}x   （界面示例：比 KV 还大 6 倍）")
    return ok


def check6_docs_carry_the_numbers():
    """9-2 / 9-14 正文必须载有这些读数与区间。"""
    txt = ""
    for name in ("02-ledger-overview.md", "15-end-to-end.md"):
        txt += io.open(os.path.join(P9, name), encoding="utf-8").read()
    need = ["5.1 GB", "1.01 GB", "1～2 GB", "16.1%", "31.3%", "0.76%"]
    missing = [n for n in need if n not in txt]
    ok = not missing
    print(f"    正文命中 {len(need) - len(missing)}/{len(need)}"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    return ok


def main():
    checks = [
        check1_exactly_five_items(),
        check2_total_matches_ui(),
        check3_framework_overhead_in_aliyun_range(),
        check4_implied_activation_ratio(),
        check5_framework_share_matches_ui(),
        check6_docs_carry_the_numbers(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_18 failed"
    print("PASS: gate_18 推理账本 6/6（5项 + 合计同量级 + 框架1~2GB + 激活30%档 + 占比 + 正文）")


if __name__ == "__main__":
    main()
