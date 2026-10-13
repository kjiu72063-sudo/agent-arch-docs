"""gate_01_vram_estimate.py — 显存估算的算术一致性

对应页面：1-4 显卡选型 / 1-9 量化与阶段 / 6-1 部署四大挑战
讲义依据：L5 P4（数据精度字节表）、L3 P46（GPU 显存五项构成）

验证什么：`显存 ≈ 参数量 × 精度字节` 这条式子在四种精度下自洽；
         混合精度 Adam 的 16 B/参数拆解算术自洽。
为什么确定：纯算术，无实测成分。
运行：python training/gate/gate_01_vram_estimate.py
"""

BYTES = {"FP32": 4.0, "FP16": 2.0, "INT8": 1.0, "INT4": 0.5}

# 混合精度 Adam 每参数的字节拆解（业界通用口径，讲义未给字节数）
MIXED_PRECISION_ADAM = {
    "fp16 参数": 2,
    "fp16 梯度": 2,
    "fp32 master weight": 4,
    "fp32 动量": 4,
    "fp32 方差": 4,
}


def check1_precision_bytes_match_lecture():
    """L5 P4 原文：FP32=4B / FP16=2B / INT8=1B / INT4=0.5B；且 1 字节 = 8 位。"""
    ok = (BYTES["FP32"] == 4 and BYTES["FP16"] == 2
          and BYTES["INT8"] == 1 and BYTES["INT4"] == 0.5)
    # 每降一半精度，字节数减半（4→2→1→0.5）
    halves = [BYTES["FP32"] / BYTES["FP16"], BYTES["FP16"] / BYTES["INT8"],
              BYTES["INT8"] / BYTES["INT4"]]
    ok = ok and all(h == 2 for h in halves)
    print(f"    字节表: {BYTES}  每档减半: {halves}")
    return ok


def estimate_vram_gb(n_params, precision, k=1.0):
    """显存估算：参数量 × 每参数字节 × K（含冗余系数）。"""
    return n_params * BYTES[precision] * k / (1024 ** 3)


def check2_7b_model_sizes():
    """70 亿参数模型在四种精度下的显存，与手算一致。"""
    n = 7e9
    got = {p: round(estimate_vram_gb(n, p), 2) for p in BYTES}
    expect = {"FP32": 26.08, "FP16": 13.04, "INT8": 6.52, "INT4": 3.26}
    ok = got == expect
    print(f"    70亿参数: {got} GiB")
    print(f"    手算核对: {expect} GiB")
    return ok


def check3_mixed_precision_adam_breakdown():
    """混合精度 Adam = 每参数 16 B，且等于拆解项之和。"""
    total = sum(MIXED_PRECISION_ADAM.values())
    ok = total == 16
    # 优化器状态（fp32 master + 动量 + 方差）= 12 B；参数 + 梯度 = 4 B
    opt_states = (MIXED_PRECISION_ADAM["fp32 master weight"]
                  + MIXED_PRECISION_ADAM["fp32 动量"]
                  + MIXED_PRECISION_ADAM["fp32 方差"])
    p_and_g = (MIXED_PRECISION_ADAM["fp16 参数"] + MIXED_PRECISION_ADAM["fp16 梯度"])
    ok = ok and opt_states == 12 and p_and_g == 4 and opt_states + p_and_g == 16
    print(f"    16 B = 优化器状态 {opt_states} B + 参数梯度 {p_and_g} B")
    return ok


def check4_k_multiplier_linearity():
    """K 系数线性可乘：K=2 的显存恰为 K=1 的两倍（用于表示参数/梯度/优化器状态的倍数）。"""
    n, p = 7e9, "FP16"
    ok = abs(estimate_vram_gb(n, p, 2.0) - 2 * estimate_vram_gb(n, p, 1.0)) < 1e-9
    # 仅优化器状态的显存（12B/参数）
    opt_only = n * 12 / (1024 ** 3)
    print(f"    70亿参数仅优化器状态(12B/参数) = {opt_only:.2f} GiB")
    return ok


def main():
    checks = [
        check1_precision_bytes_match_lecture(),
        check2_7b_model_sizes(),
        check3_mixed_precision_adam_breakdown(),
        check4_k_multiplier_linearity(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_01 failed"
    print("PASS: gate_01 显存估算 4/4（精度字节表 + 70亿算例 + 16B拆解 + K线性）")


if __name__ == "__main__":
    main()
