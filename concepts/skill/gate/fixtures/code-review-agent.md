---
id: code-review-agent
name: 代码审查 Skill
description: 审查代码改动（diff/PR），按严重程度输出问题清单与可运行修复建议。当用户要求 review 代码、提交 PR 或给出 diff 时使用。
version: 1.2.0
inputs:
  - name: diff
    type: string
    description: 待审查的 diff 或文件路径
  - name: rules
    type: string
    description: 可选，项目规范路径（默认 docs/quality.md）
outputs:
  - name: report
    type: object
    description: 含 issues(P0/P1/P2)、suggestions、verdict
tags:
  - review
  - quality
  - static-analysis
dependencies:
  - read_file
  - run:ruff
---

# 代码审查 Skill

## 触发条件
当用户要求 review 代码、提交 PR、或提供 diff 时使用。

## 执行步骤
1. 读取 `diff` 指定的改动内容。
2. 以独立 Verifier 心态检查：正确性 / 可读性 / 边界条件 / 安全隐患。
3. 按严重程度输出：
   - **P0**（阻断）：安全漏洞、数据丢失风险
   - **P1**（重要）：逻辑错误、性能问题
   - **P2**（建议）：风格、命名、可读性

## 输出格式
```json
{
  "issues": [{"level": "P1", "file": "src/x.py", "line": 42, "desc": "..."}],
  "suggestions": ["..."],
  "verdict": "approve | request-changes"
}
```

## 边界与约束
- 只读审查，不改文件；需要改动时交给 harness 权限系统。
- 发现敏感操作（写文件/发请求）→ 标记为 P0 并停止自动处理。

## 失败处理
- 无法定位问题时主动提问，不猜测、不编造。
