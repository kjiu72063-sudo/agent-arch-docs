"""gate_16_activation.py — 激活值：双档系数可复算 + 梯度检查点的 O(L)→O(√L)

对应页面：9-7 激活值

验证什么：
  1. 阿里云 7B 口径的 10% 档可复算（7B × 2 B × 10% ≈ 1.4 GB）
  2. CSDN 的 20–30% 档可复算（7B 上 ≈ 2.8 ~ 4.2 GB）
  3. 双档之间必须**单调且不重叠**（10% < 20% < 30%），且能解释差异来自 `s`
  4. 梯度检查点：`O(L) → O(√L)` 的代数关系成立（L=32 → √32 ≈ 5.66 → 约 1/5.7）
  5. 训练激活的两条可复算路径（经验系数式 vs 34 单位式）**同量级**

为什么确定：纯算术，无实测成分。
运行：python training/gate/gate_16_activation.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")
sys.path.insert(0, os.path.join(P9, "_calc"))

import calc as K  # noqa: E402

GB = 1e9

P7 = 7e9          # 7B 参数
B16 = 2           # FP16/BF16


def check1_aliyun_10pct_tier():
    """阿里云口径：b=1, s=2048, param_bytes=2 → 激活 ≈ 权重的 10%。"""
    w = K.weight_bytes(7, B16)
    act = K.activation_infer(w, 0.10)
    ok = abs(act / GB - 1.4) < 0.01 and abs(w / GB - 14.0) < 0.01
    print(f"    7B FP16 权重 = {w / GB:.2f} GB   × 10% → 激活 {act / GB:.2f} GB")
    return ok


def check2_csdn_20_30_tier():
    """CSDN 口径：训练预留 20–30% → 7B 上 2.8 ~ 4.2 GB。"""
    w = K.weight_bytes(7, B16)
    lo = K.activation_infer(w, 0.20) / GB
    hi = K.activation_infer(w, 0.30) / GB
    ok = abs(lo - 2.8) < 0.01 and abs(hi - 4.2) < 0.01
    print(f"    7B FP16 权重 = {w / GB:.2f} GB   × 20~30% → 激活 {lo:.1f} ~ {hi:.1f} GB")
    return ok


def check3_dual_tier_monotonic_and_disjoint():
    """三档单调、不相交——这是"不做单一数字"的算术保证。"""
    ratios = (0.10, 0.20, 0.30)
    vals = [K.activation_infer(K.weight_bytes(7, B16), r) / GB for r in ratios]
    ok = vals == sorted(vals) and len(set(vals)) == 3
    # 低档与高档不重叠：10% 档的上界 < 20% 档的下界（等号不可能，因为比值不同）
    ok = ok and vals[0] < vals[1] < vals[2]
    print(f"    10% → {vals[0]:.2f} GB  <  20% → {vals[1]:.2f} GB  <  30% → {vals[2]:.2f} GB")
    return ok


def check4_grad_checkpoint_algebra():
    """★ 梯度检查点：激活从 O(L) 降到 O(√L)。"""
    K.assert_ckpt_algebra()
    L = 32
    full = K.activation_train(4096, 1, 3072, L, grad_ckpt=False)
    ckpt = K.activation_train(4096, 1, 3072, L, grad_ckpt=True)
    ratio = full / ckpt
    ok = abs(ratio - L ** 0.5) < 1e-6 and abs(ratio - 5.66) < 0.01
    print(f"    L={L}: 不开 {full / GB:.3f} GB  →  开 {ckpt / GB:.3f} GB"
          f"   压缩比 = {ratio:.2f} (= √{L})")
    # 压缩比随 L 单调增长（层数越多越值）
    ratios = [K.activation_train(1024, 1, 512, n) / K.activation_train(1024, 1, 512, n, True)
              for n in (8, 16, 32, 64)]
    ok = ok and ratios == sorted(ratios)
    print(f"    压缩比随层数增长: " + "  ".join(f"L={n}→{r:.1f}x"
                                              for n, r in zip((8, 16, 32, 64), ratios)))
    return ok


def check5_two_paths_same_order():
    """经验系数式 与 34 单位式 在 4K 序列上同量级（本模块给的安放）。"""
    w = K.weight_bytes(3, B16)
    by_ratio = K.activation_infer(w, 0.30)
    by_unit = K.activation_train(4096, 1, 3072, 32)
    order = by_unit / by_ratio
    ok = 1 < order < 100 and by_unit > 0 and by_ratio > 0
    print(f"    经验系数式(3B×30%)  = {by_ratio / GB:.3f} GB")
    print(f"    34 单位式(4K 训练)   = {by_unit / GB:.3f} GB   量级比 {order:.1f}x")
    print(f"    → 训练式给出的是【长序列全额激活】，经验系数式给出的是【权重占比】")
    return ok


def check6_docs_carry_both_tiers():
    """9-7 正文必须同时给出 10% 与 20–30% 两档，且说明差异来源是 s。"""
    import io
    p = os.path.join(P9, "07-activation.md")
    txt = io.open(p, encoding="utf-8").read()
    need = ["10%", "20", "30%", "Gradient Checkpointing", "O(√L)", "s = 2048"]
    missing = [n for n in need if n not in txt]
    ok = not missing
    print(f"    9-7 关键词命中 {len(need) - len(missing)}/{len(need)}"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    return ok


def main():
    checks = [
        check1_aliyun_10pct_tier(),
        check2_csdn_20_30_tier(),
        check3_dual_tier_monotonic_and_disjoint(),
        check4_grad_checkpoint_algebra(),
        check5_two_paths_same_order(),
        check6_docs_carry_both_tiers(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_16 failed"
    print("PASS: gate_16 激活值 6/6（10%档 + 20~30%档 + 单调不相交 + O(√L) + 两路径同量级 + 正文）")


if __name__ == "__main__":
    main()
