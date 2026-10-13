"""gate_17_optimizer_states.py — 优化器状态：8 B vs 12 B 口径 + 三种压缩手段

对应页面：9-8 优化器状态

验证什么：
  1. 阿里云口径下 7B 全参的优化器状态 = 56 GB（8 B/参数）
  2. CSDN 口径下 = 84 GB（12 B/参数，含 fp32 主权重）
  3. ★ **两者的差恰好是 4 B/参数**（fp32 主权重），可解释、不神秘
  4. 8 位优化器：8 B → 2 B（−75%），7B 全参省 42 GB
  5. 纯 16 位训练：省主权重 4 B/参数（状态再降位则共 8 B/参数）
  6. 8 B 与 12 B 两套"训练静态账"分别自洽（12 B / 16 B 每参数 → 87.4 / 112 GB）
  7. 优化器类型对状态字节的影响（SGD 0 / SGD+M 4 / RMSProp 4 / AdamW 8）

为什么确定：纯算术 + 口径差可解释，无实测成分。
运行：python training/gate/gate_17_optimizer_states.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")
sys.path.insert(0, os.path.join(P9, "_calc"))

import calc as K  # noqa: E402

GB = 1e9
P7 = 7e9


def check1_aliyun_8b_gives_56gb():
    """阿里云口径：AdamW = 2 个 fp32 状态 = 8 B/参数 → 7B 上 56 GB。"""
    o = P7 * 8 / GB
    ok = abs(o - 56.0) < 0.01
    print(f"    7B × 8 B/参数 = {o:.1f} GB")
    return ok


def check2_csdn_12b_gives_84gb():
    """CSDN 口径：8 B + fp32 主权重 4 B = 12 B/参数 → 7B 上 84 GB。"""
    o = P7 * 12 / GB
    ok = abs(o - 84.0) < 0.01
    print(f"    7B × 12 B/参数 = {o:.1f} GB")
    return ok


def check3_gap_is_exactly_master_weight():
    """★ 两口径的差 = 4 B/参数（fp32 主权重），不是"误差"。"""
    gap_bytes = 12 - 8
    gap_gb = (P7 * gap_bytes) / GB
    ok = gap_bytes == 4 and abs(gap_gb - 28.0) < 0.01
    # 主权重 4 B = fp32 的字节数
    ok = ok and gap_bytes == K.W_BYTES["FP32"]
    print(f"    差异 = {gap_bytes} B/参数 = fp32 主权重 → 7B 上 {gap_gb:.0f} GB")
    return ok


def check4_opt8_saves_75pct():
    """8 位优化器：8 B → 2 B（−75%）；7B 全参省 42 GB。"""
    base = P7 * 8 / GB
    opt8 = P7 * 2 / GB
    saved = base - opt8
    ok = abs(opt8 / base - 0.25) < 1e-9 and abs(saved - 42.0) < 0.01
    print(f"    8 B → 2 B：{base:.1f} GB → {opt8:.1f} GB   省 {saved:.0f} GB（降 75%）")
    return ok


def check5_pure16_saves_master_weight():
    """纯 16 位训练：去掉 fp32 主权重 → 省 4 B/参数；状态再降位则共 8 B/参数。"""
    only_master = 4
    with_states = 8
    ok = only_master == K.W_BYTES["FP32"] and with_states == 2 * K.W_BYTES["FP32"]
    total_saving = P7 * with_states / GB
    print(f"    去掉主权重 = {only_master} B/参数；状态也降位 = {with_states} B/参数")
    print(f"    7B 上界节省 = {total_saving:.0f} GB")
    return ok


def check6_two_static_ledgers_selfconsistent():
    """两套训练静态账：12 B/参数 → 87.4 GB；16 B/参数 → 112 GB。"""
    ali = (2 + 2 + 8)          # 权重 + 梯度 + 优化器（8 B 口径）
    csdn = (2 + 2 + 12)        # 含 fp32 主权重
    ali_gb = P7 * ali / GB + 1.4 + 2      # + 激活 1.4 + 其他 2（阿里云表）
    csdn_gb = P7 * csdn / GB
    ok = (ali, csdn) == (12, 16) and abs(ali_gb - 87.4) < 0.05 and abs(csdn_gb - 112.0) < 0.01
    print(f"    阿里云 {ali} B/参数 → {ali_gb:.2f} GB（标注 87.4）")
    print(f"    CSDN   {csdn} B/参数 → {csdn_gb:.1f} GB（标注 112）")
    print(f"    差 {csdn_gb - ali_gb:.1f} GB —— 80 GB 卡上前者能跑、后者不能跑")
    return ok


def check7_optimizer_type_is_variable():
    """优化器不是随便选的：SGD 0 / SGD+M 4 / RMSProp 4 / AdamW 8 B/参数。"""
    expect = {"SGD": 0, "SGD_M": 4, "RMSProp": 4, "AdamW": 8}
    ok = all(K.OPT_BYTES[k] == v for k, v in expect.items())
    span = (K.OPT_BYTES["AdamW"] - K.OPT_BYTES["SGD"]) * P7 / GB
    ok = ok and abs(span - 56.0) < 0.01
    print(f"    状态字节表: {K.OPT_BYTES}")
    print(f"    AdamW 与 SGD 在 7B 上差 {span:.0f} GB")
    return ok


def check8_docs_carry_both_ledgers():
    """9-8 正文必须同时给出 56 / 84 GB 与 87.4 / 112 GB 两组数。"""
    import io
    txt = io.open(os.path.join(P9, "08-optimizer-states.md"), encoding="utf-8").read()
    need = ["56 GB", "84 GB", "87.4 GB", "112 GB", "8 B", "12 B", "主权重"]
    missing = [n for n in need if n not in txt]
    ok = not missing
    print(f"    9-8 关键词命中 {len(need) - len(missing)}/{len(need)}"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    return ok


def main():
    checks = [
        check1_aliyun_8b_gives_56gb(),
        check2_csdn_12b_gives_84gb(),
        check3_gap_is_exactly_master_weight(),
        check4_opt8_saves_75pct(),
        check5_pure16_saves_master_weight(),
        check6_two_static_ledgers_selfconsistent(),
        check7_optimizer_type_is_variable(),
        check8_docs_carry_both_ledgers(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_17 failed"
    print("PASS: gate_17 优化器状态 8/8（8B/12B口径 + 差=主权重 + 8位优化器 + 纯16位 + 两套静态账 + 优化器变量 + 正文）")


if __name__ == "__main__":
    main()
