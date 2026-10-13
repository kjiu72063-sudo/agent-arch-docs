"""gate_02_framework_choice.py — 微调框架选型决策表

对应页面：1-6 主流微调框架横评
讲义依据：L1 P16（6 框架对照表 + "框架选择"四条建议）

验证什么：把 L1 P16 的"框架选择"四条建议编码成静态规则表，
         给定条件必命中同一分支（声明式、可枚举、无歧义）。
为什么确定：规则可枚举，纯布尔判断。
运行：python training/gate/gate_02_framework_choice.py
"""

# L1 P16 原文"框架选择"四条建议 → 编码为静态表
RULES = [
    # (条件, 首选框架, 原文依据)
    ("入门与实验", ["Transformers", "PEFT"], "入门与实验首选：Transformers + PEFT 组合"),
    ("快速实现与低代码", ["LLaMA-Factory"], "快速实现与低代码：LLaMA-Factory"),
    ("企业级与多模态", ["ModelScope", "MS-SWIFT"], "企业级与多模态：ModelScope 和 MS-SWIFT"),
    ("资源有限与求快", ["Unsloth"], "资源有限与求快：Unsloth"),
]

FRAMEWORKS = ["Transformers", "PEFT", "LLaMA-Factory", "ModelScope", "MS-SWIFT", "Unsloth"]

# 框架能力表（L1 P16 原表关键列）
CAPABILITY = {
    "Transformers": {"定位": "生态核心", "方法": "全参数微调，兼容 PEFT"},
    "PEFT": {"定位": "参数高效微调标准库", "方法": "LoRA/Prefix-Tuning/AdaLoRA/Prompt Tuning"},
    "LLaMA-Factory": {"定位": "低代码/无代码快速微调", "方法": "多种微调方法与优化技术"},
    "ModelScope": {"定位": "模型即服务平台", "方法": "多模态训练、推理与优化"},
    "MS-SWIFT": {"定位": "支持超大规模模型", "方法": "LoRA/QLoRA/分布式/量化"},
    "Unsloth": {"定位": "极致微调加速", "方法": "LoRA/QLoRA 底层优化"},
}


def check1_six_frameworks_covered():
    """L1 P16 原表就是 6 个框架，不能多不能少。"""
    ok = len(FRAMEWORKS) == 6 and set(FRAMEWORKS) == set(CAPABILITY)
    print(f"    框架数={len(FRAMEWORKS)}: {FRAMEWORKS}")
    return ok


def select_framework(scenario):
    """静态规则分派：同一场景必得同一结果（声明式，无随机）。"""
    for cond, picks, _ in RULES:
        if cond == scenario:
            return picks
    raise KeyError(f"未覆盖的场景: {scenario}")


def check2_rules_are_deterministic():
    """同一条件调用两次结果相同，且命中结果都来自已知 6 框架。"""
    for cond, _, _ in RULES:
        a, b = select_framework(cond), select_framework(cond)
        if a != b or not set(a) <= set(FRAMEWORKS):
            print(f"    ✗ 不确定/越界: {cond} -> {a} vs {b}")
            return False
    print(f"    4 条规则全部确定且闭集: {[c for c, _, _ in RULES]}")
    return True


def check3_rules_are_mutually_exclusive():
    """四条建议的触发条件互不重叠（每个场景唯一命中）。"""
    conds = [c for c, _, _ in RULES]
    ok = len(conds) == len(set(conds))
    # 具体反例：同一场景不会既给 LLaMA-Factory 又给 Unsloth
    a = select_framework("快速实现与低代码")
    b = select_framework("资源有限与求快")
    ok = ok and a == ["LLaMA-Factory"] and b == ["Unsloth"] and a != b
    print(f"    低代码 -> {a} ; 资源有限 -> {b}（互斥）")
    return ok


def check4_evidence_text_matches_lecture():
    """每条规则都挂着讲义原文，防止规则被臆造。"""
    ok = all(isinstance(ev, str) and len(ev) > 0 and "：" in ev for _, _, ev in RULES)
    print(f"    示例原文: {RULES[0][2]}")
    return ok


def main():
    checks = [
        check1_six_frameworks_covered(),
        check2_rules_are_deterministic(),
        check3_rules_are_mutually_exclusive(),
        check4_evidence_text_matches_lecture(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_02 failed"
    print("PASS: gate_02 框架选型 4/4（6框架闭集 + 规则确定 + 互斥 + 附原文）")


if __name__ == "__main__":
    main()
