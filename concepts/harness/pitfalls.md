---
title: 3-3 harness 常见坑 + 自检
---

# 3-3 · harness 常见坑 + 掌握自检

::: tip 难度分层 · 本页 = 全档自检（L0–L2）
用下方**三档表**先定位自己在哪一级；「常见坑」与难度无关，任何档都该看。
:::


harness 最容易"看起来搭了、实际兜不住"。本节给四个常见坑 + 产物化三档自检。

## 常见坑

- **坑① 权限过宽（all-or-nothing）**：要么全 ban 要么全给，缺少"部分工具需审批"的粒度 → 要么没法干活、要么裸奔。**解法**：用 allow/deny + 条件（如 write 需审批）的矩阵（见 [3-1](/concepts/harness/mechanism)）。
- **坑② 靠模型自觉守规矩**：只写 AGENTS.md 不配门禁 → 模型"忘了规矩"就违规。**解法**：机械化执行门禁脚本强制兜底，AGENTS.md 只是"声明"，门禁才是"执行"。
- **坑③ 缺 fail-closed**：后端不可用就跳过安全降级裸跑 → 危险操作直接放行。**解法**：拿不到安全后端就失败（fail-closed），绝不降级。
- **坑④ 熵失控**：长任务不落地 checkpoint、不归档 → 上下文膨胀、目标漂移、不可复现。**解法**：仓库即记录系统 + 阶段归档。

## 反模式对照（配置/代码级）

### 坑① 权限过宽 —— 粒度化矩阵

```json
// ✕ 反模式：all-or-nothing，要么干不了活要么裸奔
{ "permissions": { "allow": ["*"] } }

// ✓ 正解：allow/deny + 条件审批
{ "permissions": {
    "allow": ["Read(**)", "Bash(uv run pytest:*)"],
    "deny":  ["Bash(rm -rf:*)", "Write(.env)"],
    "require_approval": ["Write(src/**)"]
} }
```

### 坑② 靠模型自觉 —— 声明 ≠ 执行

```bash
# ✕ 反模式：AGENTS.md 里写"改动必须通过测试"，但没有东西强制执行
echo "改动必须通过 pytest" >> AGENTS.md

# ✓ 正解：机械化门禁，违规直接失败（exit≠0 阻断）
# .git/hooks/pre-commit
uv run pytest || exit 1
uv run ruff check . || exit 1
```

### 坑③ 缺 fail-closed —— 拿不到沙箱就停，不降级

```python
# ✕ 反模式：沙箱不可用就跳过隔离裸跑
try:
    sandbox = get_sandbox()
except SandboxUnavailable:
    run_directly(cmd)          # 危险：越权命令被放行

# ✓ 正解：fail-closed，拿不到安全后端就失败
sandbox = get_sandbox()        # 抛错即中止，绝不降级
assert sandbox.available, "SANDBOX_UNAVAILABLE：拒绝在无隔离环境执行"
```

### 坑④ 熵失控 —— checkpoint 与归档

```python
# ✕ 反模式：长任务只在内存里推进，崩了全丢、也无法复现
state = {}
for step in plan:
    state.update(run(step))

# ✓ 正解：每阶段落地 checkpoint + 归档，可恢复、可复现
for i, step in enumerate(plan):
    state.update(run(step))
    save_checkpoint(f"ckpt-{i}.json", state)     # 可恢复
    write_log(f"stage-{i}.md", summarize(state)) # 可复现
```

## 产物化三档自检

| 档位 | 必须提交的产物 |
|---|---|
| **了解** | 说清 harness 与 prompt/context 的区别，列举 5 个构成（工具/权限/环境/约束/守护） |
| **熟悉** | 为真实项目写一份 `AGENTS.md` + 权限矩阵，并跑通一个 gate 门禁脚本对"违规改动"返回失败 |
| **精通** | 设计完整的 harness：权限矩阵 + 机械化门禁 + fail-closed + 熵管理，让 agent 长任务在受控环境不跑飞，且越权动作被确定性拦截 |

::: tip 达标判断
"熟悉"档硬指标：你写的门禁脚本在**故意制造违规**（如漏跑测试、格式不合规）时必然返回失败——这验证了"机械化守护"真的住了。
:::

::: info 下一章承接
harness 把"能做什么、被什么约束"定死之后，agent 需要在里面**反复执行、验证、重试**——这就是 [04 loop engineering](/concepts/loop)。loop 运行在 harness 内，每轮读写 context、受 harness 权限与预算约束。
:::

> 上一节：[3-2 harness 设计决策 + 验证](/concepts/harness/design) ｜ 下一章：[04 loop engineering](/concepts/loop)