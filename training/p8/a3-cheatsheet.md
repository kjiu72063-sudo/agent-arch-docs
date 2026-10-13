---
title: A3 命令与配置速查
---

# A3 · 命令与配置速查

> 本页是**纯命令清单**：从环境安装到部署上线的全部可执行命令与关键配置。
> 来源：Part 1–6 各页的代码段（**非新内容**）。每条命令后的 `〔Lx Pxx〕` 为讲义页码，无标注者为配套代码资产。

## 1. 环境安装

### 1.1 基础环境

```bash
# 检查是否有 CUDA 工具包
nvcc -V

# 检查 CUDA 驱动
nvidia-smi

# Anaconda（Ubuntu/CentOS）
wget https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh
```
〔L1 P11–P12〕

```bash
# git
sudo apt install git        # Ubuntu
sudo yum install git        # CentOS
```
〔L1 P20〕

### 1.2 LLaMA-Factory

```bash
# 下载源码
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git

# 配置虚拟环境与 Python 版本
conda create -n llama_env python=3.11

# 安装依赖
cd LLaMA-Factory
pip install -e ".[torch,metrics]" --no-build-isolation
```

**扩展模块**：

```bash
pip install flash-attn --no-build-isolation     # 注意：V100 不支持该库
pip install bitsandbytes
pip install deepspeed==0.16.4                   # 根据 torch 版本，推荐与官网一致
pip install accelerate
```
〔L1 P20–P21〕

### 1.3 部署侧依赖

```bash
# vLLM + FastAPI
pip install vllm==0.8.2
pip install flash-attn==2.7.2.post1
pip install fastapi

# SGLang
pip install "sglang[all]>=0.4.6.post4" -i https://pypi.tuna.tsinghua.edu.cn/simple/
pip install flashinfer-python -i https://pypi.tuna.tsinghua.edu.cn/simple/

# Ollama Python SDK / WebUI
pip install ollama
pip install open-webui                          # 推荐 python3.11

# OpenVINO
pip install -U openvino

# 蒸馏环境
pip install peft==0.17.1 transformers==4.57.0 pandas==2.3.3 torch==2.5.1+cu124

# 其他
pip install galore-torch                        # GaLore
pip install auto_gptq                           # GPTQ 量化
```
〔L5 P50 / P54 / P62、`SGlang部署.ipynb`、`ollama与python交互.ipynb`、`requirements.txt`、L2 P50–P51〕

### 1.4 云环境（AutoDL）

```bash
# 学术加速
source /etc/network_turbo
```
〔L1 P13 / P15、L5 P27〕

## 2. 模型下载

```bash
# 魔搭社区
# https://www.modelscope.cn/models
# 默认下载路径：~/.cache/ 目录下对应厂商的文件夹
```
〔L1 P24〕

```bash
# HuggingFace 镜像与加速
export HF_ENDPOINT=https://hf-mirror.com      # 镜像网站
export HF_HUB_ENABLE_HF_TRANSFER=1            # 开启加速
```

```python
# 首次下载后，再次加载本地数据集
datasets = load_dataset(path="/root/.cache/huggingface/hub/datasets--vtllms--sealqa")
```
〔L2 P11〕

## 3. 数据集注册

```bash
# 数据集存放路径：LLaMA-Factory/data
# 注册文件
vi data_info.json
```

> **无论是系统数据集还是自定义数据集，都需要注册至 `dataset_info.json` 中才能在训练微调中使用。** 〔L2 P8〕

| 格式 | 必填字段 | 特点 |
|---|---|---|
| **Alpaca** | `instruction` / `input` / `output` | 单轮 |
| **ShareGPT** | 多轮对话结构 | 多轮 |

〔L2 P9–P10〕

## 4. 训练：LLaMA-Factory 两种入口

### 4.1 WebUI

```bash
GRADIO_SERVER_PORT=6006 llamafactory-cli webui
```
〔L1 P23〕

### 4.2 命令行脚本模式

```bash
llamafactory-cli train  examples/train_lora/llama3_lora_sft.yaml
llamafactory-cli chat   examples/inference/llama3_lora_sft.yaml
llamafactory-cli export examples/merge_lora/llama3_lora_sft.yaml
```
〔L1 P23〕

### 4.3 单机多卡（DDP + DeepSpeed）

