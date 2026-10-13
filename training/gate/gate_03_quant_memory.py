"""gate_03_quant_memory.py — 量化内存换算

对应页面：1-9 调参难点（量化与阶段）/ 3-6 量化技术专题 / 6-2 KV Cache
讲义依据：L5 P4（精度字节表）、L5 P11（压缩缓存"内存能少 75%（比如 FP16 转 INT8）"）

验证什么：量化内存换算的算术一致性；并**检出原文数值矛盾**。
为什么确定：纯算术。
运行：python training/gate/gate_03_quant_memory.py
"""

BYTES = {"FP32": 4.0, "FP16": 2.0, "INT8": 1.0, "INT4": 0.5}


def saving_ratio(src, dst):
    """从 src 精度换到 dst 精度，内存节省比例。"""
    return 1.0 - BYTES[dst] / BYTES[src]


def check1_fp16_to_int8_halves():
    """FP16 -> INT8：2B -> 1B，省 50%。"""
    r = saving_ratio("FP16", "INT8")
    ok = abs(r - 0.5) < 1e-12
    print(f"    FP16(2B) -> INT8(1B): 省 {r:.0%}")
    return ok


def check2_fp16_to_int4_quarters():
    """FP16 -> INT4：2B -> 0.5B，省 75%。"""
    r = saving_ratio("FP16", "INT4")
    ok = abs(r - 0.75) < 1e-12
    print(f"    FP16(2B) -> INT4(0.5B): 省 {r:.0%}")
    return ok


def check3_detect_lecture_inconsistency():
    """L5 P11 原文说"内存能少 75%（比如 FP16 转 INT8）"——两者不能同时成立。

    本项**断言原文存在矛盾**：FP16->INT8 是 50%，只有 FP16->INT4 才是 75%。
    """
    int8 = saving_ratio("FP16", "INT8")
    int4 = saving_ratio("FP16", "INT4")
    inconsistent = (abs(int8 - 0.75) > 1e-12) and (abs(int4 - 0.75) < 1e-12)
    print(f"    原文「75%（FP16 转 INT8）」→ 实际 INT8={int8:.0%}, INT4={int4:.0%}  ⇒ 原文笔误")
    return inconsistent


def kv_cache_bytes(n_layers, n_kv_heads, head_dim, seq_len, batch, dtype_bytes):
    """KV Cache 字节量：2(K,V) × 层数 × batch × 序列长 × kv头数 × 头维 × 每元素字节。"""
    return 2 * n_layers * batch * seq_len * n_kv_heads * head_dim * dtype_bytes


def check4_kv_cache_int8_vs_int4():
    """KV Cache 压缩：同一配置下 INT8 与 INT4 的实际字节比 = 1:0.5。"""
    cfg = dict(n_layers=28, n_kv_heads=4, head_dim=128, seq_len=8192, batch=16)
    b8 = kv_cache_bytes(**cfg, dtype_bytes=BYTES["INT8"])
    b4 = kv_cache_bytes(**cfg, dtype_bytes=BYTES["INT4"])
    ratio = b4 / b8
    ok = abs(ratio - 0.5) < 1e-12
    print(f"    KV Cache: INT8={b8/1024**3:.2f} GiB, INT4={b4/1024**3:.2f} GiB, 比={ratio:.2f}")
    return ok


def main():
    checks = [
        check1_fp16_to_int8_halves(),
        check2_fp16_to_int4_quarters(),
        check3_detect_lecture_inconsistency(),
        check4_kv_cache_int8_vs_int4(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_03 failed"
    print("PASS: gate_03 量化内存 4/4（INT8减半 + INT4减75% + 检出原文矛盾 + KV压缩比）")


if __name__ == "__main__":
    main()
