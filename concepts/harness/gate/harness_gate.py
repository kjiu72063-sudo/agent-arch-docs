"""harness_gate.py — harness 章 L5 验收（对 gate/fixtures/ 下的真实文件断言）
运行：python gate/harness_gate.py
真实检查对象：fixtures/AGENTS.md（目录式规范）、fixtures/permissions.json（权限/沙箱配置）
本 gate 不再使用任何内置模拟字符串：文件缺失或不符合规范即失败。
"""
import json
import os
import re

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def load_fixture(name):
    """读取真实 fixture 文件（不存在则抛错，绝不退化为内置字符串）。"""
    path = os.path.join(FIXTURES, name)
    with open(path, encoding="utf-8") as f:
        return f.read() if name.endswith(".md") else json.load(f)


def is_map_style_agents():
    """真实验证：fixtures/AGENTS.md 必须是目录式 —— 行数 ≤ 120 且含深层文档指针。"""
    content = load_fixture("AGENTS.md")
    lines = content.splitlines()
    pointers = [l for l in lines if "docs/" in l or "AGENTS_" in l]
    print(f"    AGENTS.md {len(lines)} 行, 深层指针 {len(pointers)} 处")
    return len(lines) <= 120 and len(pointers) >= 3


def agents_md_has_no_long_manual():
    """真实验证：AGENTS.md 不沦为手册 —— 硬性纪律段落应精简（≤15 行），其余靠指针。"""
    content = load_fixture("AGENTS.md")
    m = re.search(r"## 硬性纪律.*?(?=\n## )", content, re.S)
    discipline = m.group(0).splitlines() if m else []
    print(f"    硬性纪律段 {len(discipline)} 行")
    return 0 < len(discipline) <= 15


def gate_output_has_fix_instruction():
    """真实验证：门禁输出应含可被 agent 读取的修复指令（读真实配置里的 on_failure 说明）。"""
    cfg = load_fixture("permissions.json")
    note = cfg["gate"]["on_failure"]
    print(f"    on_failure: {note}")
    return "修复指令" in note


def deny_out_of_scope_action():
    """真实验证：读真实 permissions.json，断言越权动作被 deny（非硬编码模拟）。"""
    perms = load_fixture("permissions.json")["permissions"]
    denied = perms["deny"]
    has_push = any("git_push" in d for d in denied)
    has_http = any("http_request" in d for d in denied)
    allow_push = any("git_push" in a for a in perms["allow"])
    print(f"    deny={len(denied)} 条, allow={len(perms['allow'])} 条")
    return has_push and has_http and not allow_push


def sandbox_is_fail_closed():
    """真实验证：沙箱配置为 fail_closed（无后端直接失败，绝不裸跑）。"""
    sb = load_fixture("permissions.json")["sandbox"]
    return sb.get("enabled") is True and sb.get("fail_closed") is True


def main():
    checks = [
        is_map_style_agents(),
        agents_md_has_no_long_manual(),
        gate_output_has_fix_instruction(),
        deny_out_of_scope_action(),
        sandbox_is_fail_closed(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "harness gate failed"
    print("PASS: harness gate 5/5（对 fixtures 真实文件断言）")


if __name__ == "__main__":
    main()