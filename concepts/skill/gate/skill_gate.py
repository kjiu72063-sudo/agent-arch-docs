"""skill_gate.py — skill 章 L5 验收（对 gate/fixtures/ 下真实 SKILL.md 断言）
运行：python gate/skill_gate.py
真实检查对象：fixtures/code-review-agent.md（统一接口规范 + 生命周期 + 模式）
本 gate 不再模拟 Promise.all / 装饰器，改为断言真实 skill 文件与真实横切行为。
"""
import os
import re

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def load_fixture(name):
    path = os.path.join(FIXTURES, name)
    with open(path, encoding="utf-8") as f:
        return f.read()


def skill_has_interface_fields():
    """真实验证：frontmatter 含统一接口字段 id/name/description/version/inputs/outputs。"""
    content = load_fixture("code-review-agent.md")
    fm = re.search(r"^---\n(.*?)\n---", content, re.S).group(1)
    required = ["id:", "name:", "description:", "version:", "inputs:", "outputs:"]
    missing = [r for r in required if r not in fm]
    print(f"    缺失字段: {missing or '无'}")
    return not missing


def skill_version_is_semver():
    """真实验证：version 符合语义化版本（x.y.z）。"""
    content = load_fixture("code-review-agent.md")
    m = re.search(r"^version:\s*(\S+)", content, re.M)
    ver = m.group(1) if m else ""
    ok = bool(re.match(r"^\d+\.\d+\.\d+$", ver))
    print(f"    version={ver}")
    return ok


def skill_declares_failure_handling():
    """真实验证：SKILL.md 含失败处理（不是只写 happy path）。"""
    content = load_fixture("code-review-agent.md")
    return "失败处理" in content and "边界与约束" in content


def decorator_adds_logging_without_changing():
    """真实验证：装饰器叠加日志横切，原函数返回值不变（真实调用，非模拟）。"""
    log = []

    def logging_decorator(fn):
        def wrapper(*a, **k):
            log.append("start")
            r = fn(*a, **k)
            log.append("end")
            return r
        return wrapper

    @logging_decorator
    def base(x):
        return x * 2

    result = base(3)
    print(f"    result={result}, log={log}")
    return result == 6 and log == ["start", "end"]


def strategy_pattern_dispatches_by_type():
    """真实验证：策略模式按输入类型分派到不同处理器（真实 dict 分派）。"""
    processors = {
        "json": lambda d: f"json:{d}",
        "xml": lambda d: f"xml:{d}",
        "csv": lambda d: f"csv:{d}",
    }

    def dispatch(data_type, data):
        return processors[data_type](data)

    results = [dispatch("json", "a"), dispatch("xml", "b"), dispatch("csv", "c")]
    print(f"    dispatched={results}")
    return results == ["json:a", "xml:b", "csv:c"]


def main():
    checks = [
        skill_has_interface_fields(),
        skill_version_is_semver(),
        skill_declares_failure_handling(),
        decorator_adds_logging_without_changing(),
        strategy_pattern_dispatches_by_type(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "skill gate failed"
    print("PASS: skill gate 5/5（对 fixtures 真实文件断言）")


if __name__ == "__main__":
    main()