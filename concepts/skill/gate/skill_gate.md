---
title: skill 验收 gate
---

# skill 验收 gate

对应 [6-2 design](/concepts/skill/design) 的 L5 验收。脚本：`gate/skill_gate.py`（本地可运行）。

运行：
```bash
python concepts/skill/gate/skill_gate.py
```

## 验证内容（5 项，对真实文件断言 + 真实调用）

检查对象：`gate/fixtures/code-review-agent.md`（**真实 SKILL.md**）。

| # | 验证 | 方式 |
|---|---|---|
| ① | 统一接口字段齐备 | frontmatter 含 id/name/description/version/inputs/outputs |
| ② | 版本合规 | `version` 符合语义化 `x.y.z` |
| ③ | 含失败处理 | 存在"失败处理"与"边界与约束"段 |
| ④ | 装饰器横切不改原逻辑 | **真实调用** `base(3)=6` 且日志 `['start','end']` |
| ⑤ | 策略模式按类型分派 | **真实 dict 分派** → `json:a / xml:b / csv:c` |

## 实测输出

```
version=1.2.0
result=6, log=['start', 'end']
dispatched=['json:a', 'xml:b', 'csv:c']
check1..check5: PASS
PASS: skill gate 5/5（对 fixtures 真实文件断言）
```

> **fixture 即范例**：`gate/fixtures/code-review-agent.md` 是可直接抄用的 SKILL.md 模板。

> 上一节：[6-3 常见坑 + 自检](/concepts/skill/pitfalls) ｜ 回到：[06 skill](/concepts/skill)
