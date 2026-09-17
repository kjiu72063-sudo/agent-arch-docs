---
title: DeepAgent
---

# DeepAgent

Track B 第二个实例：**LangChain `deepagents`**——基于 LangGraph + 中间件，`create_deep_agent` 一行建 agent。它是主轴里 **graph + loop** 的活教材。

::: tip 一句话
DeepAgent 证明"图编排"不只是概念：用 LangGraph 的状态图把**规划、子 agent、上下文总结**串起来，复杂 agent 也能声明式建出来。
:::

## 精确映射：本实例 × 主轴机制

DeepAgent 最凸显的工程层是 **graph + loop**：

```mermaid
flowchart LR
  C["create_deep_agent\n一行建 agent"] --> G["graph 编排\nLangGraph StateGraph"]
  G --> L["loop 循环\n推理 + 工具"]
  L --> S["子 agent 调用"]
  L --> Ctx["上下文自动总结"]
  S -->|文件系统/子agent| T["tools 工具"]
  style G fill:#b45309,color:#fff
  style L fill:#0d7d6e,color:#fff
```

| 本实例的具体件 | 对应主轴机制 | 章节 |
|---|---|---|
| `ContextSummarizationMiddleware(max_messages=30)` | compaction（超阈值压缩，防窗口膨胀） | [2-2](/concepts/context/design) |
| `subagents=[SubAgent(...)]` 包装成工具 | 子 agent 作为节点 / 工具 | [5-2](/concepts/graph/design) |
| `messages` / `intermediate_steps` 的 reducer | graph reducer（`add_messages` / `operator.add`） | [5-1](/concepts/graph/mechanism) |
| 推理循环 + 工具往返 | loop 五零件 | [4-1](/concepts/loop/mechanism) |
| 三 toolkit（fs / bash / interpreter） | 工具能力 + 沙箱执行 | [3-1](/concepts/harness/mechanism) |

## 中间件时序：一次带规划的执行

```mermaid
sequenceDiagram
  participant U as 用户
  participant D as DeepAgent(LangGraph)
  participant Plan as 规划节点
  participant Sub as 子 Agent/工具
  participant Sum as 上下文总结中间件
  U->>D: 复杂任务
  D->>Plan: 先拆解成子任务
  Plan->>Sub: 逐子任务执行
  Sub-->>Sum: 中间结果
  Sum->>Sum: 压缩/总结防窗口膨胀
  Sum-->>D: 精简后的上下文
  D->>U: 汇总最终结果
```

## 中间件机制（LangChain deepagents，【事实】）

`create_deep_agent` 通过 **middleware** 在 agent 节点前后挂载横切能力，用 `MiddlewareReturn.state_update` 写回 LangGraph 状态：

| 中间件 | 作用 |
|---|---|
| `ContextSummarizationMiddleware` | 消息超阈值（默认 30）时，对旧消息分组生成摘要并以 `SystemMessage` 替换，防窗口膨胀 |
| `ContextExtractionMiddleware` | 从对话提取结构化实体/状态写入 context（确定性，呼应 [02 DSE](/concepts/context/design)） |
| `SubAgentMiddleware` | 把子 agent 包装成 `StructuredTool`，父 agent 推理时看到"工具形式的子 agent" |
| `AsyncToolsMiddleware` | 把同步工具包装为异步，避免阻塞 |

**工具注册**：`create_deep_agent` 的 `tools` 参数接受三个预置 toolkit（`langchain_agentic_toolkits`）：

| Toolkit | 包含工具 |
|---|---|
| `fs_toolkit()` | read_file / write_file / list_directory / file_search |
| `interactive_bash_toolkit()` | 交互式 bash（持久 shell 会话） |
| `safe_code_interpreter_toolkit()` | 沙箱化 Python 执行（stdout/stderr） |

**手动上下文工具**：DeepAgent 暴露 `add_context(content, key)` / `delete_context(key)` 供 agent 跨轮次保留重要信息（写进 `context_manager`）。