```bash
# FSDP + QLoRA
bash /root/autodl-tmp/LLaMA-Factory/examples/extras/fsdp_qlora/train.sh
llamafactory-cli chat examples/inference/llama3_lora_fsdp.yaml
```
〔L3 P54〕

### 4.4 多机多卡（torchrun）★

**Naive DDP**（两台机器）

```bash
# 主节点（node1）
FORCE_TORCHRUN=1 NNODES=2 NODE_RANK=0 MASTER_ADDR=<node1的IP> MASTER_PORT=10000 \
  llamafactory-cli train examples/train_lora/llama3_lora_sft.yaml

# 从节点（node2）—— MASTER_ADDR 必须与主节点一致！
FORCE_TORCHRUN=1 NNODES=2 NODE_RANK=1 MASTER_ADDR=<node1的IP> MASTER_PORT=10000 \
  llamafactory-cli train examples/train_lora/llama3_lora_sft.yaml
```

**DeepSpeed**

```bash
# 主节点
FORCE_TORCHRUN=1 NNODES=2 NODE_RANK=0 MASTER_ADDR=<node1的IP> MASTER_PORT=10000 \
  llamafactory-cli train examples/train_lora/llama3_lora_sft_ds3.yaml

# 从节点
FORCE_TORCHRUN=1 NNODES=2 NODE_RANK=1 MASTER_ADDR=<node1的IP> MASTER_PORT=10000 \
  llamafactory-cli train examples/train_lora/llama3_lora_sft_ds3.yaml
```

::: warning ⚠ 已修正原文错误
原 docx 中两机填了**不同的** `MASTER_ADDR`（如 `172.19.138.2` vs `172.20.138.2`），
**这是错的**。`MASTER_ADDR` 是**主节点**地址，**所有节点必须填同一个值**。上表已按正确做法写。
另：原文路径前缀 `autodl-tmp` 与 `lanyun-tmp` 混用，请按自己机器的真实路径替换。
:::

**四个环境变量**：

| 变量 | 含义 |
|---|---|
| `FORCE_TORCHRUN=1` | 强制用 torchrun 多进程启动 |
| `NNODES=2` | 总节点数 |
| `NODE_RANK=0/1` | 主=0，从=1 |
| `MASTER_ADDR` + `MASTER_PORT` | 主节点地址与端口，**所有节点一致** |

**SSH 免密互连**（两台机器互连）

```bash
cd /root/.ssh
ssh-keygen -t rsa                                        # 一路回车
ssh-copy-id -i ~/.ssh/id_rsa.pub user@<从机器IP>          # 复制公钥
ssh user@<从机器IP>                                       # 测试互连
# 在从机器上重复上述 1–3 步
```
〔docx〕

## 5. 知识蒸馏

```bash
# 训练（白盒响应式 · 4B 教师 → 1.7B 学生）
python train.py

# 推理验证
python inference.py
```

**关键配置**（`train.py`）：

| 项 | 值 |
|---|---|
| LoRA | `r=8`, `lora_alpha=256`, `lora_dropout=0.1`, `target_modules=[q,k,v,o,gate,up,down]_proj` |
| 训练 | `per_device_train_batch_size=1`, `gradient_accumulation_steps=16`, `bf16=True` |
| 优化 | `learning_rate=0.0005`, `lr_scheduler_type='cosine'` |
| **蒸馏** | **`temperature=6`**（范围【3–20】）、**`alpha=0.5`** |
| 数据 | `max_seq_len=512` |

〔`White_box_Distillation/train.py`、L4 P26〕

## 6. 量化

| 方案 | 要点 |
|---|---|
| `bnb` | 精度保持最好，支持 QLoRA 量化训练 |
| `HQQ` | 无需校准数据，秒级量化（纯推理）|
| `EETQ` | NVIDIA 硬件感知，推理最快 |
| `GPTQ` | 逐列量化 + 误差反馈，`pip install auto_gptq` |
| `AWQ` | 激活感知，无需训练，校准集更小 |

**GPTQ 量化流程**（LLaMA-Factory）：

```text
lora 微调 → lora adapter 权重合并导出合并模型 → 量化模型输出
```
〔L1 P27、L2 P39–P49、L2 P51〕

**学习率参考**：

