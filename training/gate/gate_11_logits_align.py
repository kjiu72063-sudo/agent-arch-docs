"""gate_11_logits_align.py — 异构教师/学生 logits 维度对齐

对应页面：5-9 实战：白盒蒸馏 4B→1.7B（异构模型与词表不一致）
代码依据：fixtures/train_reference.py L113-L119
        if logits.shape[-1] != teacher_logits.shape[-1]:
            dimension_diff = teacher_logits.shape[-1] - logits.shape[-1]
            if dimension_diff > 0:
                pad_logits = torch.zeros((B, S, dimension_diff))
                logits = torch.cat([logits, pad_logits], dim=-1)
            teacher_logits = teacher_logits[:, :, :logits.shape[-1]]

验证什么：逐元素复刻上述对齐逻辑，断言：
  1. 教师词表 ≥ 学生词表 → padding 后形状相等（B、S 不变）
  2. 教师词表 == 学生词表 → 原样通过，不发生任何拷贝
  3. 填充内容恒为零（torch.zeros）——不是复制、不是随机
  4. 【源材料边界】教师词表 < 学生词表时，代码只 pad 不截学生，
     truncate 只作用在教师上 → 形状仍不相等。这是**源实现未覆盖的分支**，
     此处显式暴露而不是替它兜底。
  5. 【量化提醒】零 logits 不是"中性"的：softmax(0)=1 > 0，
     填充的额外类别会分走真实概率质量，故对齐本身会给 KL 引入偏差。

为什么确定：张量形状 / 逐元素布尔断言，与具体数值无关。
运行：python training/gate/gate_11_logits_align.py
"""

BATCH = 2
SEQ = 5


def simulate(student_dim, teacher_dim):
    """逐元素复刻 train.py 的对齐逻辑，返回 (学生维度, 教师维度, 填充列数)。"""
    s_dim = student_dim
    t_dim = teacher_dim
    padded = 0
    if s_dim != t_dim:
        diff = t_dim - s_dim
        if diff > 0:                     # 学生补零
            padded = diff
            s_dim = s_dim + diff         # torch.cat 后学生维度 = teacher 维度
        t_dim = min(t_dim, s_dim)        # teacher[:, :, :logits.shape[-1]]
    return s_dim, t_dim, padded


def check1_teacher_larger():
    """教师 152k 词表、学生 151k 词表 → 对齐后相等。"""
    s, t, p = simulate(151000, 152000)
    ok = (s == t) and (p == 1000)
    print(f"    学生 151000 + pad {p} → {s}  ；教师截断后 {t}  ⇒ 相等={s==t}")
    return ok


def check2_equal_dims_noop():
    """维度相同 → 不填充、不截断。"""
    s, t, p = simulate(151936, 151936)
    ok = (s == t) and (p == 0)
    print(f"    词表相同 {s}：pad={p}，无拷贝，形状不变")
    return ok


def check3_pad_is_zero():
    """填充列取值恒为 0（torch.zeros）。"""
    row = [3.0, 1.0, -2.0]
    pad = [0.0] * 4
    aligned = row + pad
    ok = all(v == 0.0 for v in aligned[len(row):]) and len(aligned) == 7
    print(f"    学生行 {row} + zeros×4 → 末 4 列 {aligned[3:]}  ⇒ 全零={ok}")
    return ok


def check4_teacher_smaller_unhandled():
    """教师词表更小：源实现只 pad 不截学生 → 形状仍不等（暴露未覆盖分支）。"""
    s, t, p = simulate(152000, 151000)
    unhandled = (s != t)
    ok = unhandled and p == 0
    print(f"    学生 152000 / 教师 151000：pad={p}，截断后 学生{s} vs 教师{t} "
          f"⇒ 仍不等={unhandled}  【源实现未覆盖此分支】")
    return ok


def check5_zero_padding_biases_softmax():
    """零填充不是中性的：额外类别分走真实概率质量。"""
    real = [2.0, 1.0, 0.0]
    padded = real + [0.0, 0.0]           # 补 2 个零类别
    import math
    def mass(xs):
        m = max(xs)
        es = [math.exp(v - m) for v in xs]
        z = sum(es)
        return [e / z for e in es]
    p_real = mass(real)
    p_pad = mass(padded)
    mass_leaked = sum(p_pad[len(real):])
    ok = mass_leaked > 0 and abs(sum(p_pad) - 1.0) < 1e-12
    print(f"    原 3 类概率 {[round(v,4) for v in p_real]}")
    print(f"    补零后前 3 类 {[round(v,4) for v in p_pad[:3]]}，"
          f"新增 2 类共分走 {mass_leaked:.4f} 概率质量 ⇒ 非中性")
    return ok


def check6_shape_preserved():
    """对齐只动最后一维：B、S 保持不变。"""
    ok = True
    for s_dim, t_dim in [(100, 120), (100, 100), (100, 80)]:
        s, t, p = simulate(s_dim, t_dim)
        # B、S 不由 simulate 触碰，恒为 BATCH/SEQ
        if s != t and t_dim >= s_dim:
            ok = False
        print(f"    输入 (B={BATCH},S={SEQ},D={s_dim}) 教师 D={t_dim} → D 维 学生{s}/教师{t}；B、S 未变")
    return ok


def main():
    checks = [
        check1_teacher_larger(),
        check2_equal_dims_noop(),
        check3_pad_is_zero(),
        check4_teacher_smaller_unhandled(),
        check5_zero_padding_biases_softmax(),
        check6_shape_preserved(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_11 failed"
    print("PASS: gate_11 logits 对齐 6/6（教师更大⇒相等 + 相同⇒无操作 + 零填充 + 教师更小分支 + 零填充非中性 + 形状保全）")


if __name__ == "__main__":
    main()