**状态 channel**（与 [05 graph 的 reducer](/concepts/graph/mechanism) 互链，【事实】）：
- `messages: Annotated[list[BaseMessage], add_messages]` — 对话累积；
- `intermediate_steps: Annotated[list, operator.add]` — 工具执行记录累积；
- `context_manager` — 持久化工作记忆。

> 这说明 05 讲的 reducer（`operator.add`/`add_messages`）在真实框架里就是 `messages`、`intermediate_steps` 等键的合并规则——抽象概念落到真实现。

## 源码级：`create_deep_agent` 可运行调用

以下代码依据 LangChain `deepagents` 公开 API（【事实】；具体签名以官方为准）。

```python
# 安装：pip install deepagents langchain
from deepagents import create_deep_agent, fs_toolkit, interactive_bash_toolkit
from deepagents.middleware import ContextSummarizationMiddleware, SubAgent
from langchain.chat_models import init_chat_model

model = init_chat_model("openai:gpt-4o")

# ① 三个预置 toolkit 直接解包进 tools
tools = [
    *fs_toolkit(),                 # 文件系统读写
    *interactive_bash_toolkit(),   # 持久 shell 会话
    # *safe_code_interpreter_toolkit(),  # 沙箱化 Python（可选）
]

# ② 子 agent：包装成"工具"供父 agent 调用
sub_calculator = create_deep_agent(
    model=model, tools=[],
    system_prompt="你是计算专家，只做数学计算。",
)

agent = create_deep_agent(
    model=model,
    tools=tools,
    # ③ 中间件：上下文自动总结（超 30 条消息即压缩，防窗口膨胀）
    middleware=[ContextSummarizationMiddleware(max_messages=30)],
    subagents=[SubAgent(
        name="calculator_agent",
        agent=sub_calculator,
        description="用于复杂数学计算。输入应是清晰的问题陈述。",
    )],
    system_prompt="你是主 agent，负责拆解任务并调度子 agent。",
)

# ④ 直接可 invoke（内部是 LangGraph 图）
result = agent.invoke({"messages": [("user", "帮我重构 utils.py 并跑通测试")]})
print(result["messages"][-1].content)
```

**这段代码印证了三条主轴机制**：

| 代码里的东西 | 对应主轴机制 |
|---|---|
| `middleware=[ContextSummarizationMiddleware(30)]` | 02 context 的 compaction（超阈值压缩） |
| `subagents=[SubAgent(...)]` 被包装成工具 | 04/05 的"子 agent 作为节点/工具" |
| `messages` / `intermediate_steps` 用 reducer 合并 | 05 graph 的 reducer 落真实键 |

**手动上下文管理**：agent 可调用 `add_context(content, key)` / `delete_context(key)` 跨轮次保留信息（写进 `context_manager`）。

### 中间件链配置（+1 真实代码块）

多个中间件按注册顺序**环绕**每次模型调用（onion 模型），顺序决定横切行为：

```python
# 【示意实现】中间件链：顺序 = 横切执行顺序
from deepagents.middleware import (
    ContextSummarizationMiddleware,   # 超阈值压缩上下文
    TodoListMiddleware,               # 注入/维护待办清单
)

agent = create_deep_agent(
    model=model,
    tools=tools,
    middleware=[
        TodoListMiddleware(),                      # ① 先进：注入计划
        ContextSummarizationMiddleware(max_messages=30),  # ② 后进：临近调用前压缩
    ],
)
# 调用链：before_model(TodoList) → before_model(Summarize) → LLM
#         → after_model(Summarize) → after_model(TodoList)
```

### 子 agent 编排（LangGraph 视角，+1 真实代码块）

DeepAgent 内部就是一张 LangGraph 图：主 agent 是"规划+调度"节点，子 agent 被包装成可调用工具。

