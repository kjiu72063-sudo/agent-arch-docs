---
title: 5-3 graph 常见坑 + 自检
---

# 5-3 · graph 常见坑 + 掌握自检

graph 最容易在"滥用图 / reducer 理解错 / 缺 checkpoint"上翻车。本节给四个常见坑 + 产物化三档。

## 常见坑

- **坑① 滥用图**：单线性任务也上 StateGraph → 复杂度白增。**解法**：先问"需要分支/并行/多角色吗？"不需要就用单 loop（见 [04](/concepts/loop)）。
- **坑② reducer 理解错**：以为带 reducer 的字段是"最后一次覆盖"，实际是**合并**（如 `operator.add` 累加消息）。**解法**：用 `Annotated` + reducer 明确每个字段的合并语义（见 [5-1](/concepts/graph/mechanism)）。
- **坑③ 条件边路由函数返回值与映射表不符**：`route()` 返回的值不在 `{...}` 映射里 → 运行时找不到目标节点报错。**解法**：返回值和映射 key 严格一致。
- **坑④ 缺 checkpoint**：长任务/多线程会话不落 checkpoint → 中断即丢，无法续跑。**解法**：`compile(checkpointer=...)` + 设 `thread_id`。

## 反模式对照（代码级）

### 坑① 滥用图 —— 先问"真的需要编排吗"

```python
# ✕ 反模式：单线性任务也上 StateGraph（A→B→C 无分支无并行）
g.add_edge("a", "b"); g.add_edge("b", "c")   # 用一条顺序函数就够了

# ✓ 正解：只有出现"分支 / 并行 / 多角色 + 状态共享"时才上图
g.add_conditional_edges("review", route, {"ok": "done", "retry": "fix"})
g.add_conditional_edges("plan", fan_out, ["worker1", "worker2"])   # Send 并行
```

### 坑② reducer 理解错 —— 是"合并"不是"覆盖"

```python
# ✕ 反模式：以为 messages 会被最后一次赋值覆盖
class S(TypedDict):
    messages: list          # 每个节点 return 会整体替换 → 历史丢失

# ✓ 正解：用 Annotated + reducer 声明合并语义
from typing import Annotated
from operator import add
from langgraph.graph.message import add_messages

class S(TypedDict):
    messages: Annotated[list, add_messages]   # 追加合并，不覆盖
    steps:    Annotated[list, add]            # 累加
```

### 坑③ 条件边返回值与映射不符 —— 键必须严格一致

```python
# ✕ 反模式：route 返回 "approve"，映射表里却是 "approved" → 运行时报错
g.add_conditional_edges("check", route, {"approved": "done", "rejected": "fix"})
def route(s): return "approve"          # 拼写不一致 → KeyError

# ✓ 正解：返回值即映射 key，且给一个兜底分支
def route(s) -> str:
    return "approved" if s["ok"] else "rejected"
g.add_conditional_edges("check", route, {"approved": "done", "rejected": "fix"})
```

### 坑④ 缺 checkpoint —— 中断即丢

```python
# ✕ 反模式：不设 checkpointer，长任务中断后只能从头再来
graph = builder.compile()

# ✓ 正解：挂 checkpointer + 固定 thread_id，可续跑、可时间旅行
from langgraph.checkpoint.memory import MemorySaver
graph = builder.compile(checkpointer=MemorySaver())
graph.invoke({"messages": [...]}, config={"configurable": {"thread_id": "t-1"}})
# 中断后用同一 thread_id 再 invoke 即从断点继续（生产换 PostgresSaver/DynamoDBSaver）
```

## 产物化三档自检

| 档位 | 必须提交的产物 |
|---|---|
| **了解** | 区分 workflow 与 agent/graph，说出 Node/Edge/State/Reducer 各自是什么 |
| **熟悉** | 用 LangGraph 搭一个**含条件边 + reducer** 的 3 节点 StateGraph，`compile()` 后 `invoke()` 跑通，并说明 reducer 如何合并 |
| **精通** | 为真实多 agent 任务选型（routing / parallel / orchestrator-worker），实现带 checkpoint/persistence 的图，并判断它能否降级为单 loop |

::: tip 达标判断
"熟悉"档硬指标：你能让 `messages` 在多个节点追加后**看到累加结果**（reducer 生效），并让条件边按 `approved` 真/假走不同分支——这验证了 reducer 与条件边真的跑起来了。
:::

::: info 下一章承接
图的节点可以是一个 loop，loop 里可以调用一个"能力单元"。这种可复用、按需注入的能力，就是横切主轴的 [06 skill 体系架构](/concepts/skill)。
:::

> 上一节：[5-2 graph 设计决策 + 验证](/concepts/graph/design) ｜ 下一章：[06 skill 体系架构](/concepts/skill)