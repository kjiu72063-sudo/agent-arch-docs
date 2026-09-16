"""graph_gate.py — graph 章 L5 验收：条件边 + reducer 累加 + checkpoint 续跑 + Send 并行归并
运行：pip install langgraph 后 python gate/graph_gate.py
"""
from typing import Annotated, TypedDict
import operator
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send


class State(TypedDict):
    messages: Annotated[list[str], operator.add]
    approved: bool


def prepare(state):
    return {"messages": ["prepared"]}


def ok_n(state):
    return {"messages": ["approved: done"]}


def no_n(state):
    return {"messages": ["rejected: needs fix"]}


def route(state):
    return "approved" if state["approved"] else "rejected"


def build_base():
    b = StateGraph(State)
    b.add_node("prepare", prepare)
    b.add_node("approved", ok_n)
    b.add_node("rejected", no_n)
    b.add_edge(START, "prepare")
    b.add_conditional_edges("prepare", route,
                            {"approved": "approved", "rejected": "rejected"})
    b.add_edge("approved", END)
    b.add_edge("rejected", END)
    return b


class PState(TypedDict):
    urls: list
    results: Annotated[list, operator.add]


def fan_out(state):
    return [Send("worker", {"url": u}) for u in state["urls"]]


def worker(state):
    return {"results": [f"fetched:{state['url']}"]}


def collect(state):
    return {"results": []}


def build_parallel():
    b = StateGraph(PState)
    b.add_node("fan", lambda s: {"results": []})
    b.add_node("worker", worker)
    b.add_node("collect", collect)
    b.add_edge(START, "fan")
    b.add_conditional_edges("fan", fan_out, ["worker"])
    b.add_edge("worker", "collect")
    b.add_edge("collect", END)
    return b


def main():
    checks = []
    # ① 条件边分派（approved=True → approved 分支）
    g = build_base().compile()
    r = g.invoke({"messages": [], "approved": True})
    checks.append(r["messages"] == ["prepared", "approved: done"])
    # ② reducer 追加：两节点各自 append 不覆盖
    checks.append(r["messages"] == ["prepared", "approved: done"])
    # ③ checkpoint 续跑：同 thread 恢复
    mem = MemorySaver()
    g2 = build_base().compile(checkpointer=mem)
    cfg = {"configurable": {"thread_id": "t-1"}}
    g2.invoke({"messages": [], "approved": True}, cfg)
    r2 = g2.invoke({"messages": []}, cfg)
    checks.append("prepared" in r2["messages"])
    # ④ Send 并行归并：3 个 url 全部取到
    gp = build_parallel().compile()
    rp = gp.invoke({"urls": ["a", "b", "c"], "results": []})
    checks.append(sorted(rp["results"]) == ["fetched:a", "fetched:b", "fetched:c"])

    ok = all(checks)
    for i, c in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if c else 'FAIL'}")
    assert ok
    print("PASS: graph gate 全部通过")


if __name__ == "__main__":
    main()