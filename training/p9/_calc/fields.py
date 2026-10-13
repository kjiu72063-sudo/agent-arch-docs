# -*- coding: utf-8 -*-
"""
p9/_calc/fields.py —— 计算器字段清单（机器可读）
================================================================
用途：gate_24「参数词典完整性」的唯一事实源。

断言方向固定为：
    计算器字段清单  ⊆  9-A 参数词典词条
即"每个计算器字段都必须在词典里被讲到"——把
「大纲没讲的必须提出来」变成可自动检查的断言（方案 §8 第 12 项）。

字段来源：录屏 2544×1400 场景切帧 35 帧 OCR + 首轮 5 张截图。
分组与 9-A《参数词典》的 §1 ~ §7 一一对应。

label 必须与 A-param-dict.md 中的字面文本一致（gate 做子串匹配）。
"""

GROUP_ARCH = "§1 架构组"
GROUP_INFER = "§2 推理组"
GROUP_TRAIN = "§3 微调组"
GROUP_PRESET = "§4 容量规划预设"
GROUP_SLA = "§5 SLA 与预算约束"
GROUP_HW = "§6 硬件与拓扑"
GROUP_PANEL = "§7 结果面板"

KIND_KNOB = "knob"          # 真旋钮：能改动显存账本任一项
KIND_NOFX = "nofx"          # 明确不改账本的旋钮
KIND_LATENCY = "latency"    # 只影响时延 / 成本
KIND_DISPLAY = "display"    # 只读派生 / 预设按钮 / 展示项
KIND_SECONDARY = "secondary"  # 次生参数：界面有，公式未给

