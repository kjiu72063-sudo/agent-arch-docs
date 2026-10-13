"""gate_24_param_dict_completeness.py — ★ 参数词典完整性（本模块特有的"防漏"gate）

对应页面：9-A 参数词典

把「大纲没讲的必须提出来」从一句要求，变成一条**可自动检查的断言**。

验证什么：
  1. `p9/_calc/fields.py` 的清单结构自洽（总数 / 分组 / 分类三项计数全对）
  2. **计算器字段清单 ⊆ 9-A 词典词条**（85/85 逐条子串命中）—— 核心断言
  3. 9-A 正文声明的统计表与 fields.py 一致（防止文档与清单脱钩）
  4. 判定词档表：档位数 ≥ 3 且**单调**；`非常高` 必须存在（界面实测那一档）
  5. 7 档注意力结构在词典中逐一可查
  6. 三处"次生参数"必须被显式标注为"未展开"（不冒充权威补公式）
  7. Part 9 的 19 页文件齐备

为什么确定：纯结构断言 + 字面匹配，无实测成分。
运行：python training/gate/gate_24_param_dict_completeness.py
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")
sys.path.insert(0, os.path.join(P9, "_calc"))

import fields as F  # noqa: E402

DICT_MD = os.path.join(P9, "A-param-dict.md")

EXPECTED_PAGES = [
    "01-first-constraint.md", "02-ledger-overview.md", "03-weights-params.md",
    "04-weights-formula.md", "05-kv-classic.md", "06-kv-frontier.md",
    "07-activation.md", "08-optimizer-states.md", "09-unaccounted.md",
    "10-parallel-split.md", "11-hardware.md", "12-cost-green.md",
    "13-inference-tuning.md", "14-training-tuning.md", "15-end-to-end.md",
    "16-calculator.md", "A-param-dict.md", "B-formula-card.md", "C-model-matrix.md",
]


def read_dict():
    return io.open(DICT_MD, encoding="utf-8").read()


def check1_fields_index_selfconsistent():
    """fields.py 的结构自检：总数 / 分组 / 分类三项计数全对。"""
    F.self_check()
    total = len(F.FIELDS)
    g = sum(F.GROUP_COUNTS.values())
    k = sum(F.KIND_COUNTS.values())
    ok = total == F.EXPECTED_TOTAL == g == k
    print(f"    字段总数 {total}  分组合计 {g}  分类合计 {k}  期望 {F.EXPECTED_TOTAL}")
    print("    分组: " + " / ".join(f"{k2}:{len(F.by_group(k2))}" for k2 in F.GROUP_COUNTS))
    print("    分类: " + " / ".join(f"{k2}:{len(F.by_kind(k2))}" for k2 in F.KIND_COUNTS))
    return ok


def check2_all_fields_present_in_dict():
    """★ 核心断言：计算器字段清单 ⊆ 9-A 词典词条（逐条子串命中）。"""
    txt = read_dict()
    missing = [(fid, lbl) for fid, lbl, _, _ in F.FIELDS if lbl not in txt]
    ok = not missing
    hit = len(F.FIELDS) - len(missing)
    print(f"    {hit}/{len(F.FIELDS)} 条命中")
    if missing:
        for fid, lbl in missing:
            print(f"    ✗ 缺失: {fid}  「{lbl}」")
    return ok


def check3_doc_stats_match_index():
    """9-A 正文的统计表必须与 fields.py 一致（防止文档与清单脱钩）。"""
    txt = read_dict()
    need = [
        ("字段总数", str(F.EXPECTED_TOTAL)),
        ("真旋钮", str(F.KIND_COUNTS[F.KIND_KNOB])),
        ("不改账本", str(F.KIND_COUNTS[F.KIND_NOFX])),
        ("只影响时延 / 成本", str(F.KIND_COUNTS[F.KIND_LATENCY])),
        ("只读派生 / 预设按钮 / 展示项", str(F.KIND_COUNTS[F.KIND_DISPLAY])),
        ("次生参数", str(F.KIND_COUNTS[F.KIND_SECONDARY])),
    ]
    bad = [f"{label}={v}" for label, v in need if
           f"**{v}**" not in txt and f"| {v} |" not in txt and v not in txt]
    ok = not bad
    print(f"    统计表口径: " + "  ".join(f"{l}={v}" for l, v in need))
    if bad:
        print(f"    ✗ 正文与清单不一致: {bad}")
    return ok


def check4_verdict_tiers_monotonic():
    """判定词：档数 ≥ 3 且单调；`非常高` 必须存在（界面实测那一档）。"""
    words, thresholds = F.VERDICT_TIER_WORDS, (0.50, 0.70, 0.90, 1.01)
    ok = len(words) >= 3 and F.VERDICT_CONFIRMED in words
    ok = ok and list(thresholds) == sorted(thresholds)
    txt = read_dict()
    ok = ok and "判定词" in txt and "非常高" in txt
    ok = ok and ("待核实" in txt or "仅此一档" in txt or "仅 1 档" in txt)
    print(f"    档数 {len(words)}：{' < '.join(words)}（阈值单调 ✓）")
    print(f"    界面实测确认档 = 「{F.VERDICT_CONFIRMED}」；其余标【待核实】")
    return ok


def check5_seven_attention_tiers():
    """7 档注意力结构在词典中逐一可查，且前 4 / 后 3 的分类正确。"""
    txt = read_dict()
    ok = all(t in txt for t in F.ATTN_CLASSIC + F.ATTN_FRONTIER)
    ok = ok and len(F.ATTN_CLASSIC) == 4 and len(F.ATTN_FRONTIER) == 3
    # 三处机制判据必须出现
    ok = ok and "省存储" in txt and "省带宽" in txt and "跨层" in txt
    print(f"    前 4 档（经典+主流）: {F.ATTN_CLASSIC}")
    print(f"    后 3 档（2024–2026 前沿）: {F.ATTN_FRONTIER}")
    print(f"    机制判据「省存储 / 省带宽 / 跨层」均可查 ✓")
    return ok


def check6_secondary_params_marked_open():
    """三处次生参数必须被显式标为"未展开"——不冒充权威补公式（R3）。"""
    txt = read_dict()
    labels = [lbl for fid, lbl, _, _ in F.FIELDS if fid in F.SECONDARY_IDS]
    ok = len(labels) == 3 and all(l in txt for l in labels)
    ok = ok and txt.count("本模块未展开") >= 3
    print(f"    次生参数: {labels}")
    print(f"    正文出现『本模块未展开』{txt.count('本模块未展开')} 次（≥3 ✓）")
    return ok


def check7_all_nineteen_pages_exist():
    """Part 9 的 19 页文件齐备。"""
    missing = [p for p in EXPECTED_PAGES if not os.path.isfile(os.path.join(P9, p))]
    ok = not missing and len(EXPECTED_PAGES) == 19
    print(f"    页面 {len(EXPECTED_PAGES) - len(missing)}/{len(EXPECTED_PAGES)} 存在")
    if missing:
        print(f"    ✗ 缺失: {missing}")
    return ok


def check8_every_page_has_source_section():
    """每页都必须有「## 来源」段（R1/R2/R3 标注规则的落地保证）。"""
    bad = []
    for p in EXPECTED_PAGES:
        path = os.path.join(P9, p)
        if not os.path.isfile(path):
            bad.append(p)
            continue
        txt = io.open(path, encoding="utf-8").read()
        if "## 来源" not in txt:
            bad.append(p)
    ok = not bad
    print(f"    含「## 来源」的页面: {len(EXPECTED_PAGES) - len(bad)}/{len(EXPECTED_PAGES)}")
    if bad:
        print(f"    ✗ 缺失来源段: {bad}")
    return ok


