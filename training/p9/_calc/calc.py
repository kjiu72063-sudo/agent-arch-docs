# -*- coding: utf-8 -*-
"""
p9/_calc/calc.py —— 「显存与容量规划」公式参考实现
================================================================
与 9-15 交互式计算器（.vitepress/components/P9Calculator.vue）同源，
与 9-3 ~ 9-10 正文一致。纯标准库，无外部依赖。

用途：
  1) 供 gate_13 ~ gate_24 做交叉校验（文档 ↔ 组件 ↔ 本模块三方一致）
  2) 供读者离线复算（不想开浏览器时）

公式出处（正文页）：
  权重      Φ × 位宽字节                          9-3 / 9-4
  KV(通式)  2·L·n_kv·d_head·s·b·C·kv_bytes        9-5   MHA/GQA/MQA/SWA
  KV(MLA)   L·d_c·s·b·C·kv_bytes                  9-5   潜变量式
  KV(CSA2)  KV(MLA) / 4                           9-6   跨层复用
  激活(推)  权重 × 系数（默认 0.30）               9-7
  激活(训)  34·s·b·h·2B·L                        9-7 / 9-14
  梯度      可训练参数 × 2 B                       9-13
  优化器    可训练参数 × opt_bytes                 9-8
  框架开销  经验值 1~2 GB                          9-9
  摊分      ÷ (TP × PP × [DP])                    9-10

边界：只做算术与结构断言，不预测真实显存（容差 ±20%）。
"""

from __future__ import annotations

GB = 1e9
GiB = float(1024 ** 3)

W_BYTES = {"FP32": 4, "FP16": 2, "BF16": 2, "FP8": 1, "INT8": 1, "INT4": 0.5}
OPT_BYTES = {"SGD": 0, "SGD_M": 4, "RMSProp": 4, "AdamW": 8}

ATTN_TIERS = ("MHA", "GQA", "MQA", "MLA", "SWA", "DSA", "CSA2")
# 归属：前 4 档＝经典+主流；后 3 档＝2024–2026 前沿
ATTN_CLASSIC = ("MHA", "GQA", "MQA", "MLA")
ATTN_FRONTIER = ("SWA", "DSA", "CSA2")


# ─────────────────────────── 单项公式 ───────────────────────────

def weight_bytes(params_b: float, nbytes: float) -> float:
    """模型权重字节数。MoE 必须传【总参数量】（全部加载）。"""
    return params_b * GB * nbytes


def head_dim(h: int, n_q: int) -> float:
    return h / n_q


def kv_bytes(attn: str, L: int, n_q: int, n_kv: int, h: int, d_c: int,
             s: int, b: int = 1, C: int = 1, kv_b: float = 2,
             win: int | None = None) -> float:
    """KV Cache 字节数（按注意力结构分形态）。"""
    d_head = head_dim(h, n_q)
    if attn == "MHA":
        return 2 * L * n_q * d_head * s * b * C * kv_b
    if attn == "GQA":
        return 2 * L * n_kv * d_head * s * b * C * kv_b
    if attn == "SWA":
        eff = min(s, win) if win else s
        return 2 * L * n_kv * d_head * eff * b * C * kv_b
    if attn == "MQA":
        return 2 * L * 1 * d_head * s * b * C * kv_b
    if attn in ("MLA", "DSA"):
        # DSA 省【带宽】不省【存储】→ 存储与 MLA 同式
        return L * d_c * s * b * C * kv_b
    if attn == "CSA2":
        return L * d_c * s * b * C * kv_b / 4      # 跨层复用 global KV → ~1/4
    raise ValueError(f"unknown attention: {attn}")


def kv_read_bytes(attn: str, L: int, d_c: int, s: int, topk: int = 2048,
                  b: int = 1, C: int = 1, kv_b: float = 2) -> float:
    """【DSA 专用】每步实际读取的 KV 条目字节数（省带宽的口径）。
    存储不变，但每步只 touch top-K 个缓存条目。
    """
    if attn != "DSA":
        return kv_bytes(attn, L, 1, 1, d_c, d_c, s, b, C, kv_b)
    # 不做逐层 top-K 累积，只给单步读取量（用于展示"存储不变、读取量下降"）
    return L * min(s, topk) * d_c * b * C * kv_b


def activation_infer(w_bytes: float, ratio: float = 0.30) -> float:
    """推理激活值 ≈ 权重 × 经验系数。10%（阿里云条件）/ 20~30%（保守档）。"""
    return w_bytes * ratio


def activation_train(s: int, b: int, h: int, L: int,
                     grad_ckpt: bool = False,
                     flash: bool = False, fused: bool = False,
                     dyn_pad: bool = False, unit: float = 34.0) -> float:
    """训练激活值 = unit · s·b·h · 2B · L，可叠加优化系数。

    参数默认值一律为 False —— 本函数的默认语义是**教科书基线**
    （即"一项优化都不开"），这样 9-14 的复算才能与计算器界面读数对齐。
    9-15 交互式计算器的 UI 开关默认是**打开**的（那是工程实践默认），
    两者默认值不同是刻意的，不是笔误。
    """
    a = unit * s * b * h * 2 * L
    if grad_ckpt:
        a /= L ** 0.5            # O(L) → O(√L)
    if flash:
        a *= 0.75
    if fused:
        a *= 0.92
    if dyn_pad:
        a *= 0.90
    return a


