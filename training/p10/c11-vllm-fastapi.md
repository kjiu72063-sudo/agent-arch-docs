---
title: C11 · vLLM + FastAPI 部署微调后模型并调通
---

# C11 · vLLM + FastAPI 部署微调后模型并调通

::: tip 案例信息
**所属 Part**：[Part 6 · 部署与推理优化](/training/p6/01-challenges) ｜ **难度**：基础 ｜ **耗时**：50–90 分钟
**对应讲义**：[6-9 vLLM + FastAPI 实战](/training/p6/09-vllm-fastapi)、[6-8 vLLM 深入：PagedAttention](/training/p6/08-vllm-pagedattention)、[6-6 服务化与 API 设计](/training/p6/06-api)
**前置**：[C05](/training/p10/c05-lora-sft) 或 [C09](/training/p10/c09-whitebox-distill)（有一个可部署的模型/合并权重）
:::

::: warning 成本：本案例只租 1 张卡，约 ¥3–8
| 项 | 内容 |
|---|---|
| **需要几张卡** | **1 张**（24 GB 档足够跑 1.7B；部署**只要一张卡**） |
| **预估费用** | 按量计费 **约 ¥3–8**（主要是服务运行时长的费用） |
| **省钱姿势** | ① **用一个小的模型**（1.7B）做部署演示——vLLM 的机制与模型大小无关，**别拿 7B 烧钱**<br/>② 服务起来后**只验证几次请求**就够，**不要挂着一整天**；验证完立刻停服务<br/>③ **无卡模式**写 FastAPI 脚本、装依赖、读代码（`pip install` 不需要卡）<br/>④ 做完**立刻控制台关机** |
:::

::: info 部署是"最容易被忽略的持续花钱项"
训练是一次性支出，**部署是按时长计费**——服务挂着不动也在花钱。
所以本案例的省钱重点不是"少跑一步"，而是**"验证完就停"**。
:::

## ① 题目

> 用 **vLLM + FastAPI** 把 [C05/C09](/training/p10/c05-lora-sft) 产出的模型**部署成一个能调的 HTTP 服务**，要求：
>
> 1. **跑通路径 a**：直接用 vLLM 的 **OpenAI 兼容接口**（端口 6006），用 OpenAI SDK 打一发；
> 2. **跑通路径 b**：写一个 **FastAPI 前端**（端口 6008），转发到 vLLM 后端，支持**流式输出**；
> 3. **说清两个端口、两个进程**的关系——这是本题最核心的认知；
> 4. 用 `curl` / `requests` **各验证一次**，并处理 `curl` 打到错端口的经典错误；
> 5. **综合环节**：给 FastAPI 加一个 `/health` 健康检查端点，并解释"为什么生产环境必须要它"。

**一句话目标**：把"模型能跑"变成"模型能以 API 形式被调用"，并**彻底搞清 6006 与 6008 谁是谁**。

## ② 你会练到什么

| 技能点 | 对应小节 |
|---|---|
| **vLLM 的 OpenAI 兼容接口**（`/v1/chat/completions`） | [6-9](/training/p6/09-vllm-fastapi) · 路径 a |
| **`llamafactory-cli api` 启动 vLLM 后端** 与 YAML 配置 | [6-9](/training/p6/09-vllm-fastapi) |
| **OpenAI SDK 指向本地服务**（`base_url` + `api_key="EMPTY"`） | [6-9](/training/p6/09-vllm-fastapi) |
| **FastAPI 转发 + SSE 流式**（`StreamingResponse` / `[DONE]`） | [6-9](/training/p6/09-vllm-fastapi) |
| **`extra_body` 传 vLLM 私有参数**（如 `top_k`） | [6-9](/training/p6/09-vllm-fastapi) |
| **两进程两端口**的关系 | [6-6](/training/p6/06-api) |

## ③ 前置条件

| 项 | 要求 | 怎么核对 |
|---|---|---|
| 环境 | C01 已完成；**已装 `vllm` / `fastapi`** | `python -c "import vllm; print(vllm.__version__)"` |
| 依赖版本 | 按 [6-9](/training/p6/09-vllm-fastapi)：`vllm==0.8.2`、`flash-attn==2.7.2.post1`、`fastapi` | `pip list` |
| 模型 | **1.7B** 级别模型（含合并权重或 adapter 可加载的路径） | `ls /root/autodl-tmp/models/.../Qwen3-1.7B` |
| 配置 | 有一份推理 YAML（`qwen3_1_7b.yaml`） | `cat examples/inference/qwen3_1_7b.yaml` |
| GPU | ≥ 16 GB（1.7B + vLLM 的 KV cache 预留） | `nvidia-smi` |
| 端口 | 6006（vLLM）、6008（FastAPI）**都要能转发** | 本地能 `ssh -L 6006:... -L 6008:...` |
| **省钱** | 验证完立刻 `Ctrl+C` 停服务 | — |

