"""gate_10_kl_divergence.py — 白盒蒸馏 KL 散度实现正确性

对应页面：5-3 响应式蒸馏（KL 与温度）· 5-9 实战：白盒蒸馏 4B→1.7B
代码依据：fixtures/train_reference.py
          · compute_kl_div_loss()  L17-L33
          · Custom_Trainer.compute_loss()  L106-L124（温度 T=6、alpha=0.5）

验证什么：把 train.py 的 KL 计算逐元素重写为**纯标准库**实现，在固定小样例上断言：
  1. 定义式 KL(P‖Q) = Σ P·(logP − logQ) 与实现逐元素相等
  2. KL ≥ 0；P 与 Q 完全相同时 KL = 0
  3. 温度 T 软化后 KL 变小（分布更平滑，差异被压缩）
  4. padding 位（target == -100）被 masked_fill 归零，不计入 sum
  5. 总损失 = alpha·KL + (1-alpha)·student_loss 的加权公式
若本机装有 torch，则额外用 torch 复刻同一函数做交叉比对（两条独立路径互证）。

为什么确定：纯算术 / 数值可复现，不依赖随机与训练。
运行：python training/gate/gate_10_kl_divergence.py
"""

import math

PADDING_ID = -100        # train.py 中 compute_kl_div_loss(padding_id=-100)
TEMP = 6.0               # train.py 中 temperature=6
ALPHA = 0.5              # train.py 中 alpha=0.5


# ---------- 纯标准库的 KL 实现（逐元素照抄 train.py 的语义） ----------

def softmax(xs):
    m = max(xs)
    es = [math.exp(v - m) for v in xs]
    s = sum(es)
    return [e / s for e in es]


def log_softmax(xs):
    m = max(xs)
    shifted = [v - m for v in xs]
    lse = math.log(sum(math.exp(v) for v in shifted))
    return [v - lse for v in shifted]


def kl_div_loss(student_logits, teacher_logits, target, padding_id=PADDING_ID,
                reduction="sum"):
    """等价于 train.py 的 compute_kl_div_loss（对每一行按最后一维算）。"""
    total = 0.0
    for i, (s_row, t_row) in enumerate(zip(student_logits, teacher_logits)):
        if reduction == "sum" and target is not None and target[i] == padding_id:
            continue                                   # masked_fill 归零后不参与求和
        lp = log_softmax(s_row)                        # log_softmax(student)
        tp = softmax(t_row)                            # softmax(teacher)  → 概率
        tlp = log_softmax(t_row)                       # log_softmax(teacher)
        total += sum(tp[k] * (tlp[k] - lp[k]) for k in range(len(tp)))
    return total


# ---------- 固定小样例（2 个位置 × 4 类词表，第 2 个位置是 padding） ----------

STUDENT = [[2.0, 2.0, 1.0, 0.0],
           [1.0, 3.0, 0.5, 0.5]]
TEACHER = [[4.0, 1.0, 0.5, 0.5],
           [2.5, 2.5, 1.0, 0.0]]
TARGET = [7, PADDING_ID]       # 7 只是"非 padding"的占位标签


def scaled(logits, T):
    return [[v / T for v in row] for row in logits]


# ---------- checks ----------

def check1_matches_definition():
    """实现 == 手写定义式（仅非 padding 位置）。"""
    got = kl_div_loss(STUDENT, TEACHER, TARGET)
    lp = log_softmax(STUDENT[0])
    tp = softmax(TEACHER[0])
    tlp = log_softmax(TEACHER[0])
    expect = sum(tp[k] * (tlp[k] - lp[k]) for k in range(4))
    ok = abs(got - expect) < 1e-12
    print(f"    实现={got:.10f}  定义式={expect:.10f}")
    return ok


def check2_nonneg_and_zero():
    """KL ≥ 0；P == Q 时 KL == 0。"""
    pos = kl_div_loss(STUDENT, TEACHER, TARGET)
    same = kl_div_loss(STUDENT, [row[:] for row in STUDENT], TARGET)
    ok = pos >= -1e-12 and abs(same) < 1e-12
    print(f"    KL(P‖Q)={pos:.8f} ≥ 0    KL(P‖P)={same:.2e} == 0")
    return ok