# id, label, group, kind
FIELDS = [
    # ── §1 架构组（15）─────────────────────────────────────
    ("arch_params",      "总参数量",                       GROUP_ARCH, KIND_KNOB),
    ("arch_kind",        "架构",                           GROUP_ARCH, KIND_KNOB),
    ("arch_active",      "激活专家参数量",                  GROUP_ARCH, KIND_KNOB),
    ("arch_modality",    "模态",                           GROUP_ARCH, KIND_SECONDARY),
    ("arch_attn",        "注意力机制结构",                  GROUP_ARCH, KIND_KNOB),
    ("arch_layers",      "Transformer 层数",               GROUP_ARCH, KIND_KNOB),
    ("arch_hidden",      "隐藏层维度",                      GROUP_ARCH, KIND_KNOB),
    ("arch_nq",          "Query 注意力头数",               GROUP_ARCH, KIND_KNOB),
    ("arch_nkv",         "KV 注意力头数",                  GROUP_ARCH, KIND_KNOB),
    ("arch_ffn",         "FFN 中间层维度",                  GROUP_ARCH, KIND_KNOB),
    ("arch_vocab",       "词表大小",                        GROUP_ARCH, KIND_KNOB),
    ("arch_pos",         "位置编码",                        GROUP_ARCH, KIND_NOFX),
    ("arch_window",      "滑动窗口大小",                    GROUP_ARCH, KIND_KNOB),
    ("arch_linattn",     "线性注意力比例",                  GROUP_ARCH, KIND_SECONDARY),
    ("arch_dc",          "KV 潜变量维度",                  GROUP_ARCH, KIND_KNOB),

    # ── §2 推理组（14）────────────────────────────────────
    ("inf_model",        "选择模型",                        GROUP_INFER, KIND_KNOB),
    ("inf_batch",        "批量大小",                        GROUP_INFER, KIND_KNOB),
    ("inf_seq",          "序列长度",                        GROUP_INFER, KIND_KNOB),
    ("inf_conc",         "并发用户数",                      GROUP_INFER, KIND_KNOB),
    ("inf_wprec",        "推理量化",                        GROUP_INFER, KIND_KNOB),
    ("inf_kvprec",       "KV 缓存量化",                     GROUP_INFER, KIND_KNOB),
    ("inf_offload",      "启用卸载到 CPU/RAM 或 NVMe",       GROUP_INFER, KIND_KNOB),
    ("inf_chunked",      "分块预填充",                      GROUP_INFER, KIND_KNOB),
    ("inf_chunksize",    "预填充分块大小",                  GROUP_INFER, KIND_KNOB),
    ("inf_execmode",     "执行模式（图编排）",               GROUP_INFER, KIND_KNOB),
    ("inf_prefixcache",  "前缀缓存模式",                    GROUP_INFER, KIND_KNOB),
    ("inf_prefixblock",  "前缀块大小",                      GROUP_INFER, KIND_KNOB),
    ("inf_staticvram",   "静态 VRAM 预分配",                 GROUP_INFER, KIND_KNOB),
    ("inf_specdecode",   "投机解码",                        GROUP_INFER, KIND_KNOB),

    # ── §3 微调组（21）────────────────────────────────────
    ("tr_mode",          "训练模式",                        GROUP_TRAIN, KIND_KNOB),
    ("tr_basemodel",     "基础模型精度",                    GROUP_TRAIN, KIND_DISPLAY),
    ("tr_lora_r",        "LoRA 秩 (r)",                     GROUP_TRAIN, KIND_KNOB),
    ("tr_batch",         "批量大小",                        GROUP_TRAIN, KIND_KNOB),
    ("tr_seq",           "序列长度",                        GROUP_TRAIN, KIND_KNOB),
    ("tr_gradaccum",     "梯度累积",                        GROUP_TRAIN, KIND_NOFX),
    ("tr_highaccum",     "启用高范围累积步数",               GROUP_TRAIN, KIND_SECONDARY),
    ("ds_samples",       "样本数",                          GROUP_TRAIN, KIND_LATENCY),
    ("ds_seq",           "序列长度",                        GROUP_TRAIN, KIND_LATENCY),
    ("ds_epochs",        "训练轮次",                        GROUP_TRAIN, KIND_LATENCY),
    ("tr_optpreset",     "优化预设",                        GROUP_TRAIN, KIND_KNOB),
    ("tr_zero",          "ZeRO 阶段",                       GROUP_TRAIN, KIND_KNOB),
    ("tr_optimizer",     "优化器类型",                      GROUP_TRAIN, KIND_KNOB),
    ("tech_flash",       "Flash Attention",                 GROUP_TRAIN, KIND_KNOB),
    ("tech_ckpt",        "梯度检查点",                      GROUP_TRAIN, KIND_KNOB),
    ("tech_opt8",        "8 位优化器",                      GROUP_TRAIN, KIND_KNOB),
    ("tech_paged",       "分页优化器",                      GROUP_TRAIN, KIND_NOFX),
    ("tech_fused",       "融合内核",                        GROUP_TRAIN, KIND_KNOB),
    ("tech_pack",        "序列打包",                        GROUP_TRAIN, KIND_NOFX),
    ("tech_dynpad",      "动态填充",                        GROUP_TRAIN, KIND_KNOB),
    ("tech_pure16",      "纯 16 位训练",                    GROUP_TRAIN, KIND_KNOB),

    # ── §4 容量规划预设（9）───────────────────────────────
    ("pre_autofit",      "自动适配",                        GROUP_PRESET, KIND_DISPLAY),
    ("pre_bestprec",     "最佳精度",                        GROUP_PRESET, KIND_DISPLAY),
    ("pre_maxctx",       "最大上下文",                      GROUP_PRESET, KIND_DISPLAY),
    ("pre_maxtput",      "最高吞吐量",                      GROUP_PRESET, KIND_DISPLAY),
    ("pre_mincost",      "最低成本配置",                    GROUP_PRESET, KIND_DISPLAY),
    ("pre_maxtput2",     "最大吞吐量",                      GROUP_PRESET, KIND_DISPLAY),
    ("pre_evalcount",    "评估配置数",                      GROUP_PRESET, KIND_DISPLAY),
    ("pre_hwtype",       "硬件类型",                        GROUP_PRESET, KIND_DISPLAY),
    ("pre_precision",    "精度（量化）",                    GROUP_PRESET, KIND_KNOB),

    # ── §5 SLA 与预算约束（3）─────────────────────────────
    ("sla_ttft",         "最大 TTFT 延迟目标",               GROUP_SLA, KIND_LATENCY),
    ("sla_tps",          "最低 TPS 目标",                   GROUP_SLA, KIND_LATENCY),
    ("sla_filter",       "按延迟/小时成本/最低速度过滤配置",   GROUP_SLA, KIND_LATENCY),

    # ── §6 硬件与拓扑（11）────────────────────────────────
    ("hw_rig",           "单机 Rig / 集群",                  GROUP_HW, KIND_DISPLAY),
    ("hw_gpu",           "设备 / GPU",                      GROUP_HW, KIND_KNOB),
    ("hw_quality",       "GPU 质量（性能系数）",             GROUP_HW, KIND_LATENCY),
    ("hw_interconnect",  "GPU 互连类型",                    GROUP_HW, KIND_LATENCY),
    ("hw_nodes",         "物理节点数 (Nodes)",               GROUP_HW, KIND_KNOB),
    ("hw_gpuspernode",   "单节点 GPU 数",                   GROUP_HW, KIND_KNOB),
    ("hw_pp",            "流水线并行 (PP) 维度",             GROUP_HW, KIND_KNOB),
    ("hw_tp",            "张量并行 (TP) 维度",               GROUP_HW, KIND_KNOB),
    ("hw_inferorche",    "推理并行编排",                    GROUP_HW, KIND_KNOB),
    ("hw_grid",          "总计 / 3D 网格",                  GROUP_HW, KIND_DISPLAY),
    ("hw_save",          "保存配置",                        GROUP_HW, KIND_DISPLAY),

    # ── §7 结果面板（12）──────────────────────────────────
    ("panel_ring",       "显存占用环",                      GROUP_PANEL, KIND_DISPLAY),
    ("panel_verdict",    "判定词",                          GROUP_PANEL, KIND_DISPLAY),
    ("panel_spec",       "模型规格卡",                      GROUP_PANEL, KIND_DISPLAY),
    ("panel_ledger",     "内存分配",                        GROUP_PANEL, KIND_DISPLAY),
    ("panel_gentps",     "生成速度",                        GROUP_PANEL, KIND_LATENCY),
    ("panel_perToken",   "每 token 延迟",                   GROUP_PANEL, KIND_LATENCY),
    ("panel_ttft",       "首个令牌时间 (TTFT)",              GROUP_PANEL, KIND_LATENCY),
    ("panel_rental",     "估算 GPU 租赁",                   GROUP_PANEL, KIND_LATENCY),
    ("panel_power",      "功耗",                            GROUP_PANEL, KIND_LATENCY),
    ("panel_co2day",     "CO₂/天",                          GROUP_PANEL, KIND_LATENCY),
    ("panel_traincost",  "GPU 训练成本估算",                GROUP_PANEL, KIND_LATENCY),
    ("panel_elec",       "本地电费支出预测 / 环境影响",       GROUP_PANEL, KIND_LATENCY),
]

