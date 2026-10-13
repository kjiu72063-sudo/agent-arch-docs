"""gate_14_kv_formula.py — KV Cache 公式：通式退化 + 7 档单调 + 三种前沿机制

对应页面：9-5 KV Cache（上）/ 9-6 KV Cache（下）

验证什么：
  1. 通式 `2·L·n_kv·d_head·s·b·C·bytes` 在 `n_kv = n_q` 时**退化为**
     `2·L·h·s·b·C·bytes` —— 即阿里云 PAI 与 CSDN-leo0308 给出的 MHA 特例
  2. 7 档注意力结构各自算出 KV 且满足应有的单调关系
     （MHA > GQA > MQA；MLA 走潜变量式）
  3. ★ 三种前沿机制的方向性断言：
       SWA  降【存储】（有效长度饱和）
       DSA  降【读取条目数】而**存储不变**
       CSA2 降【跨层重复】（存储 → MLA 的 1/4）

为什么确定：纯算术 + 方向性不等式，无实测成分。
运行：python training/gate/gate_14_kv_formula.py
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")
sys.path.insert(0, os.path.join(P9, "_calc"))

import calc as K  # noqa: E402  （本模块公式参考实现）

# 计算器默认架构
KW = dict(L=32, n_q=48, n_kv=48, h=3072, d_c=512 + 64, s=4096, b=1, C=1, kv_b=2)


def check1_general_formula_degenerates_to_mha():
    """通式在 n_kv = n_q 时 == 两篇参考的 MHA 公式。"""
    general = K.kv_bytes("MHA", **KW)
    reference = 2 * KW["L"] * KW["h"] * KW["s"] * KW["b"] * KW["C"] * KW["kv_b"]
    ok = abs(general - reference) < 1e-6
    print(f"    通式          = {general:,.0f} B")
    print(f"    两篇参考 MHA  = {reference:,.0f} B")
    return ok


def check2_tier_monotonic():
    """MHA > GQA > MQA；位宽 FP16 > INT8 > INT4；MLA/DSA/CSA2 各有正确关系。"""
    kw = dict(KW, n_kv=8)          # 用 n_kv=8 才能体现 GQA 与 MQA 的差
    mha = K.kv_bytes("MHA", **kw)
    gqa = K.kv_bytes("GQA", **kw)
    mqa = K.kv_bytes("MQA", **kw)
    ok = mha > gqa > mqa

    # 位宽单调
    kw2 = dict(KW, kv_b=None)
    mla16 = K.kv_bytes("MLA", **dict(KW, kv_b=2))
    mla8 = K.kv_bytes("MLA", **dict(KW, kv_b=1))
    mla4 = K.kv_bytes("MLA", **dict(KW, kv_b=0.5))
    ok = ok and mla16 > mla8 > mla4

    # GQA 的降幅恰为 n_kv / n_q
    ratio = mha / gqa
    ok = ok and abs(ratio - KW["n_q"] / 8) < 1e-9
    # MQA 的降幅恰为 n_q
    ok = ok and abs(mha / mqa - KW["n_q"]) < 1e-9
    print(f"    MHA {mha / 1e9:.4f} GB > GQA {gqa / 1e9:.4f} GB > MQA {mqa / 1e9:.4f} GB")
    print(f"    MHA/GQA = {ratio:.1f} (= n_q/n_kv)   MHA/MQA = {mha / mqa:.1f} (= n_q)")
    print(f"    MLA 位宽单调: FP16 {mla16 / 1e9:.4f} > INT8 {mla8 / 1e9:.4f} > INT4 {mla4 / 1e9:.4f} GB")
    return ok


def check3_mla_ratio_is_2h_over_dc():
    """MLA/MHA 的 KV 比值 == 2h / d_c（三篇参考均无此式）。"""
    r = K.assert_mla_ratio()
    expect_default = 2 * KW["h"] / KW["d_c"]
    default = K.kv_bytes("MHA", **dict(KW, n_kv=KW["n_q"])) / K.kv_bytes("MLA", **KW)
    ok = abs(r - 2 * 3072 / 576) < 1e-9 and abs(default - expect_default) < 1e-9
    print(f"    DeepSeek-V3 口径  2h/d_c = {r:.2f}x")
    print(f"    计算器默认模型    2h/d_c = {default:.2f}x  (= 2×3072/576)")
    return ok


def check4_swa_saves_storage():
    """SWA 降【存储】：s 超过 W 后 KV 成为常数。"""
    kw = dict(KW, n_kv=8, win=4096)
    a = K.kv_bytes("SWA", **dict(kw, s=8192))
    b = K.kv_bytes("SWA", **dict(kw, s=131072))
    mha_long = K.kv_bytes("MHA", **dict(kw, s=131072))
    ok = abs(a - b) < 1e-6 and b < mha_long
    print(f"    SWA s=8192  {a / 1e9:.4f} GB")
    print(f"    SWA s=131072 {b / 1e9:.4f} GB   ← 完全相同（窗口饱和）")
    print(f"    MHA s=131072 {mha_long / 1e9:.4f} GB   ← SWA 省 {mha_long / b:.0f}x")
    return ok


def check5_dsa_saves_bandwidth_not_storage():
    """★ DSA 降【读取条目数】而**存储不变**（选型误判的头号来源）。"""
    storage_dsa = K.kv_bytes("DSA", **KW)
    storage_mla = K.kv_bytes("MLA", **KW)
    # 存储完全相等
    ok = abs(storage_dsa - storage_mla) < 1e-6
    # 读取量随 top-K 下降：topK 越小读得越少
    read_2k = K.kv_read_bytes("DSA", L=KW["L"], d_c=KW["d_c"], s=KW["s"], topk=2048)
    read_1k = K.kv_read_bytes("DSA", L=KW["L"], d_c=KW["d_c"], s=KW["s"], topk=1024)
    read_4k = K.kv_read_bytes("DSA", L=KW["L"], d_c=KW["d_c"], s=KW["s"], topk=4096)
    ok = ok and read_1k < read_2k < read_4k and read_2k < storage_mla
    print(f"    存储：DSA {storage_dsa / 1e9:.4f} GB  ==  MLA {storage_mla / 1e9:.4f} GB"
          f"   ← 完全不降")
    print(f"    读取：topK=1024 {read_1k / 1e6:.1f} MB  <  2048 {read_2k / 1e6:.1f} MB"
          f"  <  4096 {read_4k / 1e6:.1f} MB   ← 单调")
    return ok


def check6_csa2_saves_crosslayer():
    """CSA2 降【跨层重复】：存储 → MLA 的 1/4。"""
    mla = K.kv_bytes("MLA", **KW)
    csa2 = K.kv_bytes("CSA2", **KW)
    ok = abs(csa2 - mla / 4) < 1e-6
    print(f"    MLA {mla / 1e9:.4f} GB  →  CSA2 {csa2 / 1e9:.4f} GB   比值 {mla / csa2:.1f}x")
    return ok


def check7_docs_carry_all_seven_tiers():
    """9-5 / 9-6 正文必须逐一提到 7 档，且 9-A 词典含全 7 档。"""
    txt = ""
    for name in ("05-kv-classic.md", "06-kv-frontier.md", "A-param-dict.md"):
        txt += io.open(os.path.join(P9, name), encoding="utf-8").read()
    need = ["MHA", "GQA", "MQA", "MLA", "SWA", "DSA", "CSA2"]
    missing = [n for n in need if n not in txt]
    ok = not missing
    print(f"    7 档命中 {len(need) - len(missing)}/7"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    return ok


def main():
    checks = [
        check1_general_formula_degenerates_to_mha(),
        check2_tier_monotonic(),
        check3_mla_ratio_is_2h_over_dc(),
        check4_swa_saves_storage(),
        check5_dsa_saves_bandwidth_not_storage(),
        check6_csa2_saves_crosslayer(),
        check7_docs_carry_all_seven_tiers(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_14 failed"
    print("PASS: gate_14 KV 公式 7/7（通式退化 + 7档单调 + MLA比值 + SWA存储 + DSA带宽 + CSA2跨层 + 正文）")


if __name__ == "__main__":
    main()