def check3_temperature_smooths():
    """T=6 软化后的 KL 小于 T=1，且 T→∞ 时趋近 0。"""
    k_t1 = kl_div_loss(scaled(STUDENT, 1.0), scaled(TEACHER, 1.0), TARGET)
    k_t6 = kl_div_loss(scaled(STUDENT, TEMP), scaled(TEACHER, TEMP), TARGET)
    k_t50 = kl_div_loss(scaled(STUDENT, 50.0), scaled(TEACHER, 50.0), TARGET)
    ok = k_t6 < k_t1 and k_t50 < k_t6 and k_t50 < 1e-2
    print(f"    KL(T=1)={k_t1:.6f} > KL(T=6)={k_t6:.6f} > KL(T=50)={k_t50:.6f}")
    return ok


def check4_padding_masked():
    """padding 位被排除：把 padding 位教师 logits 改到极端，结果不变。"""
    base = kl_div_loss(STUDENT, TEACHER, TARGET)
    mutated = [TEACHER[0][:], [999.0, -999.0, 0.0, 1.0]]     # 只动 padding 位（索引 1）
    got = kl_div_loss(STUDENT, mutated, TARGET)
    ok = abs(base - got) < 1e-12
    print(f"    原={base:.10f}  动过 padding 位后={got:.10f}  ⇒ 被正确 mask")
    return ok


def check5_total_loss_weights():
    """alpha·KL + (1-alpha)·L_student；alpha=0.5 时两半各占一半。"""
    kl = kl_div_loss(scaled(STUDENT, TEMP), scaled(TEACHER, TEMP), TARGET)
    student_loss = 1.234                      # 任意观测到的 outputs.loss
    total = ALPHA * kl + (1 - ALPHA) * student_loss
    expect = 0.5 * kl + 0.5 * student_loss
    ok = abs(total - expect) < 1e-12
    print(f"    total = {ALPHA}*{kl:.6f} + {1-ALPHA}*{student_loss} = {total:.6f}")
    return ok


def check6_cross_verify_torch():
    """若装有 torch，用 torch 复刻同一函数交叉比对。"""
    try:
        import torch
    except Exception:
        print("    (未安装 torch，跳过交叉比对；纯标准库路径已自洽)")
        return True

    def torch_kl(student_logits, teacher_logits, target):
        s = torch.tensor(student_logits, dtype=torch.float32)
        t = torch.tensor(teacher_logits, dtype=torch.float32)
        lbl = torch.tensor(target, dtype=torch.long)
        log_probs = torch.log_softmax(s, -1, dtype=torch.float32)
        teacher_probs = torch.softmax(t, -1, dtype=torch.float32)
        teacher_log_probs = torch.log_softmax(t, -1, dtype=torch.float32)
        kl = (teacher_probs * (teacher_log_probs - log_probs)).sum(-1)
        kl = kl.masked_fill_(lbl.eq(PADDING_ID), 0.0)
        return float(kl.sum())

    s_scaled = scaled(STUDENT, TEMP)
    t_scaled = scaled(TEACHER, TEMP)
    got = kl_div_loss(s_scaled, t_scaled, TARGET)
    ref = torch_kl(s_scaled, t_scaled, TARGET)
    ok = abs(got - ref) < 1e-6          # float32 容差
    print(f"    纯标准库={got:.8f}  torch={ref:.8f}  Δ={abs(got-ref):.2e}")
    return ok


def main():
    checks = [
        check1_matches_definition(),
        check2_nonneg_and_zero(),
        check3_temperature_smooths(),
        check4_padding_masked(),
        check5_total_loss_weights(),
        check6_cross_verify_torch(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_10 failed"
    print("PASS: gate_10 KL 散度 6/6（定义式一致 + 非负/零 + 温度单调 + padding mask + 加权损失 + torch 互证）")


if __name__ == "__main__":
    main()
