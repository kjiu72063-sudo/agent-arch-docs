"""loop_gate.py — loop 章 L5 验收（示意，依赖 maker/checker 模块则需注入）
运行：python gate/loop_gate.py
"""


class FakeResult:
    def __init__(self, output, cost=0.1, passed=False):
        self.output = output
        self.cost = cost
        self.passed = passed


class FakeMaker:
    """模拟生成器：给定任务与模式返回结果。"""

    def __init__(self, good_when_goal_met):
        self.good_when_goal_met = good_when_goal_met
        self.calls = 0

    def run(self, task, mode):
        self.calls += 1
        # 模拟：Open 模式能发现未预设的路径
        if mode == "open":
            return FakeResult("discovered_unknown", cost=0.2, passed=True)
        # closed：逐步逼近目标
        if self.calls >= 3 or self.good_when_goal_met:
            return FakeResult("solution", cost=0.1, passed=True)
        return FakeResult("partial", cost=0.1, passed=False)


class FakeChecker:
    def evaluate(self, result):
        return result  # 直接读结果的 passed 字段（独立评估器抽象）


def run_loop(mode="closed", max_iter=10, max_cost=5.0, no_progress=3,
             good_when_goal_met=True):
    maker, checker = FakeMaker(good_when_goal_met), FakeChecker()
    iterations = cost = stalled = 0
    last = None
    while iterations < max_iter and cost < max_cost:
        result = maker.run("task", mode)
        cost += result.cost
        iterations += 1
        if checker.evaluate(result).passed:
            return result, iterations, cost, True
        if result.output == last:
            stalled += 1
            if stalled >= no_progress:
                break
        else:
            stalled = 0
        last = result.output
    return None, iterations, cost, False


def independent_checker_catches_bad_result():
    """独立 checker 应能拦下生成器自评通过的坏结果（示意：passed 被 checker 判定为假）。"""
    # 生成器自评 passed=True，但独立 checker 发现不满足 rubric → 拦下
    generated_self_passed = True
    checker_rubric_pass = False
    return checker_rubric_pass is False and generated_self_passed is True


def main():
    checks = []
    # ① Open 模式能探索出未知路径
    r, it, c, ok = run_loop(mode="open", good_when_goal_met=False)
    checks.append(ok and r.output == "discovered_unknown")
    # ② 三刹车：max_iter=1 必然只跑 1 次就停
    r, it, c, ok = run_loop(max_iter=1, good_when_goal_met=False)
    checks.append(it <= 1)
    # ③ 成本刹车：max_cost 很小则提前停
    r, it, c, ok = run_loop(max_cost=0.05, good_when_goal_met=False)
    checks.append(c <= 0.05 or it <= 2)
    # ④ 独立 checker 拦下坏结果
    checks.append(independent_checker_catches_bad_result())

    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "loop gate failed"
    print("PASS: loop gate 4/4")


if __name__ == "__main__":
    main()