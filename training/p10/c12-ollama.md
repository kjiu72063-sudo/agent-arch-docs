---
title: C12 · Ollama 自定义模型 + 前缀缓存/批处理吞吐优化
---

# C12 · Ollama 自定义模型 + 前缀缓存/批处理吞吐优化

::: tip 案例信息
**所属 Part**：[Part 6 · 部署与推理优化](/training/p6/01-challenges) ｜ **难度**：综合 ｜ **耗时**：60–100 分钟
**对应讲义**：[6-7 Ollama 部署全流程](/training/p6/07-ollama)、[6-10 其他部署方案](/training/p6/10-others)、[6-8 vLLM 深入](/training/p6/08-vllm-pagedattention)
**前置**：[C11](/training/p10/c11-vllm-fastapi)（已跑过 vLLM 部署），建议有 [C09](/training/p10/c09-whitebox-distill) 的 LoRA adapter
:::

::: warning 成本：本案例只租 1 张卡，约 ¥3–8
| 项 | 内容 |
|---|---|
| **需要几张卡** | **1 张**（24 GB 档足够；若只在 CPU 上跑 0.6B，**甚至可以不租卡**） |
| **预估费用** | 按量计费 **约 ¥3–8**（主要成本是服务运行时长） |
| **省钱姿势** | ① **用最小的模型**（`qwen3:0.6b`）做演示——Ollama 的机制与模型大小无关<br/>② **CPU 也能跑 0.6B**（小模型 + 量化后），可以考虑在**无卡模式**下完成大部分步骤<br/>③ 吞吐对比**只跑 3–5 次请求**取均值，不要长时间压测<br/>④ **无卡模式**写 Modelfile、装 Ollama、读文档<br/>⑤ 做完**立刻停服务 + 关机** |
:::

::: info 这道题与 C11 是一对反例
[C11 的 vLLM](/training/p10/c11-vllm-fastapi) 是"**高吞吐、高并发、专业部署**"；
本案例的 Ollama 是"**轻量、易用、个人/小项目**"。
**同一个模型，两条路线，你得说清什么时候用哪个。**
:::

## ① 题目

> 用 **Ollama** 部署模型，并做一轮吞吐观察，要求：
>
> 1. **装好 Ollama**（云上用一键脚本或本地下载上传），跑通 `ollama run`;
> 2. **用 Modelfile 创建一个自定义模型**：挂上 LoRA adapter（`ADAPTER`）+ 设参数 + 写 `SYSTEM` + **配 `TEMPLATE`**；
> 3. **说清 `TEMPLATE` 为什么必须与训练时一致**——不一致会怎样；
> 4. **用 HTTP API**（端口 11434）调一次 `/api/chat`；
> 5. **观察吞吐**：连续发几次相同前缀的请求，说明"**前缀缓存**"（prefix caching）在其中的作用；
> 6. **综合环节**：与 [C11 的 vLLM](/training/p10/c11-vllm-fastapi) 做**路线对比**，给出"什么时候选 Ollama、什么时候选 vLLM"的结论。

**一句话目标**：把"装个 Ollama 玩一玩"升级成"**会自定义模型 + 懂它和 vLLM 的定位差异**"。

## ② 你会练到什么

| 技能点 | 对应小节 |
|---|---|
| **Ollama 三种安装方式**及云端推荐做法 | [6-7](/training/p6/07-ollama) · 安装 |
| **Modelfile 的完整字段**：`FROM` / `ADAPTER` / `PARAMETER` / `SYSTEM` / `TEMPLATE` | [6-7](/training/p6/07-ollama) · §(5) 自定义模型 |
| **GGUF 与量化** | [6-7](/training/p6/07-ollama) |
| **HTTP API**：`/api/generate` / `/api/chat`（11434） | [6-7](/training/p6/07-ollama) · §(6) |
| **前缀缓存与批处理**在吞吐里的作用 | [6-8](/training/p6/08-vllm-pagedattention)、[6-10](/training/p6/10-others) |
| **两条部署路线的取舍** | [6-7](/training/p6/07-ollama) · §(8) 适用场景 |

## ③ 前置条件

