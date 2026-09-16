---
title: 5-2 graph 设计决策与验证
---

# 5-2 · graph 设计决策与验证

5-1 让你能跑通 StateGraph，本节把深度推到**设计者级**：什么时候用哪种 reducer、生产用哪种 checkpointer、HITL 该用静态还是动态 interrupt、怎么用 Send 做并行归并，以及怎样用一个 gate 脚本验收整张图。

::: tip 承接 5-1
5-1 给了可运行 StateGraph（条件边 + `operator.add` reducer + compile + checkpoint）。本节在其上回答"**何时选哪个**"并给**可运行验收 gate**。
:::

## 决策一：reducer 三类语义（对照实验）

LangGraph 的 reducer 不是"覆盖/追加"二选一，而是**三类**（LangGraph Graph API，【事实】）：

| Reducer | 写法 | 合并语义 | 适用 |
|---|---|---|---|
| Replace（默认） | `count: int` | **后写覆盖先写** | 单一进度、状态标志 |
| Append | `Annotated[list, operator.add]` | **追加合并**（并行安全） | 消息历史、中间结果收集 |
| 自定义二元函数 | `Annotated[dict, merge_fn]` | 你定义 how 合并 | 需要 merge 规则（如字典浅合并） |

**关键洞见**：Append 类 reducer 是**并行执行安全**的根基——当 `Send` 扇出多个 worker 时，它们的输出都作为 partial state 到达，由 reducer **确定性合并，无竞态**（LangGraph，【事实】）。

```python
# 对照实验：同一输入，Replace vs Append 结果不同
from typing import Annotated, TypedDict
import operator

class ReplaceState(TypedDict):
    items: list[str]              # 默认 replace

class AppendState(TypedDict):
    items: Annotated[list[str], operator.add]   # append

def add_one(state):
    return {"items": ["w1"]}

def add_two(state):
    return {"items": ["w2"]}

# ReplaceState: 后写的 w2 覆盖 w1 → ["w2"]
# AppendState:  追加合并   → ["w1", "w2"]
```
> 记住（来自 LangGraph 社区常见坑，【事实】）：`operator.add` 是**追加**不是替换——并行场景用错 reducer 会"列表一直重置"。

## 决策二：checkpointer 生产选型

`MemorySaver` 只是本地测试用。生产选型（LangGraph 官方，【事实】）：

| 后端 | 适用 | 说明 |
|---|---|---|
| `InMemorySaver` | 本地开发/测试 | 进程退出即丢，勿上生产 |
| `PostgresSaver` | **生产推荐** | 需连接池 + `autocommit` + `setup()`(放 CI 迁移，不在热路径) |
| `DynamoDBSaver` | Serverless | AWS 部署 |

```python
# 生产接线（Postgres）
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool

pool = ConnectionPool(conninfo="postgresql://...", autocommit=True,
                      row_factory=dict_row, min_size=2, max_size=10)
checkpointer = PostgresSaver(pool)
checkpointer.setup()          # 部署时跑一次，勿放请求热路径
graph = builder.compile(checkpointer=checkpointer)
```

**`thread_id` 隔离状态**：同 `thread_id` 续跑（崩溃恢复）、不同则新跑。这正是多会话/多用户隔离的关键，也呼应 02 的记忆分层。

```python
config = {"configurable": {"thread_id": "session-42"}}
graph.invoke(initial, config)        # 第一次
graph.invoke(None, config)           # 崩溃后用同一 thread_id 续跑
```

## 决策三：Human-in-the-Loop（HITL）两种 interrupt

| 方式 | 用法 | 场景 |
|---|---|---|
| 静态 `interrupt_before=["node"]` | 编译时指定位置 | 审批节点前暂停（位置确定） |
| 动态 `interrupt()` | 节点内按运行条件暂停 | 运行时被规则/阈值触发（条件未知） |

```python
# 静态：compile 时指定在 execute 前暂停，人工批准后以同 thread 续跑
app = graph.compile(checkpointer=memory, interrupt_before=["execute"])
app.invoke(initial, config)                       # 停在 execute 前
app.invoke({"approved": True}, config)            # 人工批准 → 继续

# 动态：节点内按需暂停（配合 state 条件）
from langgraph.types import interrupt
def review_node(state):
    if state.get("needs_approval"):
        decision = interrupt({"question": "是否批准?"})   # 暂停，等人工
        return {"approved": decision}
```

## 决策四：Send 并行 + map-reduce

用 `Send` 做**动态扇出**——每个条目触发一次 worker 节点，再用 `operator.add` reducer 归并（LangGraph，【事实】）：

```python
from langgraph.types import Send

def fan_out(state):
    return [Send("worker", {"url": u}) for u in state["urls"]]

# worker 返回 {"results": [r]}；results 用 operator.add → 并行结果自动归并、无竞态
builder.add_conditional_edges("dispatcher", fan_out, ["worker"])
builder.add_edge("worker", "collect")
```

**决策表：何时用图 + 哪种**（承接 [5-3 常见坑](/concepts/graph/pitfalls) 的"别滥用图"）：
| 场景 | 方案 |
|---|---|
| 单线性反复 | 单 loop（04），不上图 |
| 固定流水线 | workflow，静态边 |
| 多分支/模型决策 | 条件边 |
| 并行收集数据 | Send 扇出 + reducer 归并 |
| 需要暂停等人 | checkpointer + interrupt（HITL） |

## 验收 gate：可运行脚本断言

```python
# gate/graph_gate.py —— 5-3 验收（示意，运行需 langgraph）
def run():
    checks = []
    # ① 条件边按 approved 走不同分支
    checks.append(run_conditional_edge(approved=True) == ["prepared","approved: done"])
    # ② reducer 累加：两个节点追加不覆盖
    checks.append(run_reducer_append() == ["w1","w2"])
    # ③ checkpoint 续跑：同 thread 恢复，不同 thread 新跑
    checks.append(run_checkpoint_resume())
    # ④ Send 并行归并：N 个 worker 结果全归并、无丢失
    checks.append(run_send_fanout() is True)
    # ⑤ interrupt 恢复：批准后继续
    checks.append(run_interrupt_resume())
    for i, ok in enumerate(checks, 1):
        assert ok, f"检查 {i} 失败"
    print("PASS: 5/5")
```
> 运行：`python gate/graph_gate.py`（需 `pip install langgraph`）。这一步把"会用"变成"可验证会了"。

## 三档自检（5-2 版）

| 档位 | 必须提交的产物 |
|---|---|
| 熟悉 | 能解释 reducer 三类语义，并指出 `operator.add` 在并行下为何安全 |
| 精通 | 实现一个**可中断 + 可续跑（checkpoint）+ Send 并行归并**的生产图，并说出该用哪种 checkpointer 与 interrupt |

> 上一节：[5-1 graph 机制详解](/concepts/graph/mechanism) ｜ 下一节：[5-3 常见坑 + 自检](/concepts/graph/pitfalls)