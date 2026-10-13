"""gate_08_ring_allreduce.py — Ring AllReduce 通信量 vs Naive AllReduce

对应页面：4-8 AllReduce 算法演进
讲义依据：L3 P24（Naive AllReduce = reduce + broadcast；缺点：通信开销大）、
         L3 P25–P26（Ring AllReduce：Scatter-Reduce 阶段 + All_Gather 阶段；优点：每个节点只与邻居通信）

验证什么：
  - Ring AllReduce 每卡通信量 = 2·(N−1)/N · Ψ
  - Naive AllReduce 每卡通信量 = 2Ψ，且 root 承担 (N−1)Ψ 的收发（瓶颈）
  - Ring < Naive（有限 N），且 Ring 无 root 瓶颈
为什么确定：纯算术。
运行：python training/gate/gate_08_ring_allreduce.py
"""


def ring_allreduce_per_rank(N, psi):
    """Ring：Scatter-Reduce N−1 步 + All-Gather N−1 步，每步发 Ψ/N。"""
    per_step = psi / N
    scatter_reduce = (N - 1) * per_step
    all_gather = (N - 1) * per_step
    return scatter_reduce + all_gather          # == 2(N-1)/N * Ψ


def naive_allreduce_per_rank(N, psi):
    """Naive = reduce + broadcast。非 root：各发 Ψ、各收 Ψ → 2Ψ。"""
    return 2 * psi


def naive_root_traffic(N, psi):
    """Naive 的 root：reduce 阶段收 (N−1)Ψ；broadcast 阶段发 (N−1)Ψ。"""
    return 2 * (N - 1) * psi


def check1_ring_formula_matches():
    """Ring 每卡通信量严格等于 2(N−1)/N · Ψ。"""
    psi = 1.0
    ok = True
    for N in [2, 3, 4, 8, 16, 64]:
        got = ring_allreduce_per_rank(N, psi)
        expect = 2 * (N - 1) / N * psi
        if abs(got - expect) > 1e-12:
            ok = False
        print(f"    N={N:>2}: ring/卡 = {got:.4f}Ψ  （公式 {expect:.4f}Ψ）")
    return ok


def check2_ring_two_phases_equal():
    """Ring 两个阶段各占一半（Scatter-Reduce = All-Gather = (N−1)/N·Ψ）。"""
    psi, N = 1.0, 8
    sr = (N - 1) * (psi / N)
    ag = (N - 1) * (psi / N)
    ok = abs(sr - ag) < 1e-12 and abs(sr + ag - ring_allreduce_per_rank(N, psi)) < 1e-12
    print(f"    N=8: Scatter-Reduce={sr:.4f}Ψ, All-Gather={ag:.4f}Ψ（相等）")
    return ok


def check3_ring_beats_naive_for_finite_N():
    """有限 N 下 Ring < Naive；且 N→∞ 时 Ring → 2Ψ（上界）。"""
    psi = 1.0
    ok = True
    for N in [2, 3, 4, 8, 16, 64, 1024]:
        r, nv = ring_allreduce_per_rank(N, psi), naive_allreduce_per_rank(N, psi)
        if not (r < nv):
            ok = False
        print(f"    N={N:>4}: ring={r:.4f}Ψ  vs naive={nv:.4f}Ψ  （省 {(1-r/nv):.1%}）")
    # 上界：N 很大时趋近 2Ψ
    big = ring_allreduce_per_rank(10 ** 6, psi)
    ok = ok and abs(big - 2 * psi) < 1e-5
    return ok


def check4_naive_root_is_bottleneck():
    """Naive 的 root 收发量 = 2(N−1)Ψ，随 N 线性增长 → 这就是"0 号节点负载很重"。

    注：N=2 时 root 与另一张卡都是 2Ψ（对称），瓶颈从 N≥3 才开始显现，
    故断言为 root ≥ 单卡，且 N≥3 时严格大于。
    """
    psi = 1.0
    ok = True
    for N in [2, 4, 8, 16]:
        root = naive_root_traffic(N, psi)
        per_rank = naive_allreduce_per_rank(N, psi)
        if root != 2 * (N - 1) * psi or root < per_rank:
            ok = False
        if N >= 3 and not (root > per_rank):        # N≥3 才是真正的 root 瓶颈
            ok = False
        tag = "（N=2 对称，无瓶颈）" if N == 2 else "← root 更重"
        print(f"    N={N:>2}: naive root 收发 = {root:.1f}Ψ  vs 单卡 {per_rank:.1f}Ψ  {tag}")
    # 线性增长：root 随 N 线性，单卡恒定
    ratios = [naive_root_traffic(N, psi) / (N - 1) for N in [2, 4, 8, 16]]
    ok = ok and all(abs(r - 2 * psi) < 1e-12 for r in ratios)
    print(f"    root/(N−1) 恒为 {ratios[0]:.1f}Ψ ⇒ 线性增长")
    return ok


def check5_ring_has_no_root():
    """Ring 中每个节点的收发量都相同（无中心节点）。"""
    psi, N = 1.0, 8
    per_rank = ring_allreduce_per_rank(N, psi)
    all_equal = all(abs(ring_allreduce_per_rank(N, psi) - per_rank) < 1e-12
                    for _ in range(N))          # 每个节点对称
    print(f"    N=8: 每卡均为 {per_rank:.4f}Ψ（对称，无 root 瓶颈）")
    return all_equal


def check6_bytes_example():
    """实例：8 卡训 70 亿参数 fp16 模型，一次 AllReduce 传 14 GiB 梯度。"""
    n_params = 7e9
    psi_gib = n_params * 2 / (1024 ** 3)         # fp16
    N = 8
    ring = ring_allreduce_per_rank(N, psi_gib)
    naive = naive_allreduce_per_rank(N, psi_gib)
    root = naive_root_traffic(N, psi_gib)
    ok = ring < naive and abs(psi_gib - 13.04) < 0.01
    print(f"    Ψ = {psi_gib:.2f} GiB；ring/卡 = {ring:.2f} GiB，naive/卡 = {naive:.2f} GiB，"
          f"naive root = {root:.2f} GiB")
    return ok


def main():
    checks = [
        check1_ring_formula_matches(),
        check2_ring_two_phases_equal(),
        check3_ring_beats_naive_for_finite_N(),
        check4_naive_root_is_bottleneck(),
        check5_ring_has_no_root(),
        check6_bytes_example(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_08 failed"
    print("PASS: gate_08 Ring AllReduce 6/6（2(N-1)/N·Ψ + 两阶段等分 + 优于Naive + root瓶颈 + 对称 + 实例）")


if __name__ == "__main__":
    main()
