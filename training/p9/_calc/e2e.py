# -*- coding: utf-8 -*-
# 9-14 端到端复算：推理预设 vs QLoRA 预设
B = 1e9
GiB = 1024**3

# ---- 共用架构（计算器默认态）----
L      = 32        # Transformer 层数
h      = 3072      # 隐藏层维度
n_q    = 48        # Query 头数
n_kv   = 48        # KV 头数（MHA：= n_q）
ffn    = 18944
vocab  = 152064
s      = 4096      # 序列长度
b      = 1         # 批量
C      = 1         # 并发用户数
d_c    = 512 + 64  # MLA 潜变量维度

print("=== 0. 架构自洽检查 ===")
d_head = h // n_q
print(f"head_dim = h / n_q = {d_head}")
print(f"MLA 潜变量 d_c = 512 + 64 = {d_c}   (计算器第15项默认 576 -> 吻合)")

# ---- A. 推理预设：INT8 + MLA + 4K ----
print("\n=== A. 推理预设（INT8 + MLA + s=4096 + b=1 + C=1）===")
A_w = 3 * B * 1                                   # 标签值 3B x INT8
A_kv_mha = 2 * L * n_q * d_head * s * b * C * 2   # MHA 展开 = 2*L*h*s*b*C*2
A_kv_mla = L * d_c * s * b * C * 2                # MLA 潜变量式
A_frame = 1.01 * B
A_total_ui = 5.1 * B

print(f"① 权重   3B x 1B(INT8)                 = {A_w/B:.3f} GB")
print(f"② KV-MHA 2*L*n_q*d_head*s*b*C*2       = {A_kv_mha/B:.4f} GB")
print(f"② KV-MLA L*d_c*s*b*C*2                = {A_kv_mla/B:.4f} GB = {A_kv_mla/GiB:.4f} GiB")
print(f"   模型规格卡显示 注意力结构: MLA  ->  取 MLA 式")
resid = A_total_ui - A_w - A_kv_mla - A_frame
print(f"④ 残差(激活+预分配) = 5.1 - 3.0 - {A_kv_mla/B:.4f} - 1.01 = {resid/B:.4f} GB")
print(f"   占权重比例 = {resid/A_w*100:.1f}%    (对照 阿里云10% / CSDN20~30% 双档)")
t30 = A_w + A_kv_mla + 0.30*A_w + A_frame
print(f"   若激活取 30% 档: 合计 = {t30/B:.4f} GB  vs 界面 5.1 GB  差 {abs(t30-A_total_ui)/A_total_ui*100:.2f}%")
t10 = A_w + A_kv_mla + 0.10*A_w + A_frame
print(f"   若激活取 10% 档: 合计 = {t10/B:.4f} GB  vs 界面 5.1 GB  差 {abs(t10-A_total_ui)/A_total_ui*100:.2f}%")
# 若权重用架构反推的 7.26B
A_w2 = 7.26 * B * 1
print(f"   若权重改用架构反推 7.26B x INT8 = {A_w2/B:.2f} GB -> 合计 {(A_w2+A_kv_mla+0.3*A_w2+A_frame)/B:.3f} GB  (超出界面 71%)")

# ---- B. QLoRA 预设 ----
print("\n=== B. QLoRA 预设（rank16 + 4bit 基座 + ZeRO3 + s=4096）===")
r = 16
B_w = 3 * B * 0.5
lo = {
    "仅注意力 q/k/v/o": L * 4 * 2 * h * r,
    "全线性层 (q/k/v/o + gate/up/down)": L * (4 * 2 * h * r + 2 * (h * r + r * ffn) + (ffn * r + r * h)),
}
for k, v in lo.items():
    print(f"  LoRA 参数量 · {k} = {v/1e6:.2f} M")
print(f"① 权重   3B x 0.5B(4bit)               = {B_w/B:.3f} GB")
act34 = 34 * s * b * h * 2 * L
for k, v in lo.items():
    g, o = v * 2, v * 8
    print(f"   [{k}] ②梯度 {g/B:.4f} GB + ③优化器 {o/B:.4f} GB + ④激活 {act34/B:.4f} GB + ⑤框架 1.010 GB = {(B_w+g+o+act34+1.01*B)/B:.3f} GB")
print(f"④ 激活(Megatron 口径 34 单位/层) = 34 * s*b*h * 2B * L = {act34/B:.4f} GB = {act34/GiB:.4f} GiB")
B_total_ui = 31.2 * B
resB = B_total_ui - B_w - 1.01 * B
print(f"   残差(激活+梯度+优化器) = 31.2 - 1.5 - 1.01 = {resB/B:.4f} GB")
print(f"   34 口径激活 / 残差 = {act34/resB*100:.1f}%   -> 吻合")
print("   系数扫描（求使总量逼近界面 31.2 GB 的系数 k）:")
for k in (24, 28, 30, 32, 34, 36, 40):
    a = k * s * b * h * 2 * L
    t2 = B_w + 0.0464 * B * 0.002 + 0.0464 * B * 8 / 1000 + a + 1.01 * B
    print(f"     k={k}: 激活 {a/B:.3f} GB -> 合计 {t2/B:.3f} GB  (差 {abs(t2-31.2*B)/(31.2*B)*100:.1f}%)")

# ---- C. 可行化路径 ----
print("\n=== C. QLoRA 的可行化路径（目标：落进 32GB 卡）===")
for ss in (4096, 2048, 1024):
    a = 34 * ss * b * h * 2 * L
    print(f"  s={ss:<5}: 激活 {a/B:7.3f} GB -> 已知项合计 {(B_w+a+1.01*B)/B:6.3f} GB  = {((B_w+a+1.01*B)/(31.2*B)*100):5.1f}% of 31.2")
ck = act34 / (L ** 0.5)
print(f"  s=4096 + 梯度检查点(理论上界 1/sqrt({L}) = 1/{L**0.5:.2f}): 激活 {ck/B:.3f} GB -> 合计 {(B_w+ck+1.01*B)/B:.3f} GB")
print(f"  两者同开(s=2048+检查点): 激活 {34*2048*b*h*2*L/(L**0.5)/B:.3f} GB -> 合计 {(B_w+34*2048*b*h*2*L/(L**0.5)+1.01*B)/B:.3f} GB")
