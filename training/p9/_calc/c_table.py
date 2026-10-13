# -*- coding: utf-8 -*-
"""9-C 主流模型配置对照表 · 数据生成"""
import sys, io
sys.path.insert(0, ".")
import calc as K

GB = 1e9
MODELS = [
    # name, params_B, attn, L, h, nq, nkv, ffn, vocab, dc, win
    ("Custom 3B · MoE · MLA（计算器默认）", 3.0,   "MLA", 32, 3072, 48,  48, 18944, 152064, 576, 4096),
    ("Qwen2.5-3B",                        3.09,  "GQA", 36, 2048, 16,  2,  11008, 151936, 0,   32768),
    ("Qwen2.5-7B",                        7.62,  "GQA", 28, 3584, 28,  4,  18944, 152064, 0,   32768),
    ("Llama-3.1-8B",                      8.03,  "GQA", 32, 4096, 32,  8,  14336, 128256, 0,   131072),
    ("Mistral-7B-v0.1",                   7.24,  "SWA", 32, 4096, 32,  8,  14336, 32000,  0,   4096),
    ("DeepSeek-V3（总/激活 671B/37B）",    671.0, "MLA", 61, 7168, 128, 128, 18432, 129280, 576, 131072),
]

S_BASE = 4096
print(f"KV Cache @ s={S_BASE}, b=1, C=1, FP16  —— 单位 GB / GiB")
print("-" * 118)
print(f"{'模型':38} {'L':>3} {'h':>5} {'nq':>4} {'nkv':>4} {'d_head':>6} {'结构':>5} "
      f"{'KV(本模型)':>11} {'KV(若全MHA)':>12} {'倍数':>6}")
print("-" * 118)
rows = []
for name, p, attn, L, h, nq, nkv, ffn, vocab, dc, win in MODELS:
    kw = dict(L=L, n_q=nq, n_kv=nkv, h=h, d_c=dc, s=S_BASE, b=1, C=1, kv_b=2, win=win)
    kv = K.kv_bytes(attn, **kw)
    mha = K.kv_bytes("MHA", L=L, n_q=nq, n_kv=nq, h=h, d_c=dc, s=S_BASE, b=1, C=1, kv_b=2)
    ratio = mha / kv
    dh = int(h // nq)
    rows.append((name, L, h, nq, nkv, dh, attn, kv, mha, ratio))
    print(f"{name:38} {L:>3} {h:>5} {nq:>4} {nkv:>4} {dh:>6} {attn:>5} "
          f"{kv/GB:>8.3f}GB {mha/GB:>9.3f}GB {ratio:>5.2f}x")

print()
print("=" * 118)
print("SWA 的窗口饱和：Mistral-7B 在长上下文下 KV 不再增长")
print("-" * 118)
L, h, nq, nkv, win = 32, 4096, 32, 8, 4096
for s in (4096, 8192, 32768, 131072):
    swa = K.kv_bytes("SWA", L=L, n_q=nq, n_kv=nkv, h=h, d_c=0, s=s, kv_b=2, win=win)
    mha = K.kv_bytes("MHA", L=L, n_q=nq, n_kv=nq, h=h, d_c=0, s=s, kv_b=2)
    print(f"  s={s:>7}: SWA {swa/GB:>7.3f} GB   MHA {mha/GB:>8.3f} GB   节省 {mha/swa:>5.1f}x")

print()
print("=" * 118)
print("MLA 内部结构（DeepSeek-V3）：d_c = 512 + 64 = 576")
print("-" * 118)
L, dc, s = 61, 576, 4096
mla = K.kv_bytes("MLA", L=L, n_q=128, n_kv=128, h=7168, d_c=dc, s=s, kv_b=2)
mha = K.kv_bytes("MHA", L=L, n_q=128, n_kv=128, h=7168, d_c=dc, s=s, kv_b=2)
print(f"  MLA KV @4K  = {mla/GB:.4f} GB   MHA KV @4K = {mha/GB:.4f} GB   比值 {mha/mla:.2f}x")
print(f"  理论比值 2h/d_c = {2*7168/dc:.2f}x   <- 完全吻合")

print()
print("=" * 118)
print("KV 随序列长度的线性（以 Llama-3.1-8B 的 GQA 为例，b=1, C=1, FP16）")
print("-" * 118)
L, h, nq, nkv = 32, 4096, 32, 8
for s in (2048, 4096, 8192, 16384, 32768):
    kv = K.kv_bytes("GQA", L=L, n_q=nq, n_kv=nkv, h=h, d_c=0, s=s, kv_b=2)
    print(f"  s={s:>6}: {kv/GB:.3f} GB  ({kv/GB/1024*1000:.2f} 相对 1K token 的千分比)")

print()
print("=" * 118)
print("阿里云 7B 账本 vs 计算器/本模块口径 对照（推导 9-C 附录表）")
print("-" * 118)
ali = {
    "全参数微调": dict(w=14, g=14, o=56, a=1.4, m=2, total=87.4),
    "LoRA":       dict(w=14, g=0.14, o=0.56, a=1.4, m=2, total=18.1),
    "QLoRA-8bit": dict(w=7,  g=0.14, o=0.56, a=1.4, m=2, total=11.1),
    "QLoRA-4bit": dict(w=3.5, g=0.14, o=0.56, a=1.4, m=2, total=7.6),
}
for k, v in ali.items():
    s = v["w"] + v["g"] + v["o"] + v["a"] + v["m"]
    print(f"  {k:12} {v['w']:>5} + {v['g']:>5} + {v['o']:>5} + {v['a']:>4} + {v['m']:>3} = {s:>6.2f}"
          f"   标注 {v['total']:>6.1f}   {'OK' if abs(s-v['total'])<0.6 else 'DIFF'}")

print()
print("=" * 118)
print("计算器 104 备选配置摘选（按 $/百万 token 排序，租金/吞吐为界面读数）")
print("-" * 118)
cfgs = [("1x T4 (16GB)", 0.12, 425), ("1x RTX 3060 Ti (8GB)", 0.15, 297),
        ("1x RTX 3070 (8GB)", 0.17, 328), ("（$0.20/hr 档）", 0.20, 345),
        ("RTX 5090 (32GB)", 1.10, 349)]
for name, rent, tps in cfgs:
    cpm = rent / (tps * 3600) * 1e6
    print(f"  {name:24} ${rent:.2f}/hr  {tps:>4} t/s  ->  ${cpm:.4f}/百万token")