def lora_params(L: int, h: int, ffn: int, r: int, scope: str = "attn") -> float:
    """LoRA 可训练参数量。scope='attn' 仅 q/k/v/o；'full' 含 gate/up/down。"""
    if scope == "attn":
        return float(L * 4 * 2 * h * r)
    if scope == "full":
        return float(L * (4 * 2 * h * r + 2 * (h * r + r * ffn) + (ffn * r + r * h)))
    raise ValueError(scope)


def gradient_bytes(trainable: float) -> float:
    return trainable * 2


def optimizer_bytes(trainable: float, opt: str = "AdamW", opt8: bool = False,
                    pure16: bool = False) -> float:
    b = OPT_BYTES[opt] if opt in OPT_BYTES else 8
    if opt8:
        b *= 0.25        # 8 B → 2 B（bitsandbytes）
    if pure16:
        b *= 0.5         # 去掉 fp32 主权重 / 状态降位（上界估算）
    return trainable * b


def lora_params_count(*args, **kwargs):
    return lora_params(*args, **kwargs)


# ─────────────────────────── 整本账 ───────────────────────────

def ledger_infer(params_b, attn, L, h, n_q, n_kv, d_c, s, b, C,
                 w_prec="INT8", kv_prec="FP16", win=None,
                 act_ratio=0.30, framework_gb=1.01, moe=False):
    """推理账本 5 项：权重 / KV / 激活 / 框架开销 / 多GPU开销。"""
    w = weight_bytes(params_b, W_BYTES[w_prec])
    kv = kv_bytes(attn, L, n_q, n_kv, h, d_c, s, b, C, W_BYTES[kv_prec], win)
    items = {
        "模型权重": w,
        "KV缓存": kv,
        "激活值": activation_infer(w, act_ratio),
        "框架开销": framework_gb * GB,
        "多GPU开销": 0.0,          # 单卡 ≈ 0；多卡无公开公式 → 【推断】
    }
    return items, sum(items.values())


def ledger_train(params_b, mode, opt, L, h, ffn, n_q, n_kv, d_c, s, b, C,
                 attn="MLA", r=16, scope="attn", w_prec="FP16", kv_prec="FP16",
                 framework_gb=1.01, techs=None, win=None, unit=34.0):
    """训练账本 5 项：权重 / 梯度 / 优化器状态 / 激活 / 框架开销。"""
    t = techs or {}
    wb = 0.5 if mode == "QLoRA" else W_BYTES[w_prec]
    w = weight_bytes(params_b, wb)
    tr = params_b * GB if mode == "全参" else lora_params(L, h, ffn, r, scope)
    items = {
        "模型权重": w,
        "梯度": gradient_bytes(tr),
        "优化器状态": optimizer_bytes(tr, opt, t.get("opt8", False), t.get("pure16", False)),
        "激活值": activation_train(s, b, h, L, t.get("ckpt", False),
                                 t.get("flash", False), t.get("fused", False),
                                 t.get("dynpad", False), unit),
        "框架开销": framework_gb * GB,
    }
    return items, sum(items.values())


def per_card(items: dict, tp=1, pp=1, gpus=1, zero=0):
    """每卡摊分（9-10）。DP = gpus / (tp·pp)；DP=1 时 ZeRO 除以 1＝等于没开。"""
    d = max(1, tp * pp)
    dp = max(1, int(gpus / d))
    z = zero if dp > 1 else 0
    out = {}
    for k, v in items.items():
        div = d
        if k == "优化器状态":
            div = d * (dp if z >= 1 else 1)
        elif k == "梯度":
            div = d * (dp if z >= 2 else 1)
        elif k == "模型权重":
            div = d * (dp if z >= 3 else 1)
        out[k] = v / div
    return out, dp


# ─────────────────────── 立场断言（gate 用） ───────────────────────

def assert_kv_monotonic() -> None:
    """① 结构单调：MHA > GQA > MQA；② 位宽单调：FP16 > INT8 > INT4。"""
    kw = dict(L=32, n_q=48, n_kv=8, h=3072, d_c=576, s=4096, b=1, C=1)
    mha = kv_bytes("MHA", **kw, kv_b=2)
    gqa = kv_bytes("GQA", **kw, kv_b=2)
    mqa = kv_bytes("MQA", **kw, kv_b=2)
    assert mha > gqa > mqa, (mha, gqa, mqa)
    mla16 = kv_bytes("MLA", **kw, kv_b=2)
    mla8 = kv_bytes("MLA", **kw, kv_b=1)
    mla4 = kv_bytes("MLA", **kw, kv_b=0.5)
    assert mla16 > mla8 > mla4