::: tip 为什么选 1.7B 而不是 7B
部署案例的**考点是"机制"**（OpenAI 兼容、流式、转发），**不是吞吐竞赛**。
1.7B 起得快、占得少、验证快——**同样的知识，十分之一的钱**。
:::

## ④ 分步操作

### 步骤 1 · 无卡模式：先把推理 YAML 与依赖备好

```bash
# 控制台切「无卡模式」→ SSH 进去
conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory

# 装依赖（不需要卡）
pip install vllm==0.8.2 fastapi

# 写/改推理 YAML
vi examples/inference/qwen3_1_7b.yaml
```

```yaml
# qwen3_1_7b.yaml
model_name_or_path: /root/autodl-tmp/models/hub/models/Qwen/Qwen3-1.7B
template: qwen3
infer_backend: vllm
vllm_config:
  dtype: float16            # ⚠️ 原文示例写的是 float32，推理不常见，应改 float16
  gpu_memory_utilization: 0.9
  max_model_len: 8192
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`infer_backend: vllm`** | 用 vLLM 做后端 | 也可以选 `huggingface` 后端，但那样**没有 PagedAttention 的收益**（[6-8](/training/p6/08-vllm-pagedattention)） |
| **`dtype: float16`** | 权重与计算精度 | ⚠️ **讲义原文示例写 `float32`，推理几乎不用**——显存翻倍且更慢。**改成 `float16`** |
| **`gpu_memory_utilization: 0.9`** | vLLM 可用的显存比例 | 0.9 是常用值；**留 0.1 给 CUDA 上下文**，设 1.0 容易起不来 |
| **`max_model_len: 8192`** | 最大上下文长度 | 影响到 KV cache 的预留量。**设太大 = 预留太多 = 起不来**（[9-B §2](/training/p9/B-formula-card)） |
| `template: qwen3` | 对话模板 | **必须与模型匹配**，否则输出劣化（[C02](/training/p10/c02-model-download-webui) 的老坑） |

> 🖼 **截图槽 `c11-01`** — 应截：`qwen3_1_7b.yaml` 的内容（含 `infer_backend` 与 `dtype: float16`）
> 文件名：`c11/01-infer-yaml.png`

### 步骤 2 · 启动路径 a：vLLM 的 OpenAI 兼容服务（端口 6006）

```bash
# 回控制台开机
conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory

API_PORT=6006 llamafactory-cli api \
  examples/inference/qwen3_1_7b.yaml \
  infer_backend=vllm vllm_enforce_eager=true
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`llamafactory-cli api`** | 启动 API 服务 | 与 `webui`（图形）、`train`（训练）并列的第三个入口 |
| **`API_PORT=6006`** | 服务端口 | 强制 6006，与讲义统一，**便于记忆与端口转发** |
| `infer_backend=vllm` | 命令行覆盖 YAML | 双保险，确保走 vLLM |
| **`vllm_enforce_eager=true`** | 禁用 CUDA Graph 捕获 | **调试期更稳**：CUDA Graph 在某些环境下会卡死或报错；跑通后可关掉换性能 |
| **路径 a 的意义** | 直接用 vLLM 自带的 OpenAI 兼容接口 | **免写代码就能被 OpenAI SDK 调用**——这是 vLLM 最大的便利 |

**预期**：终端打印 vLLM 启动日志（含 `Uvicorn running on ... 6006`）；**服务已就绪**。

**本地开隧道**（在你自己电脑上，不是服务器）：

```bash
ssh -L 6006:127.0.0.1:6006 -L 6008:127.0.0.1:6008 -p <端口> root@<地址>
```

> 🖼 **截图槽 `c11-02`** — 应截：vLLM 服务启动完成的终端输出（能看到 6006）
> 文件名：`c11/02-vllm-start.png`

### 步骤 3 · 用 OpenAI SDK 验证路径 a

