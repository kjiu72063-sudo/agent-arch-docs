---
title: harness 验收 gate
---

# harness 验收 gate

对应 [3-2 design](/concepts/harness/design) 的 L5 验收。脚本：`gate/harness_gate.py`（本地可运行）。

运行：
```bash
python concepts/harness/gate/harness_gate.py
```

## 验证内容（5 项，对真实文件断言）

检查对象：`gate/fixtures/AGENTS.md`、`gate/fixtures/permissions.json`（**真实文件，非内置字符串**）。

| # | 验证 | 方式 |
|---|---|---|
| ① | AGENTS.md 是地图式 | 行数 ≤120 且深层指针 ≥3 处 |
| ② | 不沦为手册 | 硬性纪律段 ≤15 行 |
| ③ | 门禁可自纠（**错误信息三要素**） | `on_failure` 同时含 `❌` + `✅ FIX` + `📖 See` |
| ④ | 越权被拦截 | `git_push`/`http_request` 在 deny 且不在 allow |
| ⑤ | 沙箱 fail-closed | `sandbox.enabled` 与 `fail_closed` 均为 true |

## 实测输出

```
AGENTS.md 36 行, 深层指针 5 处
硬性纪律段 5 行
三要素: ❌=True ✅FIX=True 📖See=True
deny=2 条, allow=4 条
check1..check5: PASS
PASS: harness gate 5/5（对 fixtures 真实文件断言）
```

> **fixtures 即范例**：`gate/fixtures/AGENTS.md` 与 `permissions.json` 可直接抄用为 harness 配置模板。

::: details 展开完整脚本 `gate/harness_gate.py`
```python
"""harness_gate.py — harness 章 L5 验收（对 gate/fixtures/ 下的真实文件断言）
运行：python gate/harness_gate.py
真实检查对象：fixtures/AGENTS.md（目录式规范）、fixtures/permissions.json（权限/沙箱配置）
本 gate 不使用任何内置模拟字符串：文件缺失或不符合规范即失败。
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
    """真实验证：门禁输出必须含"错误信息即 Prompt"三要素
    ❌ 什么错了 / ✅ FIX 怎么改 / 📖 See 去哪看文档。"""
    cfg = load_fixture("permissions.json")
    note = cfg["gate"]["on_failure"]
    has_err = "❌" in note
    has_fix = "✅ FIX" in note
    has_see = "📖 See" in note
    print(f"    三要素: ❌={has_err} ✅FIX={has_fix} 📖See={has_see}")
    return has_err and has_fix and has_see


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
```
:::

> 上一节：[3-3 常见坑 + 自检](/concepts/harness/pitfalls) ｜ 回到：[03 harness](/concepts/harness)