# 与 9-A《参数词典》§8 的统计表必须一致
EXPECTED_TOTAL = 85
GROUP_COUNTS = {
    GROUP_ARCH: 15, GROUP_INFER: 14, GROUP_TRAIN: 21,
    GROUP_PRESET: 9, GROUP_SLA: 3, GROUP_HW: 11, GROUP_PANEL: 12,
}
KIND_COUNTS = {
    KIND_KNOB: 46, KIND_NOFX: 4, KIND_LATENCY: 16,
    KIND_DISPLAY: 16, KIND_SECONDARY: 3,
}

# 次生参数（界面有、公式未给）——9-A 明确标注"本模块未展开"
SECONDARY_IDS = ("arch_modality", "arch_linattn", "tr_highaccum")

# 判定词档表（仅"非常高"经界面实测确认；其余标【待核实】）
VERDICT_TIER_WORDS = ("可以", "充足", "偏高", "非常高")
VERDICT_CONFIRMED = "非常高"

# 7 档注意力结构（归属分类）
ATTN_CLASSIC = ("MHA", "GQA", "MQA", "MLA")
ATTN_FRONTIER = ("SWA", "DSA", "CSA2")


def labels():
    return [lbl for _, lbl, _, _ in FIELDS]


def by_group(group):
    return [f for f in FIELDS if f[2] == group]


def by_kind(kind):
    return [f for f in FIELDS if f[3] == kind]


def self_check():
    """清单自身的结构自检（gate_24 会调用）。"""
    assert len(FIELDS) == EXPECTED_TOTAL, (len(FIELDS), EXPECTED_TOTAL)
    assert len({f[0] for f in FIELDS}) == EXPECTED_TOTAL, "id 必须唯一"
    for g, n in GROUP_COUNTS.items():
        got = len(by_group(g))
        assert got == n, (g, got, n)
    for k, n in KIND_COUNTS.items():
        got = len(by_kind(k))
        assert got == n, (k, got, n)
    assert sum(GROUP_COUNTS.values()) == EXPECTED_TOTAL
    assert sum(KIND_COUNTS.values()) == EXPECTED_TOTAL
    for sid in SECONDARY_IDS:
        assert any(f[0] == sid for f in FIELDS), sid
    assert len(VERDICT_TIER_WORDS) >= 3
    assert VERDICT_CONFIRMED in VERDICT_TIER_WORDS


if __name__ == "__main__":
    self_check()
    print(f"字段总数 {len(FIELDS)}")
    for g, n in GROUP_COUNTS.items():
        print(f"  {g}: {len(by_group(g))}")
    for k, n in KIND_COUNTS.items():
        print(f"  [{k}] {len(by_kind(k))}")
    print("self_check OK")