| 方法 | 学习率范围 |
|---|---|
| LoRA | **1e-4 ~ 5e-4** |
| QLoRA | **5e-5 ~ 2e-4**（由于量化，略低）|

〔L2 P17〕

## 7. 核心超参速查

### 7.1 LoRA

| 参数 | 推荐值 | 说明 |
|---|---|---|
| `rank` (r) | 4（简单任务/小数据）、8、16（复杂任务/大数据）| 低秩矩阵维度 |
| `lora_alpha` | **16–32** | 太高→不稳定/过拟合；太低→效果不明显 |
| `dropout` | **0.2–0.3** 常见；小模型 0.1、大网络 0.4–0.5 | 防过拟合 |

〔L2 P16〕

### 7.2 GaLore

| 参数 | 推荐值 | 说明 |
|---|---|---|
| `rank` | **16–512**（如 128/256/512）| 越小压缩率越高但信息损失多 |
| `update_proj_gap` | 论文常用 **200** 步 | 越小效果越好但开销越大 |
| `scale` | 默认（自动）| 补偿低秩投影的幅值损失 |
| `proj_type` | `std`（默认）| 也可选 `ortho` 等 |

> **注意：不要将 LoRA 和 GaLore/BAdam 一起使用。**
> 使用 GaLore/BAdam 时请设置 `finetuning_type` 为 **`full`** 且 `pure_bf16` 为 **`True`**。
〔L2 P26–P27〕

### 7.3 学习率调度器

| `scheduler_type` | 曲线 | 适用 |
|---|---|---|
| `constant` | 恒定 | 简单调试（大模型少用）|
| `linear` | Warmup 后线性降到 0 | 常用默认 |
| `cosine` | Warmup 后余弦降到 0 | **极其常用**，长训练首选 |
| `cosine_with_restarts` | 余弦 + 周期重启 | 陷入局部最优时 |
| `polynomial` | 多项式下降（`power` 可调）| 更灵活 |

〔L1 P29〕

### 7.4 RoPE 插值

| 方法 | 适用 |
|---|---|
| `linear` | 快速测试、对长文本末端质量要求不高 |
| **`dynamic`** | **绝大多数情况的首选**（免训练，推荐）|
| `yarn` | 追求极致长文本（32k/64k/128k+），需少量微调 |
| `none` | 默认，不超原始训练长度时使用 |

〔L1 P30〕

### 7.5 加速方法

| 选项 | 说明 |
|---|---|
| `unsloth` | 重写底层内核，专优 LoRA/QLoRA |
| `auto` | 自动选择 |
| `flashattn2` | FlashAttention 2，长序列有效 |
| `liger_kernel` | LigER 内核加速 |

〔L1 P31〕

## 8. 实验监控

### 8.1 SwanLab

```bash
pip install swanlab
```
〔L2 P20〕

### 8.2 TensorBoard

```bash
pip install tensorflow==2.20.0
pip install tf-keras==2.20.1
pip install tensorboard
```

```bash
# step1: 训练配置加 --report_to "tensorboard"，用 --logging_dir 指定日志路径
# step2: 启动
tensorboard --logdir="single_galore_qwen1.5_log" --host localhost --port 6006
# step3: 访问 http://localhost:6006/
```
〔L2 P21〕

## 9. 部署

### 9.1 Ollama

```bash
# 安装（Linux 方案1）
curl -fsSL https://ollama.com/install.sh | sh

# 安装（Linux 方案2 · 推荐）
source /etc/network_turbo
wget https://ollama.com/download/ollama-linux-amd64.tgz
sudo tar -C /usr -xzf ollama-linux-amd64.tgz

# 安装（Docker）
docker pull ollama/ollama
docker run -p 11434:11434 ollama/ollama

# 服务
ollama serve
nohup ollama serve > /root/ollama.log 2>&1 &     # 后台启动（默认端口 11434）

# 模型操作
ollama pull qwen3:0.6b
ollama run qwen3:0.6b                            # 未下载则自动下载
ollama list
ollama rm qwen3:0.6b

# 自定义模型
ollama create small_qwen -f ./Modelfile          # ⚠ 是 Modelfile 不是 Modulefile
ollama run small_qwen

# WebUI
open-webui serve --port 6006
```
〔L5 P26–P38〕

**Modelfile 模板**：

