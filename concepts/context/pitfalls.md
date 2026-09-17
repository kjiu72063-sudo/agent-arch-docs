---
title: 2-3 context 常见坑 + 自检
---

# 2-3 · context 常见坑 + 掌握自检

::: tip 难度分层 · 本页 = 全档自检（L0–L2）
用下方**三档表**先定位自己在哪一级；「常见坑」与难度无关，任何档都该看。
:::


读机制还不够，要能**识别坑**并知道"什么算真的会了"。本节给四个常见坑 + 产物化三档自检。

## 常见坑

- **坑① 预算算不清，超限就崩**：不在组装前记账，长任务跑到一半上下文溢出 → 强制报错。**解法**：组装前按预算记账（见 [2-1](/concepts/context/mechanism) 骨架），超限先降配。
- **坑② 检索"召回了但没用对"**：向量召回 Top-K 只看相似度，可能召回一堆同义词垃圾。**解法**：设最小分数阈值 + 按任务相关性重排，别把"相似"当"有用"。
- **坑③ 压缩丢关键信息**：把旧对话全量 LLM 摘要，结果丢掉了后续需要的约束/上下文。**解法**：压缩前保留"不可再生"的约束类信息，只对"可再生"对话做摘要。
- **坑④ 渐进披露做成"永不披露"**：只给目录不给详情入口，模型拿不到真实内容。**解法**：披露要有可操作的 locator / 二次检索动作，模型真能"取到"。

## 反模式对照（代码级）

### 坑① 预算算不清 —— 组装前记账 vs 溢出后救火

```python
# ✕ 反模式：边拼边送，超限才在服务端报错
prompt = system + task + "\n".join(all_retrieved) + tool_dump
resp = llm.chat(prompt)          # 长任务跑到一半 → context-overflow 报错

# ✓ 正解：组装前按预算记账，超限先降配（免费降 retrieved）
def assemble(parts, budget):
    if estimate(parts) > budget:
        parts["retrieved"] = parts["retrieved"][:half]   # 先砍可再生内容
    assert estimate(parts) <= budget, "仍超限 → spill/summarize"
    return join(parts)
```

### 坑② 检索只看相似度 —— 阈值 + 重排

```python
# ✕ 反模式：Top-K 相似度直接全塞，"相似"被当成"有用"
docs = vector_db.search(q, k=20)

# ✓ 正解：分数阈值过滤 + 按任务相关性重排，只留真正有用的
hits = [d for d in vector_db.search(q, k=20) if d.score >= 0.75]
docs = rerank_by_relevance(hits, task)[:5]
```

### 坑③ 压缩丢关键信息 —— 区分"可再生"与"不可再生"

```python
# ✕ 反模式：整段历史无差别 LLM 摘要 → 约束/接口约定被摘要掉
summary = llm(f"总结这段对话：{full_history}")

# ✓ 正解：约束类（不可再生）原文保留，只摘要可再生的过程性对话
keep = [m for m in history if m.kind in ("constraint", "interface", "decision")]
summary = llm(f"总结过程性对话：{procedural_history}")
compacted = keep + [summary]
```

## 产物化三档自检

> 对齐 Track 01 的写法：每档对应**可提交的产物**，不是"感觉会了"。

| 档位 | 必须提交的产物 |
|---|---|
| **了解** | 说清"增强 LLM = 指令 + 上下文 + 工具"，指出窗口是有限预算，且能列出预算的 5 类来源（system/任务/检索/记忆/工具） |
| **熟悉** | 为真实场景实现一个带预算上限 + 渐进披露 + spill 的上下文组装器（可用 Python 骨架改造），并跑通"超限→降配→不崩" |
| **精通** | 设计带 `pressure` / `context-overflow` 双触发 + prune/summarize 策略的压缩管线，并量化对比压缩前后 token 占用与信息损失 |

::: tip 达标判断
"熟悉"档的硬指标：你的组装器在**超预算输入**下不会报错，而是降配后仍产出可用上下文——这直接验证了预算控制是否真的生效。
:::

::: info 下一章承接
上下文组装好之后，谁来承载它、约束它、反复消费它？——这就是 [03 harness engineering](/concepts/harness) 要解决的：**AGENTS.md 由 harness 管理、由 context 注入，loop 每轮读写这份 context**。
:::

> 上一节：[2-2 context 设计决策 + 验证](/concepts/context/design) ｜ 下一章：[03 harness engineering](/concepts/harness)