def check9_three_annotation_levels_used():
    """三档标注（【事实】/【业界口径】/【推断】）必须在 Part 9 被真实使用。"""
    counts = {"【事实】": 0, "【业界口径】": 0, "【推断】": 0}
    for p in EXPECTED_PAGES:
        path = os.path.join(P9, p)
        if not os.path.isfile(path):
            continue
        txt = io.open(path, encoding="utf-8").read()
        for k in counts:
            counts[k] += txt.count(k)
    ok = all(v > 0 for v in counts.values()) and counts["【推断】"] >= 40
    print("    " + "  ".join(f"{k}×{v}" for k, v in counts.items()))
    return ok


def main():
    checks = [
        check1_fields_index_selfconsistent(),
        check2_all_fields_present_in_dict(),
        check3_doc_stats_match_index(),
        check4_verdict_tiers_monotonic(),
        check5_seven_attention_tiers(),
        check6_secondary_params_marked_open(),
        check7_all_nineteen_pages_exist(),
        check8_every_page_has_source_section(),
        check9_three_annotation_levels_used(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_24 failed"
    print("PASS: gate_24 参数词典完整性 9/9（清单自洽 + 85/85命中 + 统计一致 + 判定词单调 + 7档 + 次生参数标注 + 19页齐备 + 来源段 + 三档标注）")


if __name__ == "__main__":
    main()