```python
# test_openai_sdk.py
from openai import OpenAI

client = OpenAI(
    api_key="EMPTY",                              # 本地服务不校验 key，但不能为空
    base_url="http://localhost:6006/v1",          # ⚠️ 指到 vLLM 的 6006
)

resp = client.chat.completions.create(
    model="qwen3",                                # 模型名随意，服务端只加载了一个
    messages=[{"role": "user", "content": "用一句话解释什么是 PagedAttention。"}],
    max_tokens=128,
)
print(resp.choices[0].message.content)
```

```bash
python test_openai_sdk.py
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`api_key="EMPTY"`** | 本地服务不校验，但 SDK 要求非空 | 留空字符串会报错 |
| **`base_url=...6006/v1`** | 指到 vLLM 的 OpenAI 兼容路由 | **`/v1` 是关键后缀**，少写会 404 |
| `model="qwen3"` | 服务端只加载一个模型，名字不敏感 | 生产多模型时才需要精确匹配 |

::: tip 为什么用 OpenAI SDK 而不是 `requests`
**因为它证明"兼容"是真的**：任何按 OpenAI 协议写的代码，**改一行 `base_url` 就能接上**。
这就是 [6-6](/training/p6/06-api) 讲的"接口标准化"的价值。
:::

**预期**：终端打印模型回答（中文正常）。

> 🖼 **截图槽 `c11-03`** — 应截：`test_openai_sdk.py` 的输出（含模型回答）
> 文件名：`c11/03-path-a-sdk.png`

### 步骤 4 · 写 FastAPI 前端（端口 6008）——路径 b

```python
# fastapi_server.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ⚠️ 这里是 6006（vLLM 后端），不是 6008
upstream = AsyncOpenAI(api_key="EMPTY", base_url="http://localhost:6006/v1")

