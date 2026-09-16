---
title: 3-3 harness 常见坑 + 自检
---

# 3-3 · harness 常见坑 + 掌握自检

harness 最容易"看起来搭了、实际兜不住"。本节给四个常见坑 + 产物化三档自检。

## 常见坑

- **坑① 权限过宽（all-or-nothing）**：要么全 ban 要么全给，缺少"部分工具需审批"的粒度 → 要么没法干活、要么裸奔。**解法**：用 allow/deny + 条件（如 write 需审批）的矩阵（见 [3-1](/concepts/harness/mechanism)）。
- **坑② 靠模型自觉守规矩**：只写 AGENTS.md 不配门禁 → 模型"忘了规矩"就违规。**解法**：机械化执行门禁脚本强制兜底，AGENTS.md 只是"声明"，门禁才是"执行"。
- **坑③ 缺 fail-closed**：后端不可用就跳过安全降级裸跑 → 危险操作直接放行。**解法**：拿不到安全后端就失败（fail-closed），绝不降级。
- **坑④ 熵失控**：长任务不落地 checkpoint、不归档 → 上下文膨胀、目标漂移、不可复现。**解法**：仓库即记录系统 + 阶段归档。

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