def assert_frontier_mechanism() -> None:
    """③ SWA 窗口饱和；④ DSA 存储不变（省带宽不省存储）；⑤ CSA2 = MLA/4。"""
    kw = dict(L=32, n_q=48, n_kv=8, h=3072, d_c=576, b=1, C=1, kv_b=2)
    # SWA：s 超过 W 后 KV 不再增长
    assert kv_bytes("SWA", s=8192, win=4096, **kw) == kv_bytes("SWA", s=32768, win=4096, **kw)
    # SWA 在 s 超过 W 时严格小于同参数下的 MHA
    assert kv_bytes("SWA", s=32768, win=4096, **kw) < kv_bytes("MHA", s=32768, **kw)
    # DSA 存储 == MLA 存储
    assert kv_bytes("DSA", s=4096, **kw) == kv_bytes("MLA", s=4096, **kw)
    # CSA2 = MLA / 4
    assert abs(kv_bytes("CSA2", s=4096, **kw) - kv_bytes("MLA", s=4096, **kw) / 4) < 1e-6


def assert_mha_special_case() -> None:
    """⑥ 通式在 n_kv = n_q 时退化为 MHA 式 2·L·h·s·b·C·kv_b（对账两篇参考）。"""
    L, h, n_q, s, b, C, kb = 32, 3072, 48, 4096, 1, 1, 2
    general = kv_bytes("MHA", L=L, n_q=n_q, n_kv=n_q, h=h, d_c=576, s=s, b=b, C=C, kv_b=kb)
    ref = 2 * L * h * s * b * C * kb
    assert abs(general - ref) < 1e-6, (general, ref)


def assert_mla_ratio() -> float:
    """⑦ MLA/MHA 的 KV 比值 ≈ 2h / d_c。"""
    L, h, n_q, d_c, s, kb = 32, 3072, 48, 576, 4096, 2
    mha = kv_bytes("MHA", L=L, n_q=n_q, n_kv=n_q, h=h, d_c=d_c, s=s, kv_b=kb)
    mla = kv_bytes("MLA", L=L, n_q=n_q, n_kv=n_q, h=h, d_c=d_c, s=s, kv_b=kb)
    r = mha / mla
    assert abs(r - 2 * h / d_c) < 1e-6, r
    return r


def assert_ckpt_algebra() -> None:
    """⑧ 梯度检查点：激活从 O(L) 降到 O(√L)。"""
    a0 = activation_train(4096, 1, 3072, 32, grad_ckpt=False,
                          flash=False, fused=False, dyn_pad=False)
    a1 = activation_train(4096, 1, 3072, 32, grad_ckpt=True,
                          flash=False, fused=False, dyn_pad=False)
    assert abs(a1 - a0 / (32 ** 0.5)) < 1e-6


def assert_e2e_tolerance(tol_infer=0.02, tol_train=0.05) -> dict:
    """⑨ 端到端复算：与计算器界面读数同量级（9-14）。"""
    # 推理：3B · INT8 · MLA · 4096 · b1 · C1  → 界面 5.1 GB
    items, tot = ledger_infer(3, "MLA", 32, 3072, 48, 48, 576, 4096, 1, 1,
                              "INT8", "FP16", win=4096, act_ratio=0.30,
                              framework_gb=1.01)
    d_infer = abs(tot / (5.1 * GB) - 1)
    assert d_infer < tol_infer, d_infer
    # 微调：3B · QLoRA · r16 · 4bit · 4096  → 界面 31.2 GB
    _, tot2 = ledger_train(3, "QLoRA", "AdamW", 32, 3072, 18944, 48, 48, 576,
                           4096, 1, 1, attn="MLA", r=16, scope="attn")
    d_train = abs(tot2 / (31.2 * GB) - 1)
    assert d_train < tol_train, d_train
    return {"infer_gb": tot / GB, "infer_dev": d_infer,
            "train_gb": tot2 / GB, "train_dev": d_train}


VERDICT_TIERS = (("可以", 0.50), ("充足", 0.70), ("偏高", 0.90), ("非常高", 1.01))


def verdict(usage: float) -> str:
    """判定词档表（档 4『非常高』为界面实测确认，档 1–3 标【待核实】）。"""
    for word, hi in VERDICT_TIERS:
        if usage <= hi:
            return word
    return VERDICT_TIERS[-1][0]


def assert_verdict_tiers() -> None:
    """⑩ 判定词：档位数 ≥ 3 且**单调**（用词本身不作断言，因界面未证实）。"""
    assert len(VERDICT_TIERS) >= 3
    his = [hi for _, hi in VERDICT_TIERS]
    assert his == sorted(his), his
    assert verdict(0.975) == "非常高"          # 界面实测确认的那一档


if __name__ == "__main__":
    for fn in (assert_kv_monotonic, assert_frontier_mechanism, assert_mha_special_case,
               assert_ckpt_algebra, assert_verdict_tiers):
        fn()
        print(f"OK  {fn.__name__}")
    print(f"OK  assert_mla_ratio -> {assert_mla_ratio():.2f}×")
    print(f"OK  assert_e2e_tolerance -> {assert_e2e_tolerance()}")
    print("\n全部断言通过。")
