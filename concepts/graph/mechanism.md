---
title: 5-1 graph 机制详解
---

# 5-1 · graph engineering 机制详解

把 05 的"图编排"落地成**真正可运行的 LangGraph 代码**。读完你不仅能画图，还能跑通一个含条件边、reducer、compile 的 StateGraph。

::: tip 承接 04
04 的 loop 解决"一轮反复"。本章的核心增量是：**graph 的每个节点可以是一个 loop**——loop 是 graph 的原子单元，graph 把多个 loop/步骤编排成分支与并行。
:::

## 核心构件（按 LangGraph Graph API 命名）

| 构件 | 含义 |
|---|---|
| **Node（节点）** | 一个执行单元（函数 / 一个 agent / 一次 loop） |
| **Edge（边）** | 节点间的确定流转 |
| **Conditional Edge（条件边）** | 由函数/模型在运行时决定下一步分支 |
| **State（状态）** | 跨节点共享的数据 |
| **Reducer（归约器）** | 多个节点/边更新同一字段时如何合并 |

## Reducer 的真实语义（纠正常见误解）

> 很多资料把 reducer 简写为"覆盖 / 追加 / 取最大"。这在概念上沾边，但**实现语义是 Channel/Reducer 机制**（LangGraph 官方，【事实】）：

- 你定义 `State` 时用 `Annotated[type, reducer]` 标注每个字段；
- 若字段带 reducer（如 `operator.add`），多个节点更新它时会**追加合并**而非互相覆盖；
- 典型例子：`MESSAGES` 用 `operator.add`，多个 agent 往对话里加消息时**累加**，不会互相覆盖。

## 完整可运行示例：带条件边 + reducer 的 StateGraph

```python
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END

# 1) 定义 State：messages 用 operator.add 累加（reducer），approved 默认覆盖
class State(TypedDict):
    messages: Annotated[list[str], operator.add]
    approved: bool

# 2) 节点函数：返回要更新的字段
def prepare(state: State):
    return {"messages": ["prepared"]}

def approved_node(state: State):
    return {"messages": ["approved: done"]}

def rejected_node(state: State):
    return {"messages": ["rejected: needs fix"]}

# 3) 条件边的路由函数：决定下一步走哪条分支
def route(state: State):
    return "approved" if state["approved"] else "rejected"

# 4) 组装图
builder = StateGraph(State)
builder.add_node("prepare", prepare)
builder.add_node("approved", approved_node)
builder.add_node("rejected", rejected_node)

builder.add_edge(START, "prepare")
builder.add_conditional_edges(
    "prepare",
    route,                          # 路由函数
    {"approved": "approved",        # 返回值 → 目标节点
     "rejected": "rejected"},
)
builder.add_edge("approved", END)
builder.add_edge("rejected", END)

# 5) compile：把图编译成可调用对象
graph = builder.compile()

# 6) 运行：invoke 传初始 state
result = graph.invoke({"messages": [], "approved": True})
print(result["messages"])
# ['prepared', 'approved: done']   ← 注意 messages 被累加（reducer 生效）
```

## 为什么要 compile

`compile()` 不只是"形式化"：它校验图的合法性（节点/边/无悬空），并生成可执行、可保存的执行计划（LangGraph，【事实】）。编译后的 `graph` 对象还能 checkpoint。

## checkpoint / persistence（graph 相对 loop 的关键增量）

- **Checkpoint**：每次节点执行后保存 state 快照 → 支持**断点续跑、回放、多会话（thread）**。
- **Persistence**：把 checkpoint 落到存储（内存 / 数据库），重启不丢。

```python
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
config = {"configurable": {"thread_id": "session-1"}}
graph.invoke({"messages": [], "approved": True}, config)   # 走 thread，可续跑
```

## 小测验

::: details 点击展开题目与答案
**Q1（选择）**：`Annotated[list[str], operator.add]` 的 `operator.add` 是？  
A. 覆盖旧的　B. 追加合并（reducer）　C. 取最大值  
✅ B。带 reducer 的字段会累加而非互相覆盖。

**Q2（选择）**：条件边（Conditional Edge）与普通边的区别是？  
A. 速度更快　B. 下一步由路由函数/模型在运行时决定　C. 只能串行  
✅ B。

**Q3（选择）**：checkpoint 的作用是？  
A. 加速推理　B. 保存 state 快照以支持断点续跑/回放　C. 压缩上下文  
✅ B。
:::

> 上一节：[05 graph 总入口](/concepts/graph) ｜ 下一节：[5-2 设计决策 + 验证](/concepts/graph/design)