class GenerateRequest(BaseModel):
    prompt: str
    model: str = "qwen3"
    is_stream: bool = False
    max_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = -1
    system_message: str | None = None

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/generate")
async def generate(req: GenerateRequest):
    messages = []
    if req.system_message:
        messages.append({"role": "system", "content": req.system_message})
    messages.append({"role": "user", "content": req.prompt})

    if not req.is_stream:
        r = await upstream.chat.completions.create(
            model=req.model, messages=messages,
            max_tokens=req.max_tokens, temperature=req.temperature,
            top_p=req.top_p,
            extra_body={"top_k": req.top_k},      # vLLM 私有参数走 extra_body
        )
        return {"text": r.choices[0].message.content}

    async def event_stream():
        stream = await upstream.chat.completions.create(
            model=req.model, messages=messages, stream=True,
            max_tokens=req.max_tokens, temperature=req.temperature,
            top_p=req.top_p, extra_body={"top_k": req.top_k},
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {delta}\n\n"        # SSE 格式
        yield "data: [DONE]\n\n"                  # 结束标记

    return StreamingResponse(
        event_stream(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=6008)   # ⚠️ FastAPI 在 6008
```

```bash
python fastapi_server.py
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **两个进程两个端口** | vLLM=6006，FastAPI=6008 | ⭐ **本题核心**：FastAPI 是"前台"，vLLM 是"后台"，**前台转发到后台** |
| **`base_url=...6006`** | FastAPI 指向上游 vLLM | **在 FastAPI 里写 6006**；写 6008 就自己调自己了 |
| **`extra_body={"top_k": ...}`** | 传 vLLM 私有参数 | OpenAI 标准里没有 `top_k`，**必须塞 `extra_body`** 才能透传 |
| **SSE `data: ...\n\n`** | 流式格式 | 两个 `\n` 是 SSE 的分帧要求；**少一个前端就收不到** |
| **`[DONE]` 标记** | 流结束信号 | 前端靠它判断结束，**不发给前端就永远等下去** |
| `X-Accel-Buffering: no` | 禁用反向代理缓冲 | 有 Nginx 时不加这行，流式会被"攒一堆再发" |
| CORS 中间件 | 允许跨域 | 前端页面在别的端口时要它；**生产要收紧 origins** |
| **为什么要自己写 FastAPI** | 加业务逻辑 | 直接暴露 vLLM 也行（路径 a）；**路径 b 是为了加鉴权、限流、system prompt 注入、日志等** |

::: warning `dtype: float32` 这个坑会直接 OOM
讲义 [6-9](/training/p6/09-vllm-fastapi) 的 YAML 示例里写了 **`dtype: float32`**——
**推理用 fp32 极不常见**，显存直接翻倍，1.7B 也可能起不来。
步骤 1 已经改成 **`float16`**。**看到启动时显存吃满或 OOM，先查这个。**
:::

> 🖼 **截图槽 `c11-04`** — 应截：`fastapi_server.py` 里的关键两处（`base_url` 指向 6006、`uvicorn.run(... port=6008)`）
> 文件名：`c11/04-fastapi-ports.png`

### 步骤 5 · 验证路径 b：curl / requests 打 6008

```bash
# ⚠️ 注意端口是 6008，不是 6006
curl -X POST http://localhost:6008/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"你好，介绍一下你自己","max_tokens":64}'

# 流式
curl -N -X POST http://localhost:6008/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"数到五","is_stream":true,"max_tokens":64}'

# 健康检查
curl http://localhost:6008/health
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **端口写 6008** | FastAPI 的端口 | ⚠️ **讲义原文的 curl 示例把端口写成了 6006**——那是打到了 vLLM，绕过 FastAPI，**测不出路径 b** |
| `-N`（no-buffer） | curl 不缓冲 | 不加的话流式会被 curl 攒起来，看不到逐字效果 |
| `Content-Type: application/json` | 声明 JSON | 少它 / 写错 → FastAPI 报 422 |
| **先测 `/health`** | 确认服务活着 | 排错第一步：服务都没起，测别的没意义 |

::: danger 讲义原文有一处端口笔误
[6-9](/training/p6/09-vllm-fastapi) 的验证示例里，curl 打的是 `6006`——
**但 6006 是 vLLM 后端，路径 b 应该打 6008**。
**打 6006 会"成功"**（vLLM 也是 OpenAI 兼容接口），但**你验证的其实是路径 a，不是 FastAPI**。
**测试要打 6008**——这是本步骤最重要的提醒。
:::

**预期**：三条命令都返回正确结果；流式能看到逐段输出。

> 🖼 **截图槽 `c11-05`** — 应截：curl 打 **6008** 的返回（非流式 + 流式各一张）
> 文件名：`c11/05-path-b-curl.png`

### 步骤 6 · 综合环节：为什么生产必须有 `/health`

```bash
curl -i http://localhost:6008/health
# 期望：HTTP/1.1 200 OK + {"status":"ok"}
```

**它解决什么**：

| 场景 | 没有 `/health` | 有 `/health` |
|---|---|---|
| 服务刚启动、模型还在加载 | 请求超时，像"服务坏了" | 健康检查可先返回 `starting`，**区分"没起来"与"坏了"** |
| 容器编排（K8s） | 无法判断何时接流量 | **liveness / readiness 探针就靠它** |
| 上游 vLLM 挂了 | FastAPI 还"活着"，请求全超时 | 可以在 `/health` 里一并探上游，**快速暴露真故障** |
| 负载均衡 | 无法摘除坏实例 | 探针失败 → **自动摘除** |

::: tip 把健康检查做成"深度探针"
`/health` 只回 `ok` 是"浅探针"（进程活着）。
更好的做法是**顺便探一次上游 vLLM**（如发一个极小请求），叫"**深度探针**"——
**能发现"自己活着但后端死了"这种最坑的状态**。
:::

**预期**：`/health` 返回 200；能说清它在生产里的三个用途。

> 🖼 **截图槽 `c11-06`** — 应截：`curl -i /health` 的完整响应（含 200 与 JSON）
> 文件名：`c11/06-health.png`

### 步骤 7 · 停服务 + 关机（**省钱关键**）

```bash
# 在两个终端分别 Ctrl+C 停掉 FastAPI 与 vLLM
```

然后**回 AutoDL 控制台点「关机」**。

| 做法 | 结果 |
|---|---|
| **停服务 + 关机** | 停止计费 ✅ |
| 只停服务、忘记关机 | ⚠️ 实例仍在计费 |
| 关 SSH 窗口、服务还在后台 | ⚠️ 服务占着显存，实例也在计费 |

> 🖼 **截图槽 `c11-07`** — 应截：AutoDL 控制台显示「已关机」
> 文件名：`c11/07-shutdown.png`

## ⑤ 预期结果与判定标准

| # | 检查项 | 判定标准（必须看到） |
|---|---|---|
| 1 | YAML 正确 | `infer_backend: vllm`；`dtype` 是 **float16** 不是 float32 |
| 2 | **路径 a 起来了** | vLLM 服务在 6006 启动，日志可见 |
| 3 | **SDK 调通** | OpenAI SDK 打 6006 拿到回答 |
| 4 | **`/v1` 后缀在** | base_url 带了 `/v1` |
| 5 | **路径 b 起来了** | FastAPI 在 6008 运行 |
| 6 | **两进程两端口说得出** | 能说清 FastAPI(前台 6008) → vLLM(后台 6006) 的关系 |
| 7 | **FastAPI 里 base_url=6006** | 能指出"前端指后端"的方向 |
| 8 | **流式通了** | curl 能看到逐段输出（含 `[DONE]`） |
| 9 | **测的是 6008** | 验证路径 b 时端口正确，未被原文笔误带偏 |
| 10 | **`extra_body` 用对** | 能解释为什么 `top_k` 要走 `extra_body` |
| 11 | **`/health` 加了** | 返回 200 + JSON |
| 12 | **健康检查用途说得出** | 能给出 K8s 探针 / 上游探测等场景 |
| 13 | 服务已停 + 已关机 | 控制台「已关机」 |

> 第 6、9、10、12 项是重点：**"两个端口谁转发给谁"是这道题唯一真正要记牢的事。**

## ⑥ 常见报错

| 报错 | 原因 | 处置 |
|---|---|---|
| **`CUDA out of memory`（启动时）** | `dtype: float32` 或 `gpu_memory_utilization` 太高 / `max_model_len` 太大 | **改 `float16`**；降 util 到 0.85；降 `max_model_len` |
| **404 / 连不上** | `base_url` 少写 `/v1` 或端口错 | 补 `/v1`；确认打的是 6006（SDK）/ 6008（FastAPI） |
| **测路径 b 却"通过"了** | 打成了 6006（打到 vLLM 了） | **改成 6008**，才是测 FastAPI |
| `api_key` 报错 | 空字符串 | 写 `"EMPTY"` |
| 流式没有逐字效果 | 少了 `-N`，或被代理缓冲 | 加 `curl -N`；响应头加 `X-Accel-Buffering: no` |
| 流式前端一直不结束 | 没发 `[DONE]` | 补上结束标记 |
| `top_k` 不生效 / 报未知参数 | 放进了普通字段 | 放进 `extra_body` |
| SSE 分帧错乱 | `\n\n` 只写了一个 | 必须是两个换行 |
| 服务启动卡在 `Loading model` | 模型大 / 首次编译 CUDA Graph | 等一会；或 `vllm_enforce_eager=true` 跳过图捕获 |
| `ValidationError` / 422 | 请求体缺字段或类型不对 | 对照 `GenerateRequest` 的字段名与类型 |
| 浏览器跨域失败 | 没加 CORS 中间件 | 加 `CORSMiddleware`（生产记得收紧 origins） |
| 服务停了显存没释放 | 进程没真正退出 | `pkill -f uvicorn` / `pkill -f vllm`，再确认 `nvidia-smi` |

## ⑦ 延伸

1. **关掉 `vllm_enforce_eager`**：允许 CUDA Graph 捕获，看首 token 延迟与吞吐变化。**eager 与 graph 的取舍是什么？**
2. **压测一下**：写个小脚本并发打 10 个请求，观察 vLLM 的批处理效果。**为什么它比逐条串行快？** → [6-8](/training/p6/08-vllm-pagedattention)
3. **加深健康探针**：让 `/health` 顺手探一次上游 vLLM，返回真实的端到端状态。
4. **加一个鉴权**：给 FastAPI 加 `Authorization` 校验——**这就是"为什么不直接暴露 vLLM"的答案**（[6-6](/training/p6/06-api)）。
5. **换成 4-bit 量化模型**：把部署模型换成 [C06](/training/p10/c06-qlora-vs-lora) 量化后的版本，看显存与吞吐变化。**量化在部署侧的价值比训练侧更大？**
6. **接 [C12](/training/p10/c12-ollama)**：同样一个模型，用 Ollama 再部署一次，对比"轻量易用"与"高吞吐"两条路线。

---

> 下一案例：[C12 Ollama 自定义模型 + 前缀缓存/批处理吞吐优化](/training/p10/c12-ollama) ｜ [案例库总览](/training/p10/) ｜ [Part 6 末页题目](/training/p6/11-mlops)