```dockerfile
FROM qwen3:0.6b
# 指定 LoRA 适配器路径,如果有
ADAPTER ./lora-weights
# 设置模型参数
PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 32768
PARAMETER num_predict 2048
SYSTEM """你是由咕泡科技开发的智能助手，专门辅导学生做课程学习"""
# 对话模板 - 适配中文对话
TEMPLATE """<|im_start|>system
{{ .System }}<|im_end|>
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant\n
"""
```

**HTTP API**：

```bash
# 生成文本
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3:0.6b", "prompt":"你好", "stream":false,
       "options":{"temperature":0.7, "max_tokens":100}}'

# 聊天（多轮）
curl http://localhost:11434/api/chat -d '{
  "model": "qwen3:0.6b",
  "messages": [{"role":"user","content":"你好"}],
  "stream": false }'
```

### 9.2 vLLM（OpenAI 兼容）

```bash
# 通过 LLaMA-Factory 启动 vLLM 推理服务（端口 6006）
API_PORT=6006 llamafactory-cli api examples/inference/qwen3_1_7b.yaml \
  infer_backend=vllm vllm_enforce_eager=true
```

**`qwen3_1_7b.yaml`**：

```yaml
model_name_or_path: /root/autodl-tmp/Qwen/
template: qwen3
infer_backend: vllm  # choices: [huggingface, vllm, sglang]
trust_remote_code: true

#VLLM特定配置
vllm_config:
  dtype: float32
  gpu_memory_utilization: 0.9 # GPU能利用的空间比例，越高的比例代表能抗越高的并发
  max_model_len: 8192 # 能够一次性处理和生成的最大文本长度
```

> ⚠ 提示：推理场景通常用 `float16` / `bfloat16`，`float32` 会让显存翻倍。
〔L5 P50、`qwen3_1_7b.yaml`〕

### 9.3 FastAPI 服务（端口 6008）

```bash
python fastapi_server.py
# uvicorn.run(app, host="0.0.0.0", port=6008)
```

```bash
# 调用（注意端口是 6008，不是 6006）
curl -X POST "http://localhost:6008/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好","temperature": 0.6,"max_tokens": 2000}'
```

> **端口关系**：**vLLM = 6006**，**FastAPI = 6008**。客户端打 6008，FastAPI 内部再打 6006。
〔`fastapi_server.py`、`vllm&fastapi部署.ipynb`〕

### 9.4 SGLang（端口 30000）

```bash
# 启动
python3 -m sglang.launch_server \
  --model-path /root/.cache/modelscope/hub/models/Qwen/Qwen3-4B-Instruct-2507 \
  --host 0.0.0.0 --port 30000

# 后台启动
nohup python3 -m sglang.launch_server --model-path ... --host 0.0.0.0 --port 30000 &

# 多 LoRA 部署
python3 -m sglang.launch_server --model-path ... \
  --lora-paths lora0="第一个lora适配器的权重路径" lora1="第二个lora适配器的权重路径" \
  --port 30001 \
  --max-loras-per-batch 2 --lora-backend triton \
  --disable-radix-cache
```

> ⚠ 若报 `SGLang only supports sm75 and above` → **显卡算力不足，需 ≥ SM7.5**。
〔L5 P62、`SGlang部署.ipynb`〕

### 9.5 Ray Serve

```bash
serve run serve_quickstart:translator_app
```
〔L5 P57〕

## 10. 决策速查（选型）

| 场景 | 选择 |
|---|---|
| 模型能放进单卡、要速度 | **DDP** |
| 单层太大装不下 | **张量并行** |
| 状态/整体太大、想简单 | **FSDP** |
| 要卸载到 CPU/NVMe、超大规模 | **DeepSpeed ZeRO-2/3 + Offload** |
| 个人 / 小项目 / 快速验证 | **Ollama** |
| 高并发 / 生产服务 | **vLLM（+ FastAPI）** |
| 需要多模型组合编排 | **Ray Serve** |
| 多租户共用底座 | **SGLang（多 LoRA）** |
| NVIDIA GPU 推理加速 | **TensorRT** |
| Intel CPU 推理加速 | **OpenVINO** |

〔综合 Part 3–6〕

---

> 上一节：[A2 来源与页码对照](/training/p8/a2-source-map) ｜ 返回：[Part 0 导读](/training/)