| 项 | 要求 | 怎么核对 |
|---|---|---|
| 环境 | C01 已完成；能上网（装 Ollama） | `curl -I https://ollama.com` |
| Ollama | **已装**（未装则按步骤 1） | `ollama --version` |
| **LoRA adapter**（可选） | [C09](/training/p10/c09-whitebox-distill) 或 [C05](/training/p10/c05-lora-sft) 的产物 | `ls /root/autodl-tmp/output/.../adapter_model.safetensors` |
| **GGUF 模型**（可选） | 若走"自定义 GGUF"路线 | 用 modelscope 下载 |
| 端口 | 11434 可访问（本地需转发） | `ssh -L 11434:127.0.0.1:11434 ...` |
| 磁盘 | 数据盘 ≥ 10 GB（模型文件） | `df -h` |
| **省钱** | 小模型 + 少请求 | — |

::: tip `Modelfile` 的拼写
讲义 [6-7](/training/p6/07-ollama) 源材料里多处把它拼成了 `Modulefile`——
**官方文件名是 `Modelfile`**（无 `u`）。命令里写错会找不到文件。
:::

## ④ 分步操作

### 步骤 1 · 装 Ollama（云端推荐"本地下载上传"）

```bash
# 控制台切「无卡模式」（装软件不需要卡）→ SSH 进去

# 方式 B（推荐）：云主机网络对境外限速，先下到本地再传 / 或用加速
source /etc/network_turbo
wget https://ollama.com/download/ollama-linux-amd64.tgz
sudo tar -C /usr -xzf ollama-linux-amd64.tgz

# 启动服务
ollama serve &
ollama --version
```

**这一步在选什么**

| 方式 | 做法 | 为什么这么选 |
|---|---|---|
| **A. Windows exe** | 官网下载安装 | 本地开发最省事；**云上没有图形界面，不适用** |
| **B. Linux 脚本 / 手动下载**（推荐） | 一键脚本，或 `wget` + `tar` | **云上可控**：能配合 `network_turbo`，不怕脚本超时 |
| **C. Docker** | `docker run ollama/ollama` | 有 Docker 时干净；但要处理镜像拉取与 GPU 直通 |
| **先 `network_turbo`** | 开学术加速 | 同 [C02](/training/p10/c02-model-download-webui)：不加速会慢到超时 |

::: warning `ollama serve` 是前台进程
`ollama serve &` 用 `&` 放后台，或另开一个 `tmux`/终端。
**直接 `ollama serve` 会占住当前终端**——后面就没法敲别的命令了。
:::

> 🖼 **截图槽 `c12-01`** — 应截：`ollama --version` 的输出 + `ollama serve` 的启动日志
> 文件名：`c12/01-install.png`

### 步骤 2 · 拉一个基础模型并跑通

```bash
ollama pull qwen3:0.6b        # 自动下载
ollama run qwen3:0.6b         # 进入交互
# 输入：你好
# /bye 退出
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`pull` 先下再 run** | 显式下载 | 想看到下载过程、或离线前先备好 |
| **直接 `run`** | run 会自动 pull | 最省事；**但下载过程与交互混在一起**，不好观察 |
| **选 0.6B** | 最小档 | 演示机制用，省显存省钱；**机制与模型大小无关** |
| `ollama list` | 看本地有哪些模型 | 确认下载完成 |
| `ollama rm <模型>` | 删除 | 磁盘紧张时清理 |

**预期**：进入交互模式，能收到回答；`ollama list` 能看到模型。

> 🖼 **截图槽 `c12-02`** — 应截：`ollama run` 的交互（问题 + 模型回答）+ `ollama list`
> 文件名：`c12/02-run.png`

### 步骤 3 · 写 Modelfile 创建自定义模型

```bash
cat > Modelfile <<'EOF'
FROM qwen3:0.6b

# 挂 LoRA adapter（若有 C05/C09 的产物）
ADAPTER ./lora-weights

# 参数
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 32768
PARAMETER num_predict 2048

# 系统提示词
SYSTEM """你是一名专业的出行客服助手，回答要简洁、准确、有礼貌。"""

