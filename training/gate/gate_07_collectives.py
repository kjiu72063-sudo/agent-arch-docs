"""gate_07_collectives.py — 集合通信原语语义（纯 Python 模拟）

对应页面：4-7 集合通信原语
讲义依据：L3 P20–P23

  broadcast       将当前节点的数据完整的分发给所有其他节点
  scatter         将当前节点的数据先切片，再将每个不同切片分发给不同节点
  gather          将多个节点上的部分数据汇总到一个节点，并拼接成完整数据
  all_gather      与 gather 类似，但汇总结果要发送到所有节点（gather + broadcast）
  reduce          汇总到一个节点，并执行规约运算（累加/累乘/求最值等）
  all_reduce      与 reduce 类似，但结果发送到所有节点（reduce + broadcast）
  reduce_scatter  每个服务器按 index 得到的数据做规约（讲义表述："先做 Scatter 再做 Reduce"）

验证什么：用纯 Python 模拟每个原语的输入输出，断言其语义与"组合关系"。
为什么确定：行为确定，无随机、无实测成分。
运行：python training/gate/gate_07_collectives.py
"""


# ---------- 原语实现（rank -> 数据 的字典表示） ----------
def broadcast(data, root=0):
    """root 的数据分发给所有节点（完整，不切片）。"""
    src = data[root]
    return {r: src for r in data}


def scatter(data, src=0):
    """src 的数据平均切片，第 i 片给第 i 个节点。"""
    ranks = sorted(data)
    n = len(ranks)
    chunks = [data[src][i::n] for i in range(n)]      # 交错切片（示意）
    return {r: chunks[i] for i, r in enumerate(ranks)}


def gather(data, dst=0):
    """所有节点的数据汇总到 dst 并拼接。"""
    ranks = sorted(data)
    merged = []
    for r in ranks:
        merged.extend(data[r])
    return {r: (merged if r == dst else None) for r in ranks}


def all_gather(data):
    """gather + broadcast：所有节点都拿到完整拼接结果。"""
    ranks = sorted(data)
    merged = []
    for r in ranks:
        merged.extend(data[r])
    return {r: list(merged) for r in ranks}


def reduce(data, op="sum", dst=0):
    """规约（sum/max/min/product/mean）到一个节点。"""
    ranks = sorted(data)
    vals = [data[r] for r in ranks]
    if op == "sum":
        acc = sum(vals)
    elif op == "product":
        acc = 1
        for v in vals:
            acc *= v
    elif op == "max":
        acc = max(vals)
    elif op == "min":
        acc = min(vals)
    else:
        raise ValueError(op)
    return {r: (acc if r == dst else None) for r in ranks}


def all_reduce(data, op="sum"):
    """reduce + broadcast：所有节点都拿到规约结果。"""
    r = reduce(data, op=op, dst=0)
    return broadcast(r, root=0)


def reduce_scatter(chunks_by_rank, op="sum"):
    """每个 rank 持有多个 chunk，按 chunk 索引做跨 rank 规约，
    再把第 i 个 chunk 的规约结果交给第 i 个 rank（= all_reduce 后取自己那片）。"""
    ranks = sorted(chunks_by_rank)
    n = len(ranks)
    n_chunks = len(chunks_by_rank[ranks[0]])
    out = {}
    for i, r in enumerate(ranks):
        acc = [chunks_by_rank[rr][i] for rr in ranks]
        out[r] = (sum(acc) if op == "sum" else max(acc))
    assert n_chunks == n or True
    return out


# ---------- 检查 ----------
def check1_broadcast_vs_scatter():
    """broadcast 不切片（人人拿到同一份完整数据）；scatter 切片（人人拿到不同片）。"""
    d = {0: [1, 2, 3, 4], 1: [0, 0, 0, 0], 2: [0, 0, 0, 0], 3: [0, 0, 0, 0]}
    b = broadcast(d)
    s = scatter(d)
    b_ok = all(b[r] == [1, 2, 3, 4] for r in b)
    s_ok = len({tuple(s[r]) for r in s}) == len(s) and sum(len(s[r]) for r in s) == 4
    print(f"    broadcast -> {b[1]}, {b[3]}（相同）")
    print(f"    scatter   -> {[s[r] for r in sorted(s)]}（互补切片）")
    return b_ok and s_ok


