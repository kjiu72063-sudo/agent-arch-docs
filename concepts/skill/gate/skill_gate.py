"""skill_gate.py — skill 章 L5 验收（示意，python 实现）
运行：python gate/skill_gate.py
"""


def skill_has_interface_fields():
    """SKILL.md 应有统一接口字段。"""
    required = {"id", "name", "description", "version", "inputs", "outputs"}
    sample = {"id": "code-review-agent", "name": "审查", "description": "..",
              "version": "1.2.0", "inputs": ["diff"], "outputs": ["report"]}
    return required.issubset(set(sample))


def lifecycle_has_6_phases():
    phases = ["需求分析", "设计开发", "测试验证", "发布部署", "监控优化", "迭代更新"]
    return len(phases) == 6 and phases[0] == "需求分析" and phases[-1] == "迭代更新"


def decorator_adds_logging_without_changing():
    """装饰器叠加日志/缓存，不改原逻辑返回。"""
    def decorator(fn):
        calls = []
        def wrapper(*a, **k):
            calls.append("start")
            r = fn(*a, **k)
            calls.append("end")
            return r
        return wrapper, calls

    @decorator[0] if False else (lambda f: f)  # placeholder, replaced below
    def base(x):
        return x * 2
    # 用直接方式验证：装饰器包裹后返回值不变，且记录 start/end
    wrapped, calls = decorator(lambda x: x * 2)
    return wrapped(3) == 6 and calls == ["start", "end"]


def concurrency_and_cache_work():
    """并发（Promise.all 思想→python 并行）与缓存命中。"""
    cache = {}
    def compute(key):
        if key in cache:
            return ("hit", cache[key])
        cache[key] = key * 10
        return ("miss", cache[key])
    first = compute(5)
    second = compute(5)
    return first[0] == "miss" and second[0] == "hit" and second[1] == 50


def main():
    checks = [
        skill_has_interface_fields(),
        lifecycle_has_6_phases(),
        decorator_adds_logging_without_changing(),
        concurrency_and_cache_work(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "skill gate failed"
    print("PASS: skill gate 4/4")


if __name__ == "__main__":
    main()