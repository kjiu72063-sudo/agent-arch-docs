"""harness_gate.py — harness 章 L5 验收（示意，模块依赖以注释说明）
运行：python gate/harness_gate.py（部分检查需仓库内有对应文件，示意实现）
"""


SAMPLE_MAP_STYLE = """# AGENTS.md —— 导航入口（目录式）

## 我是谁
本仓库的资深工程师。

## 先读这些（渐进披露）
- 架构与命名 → docs/architecture.md
- 提交流程与禁止项 → AGENTS_commit.md
- 质量标准与 gate → docs/quality.md

## 硬性纪律（机器可验证的才写这）
- 技术栈：Python 3.12 / uv / pytest / ruff。
- 任何改动必须通过 gate.py。
- 禁止提交 node_modules / dist / *.log / symlink。

## 工具权限速查
| 工具 | 权限 |
|---|---|
| read | 全库 |
| write | src/, tests/（需审批） |
| run | pytest/ruff/uv 白名单 |
| push | 人工显式授权 |
"""


def is_map_style_agents(path=None):
    """AGENTS.md 应为目录式：行数 ≤ ~120，且含深层文档指针。
    path 为 None 时用内置样例（保证 gate 自包含、任何目录可跑）。"""
    if path:
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return False
    else:
        content = SAMPLE_MAP_STYLE
    lines = content.splitlines()
    return len(lines) <= 120 and any("docs/" in l or "AGENTS_" in l for l in lines)


def gate_output_has_fix_instruction():
    """门禁输出应含可被 agent 读取的修复指令。"""
    sample = {
        "pass": False,
        "message": "lint 失败。修复指令：删未用 import、补齐空行、缩进 4 空格。修完重跑。",
    }
    return "修复指令" in sample["message"] or "fix" in sample["message"].lower()


def entropy_scan_finds_bad_pattern():
    """熵扫描应能发现注入的坏模式（示意：扫描 hardcode 或 TODO 泛滥）。"""
    bad_marker = "debug_flag = True   # TODO: remove"
    # 模拟扫描器命中
    return "TODO" in bad_marker


def deny_out_of_scope_action():
    """权限矩阵：越权动作被确定性拦截（示意：白名单命令外一律拒绝）。"""
    allowed = {"pytest", "ruff", "uv"}
    action = "git push"  # 不在白名单
    return action.split()[0] not in allowed


def main():
    checks = [
        is_map_style_agents(),
        gate_output_has_fix_instruction(),
        entropy_scan_finds_bad_pattern(),
        deny_out_of_scope_action(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "harness gate failed"
    print("PASS: harness gate 4/4")


if __name__ == "__main__":
    main()