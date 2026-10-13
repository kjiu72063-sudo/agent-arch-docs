"""gate_13_weights_params.py — 参数量公式与"标签/架构两条链"的自洽检查

对应页面：9-3 模型权重（上）/ 9-4 模型权重（下）

验证什么：
  1. 参数量通式 Φ = V·h + L·(4h² + 3h·f) 在计算器默认架构上的逐项算术自洽
  2. 由 32 层 / 3072 / 18944 / 152064 **反推**得到的 Φ ≈ 7.26B，
     与界面标注的 `总参数量 = 3 B` **不一致**（+142%）——这是本模块发现的
     真实数据链矛盾，属"必须被断言的事实"，不是"待修复的 bug"
  3. MoE 语义：总参必须全部驻留，激活参只影响激活值/算力

为什么确定：纯算术，无实测成分。
运行：python training/gate/gate_13_weights_params.py
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")

# 计算器默认架构（架构弹窗 14 字段中的 6 个）
V = 152064      # 词表大小
h = 3072        # 隐藏层维度
L = 32          # Transformer 层数
f = 18944       # FFN 中间层维度

LABELED_PARAMS_B = 3.0      # 界面「总参数量」标签值（十亿）


def embedding_params():
    return V * h


def attn_params_per_layer():
    """注意力投影参数：QKV 各 h×h，输出 proj h×h → 4h²"""
    return 4 * h * h


def ffn_params_per_layer():
    """FFN：up(h×f) + down(f×h) + gate(h×f) → 3hf"""
    return 3 * h * f


def params_per_layer():
    return attn_params_per_layer() + ffn_params_per_layer()


def total_params():
    return embedding_params() + L * params_per_layer()


def check1_itemized_arithmetic():
    """逐项算术自洽（9-4 正文给出的四个数）。"""
    got = (embedding_params(), attn_params_per_layer(),
           ffn_params_per_layer(), params_per_layer(), total_params())
    expect = (467140608, 37748736, 174587904, 212336640, 7261913088)
    ok = got == expect
    print(f"    embedding      = {got[0]:,}")
    print(f"    attn/层        = {got[1]:,}")
    print(f"    ffn/层         = {got[2]:,}")
    print(f"    合计/层        = {got[3]:,}")
    print(f"    总计           = {got[4]:,}")
    print(f"    手算核对       = {expect[4]:,}")
    return ok


def check2_attn_ffn_ratio():
    """FFN 是每层参数的主体：3hf / 4h² = 3f / 4h。"""
    ratio = ffn_params_per_layer() / attn_params_per_layer()
    expect = 3 * f / (4 * h)
    ok = abs(ratio - expect) < 1e-12 and ratio > 4
    print(f"    FFN/注意力 = {ratio:.2f} (= 3f/4h = {expect:.2f})")
    return ok


def check3_label_vs_architecture_inconsistent():
    """★ 标签值 3 B 与架构反推 7.26 B 不自洽（本模块的核心发现之一）。"""
    derived_b = total_params() / 1e9
    gap = derived_b / LABELED_PARAMS_B - 1
    # 断言"确实不一致"，且量级为 +142%
    ok = derived_b > LABELED_PARAMS_B * 2 and abs(gap - 1.4206) < 0.01
    print(f"    架构反推 {derived_b:.2f} B  vs  界面标签 {LABELED_PARAMS_B:.0f} B"
          f"  →  偏差 +{gap * 100:.1f}%")
    return ok


def check4_moe_semantics():
    """MoE：总参全加载 → 权重按总参算；激活参只进激活值。"""
    total_b, active_b = 3.0, 0.1
    w_by_total = total_b * 1e9 * 2          # FP16
    w_by_active = active_b * 1e9 * 2
    ok = w_by_total == 30 * w_by_active and w_by_total > w_by_active
    print(f"    权重按总参 {w_by_total / 1e9:.2f} GB  vs  按激活参 {w_by_active / 1e9:.2f} GB"
          f"  （差 {w_by_total / w_by_active:.0f} 倍）")
    return ok


def check5_docs_carry_the_numbers():
    """9-3 / 9-4 正文必须载有这五个数（防止正文与 gate 脱钩）。

    正文用千分位书写（`467,140,608`），故匹配前先去掉 `,` 与 `_`。
    """
    need = ("467140608", "37748736", "174587904", "212336640", "7261913088")
    raw = ""
    for name in ("03-weights-params.md", "04-weights-formula.md"):
        raw += io.open(os.path.join(P9, name), encoding="utf-8").read()
    txt_flat = raw.replace(",", "").replace("_", "")
    missing = [n for n in need if n not in txt_flat]
    ok = not missing
    print(f"    正文命中 {len(need) - len(missing)}/{len(need)}"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    return ok


def main():
    checks = [
        check1_itemized_arithmetic(),
        check2_attn_ffn_ratio(),
        check3_label_vs_architecture_inconsistent(),
        check4_moe_semantics(),
        check5_docs_carry_the_numbers(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_13 failed"
    print("PASS: gate_13 参数量公式 5/5（逐项算术 + FFN 占比 + 标签不自洽 + MoE 语义 + 正文承载）")


if __name__ == "__main__":
    main()
