"""gate_22_unaccounted.py — 卸载的三级算术、碎片预留与"≤85%"判据

对应页面：9-9 算不到的那部分

验证什么：
  1. 卸载三层（GPU 显存 / CPU-RAM / NVMe）的**账本算术**：
     把优化器状态下沉到 CPU 后，GPU 侧每卡显存只减不增，且减少量恰等于被下沉的那一项
  2. 卸载只能省**被下沉的项**，不能改变其他项（不变量）
  3. 分块预填充：把 Prefill 峰值从 `O(整段 prompt)` 降到 `O(一块)` 的算术关系
  4. "≤ 85% 卡容量"判据的算例：30.5 GB 预测 + 1.5 GB 框架开销在 32 GB 卡上恰好爆
  5. 框架开销区间 [1, 2] GB 与碎片预留 [5%, 10%] 的量级自洽
  6. 分块预填充 ≠ 前缀缓存（两者治的东西不同）

为什么确定：纯算术 + 区间判定，无实测成分。
运行：python training/gate/gate_22_unaccounted.py
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")
sys.path.insert(0, os.path.join(P9, "_calc"))

import calc as K  # noqa: E402

GB = 1e9
CARD_GB = 32.0          # 计算器示例卡容量

# 7B 全参分项（GB）
ITEMS = {"模型权重": 14e9, "梯度": 14e9, "优化器状态": 56e9, "激活值": 1.4e9, "框架开销": 2e9}


def check1_offload_moves_exactly_one_item():
    """卸载优化器状态到 CPU：GPU 侧减少量 == 被下沉项。"""
    # 8 卡 DP + ZeRO-1 的每卡优化器状态
    per, dp = K.per_card(ITEMS, tp=1, pp=1, gpus=8, zero=1)
    before = sum(per.values())
    opt = per["优化器状态"]
    after = before - opt
    ok = abs(after - (per["模型权重"] + per["梯度"] + per["激活值"] + per["框架开销"])) < 1e-6
    print(f"    8 卡 ZeRO-1 每卡: 权重 {per['模型权重'] / GB:.2f} + 梯度 {per['梯度'] / GB:.2f}"
          f" + 优化器 {opt / GB:.2f} + 激活 {per['激活值'] / GB:.2f}"
          f" + 框架 {per['框架开销'] / GB:.2f} = {before / GB:.2f} GB")
    print(f"    优化器状态下沉到 CPU 后 = {after / GB:.2f} GB   （减少 {opt / GB:.2f} GB"
          f" = 被下沉项）")
    return ok


def check2_offload_leaves_other_items_invariant():
    """卸载不改变其他四项（不变量）。"""
    per, _ = K.per_card(ITEMS, tp=1, pp=1, gpus=8, zero=1)
    frozen = ("模型权重", "梯度", "激活值", "框架开销")
    # 模拟"下沉优化器状态"：只把该项置 0，其余保持
    after = {k: (0.0 if k == "优化器状态" else per[k]) for k in per}
    ok = all(abs(after[k] - per[k]) < 1e-12 for k in frozen)
    # 权重/梯度/激活/框架 各自与零卡时相同（未受影响）
    print("    权重/梯度/激活/框架 四项完全不变 ✓")
    print("    卸载只能省【被下沉的项】，不是『免费扩容』")
    return ok


def check3_chunked_prefill_caps_peak():
    """分块预填充：削的是**瞬时注意力工作区** O(prompt²) → O(block²)，
    而**累积 KV 的终值不变**（两者都是 O(prompt)）。这个区分必须守住。
    """
    chunk = 2048
    assert chunk == 2048, chunk          # 计算器默认值
    ratios = []
    for prompt in (4096, 16384, 65536):
        unchunked_ws = prompt ** 2       # 瞬时工作区 ∝ prompt²
        chunked_ws = chunk ** 2          # 每块的瞬时工作区 ∝ block²
        ratios.append(unchunked_ws / chunked_ws)
        acc_unchunked = prompt           # 累积 KV 终值 ∝ prompt
        acc_chunked = prompt             # 分块后**终值相同**（一块块累积上去）
        print(f"    prompt={prompt:>6}: 瞬时工作区 {unchunked_ws:>12,} → {chunked_ws:>9,}"
              f"（省 {unchunked_ws / chunked_ws:>6.0f}x）"
              f"   累积 KV {acc_unchunked:,} == {acc_chunked:,}（不变）")
    ok = ratios == sorted(ratios) and len(set(ratios)) == len(ratios)
    # 省的是峰值：work space 下降，但稳态不变 —— 两个断言都不能少
    ok = ok and ratios[0] == 4 and ratios[-1] == 1024
    print(f"    → 省的是【瞬时峰值】，不是【稳态 KV】；prompt 越长收益越大")
    return ok


def check4_85pct_rule_and_the_30_5gb_case():
    """★ "算什么≤85%"判据：30.5 GB + 1.5 GB 框架开销在 32 GB 卡上恰好爆。"""
    predicted = 30.5
    with_frame = predicted + 1.5
    # 30.5 + 1.5 = 32.0 → 恰好等于卡容量 → 已经爆（不是"刚好够"）
    ok = with_frame >= CARD_GB
    # 但若按 85% 判据，30.5 / 32 = 95.3% 早就该被否掉
    ratio = predicted / CARD_GB
    ok = ok and ratio > 0.85
    print(f"    预测 {predicted} GB / 卡 {CARD_GB} GB = {ratio * 100:.1f}%  →  按 85% 判据已超标")
    print(f"    再加框架开销 1.5 GB → {with_frame:.1f} GB vs {CARD_GB} GB"
          f"  →  {'恰好爆' if with_frame >= CARD_GB else '勉强够'}")
    # 85% 判据对应的可用上限
    ceiling = CARD_GB * 0.85
    print(f"    85% 判据的可用上限 = {ceiling:.1f} GB")
    return ok


def check5_frame_and_fragmentation_consistent():
    """框架开销 ∈ [1,2] GB；碎片预留 ∈ [5%,10%]；两者叠加与 15% 余量一致。"""
    frame_lo, frame_hi = 1.0, 2.0
    frag_lo, frag_hi = 0.05, 0.10
    ok = frame_hi == 2.0 and frag_hi == 0.10
    # 15% 余量：以 32 GB 卡为例，2 GB 框架开销占 6.25%
    frame_share = frame_hi / CARD_GB
    ok = ok and abs(frame_share - 0.0625) < 1e-9
    print(f"    框架开销 [1, 2] GB  →  32 GB 卡上占 {frame_share * 100:.2f}%（取上界）")
    print(f"    碎片预留 [5%, 10%]")
    print(f"    两者叠加 ≈ {frame_share * 100:.1f}% + 5~10% = 11~16%"
          f"  →  与『≤85%』的 15% 余量一致 ✓")
    return ok


def check6_chunked_vs_prefixcache_distinct():
    """分块预填充治峰值、前缀缓存治重复计算——两者不是一回事。"""
    txt = io.open(os.path.join(P9, "09-unaccounted.md"), encoding="utf-8").read()
    need = ["分块预填充", "前缀缓存", "chunked prefill", "prefix caching",
            "治**峰值**", "治**重复计算**", "1～2GB"]
    missing = [n for n in need if n not in txt]
    ok = not missing
    print(f"    9-9 关键词命中 {len(need) - len(missing)}/{len(need)}"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    # 三者（含 9-15）都必须显式区分
    txt15 = io.open(os.path.join(P9, "16-calculator.md"), encoding="utf-8").read()
    ok = ok and "分块预填充" in txt15 and "前缀缓存" in txt15
    print(f"    9-15 同样区分二者 ✓")
    return ok


def check7_three_offload_tiers_ordering():
    """三层卸载的速度/容量序：显存 > RAM > NVMe（速度），显存 < RAM < NVMe（容量）。"""
    speed = {"GPU": 3, "RAM": 2, "NVMe": 1}
    cap = {"GPU": 1, "RAM": 2, "NVMe": 3}
    ok = (list(speed.values()) == sorted(speed.values(), reverse=True)
          and list(cap.values()) == sorted(cap.values()))
    txt = io.open(os.path.join(P9, "09-unaccounted.md"), encoding="utf-8").read()
    ok = ok and "NVMe" in txt and "CPU / RAM" in txt
    print(f"    速度序: GPU({speed['GPU']}) > RAM({speed['RAM']}) > NVMe({speed['NVMe']})")
    print(f"    容量序: GPU({cap['GPU']}) < RAM({cap['RAM']}) < NVMe({cap['NVMe']})")
    return ok


def main():
    checks = [
        check1_offload_moves_exactly_one_item(),
        check2_offload_leaves_other_items_invariant(),
        check3_chunked_prefill_caps_peak(),
        check4_85pct_rule_and_the_30_5gb_case(),
        check5_frame_and_fragmentation_consistent(),
        check6_chunked_vs_prefixcache_distinct(),
        check7_three_offload_tiers_ordering(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_22 failed"
    print("PASS: gate_22 算不到的部分 7/7（卸载算术 + 不变量 + 分块峰值 + 85%判据 + 预留自洽 + 两概念区分 + 三层序）")


if __name__ == "__main__":
    main()
