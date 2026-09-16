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
| ③ | 门禁可自纠 | `on_failure` 含"修复指令" |
| ④ | 越权被拦截 | `git_push`/`http_request` 在 deny 且不在 allow |
| ⑤ | 沙箱 fail-closed | `sandbox.enabled` 与 `fail_closed` 均为 true |

## 实测输出

```
AGENTS.md 45 行, 深层指针 4 处
硬性纪律段 5 行
deny=2 条, allow=4 条
check1..check5: PASS
PASS: harness gate 5/5（对 fixtures 真实文件断言）
```

> **fixtures 即范例**：`gate/fixtures/AGENTS.md` 与 `permissions.json` 可直接抄用为 harness 配置模板。

> 上一节：[3-3 常见坑 + 自检](/concepts/harness/pitfalls) ｜ 回到：[03 harness](/concepts/harness)