```python
# 【示意实现】把子 agent 显式接成图的节点（概念示意，API 以官方为准）
from langgraph.graph import StateGraph, START, END
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]   # reducer：消息累积，不是覆盖
    todo: list                                 # 计划清单

def planner(state: State):
    return {"todo": ["读 utils.py", "重构", "跑测试"]}

def executor(state: State):
    # 内部可调用 calculator_agent（子 agent 作为工具）
    return {"messages": [("assistant", "executed step")]}

g = StateGraph(State)
g.add_node("planner", planner)
g.add_node("executor", executor)
g.add_edge(START, "planner")
g.add_conditional_edges("planner", lambda s: "executor" if s["todo"] else END,
                        {"executor": "executor", END: END})
g.add_edge("executor", END)
app = g.compile(checkpointer=MemorySaver())   # 挂 checkpointer 可续跑
```

::: info 【事实】
来源：[CSDN《LangChain deepagents 实践》](https://blog.csdn.net/weixin_44733966/article/details/156938858)（[S10](/practice/sources)）+ [LangChain 官方 API 文档](https://docs.langchain.com/oss/python/deepagents/overview)。上述调用为 **【示意实现】**（依来源归纳，非原文逐字复制，签名以官方为准）；"凸显 graph+loop"是本体系的结构化定位（【推断】）。详见 [事实源清单](/practice/sources)。
:::

## 局限与不适用场景

| 局限 | 说明 | 何时别用 |
|---|---|---|
| 生态耦合 | 构建在 LangChain / LangGraph 之上，版本一并演进，升级需整体跟 | 想避开 LangChain 依赖时 |
| 抽象层较多 | middleware / subagent / toolkit 多层嵌套，**调试链路长** | 简单单循环任务 |
| 嵌套放大成本 | 子 agent 作为工具会带来额外模型调用，**token 与延迟随嵌套层数放大** | 成本敏感或低延迟场景 |

**替代方案**：轻量单循环 → 直接用 [05 graph](/concepts/graph) 的 StateGraph 或裸 loop；需要完整权限外壳 → [Claude Code](/instances/claude-code) / [Codex](/instances/codex)。

## 常见坑与反模式

- **坑① 不挂 checkpointer 跑长任务**：进程中断即**全部丢失**，无法续跑。`compile(checkpointer=...)` 是长任务的必需品。
- **坑② 中间件顺序随手放**：中间件按注册顺序环绕调用，**顺序错会逻辑错**——例如把压缩放在"注入待办"之后，会把刚注入的计划一起压掉。
- **坑③ 子 agent 无节制嵌套**：subagent 里再开 subagent，token 指数上升。应限制嵌套深度并给每层设预算。
- **坑④ `messages` 忘了声明 reducer**：用普通 `list` 字段会被**整体覆盖**（历史丢失），必须 `Annotated[list, add_messages]`（见 [5-1 reducer](/concepts/graph/mechanism)）。

## 小测验

::: details 点击展开题目与答案
**Q1（选择）**：DeepAgent 是基于哪个图框架构建的？  
A. React　B. LangGraph　C. Next.js  
✅ B。它用 LangGraph 的 StateGraph 做编排。

**Q2（判断）**：DeepAgent 的上下文自动总结，是为了把窗口撑得更大。  
❌ 错。是为了**防止窗口被长任务膨胀**，压缩后保住预算（呼应 02 context）。

**Q3（选择）**：`create_deep_agent` 的价值是？  
A. 必须手写所有节点　B. 一行建出基于图的复杂 agent　C. 只能做单循环  
✅ B。
:::

## 三档自检

| 档位 | 你能做到 |
|---|---|
| 了解 | 说出 DeepAgent 基于 LangGraph，凸显 graph+loop |
| 熟悉 | 能解释"规划节点 → 子 agent → 上下文总结"的中间件时序 |
| 精通 | 能建一个带规划 + 子 agent + 上下文总结的可跑工程 |

> 上一实例：[Hermes](./hermes) ｜ 相关概念：[04 loop](/concepts/loop) · [05 graph](/concepts/graph) ｜ 下一实例：[OpenClaw](./openclaw)