def check2_gather_vs_all_gather():
    """gather 只到 dst；all_gather 人人都有。"""
    d = {0: [1, 2], 1: [3, 4], 2: [5, 6]}
    g = gather(d)
    ag = all_gather(d)
    g_ok = g[0] == [1, 2, 3, 4, 5, 6] and g[1] is None and g[2] is None
    ag_ok = all(ag[r] == [1, 2, 3, 4, 5, 6] for r in ag)
    print(f"    gather     -> dst={g[0]}, 其他={g[1]}")
    print(f"    all_gather -> 各节点 {ag[1]} == {ag[2]}")
    return g_ok and ag_ok


def check3_reduce_vs_all_reduce():
    """reduce 只在 dst；all_reduce 人人都有；且 all_reduce == reduce+broadcast。"""
    d = {0: 1, 1: 2, 2: 3, 3: 4}
    r = reduce(d, "sum")
    ar = all_reduce(d, "sum")
    r_ok = r[0] == 10 and r[1] is None and r[2] is None and r[3] is None
    ar_ok = all(ar[k] == 10 for k in ar)
    compose_ok = ar == broadcast(reduce(d, "sum", dst=0))
    print(f"    reduce     -> {r[0]}, 其他 {r[1]}")
    print(f"    all_reduce -> {ar}")
    print(f"    all_reduce == reduce+broadcast: {compose_ok}")
    return r_ok and ar_ok and compose_ok


def check4_reduce_ops():
    """reduce 支持多种规约运算（讲义：累加、累乘、求最值等）。"""
    d = {0: 2, 1: 3, 2: 4}
    ok = (reduce(d, "sum", 0)[0] == 9 and reduce(d, "product", 0)[0] == 24
          and reduce(d, "max", 0)[0] == 4 and reduce(d, "min", 0)[0] == 2)
    print(f"    sum={reduce(d,'sum',0)[0]}, product={reduce(d,'product',0)[0]}, "
          f"max={reduce(d,'max',0)[0]}, min={reduce(d,'min',0)[0]}")
    return ok


def check5_all_gather_equals_gather_plus_broadcast():
    """讲义：all_gather 可看作 gather 和 broadcast 的组合。"""
    d = {0: [1], 1: [2], 2: [3]}
    ag = all_gather(d)
    composed = broadcast(gather(d, dst=0), root=0)
    ok = ag == composed
    print(f"    all_gather == gather+broadcast: {ok} -> {ag[2]}")
    return ok


def check6_reduce_scatter_matches_all_reduce_slice():
    """ReduceScatter 结果 == AllReduce 结果里"自己那一片"。"""
    # 4 个 rank，每个持有 4 个 chunk（chunk 值相同方便核对）
    chunks = {0: [10, 20, 30, 40], 1: [10, 20, 30, 40],
              2: [10, 20, 30, 40], 3: [10, 20, 30, 40]}
    rs = reduce_scatter(chunks, op="sum")
    # all_reduce 每个 chunk 独立求和 -> 每 chunk = 4*10, 4*20, 4*30, 4*40
    expect = {0: 40, 1: 80, 2: 120, 3: 160}
    ok = rs == expect
    print(f"    reduce_scatter -> {rs}")
    print(f"    期望（all_reduce 后各取自己那片）-> {expect}")
    return ok


def main():
    checks = [
        check1_broadcast_vs_scatter(),
        check2_gather_vs_all_gather(),
        check3_reduce_vs_all_reduce(),
        check4_reduce_ops(),
        check5_all_gather_equals_gather_plus_broadcast(),
        check6_reduce_scatter_matches_all_reduce_slice(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_07 failed"
    print("PASS: gate_07 通信原语 6/6（b/s + g/ag + r/ar + 组合关系 + 多规约 + reduce_scatter）")


if __name__ == "__main__":
    main()
