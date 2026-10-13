"""gate_09_zero_memory.py — ZeRO-1/2/3 显存节省公式

对应页面：4-12 DeepSpeed 与 ZeRO
讲义依据：L3 P46（GPU 显存五项构成：模型参数/优化器状态/激活值/梯度/临时Buffer）、
         L3 P47（ZeRO 分片：优化器状态 → +梯度 → +参数）、L3 P48（ZeRO-1 五步流程）

验证什么：把 16 B/参数的混合精度 Adam 拆解代入三阶段公式，断言：
  ZeRO-1 = 12/N + 4 ；ZeRO-2 = 14/N + 2 ；ZeRO-3 = 16/N
  且 N=1 时三者都退化为 16（无分片 = 基线），N>1 时严格递减。
**讲义未给字节数与公式**，此处依业界通用口径展开，仅用于量级直觉，不作实测依据。
为什么确定：纯算术。
运行：python training/gate/gate_09_zero_memory.py
"""

# 每参数字节（混合精度 Adam）
W_HALF = 2      # fp16 参数
G_HALF = 2      # fp16 梯度
MASTER = 4      # fp32 master weight
MOMENTUM = 4    # fp32 动量
VARIANCE = 4    # fp32 方差

OPT_STATES = MASTER + MOMENTUM + VARIANCE        # 12
TOTAL = W_HALF + G_HALF + OPT_STATES             # 16


def zero_per_param(stage, N):
    """返回 (分片部分/参数, 未分片部分/参数)。"""
    if stage == 1:
        return OPT_STATES / N, W_HALF + G_HALF       # 只切优化器状态
    if stage == 2:
        return (OPT_STATES + G_HALF) / N, W_HALF     # 切 优化器状态 + 梯度
    if stage == 3:
        return TOTAL / N, 0.0                        # 全切
    raise ValueError(stage)


def ddp_per_param():
    """DDP（无分片）：每卡完整 16 B。"""
    return float(TOTAL)


def check1_breakdown_is_16():
    """16 B = 12（优化器状态）+ 2（梯度）+ 2（参数）。"""
    ok = (OPT_STATES == 12 and TOTAL == 16
          and W_HALF + G_HALF + OPT_STATES == TOTAL)
    print(f"    16 B = 优化器状态 {OPT_STATES} + 梯度 {G_HALF} + 参数 {W_HALF}")
    return ok


def check2_n1_degenerates_to_baseline():
    """N=1 时三阶段都等于 16 B/参数（无分片即基线）。"""
    ok = True
    for s in (1, 2, 3):
        share, keep = zero_per_param(s, 1)
        tot = share + keep
        if abs(tot - 16.0) > 1e-12:
            ok = False
        print(f"    N=1 ZeRO-{s}: {share:.1f} + {keep:.1f} = {tot:.1f} B/参数")
    return ok


def check3_formulas_match():
    """N=8 时三阶段每参数字节与公式一致。"""
    N = 8
    expect = {1: 12 / N + 4, 2: 14 / N + 2, 3: 16 / N}
    ok = True
    for s in (1, 2, 3):
        share, keep = zero_per_param(s, N)
        got = share + keep
        if abs(got - expect[s]) > 1e-12:
            ok = False
        print(f"    N={N} ZeRO-{s}: {got:.3f} B/参数  （公式 {expect[s]:.3f}）")
    return ok


def check4_monotonic_decrease():
    """对任意 N>1：ZeRO-3 ≤ ZeRO-2 ≤ ZeRO-1 ≤ DDP。"""
    ok = True
    for N in [2, 4, 8, 16, 64, 128]:
        vals = [sum(zero_per_param(s, N)) for s in (3, 2, 1)]
        vals.append(ddp_per_param())
        if not all(vals[i] <= vals[i + 1] + 1e-12 for i in range(len(vals) - 1)):
            ok = False
        print(f"    N={N:>3}: Z3={vals[0]:.3f}  Z2={vals[1]:.3f}  Z1={vals[2]:.3f}  DDP={vals[3]:.1f}")
    return ok


def check5_7b_model_example():
    """70 亿参数 × 16 B = 112 GB 基线；N=8 时三阶段的实际显存。"""
    n = 7e9
    base_gb = n * TOTAL / (1024 ** 3)
    ok = abs(base_gb - 104.31) < 0.05          # GiB（≈112 GB 十进制）
    print(f"    基线（DDP 每卡）= {base_gb:.2f} GiB")
    for s in (1, 2, 3):
        share, keep = zero_per_param(s, 8)
        gb = n * (share + keep) / (1024 ** 3)
        print(f"    N=8 ZeRO-{s} 每卡 = {gb:.2f} GiB")
    z3 = n * sum(zero_per_param(3, 8)) / (1024 ** 3)
    print(f"    → ZeRO-3 相比 DDP 降至 1/8（{base_gb:.1f} → {z3:.1f} GiB）")
    return ok and abs(z3 * 8 - base_gb) < 0.01


def check6_communication_tradeoff():
    """阶段越高通信越多（定性）：ZeRO-3 每次前向/反向都要 All-Gather 参数。

    以"每参数需搬运的字节数"作量级比较：
      ZeRO-1 / ZeRO-2：仅梯度相关（2 B/参数）经 reduce-scatter
      ZeRO-3：额外每次前向+反向都要 All-Gather 全部参数（2 B × 2）
    """
    ddp_comm = G_HALF                                   # 一次 all-reduce 的等效量
    z1_comm = G_HALF                                    # 梯度分片后 reduce-scatter
    z3_comm = G_HALF + 2 * W_HALF * 2                   # 梯度 + 前向/反向各一次 All-Gather
    ok = z3_comm > z1_comm >= ddp_comm >= 0
    print(f"    每参数通信量（量级）: DDP={ddp_comm} ≤ ZeRO-1={z1_comm} < ZeRO-3={z3_comm} B")
    return ok


def main():
    checks = [
        check1_breakdown_is_16(),
        check2_n1_degenerates_to_baseline(),
        check3_formulas_match(),
        check4_monotonic_decrease(),
        check5_7b_model_example(),
        check6_communication_tradeoff(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_09 failed"
    print("PASS: gate_09 ZeRO 显存 6/6（16B拆解 + N=1退化 + 三阶段公式 + 单调 + 70亿实例 + 通信权衡）")


if __name__ == "__main__":
    main()
