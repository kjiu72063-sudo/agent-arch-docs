"""gate_05_lora_params.py — LoRA 可训练参数量公式

对应页面：3-2 LoRA 深入
讲义依据：L2 P16（LoRA 作用位置 Wq/Wk/Wv/Wo；core 参数 r / lora_alpha / dropout）

验证什么：`单模块 = r×(d_in + d_out)`，`总量 = Σ r×(d_in+d_out) × 层数`；
         并用课程 `train.py` 的 LoRA 配置（r=8、7 个 target_modules）做算例。
为什么确定：纯算术。
运行：python training/gate/gate_05_lora_params.py
"""

R = 8          # train.py: lora_alpha=256, r=8, alpha/r=32
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj",
                  "gate_proj", "up_proj", "down_proj"]   # train.py 原文 7 项


def lora_params_one_module(r, d_in, d_out):
    """LoRA 对一层线性 W(d_out×d_in) 新增的参数：A(d_in×r) + B(r×d_out)。

    注：讲义只给"低秩分解"原理与作用位置，未给公式；此处按 LoRA 定义给出。
    """
    return r * d_in + r * d_out          # == r * (d_in + d_out)


def check1_single_module_formula():
    """单模块公式：r×(d_in+d_out) 与展开式 r*d_in + r*d_out 一致。"""
    cases = [(8, 2048, 2048), (8, 2048, 11008), (16, 4096, 4096), (4, 512, 512)]
    ok = True
    for r, di, do in cases:
        a = lora_params_one_module(r, di, do)
        b = r * (di + do)
        if a != b:
            ok = False
        print(f"    r={r:>2} d_in={di:>5} d_out={do:>5} -> {a:>8}  （展开式 {b:>8}）")
    return ok


def check2_qwen_style_hand_calc_matches_formula():
    """Qwen3-1.7B 量级的算例：手算 vs 公式，逐层核对。"""
    # Qwen3-1.7B 近似维度（hidden=2048, intermediate=11008, kv 投影较小）
    dims = {
        "q_proj": (2048, 2048),
        "k_proj": (2048, 512),
        "v_proj": (2048, 512),
        "o_proj": (2048, 2048),
        "gate_proj": (11008, 2048),
        "up_proj": (11008, 2048),
        "down_proj": (2048, 11008),
    }
    per_layer = sum(lora_params_one_module(R, di, do) for do, di in dims.values())
    formula = R * sum(di + do for do, di in dims.values())
    ok = per_layer == formula
    print(f"    每层 7 模块合计 = {per_layer:,} 参数（公式 {formula:,}）")
    # 反向验证：只挂 q/v 两个模块时参数更少
    per_layer_qv = (lora_params_one_module(R, *reversed(dims["q_proj"]))
                    + lora_params_one_module(R, *reversed(dims["v_proj"])))
    ok = ok and per_layer_qv < per_layer
    print(f"    仅挂 q/v 时每层 = {per_layer_qv:,} 参数（< 全 7 模块）")
    return ok


def check3_ratio_to_full_params_is_small():
    """LoRA 参数量占全参的比例应极小（LoRA 的意义）。"""
    n_layers = 28
    hidden = 2048
    inter = 11008
    # 每层全参（近似：attn 4 个投影 + mlp 3 个投影）
    full_per_layer = (3 * hidden * hidden + 3 * hidden * hidden       # q,k,v 近似
                      + hidden * hidden                               # o
                      + 3 * hidden * inter)                           # gate/up/down
    full_total = n_layers * full_per_layer
    lora_total = n_layers * sum(
        lora_params_one_module(R, di, do)
        for do, di in [(2048, 2048), (512, 2048), (512, 2048), (2048, 2048),
                       (11008, 2048), (11008, 2048), (2048, 11008)])
    ratio = lora_total / full_total
    ok = ratio < 0.05                       # 应远小于 5%
    print(f"    全参≈{full_total/1e9:.2f}B，LoRA≈{lora_total/1e6:.1f}M，占比 {ratio:.2%}")
    return ok


def check4_alpha_over_r_ratio():
    """train.py 的 lora_alpha/r = 256/8 = 32（原文注释"更偏向 lora adapter 部分"）。"""
    alpha = 256
    ratio = alpha / R
    ok = ratio == 32
    print(f"    lora_alpha={alpha}, r={R} -> alpha/r={ratio:.0f}")
    # 讲义 L2 P16 建议 alpha 16-32（绝对值）；本例用 256 是为了让 alpha/r 达到 32
    lec_low, lec_high = 16, 32
    print(f"    （讲义 L2 P16 建议 lora_alpha 取值 {lec_low}-{lec_high}；本例 256 系代码配置）")
    return ok


def main():
    checks = [
        check1_single_module_formula(),
        check2_qwen_style_hand_calc_matches_formula(),
        check3_ratio_to_full_params_is_small(),
        check4_alpha_over_r_ratio(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_05 failed"
    print("PASS: gate_05 LoRA 参数量 4/4（单模块公式 + 手算核对 + 占比极小 + alpha/r）")


if __name__ == "__main__":
    main()