# 对话模板 —— 必须与训练时一致！
TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
"""
EOF

ollama create small_qwen -f ./Modelfile
ollama run small_qwen
```

**这一步在选什么**

| 字段 | 作用 | 为什么这么写 / 常见错误 |
|---|---|---|
| **`FROM qwen3:0.6b`** | 基座 | 也可以 `FROM ./xxx.gguf`（自备 GGUF，见步骤 4） |
| **`ADAPTER ./lora-weights`** | **挂 LoRA adapter** | ⚠️ 讲义配套的 `Modulefile` 示例**实际没有 `ADAPTER` 行**——想用 LoRA 必须自己加 |
| **`PARAMETER temperature 0.3`** | 采样温度 | 客服场景要稳定，温度调低。**可被请求参数覆盖** |
| **`PARAMETER num_ctx`** | 上下文窗口 | 与模型能力匹配；**设太大吃显存**（[9-B §2](/training/p9/B-formula-card)） |
| **`PARAMETER num_predict`** | 最大生成长度 | 防"话痨"；也可请求级覆盖 |
| **`SYSTEM """..."""`** | 系统提示词 | 角色设定。**生产里常把业务规范写这里** |
| **`TEMPLATE """..."""`** | 对话拼接模板 | ⭐ **最容易出错、后果最严重的一项** |

::: danger `TEMPLATE` 与训练时不一致 = 效果直接崩
模型是在**特定格式**下训练的（`<|im_start|>role ... <|im_end|>`）。
Ollama 推理时会**按 `TEMPLATE` 拼 prompt**——**拼法一变，模型收到的就不是它熟悉的输入**。

表现：答非所问、输出乱码、重复特殊 token、不停输出。
**所以本地微调后拿给 Ollama 用，`TEMPLATE` 必须照抄训练时的模板。**
:::

::: warning 课程源码里的一处不一致
[6-7](/training/p6/07-ollama) 配套的 `Modulefile` 示例**没有 `ADAPTER` 行**——
那意味着它其实**没挂 LoRA**，只是改了参数与提示词。
**本步骤补上了 `ADAPTER`**。如果你照抄讲义那个文件却期待"微调效果"，会觉得"微调白做了"——
**原因就是 adapter 没挂上。**
:::

**预期**：`ollama create` 成功；`ollama run small_qwen` 能对话，且**带客服口吻**（SYSTEM 生效）。

> 🖼 **截图槽 `c12-03`** — 应截：完整的 `Modelfile`（含 `ADAPTER` / `SYSTEM` / `TEMPLATE` 三段）
> 文件名：`c12/03-modelfile.png`

> 🖼 **截图槽 `c12-04`** — 应截：`ollama create` 输出 + `ollama run small_qwen` 的回答
> 文件名：`c12/04-custom-run.png`

### 步骤 4 · （可选）换成自备 GGUF

```bash
# 用 modelscope 下一个 GGUF
pip install modelscope
modelscope download --model <某GGUF模型> --local_dir ./gguf_model

# Modelfile 改成指向 GGUF
# FROM ./gguf_model/xxx.gguf
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`FROM qwen3:0.6b`**（Ollama 库） | 用官方已打包的模型 | 最省事；**但你不能改量化档** |
| **`FROM ./xxx.gguf`**（自备） | 用自己下载/转换的 GGUF | **可自由选量化档（Q4_K_M 等）**；也能用官方库没有的模型 |
| GGUF 从哪来 | 下载现成的 / 自己转换 | 转换要 `llama.cpp` 工具链；**多数情况直接下现成的** |

::: tip GGUF 是什么
GGUF 是 llama.cpp 系的模型文件格式，**支持多种量化档**（Q4_K_M / Q5_K_M / Q8_0…）。
Ollama 底层就是 llama.cpp，所以它吃 GGUF。
**"量化档"直接决定显存/内存占用与质量**——这是 Ollama 侧最实用的一档调节。
:::

**预期**：能用自备 GGUF 创建模型并跑起来（选做，没做不影响后续）。

> 🖼 **截图槽 `c12-05`** — 应截：（选做）GGUF 下载完成 + `FROM ./xxx.gguf` 的 Modelfile
> 文件名：`c12/05-gguf.png`

### 步骤 5 · 用 HTTP API 调用（端口 11434）

```bash
# 非流式
curl http://localhost:11434/api/chat -d '{
  "model": "small_qwen",
  "messages": [{"role": "user", "content": "退改签怎么处理？"}],
  "stream": false
}'

# 流式
curl http://localhost:11434/api/chat -d '{
  "model": "small_qwen",
  "messages": [{"role": "user", "content": "数到五"}],
  "stream": true
}'
```

**这一步在选什么**

| 端点 | 用途 | 特点 |
|---|---|---|
| **`/api/chat`** | **多轮对话**（推荐） | 传 `messages` 数组，**能带 system/多轮历史** |
| `/api/generate` | 单次补全 | 传 `prompt` 字符串；适合简单场景 |
| **`stream: true/false`** | 流式开关 | 默认 **true**；要一次性结果就显式 `false` |
| **端口 11434** | Ollama 默认端口 | 云上要 `ssh -L 11434:...` 才能本地访问 |

**预期**：两条 curl 都返回 JSON；流式能看到多行 JSON 片段。

> 🖼 **截图槽 `c12-06`** — 应截：curl 打 11434 的返回（非流式 JSON）
> 文件名：`c12/06-api.png`

### 步骤 6 · 综合环节：观察前缀缓存与吞吐

**前缀缓存（prefix caching）**：多次请求如果**开头（system + 模板）相同**，
框架可以**复用这部分的 KV cache**，省去重复计算。

做个小实验——**同一个 system 前缀**，连发 3 次：

```bash
for i in 1 2 3; do
  curl -s http://localhost:11434/api/chat -d '{
    "model": "small_qwen",
    "messages": [
      {"role": "system", "content": "你是一名专业的出行客服助手。"},
      {"role": "user", "content": "第 '"$i"' 问：退改签怎么处理？"}
    ],
    "stream": false
  }' | python -c "import sys,json; d=json.load(sys.stdin); print('eval_count:', d.get('eval_count'), 'total_duration:', d.get('total_duration'))"
done
```

**看什么**：

| 指标 | 含义 | 期望现象 |
|---|---|---|
| **`total_duration`** | 端到端耗时 | 后续请求**常比第一次略快**（前缀已缓存） |
| **`eval_count`** | 生成的 token 数 | 看生成量是否稳定 |
| **首次 vs 后续** | 冷启动 vs 命中缓存 | **第一次最慢**（要预热/编译） |

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **固定 system 前缀** | 让前缀缓存有得可复用 | 前缀一变，缓存失效，省不下来 |
| **只跑 3–5 次** | 看趋势即可 | 这不是压测，**别为了"测准"挂一小时** |
| **首次单独看** | 冷启动含模型加载/编译 | 把首次当基线，别混进均值 |
| **Ollama 的批处理能力弱** | 单请求为主 | 真正高并发看 vLLM（[C11](/training/p10/c11-vllm-fastapi)） |

::: warning "前缀缓存"不是万能加速
它只省**相同前缀**那部分计算。**每个请求的独有部分（用户问题、生成）照算不误。**
所以：
- **适合**：固定 system + 模板、多轮对话的后续轮次、few-shot 示例固定
- **不适合**：每个请求 prompt 都完全不同
:::

**预期**：能观察到首次较慢、后续略快；能解释"省的是前缀那部分"。

> 🖼 **截图槽 `c12-07`** — 应截：3 次请求的耗时对照（终端或表格）
> 文件名：`c12/07-prefix-cache.png`

### 步骤 7 · 综合环节：Ollama vs vLLM 路线对比

| 维度 | **Ollama** | **vLLM** |
|---|---|---|
| 定位 | 个人 / 小项目 / 快速验证 | **生产 / 高并发 / 高吞吐** |
| 易用性 | ⭐⭐⭐ 一条命令搞定 | ⭐⭐ 要写配置、起服务 |
| 自定义模型 | **Modelfile 极简单** | 要改 YAML / 代码 |
| 吞吐 | 一般（单请求为主） | **强**（PagedAttention + 连续批处理） |
| 显存效率 | 中（GGUF 量化灵活） | **高**（KV cache 分页） |
| 部署形态 | 单机小服务 | 可多卡、可横向扩展 |
| 适合场景 | 本地开发、演示、隐私要求高的小规模 | 产品线上、API 服务、多用户 |

::: tip 一句话决策
**先问一句：要服务几个人？**
- 自己用 / 小团队 / 演示 → **Ollama**
- 对外产品 / 多并发 / 要指标 → **vLLM**

**两者不是新旧的替代关系，是不同量级的工具。**
:::

**预期**：能给出带条件的路线建议，而非"vLLM 更好"。

> 🖼 **截图槽 `c12-08`** — 应截：你写的 Ollama vs vLLM 对比表
> 文件名：`c12/08-compare.png`

### 步骤 8 · 停服务 + 关机

```bash
# Ctrl+C 停 ollama serve；或
pkill -f "ollama serve"
```

然后**回控制台点「关机」**。

> 🖼 **截图槽 `c12-09`** — 应截：控制台显示「已关机」
> 文件名：`c12/09-shutdown.png`

## ⑤ 预期结果与判定标准

| # | 检查项 | 判定标准（必须看到） |
|---|---|---|
| 1 | Ollama 已装 | `ollama --version` 有输出 |
| 2 | 基础模型跑通 | `ollama run` 能对话，`ollama list` 能看到 |
| 3 | **Modelfile 创建成功** | `ollama create` 无报错 |
| 4 | **`ADAPTER` 挂上了** | Modelfile 里有 `ADAPTER` 行并能解释其作用 |
| 5 | **`SYSTEM` 生效** | 自定义模型的回答带设定的角色口吻 |
| 6 | **`TEMPLATE` 写对** | 模板包含 role 标记，且与训练格式一致 |
| 7 | **知道模板错的后果** | 能说清"模板不一致 → 答非所问/乱码" |
| 8 | **API 调通** | curl 打 11434 `/api/chat` 返回 JSON |
| 9 | **`stream` 参数说得出** | 能解释默认流式与显式 `false` 的差别 |
| 10 | **前缀缓存做了实验** | 有 3 次请求的耗时对照 |
| 11 | **缓存作用解释对** | 能说清"只省相同前缀部分" |
| 12 | **路线对比有结论** | 给出带条件的 Ollama vs vLLM 建议 |
| 13 | **理解性目标：不是替代** | 能说清两者是不同量级的工具，非新旧关系 |
| 14 | 服务已停 + 已关机 | 控制台「已关机」 |

> 第 4、6、7、11、13 项是重点：**装个 Ollama 谁都会；"Modelfile 里哪几行真正决定效果""两条路线的取舍"才是这道题的价值。**

## ⑥ 常见报错

| 报错 | 原因 | 处置 |
|---|---|---|
| `ollama: command not found` | 没装 / 装到了别的 PATH | 重新 `tar -C /usr -xzf`；确认 `/usr/bin/ollama` 存在 |
| **`Modelfile` 找不到** | 文件名拼成 `Modulefile`，或路径不对 | 官方是 **`Modelfile`**；`-f` 给对路径 |
| **自定义模型"没微调效果"** | Modelfile 里**漏了 `ADAPTER` 行** | 补 `ADAPTER ./lora-weights` |
| 输出乱码 / 答非所问 | `TEMPLATE` 与训练时不一致 | 照抄训练用的模板；检查 role 标记 |
| 回答太啰嗦 / 太随机 | `temperature` 太高 | 降 `PARAMETER temperature`（如 0.3） |
| 上下文不够用 | `num_ctx` 太小 | 增大 `num_ctx`（注意吃显存） |
| 下载极慢 / 超时 | 云上没加速 | `source /etc/network_turbo` 后重试 |
| `ollama serve` 卡住终端 | 前台进程 | 用 `&` 或另开终端 |
| 本地连不上 11434 | 端口没转发 | `ssh -L 11434:127.0.0.1:11434 ...` |
| API 返回缺少 `eval_count` | 用了 `/api/generate` 或流式未聚合 | 用 `/api/chat` + `stream:false`；流式时手动聚合 |
| 显存/内存不够 | 模型太大 / 量化档太低 | 换更小模型或更高压缩的 GGUF |
| `ADAPTER` 路径报错 | adapter 不是 PEFT 格式 / 路径错 | 确认是 [C05/C09](/training/p10/c05-lora-sft) 产出的 adapter 目录 |

## ⑦ 延伸

1. **换量化档**：用不同 GGUF（Q4_K_M vs Q8_0）各建一个模型，对比回答质量与占用。**量化档怎么影响效果？**
2. **对比 vLLM 同模型吞吐**：同一个 1.7B，用 [C11](/training/p10/c11-vllm-fastapi) 的 vLLM 与 Ollama 各发 10 个并发请求，看差距。**差距来自哪项技术？** → [6-8](/training/p6/08-vllm-pagedattention)
3. **开 Web UI**：`pip install open-webui` + `open-webui serve --port 6006`，把 Ollama 接上做图形界面。
4. **`/api/chat` 多轮**：在 `messages` 里带上历史，观察模型是否"记得上文"。
5. **写一个最小前端**：一个 HTML 页面调 11434，体验流式在前端的渲染。
6. **回到 [6-10 其他部署方案](/training/p6/10-others)**：把 Ollama、vLLM、llama.cpp、TGI 放在一起，做一张"选型决策树"。

---

> 上一案例：[C11 vLLM + FastAPI 部署微调后模型并调通](/training/p10/c11-vllm-fastapi) ｜ [案例库总览](/training/p10/) ｜ [Part 6 末页题目](/training/p6/11-mlops)
