---
title: A1 术语表
---

# A1 · 术语表（中英对照）

> **用法**：Ctrl+F 在本页搜索关键词。中英对照 + 一句话定义。
> 定义来源：本课程 Part 0–7 各页；标注 `〔Lx Pxx〕` 的为讲义原页码。
> 未标页码的条目为本站在对应页面内的展开表述（另见各页「来源」段）。

## A · 训练阶段与基础

| 术语 | 英文 | 一句话定义 | 出处 |
|---|---|---|---|
| 预训练 | Pre-training | 在海量语料上训练出 Base 模型，得到通用语言能力 | [1-1](/training/p1/01-overview) |
| 监督微调 | SFT / Supervised Fine-Tuning | 用标注数据把 Base 模型调成会听指令的 Instruct 模型 | [1-1](/training/p1/01-overview) |
| 人类反馈强化学习 | RLHF | 用人类偏好训练奖励模型，再强化模型行为，实现"对齐" | [1-1](/training/p1/01-overview)、[5-7](/training/p5/07-challenges) |
| 微调 | Fine-tuning | 在已训好的模型上，用少量领域数据继续训练，让它学会新能力/风格 | [1-2](/training/p1/02-boundary) |
| 全参微调 | Full Fine-tuning | 更新模型全部参数 | [3-4](/training/p3/04-full-freeze) |
| 冻结微调 | Freeze | 只训部分层，其余冻结不更新 | [3-4](/training/p3/04-full-freeze) |
| 自我认知数据集 | — | 让模型知道自己"是谁"的问答数据（如 `identity_modify.json`） | [2-4](/training/p2/04-custom-dataset)、[5-9](/training/p5/09-practice) |

## B · 数据工程

| 术语 | 英文 | 一句话定义 | 出处 |
|---|---|---|---|
| 指令微调数据 | Instruction Data | 形如"指令 + 输入 + 输出"的训练样本 | [2-1](/training/p2/01-data-strategy) |
| Alpaca 格式 | Alpaca Format | 单轮格式：`instruction` / `input` / `output` | [2-2](/training/p2/02-data-format) |
| ShareGPT 格式 | ShareGPT Format | 多轮对话格式：`conversations`（human/gpt 交替） | [2-2](/training/p2/02-data-format) |
| 数据集注册 | `dataset_info.json` | LLaMA-Factory 中声明数据集路径与字段映射的配置文件 | [2-2](/training/p2/02-data-format) |
| 数据多样性 | Data Diversity | 任务 / 长度 / 语种三个维度的多样性 | [5-8](/training/p5/08-industry) 〔L4 P23〕 |
| 难度打分筛选 | Difficulty Scoring | 用 `教师得分 − 学生得分` 衡量样本学习价值，过滤低分样本 | [5-8](/training/p5/08-industry) 〔L4 P24〕 |
| 数据扩展 | Data Expansion | 用 Prompt 模板让教师模型批量生成数据 | [5-8](/training/p5/08-industry) 〔L4 P25〕 |

## C · 微调方法与加速

| 术语 | 英文 | 一句话定义 | 出处 |
|---|---|---|---|
| 参数高效微调 | PEFT | 只训练少量新增参数，冻结主体 | [3-1](/training/p3/01-methods-overview) |
| 低秩适配 | LoRA | 用低秩矩阵 `A×B` 近似权重增量，只训这两个小矩阵 | [3-2](/training/p3/02-lora) |
| LoRA 秩 | `r` | 低秩维度，越小参数量越少 | [3-2](/training/p3/02-lora) |
| LoRA 缩放 | `lora_alpha` | 缩放系数，`alpha/r` 决定 adapter 的影响权重 | [3-2](/training/p3/02-lora)、[5-9](/training/p5/09-practice) |
| 目标模块 | `target_modules` | 挂 LoRA 的层（如 q/k/v/o + gate/up/down） | [5-9](/training/p5/09-practice) |
| 量化 LoRA | QLoRA | 4-bit 量化底座 + LoRA，大幅省显存 | [3-3](/training/p3/03-qlora) |
| 分位数量化 | NF4 | 4-bit 的 NormalFloat 量化数据类型 | [3-3](/training/p3/03-qlora) |
| 双重量化 | Double Quantization | 对量化常数再做一次量化，进一步省显存 | [3-3](/training/p3/03-qlora) |
| 梯度低秩投影 | GaLore | 把梯度投影到低秩空间做优化器更新 | [3-4](/training/p3/04-full-freeze) |
| 分块优化器 | BAdam | 分块更新 Adam 状态以省显存 | [3-4](/training/p3/04-full-freeze) |
| 缩放点积注意力优化 | FlashAttention | 用分块 + 重计算减少 HBM 读写 | [3-5](/training/p3/05-accel) |
| 自动混合精度 | AMP | 混合使用低精度与 fp32，兼顾速度与稳定 | [3-5](/training/p3/05-accel)、[4-14](/training/p4/14-optim-practice) |
| 激活重计算 | Checkpointing / Recomputation | 不保存中间激活，反向时重算，用计算换显存 | [3-5](/training/p3/05-accel)、[4-11](/training/p4/11-model-pipeline-parallel) |
| 梯度累计 | Gradient Accumulation | 累加多个 micro-batch 的梯度再更新，模拟大 batch | [4-14](/training/p4/14-optim-practice) 〔L3 P53〕 |

## D · 量化

| 术语 | 英文 | 一句话定义 | 出处 |
|---|---|---|---|
| 量化 | Quantization | 用更低精度（如 int8）表示权重，省显存 | [3-6](/training/p3/06-quantization) |
| 训练后量化 | PTQ | 训练完成后对模型做量化 | [3-6](/training/p3/06-quantization) |
| 量化感知训练 | QAT | 训练时就模拟量化误差 | [3-6](/training/p3/06-quantization) |
| GPTQ | — | 基于二阶信息的训练后权重量化方法 | [3-6](/training/p3/06-quantization) |
| AWQ | Activation-aware Weight Quantization | 按激活重要性保护关键权重的量化 | [3-6](/training/p3/06-quantization) |
| HQQ | Half-Quadratic Quantization | 无需校准数据的量化方法 | [3-6](/training/p3/06-quantization) |
| 精度字节 | — | FP32=4B / FP16=2B / INT8=1B / INT4=0.5B | [6-1](/training/p6/01-challenges) 〔L5 P4〕 |

## E · 分布式训练

| 术语 | 英文 | 一句话定义 | 出处 |
|---|---|---|---|
| 数据并行 | DP / Data Parallelism | 每卡一份完整模型，切分数据 | [4-1](/training/p4/01-basics)、[4-10](/training/p4/10-ddp) |
| 模型并行 | MP / Model Parallelism | 把模型本身切开放到多卡 | [4-1](/training/p4/01-basics)、[4-11](/training/p4/11-model-pipeline-parallel) |
| 张量并行 | TP | 按张量（参数矩阵）切分 | [4-11](/training/p4/11-model-pipeline-parallel) 〔L3 P40〕 |
| 流水线并行 | PP | 按层切分 + 微批次流水 | [4-11](/training/p4/11-model-pipeline-parallel) 〔L3 P42〕 |
| 层级并行 | Layer-wise Parallelism | 把不同层放到不同 GPU | [4-11](/training/p4/11-model-pipeline-parallel) 〔L3 P37〕 |
| 气泡 | Bubble | 设备空转等待的时间 | [4-11](/training/p4/11-model-pipeline-parallel) 〔L3 P39〕 |
| 1F1B | One Forward One Backward | 前向/反向交错，及时释放内存（PipeDream）| [4-11](/training/p4/11-model-pipeline-parallel) 〔L3 P45〕 |
| GPipe | — | Google 的微批次流水线方案，配重计算 | [4-11](/training/p4/11-model-pipeline-parallel) 〔L3 P44〕 |
| 分布式数据并行 | DDP | 多进程、每进程独立优化器、只传梯度 | [4-10](/training/p4/10-ddp) 〔L3 P34〕 |
| 零冗余优化器 | ZeRO | 把优化器状态/梯度/参数分片到各卡，消除冗余 | [4-12](/training/p4/12-deepspeed-zero) 〔L3 P47〕 |
| ZeRO-1 / 2 / 3 | — | 分别切优化器状态 / +梯度 / +参数 | [4-12](/training/p4/12-deepspeed-zero) 〔L3 P47〕 |
| 完全分片数据并行 | FSDP | PyTorch 原生的 ZeRO-3 实现 | [4-13](/training/p4/13-fsdp) 〔L3 P50〕 |
| 卸载 | Offloading | 把数据从 GPU 显存搬到 CPU 内存 | [4-14](/training/p4/14-optim-practice) 〔L3 P53〕 |
| 3D 并行 | 3D Parallelism | 数据 + 张量 + 流水线并行组合 | [4-13](/training/p4/13-fsdp) 〔L3 P51〕 |

## F · 通信与网络

| 术语 | 英文 | 一句话定义 | 出处 |
|---|---|---|---|
| 远程直接内存访问 | RDMA | 绕过内核与 CPU，直接访问远端内存 | [4-3](/training/p4/03-rdma) 〔L3 P11〕 |
| 集合通信 | Collective Communication | 进程组内所有进程参与的通信 | [4-7](/training/p4/07-primitives) 〔L3 P20〕 |
| 广播 | Broadcast | 一个节点发给所有节点 | [4-7](/training/p4/07-primitives) 〔L3 P20〕 |
| 散射 | Scatter | 切片后分发给不同节点 | [4-7](/training/p4/07-primitives) 〔L3 P20〕 |
| 汇聚 | Gather | 多个节点数据汇总到一个节点 | [4-7](/training/p4/07-primitives) 〔L3 P21〕 |
| 全汇聚 | All-Gather | 汇总结果发到所有节点（gather + broadcast）| [4-7](/training/p4/07-primitives) 〔L3 P21〕 |
| 规约 | Reduce | 汇总并做规约运算（累加/累乘/最值）| [4-7](/training/p4/07-primitives) 〔L3 P22〕 |
| 全规约 | All-Reduce | 规约结果发到所有节点（reduce + broadcast）| [4-7](/training/p4/07-primitives) 〔L3 P22〕 |
| 散射规约 | Reduce-Scatter | 先 scatter 再 reduce | [4-7](/training/p4/07-primitives) 〔L3 P23〕 |
| 环规约 | Ring All-Reduce | 两阶段（Scatter-Reduce + All-Gather）高效 AllReduce | [4-8](/training/p4/08-allreduce) 〔L3 P25–P26〕 |
| 朴素全规约 | Naive AllReduce | reduce + broadcast，开销大 | [4-8](/training/p4/08-allreduce) 〔L3 P24〕 |
| 通信后端 | Backend | 具体通信库（NCCL / Gloo）| [4-9](/training/p4/09-backends) |
| NCCL | NVIDIA Collective Comm. Library | NVIDIA 为 GPU 优化的集合通信库 | [4-9](/training/p4/09-backends) 〔L3 P28〕 |
| Gloo | — | Facebook 开源、不依赖特定硬件的通信库 | [4-9](/training/p4/09-backends) 〔L3 P30〕 |
| NVLink / NVSwitch | — | GPU 间高速直连 / 多 GPU 全互联 | [4-9](/training/p4/09-backends) 〔L3 P29〕 |
| InfiniBand | IB | 高性能交换式网络，原生 RDMA | [4-6](/training/p4/06-ib-roce) 〔L3 P18〕 |
| RoCE | RDMA over Converged Ethernet | 在以太网上实现（近乎）无损 RDMA | [4-6](/training/p4/06-ib-roce) 〔L3 P19〕 |
| 优先级流控 | PFC | RoCE 的无损机制之一 | [4-6](/training/p4/06-ib-roce) 〔L3 P19〕 |
| 显式拥塞通知 | ECN | RoCE 的无损机制之一 | [4-6](/training/p4/06-ib-roce) 〔L3 P19〕 |
| 胖树拓扑 | Fat-Tree | 用低性能交换机搭无阻塞网络，ECMP 均衡 | [4-4](/training/p4/04-topology) 〔L3 P14〕 |
| 环面拓扑 | Torus | 机内私有连接 + 机间 RDMA 交换机成环 | [4-4](/training/p4/04-topology) 〔L3 P13〕 |

## G · 知识蒸馏

| 术语 | 英文 | 一句话定义 | 出处 |
|---|---|---|---|
| 知识蒸馏 | Knowledge Distillation | 用大模型的输出当监督信号训练小模型 | [5-1](/training/p5/01-what) 〔L4 P5〕 |
| 教师 / 学生模型 | Teacher / Student | 知识提供方 / 接收方 | [5-1](/training/p5/01-what) 〔L4 P5〕 |
| 白盒蒸馏 | White-box KD | 能拿到输出概率分布（+中间层）做对齐 | [5-2](/training/p5/02-taxonomy) 〔L4 P7〕 |
| 黑盒蒸馏 | Black-box KD | 只用大模型生成数据再微调小模型 | [5-2](/training/p5/02-taxonomy) 〔L4 P7〕 |
| 响应式蒸馏 | Response-Based KD | 对齐最终输出 | [5-3](/training/p5/03-response) 〔L4 P8〕 |
| 特征式蒸馏 | Feature-Based KD | 对齐中间层特征图 | [5-4](/training/p5/04-feature) 〔L4 P11〕 |
| 关系式蒸馏 | Relation-Based KD | 对齐样本间/层间关系 | [5-5](/training/p5/05-relation) 〔L4 P15〕 |
| 温度系数 | Temperature `T` | 软化 logits 分布的系数（常用 3–20）| [5-3](/training/p5/03-response) 〔L4 P9〕 |
| KL 散度 | Kullback-Leibler Divergence | 衡量两个概率分布差异 | [5-3](/training/p5/03-response) 〔L4 P10〕 |
| 标签平滑 | Label Smoothing | 软化标签、抑制过度自信 | [5-3](/training/p5/03-response) 〔L4 P9〕 |
| 学生损失 | `L_student` | 与真实硬标签的交叉熵 | [5-3](/training/p5/03-response) 〔L4 P8〕 |
| 蒸馏损失 | `L_distill` | 与教师输出的 KL 散度 | [5-3](/training/p5/03-response) 〔L4 P8〕 |
| 特征图匹配 | FitNet | 直接匹配特征图的 L2 距离 | [5-4](/training/p5/04-feature) 〔L4 P11〕 |
| 注意力迁移 | Attention Transfer | 匹配注意力图 | [5-4](/training/p5/04-feature) 〔L4 P11〕 |
| 格拉姆矩阵 | Gram Matrix | 特征通道间二阶统计量，与位置无关 | [5-4](/training/p5/04-feature) 〔L4 P14〕 |
| 解流程蒸馏 | FSP | 用层间内积构建关系矩阵 | [5-5](/training/p5/05-relation) 〔L4 P16〕 |
| 关系知识蒸馏 | RKD | 用样本间距离/夹角构建关系矩阵 | [5-5](/training/p5/05-relation) 〔L4 P17〕 |
| 自蒸馏 | Self-Distillation | 模型自己教自己（深层教浅层）| [5-6](/training/p5/06-evolution) 〔L4 P18〕 |
| 多教师蒸馏 | MKD | 结合多个教师的知识（如 BERT + RoBERTa）| [5-6](/training/p5/06-evolution) 〔L4 P19〕 |
| 暗知识 | Dark Knowledge | 藏在概率分布里的类别间关系 | [5-3](/training/p5/03-response)、[5-7](/training/p5/07-challenges) |
| 思维链 | COT / Chain-of-Thought | 模型的推理过程；小模型难以理解大模型 COT | [5-7](/training/p5/07-challenges) 〔L4 P20〕 |

## H · 部署与推理优化

| 术语 | 英文 | 一句话定义 | 出处 |
|---|---|---|---|
| 键值缓存 | KV Cache | 缓存历史 K/V，避免重复计算，复杂度 O(n²)→O(n) | [6-2](/training/p6/02-kvcache) 〔L5 P10〕 |
| 预填充阶段 | Prefill | 一次性并行计算完整输入的 Q/K/V | [6-8](/training/p6/08-vllm-pagedattention) 〔L5 P41〕 |
| 解码阶段 | Decode | 逐 token 生成，依赖 KV Cache | [6-8](/training/p6/08-vllm-pagedattention) 〔L5 P41〕 |
| 内部碎片 | Internal Fragmentation | 实际 token 数 < 预留长度造成的浪费 | [6-8](/training/p6/08-vllm-pagedattention) 〔L5 P42〕 |
| 外部碎片 | External Fragmentation | 请求大小不一导致内存块不连续 | [6-8](/training/p6/08-vllm-pagedattention) 〔L5 P42〕 |
| 分页注意力 | PagedAttention | 把 KV Cache 切块 + 指针链接，非连续存储 | [6-8](/training/p6/08-vllm-pagedattention) 〔L5 P43〕 |
| 块表 | Block Table | 逻辑块 → 物理块的映射表 | [6-8](/training/p6/08-vllm-pagedattention) 〔L5 P44〕 |
| 写时复制 | Copy-on-Write | 共享块在写入时才复制 | [6-8](/training/p6/08-vllm-pagedattention) 〔L5 P45〕 |
| 连续批处理 | Continuous Batching | 序列完成后立即插入新序列，吞吐高 8 倍 | [6-3](/training/p6/03-batching) 〔L5 P13〕 |
| 模型剪枝 | Pruning | 删除/置零不重要参数，减小模型 | [6-4](/training/p6/04-pruning) 〔L5 P14〕 |
| 结构化剪枝 | Structured Pruning | 以通道/卷积核/注意力头/层为单位剪 | [6-4](/training/p6/04-pruning) 〔L5 P14〕 |
| 非结构化剪枝 | Unstructured Pruning | 逐个权重剪，产生稀疏矩阵 | [6-4](/training/p6/04-pruning) 〔L5 P15〕 |
| 开放神经网络交换 | ONNX | 跨框架的模型中间格式 | [6-5](/training/p6/05-compile) 〔L5 P21〕 |
| 张量RT | TensorRT | NVIDIA 的 GPU 推理加速运行时 | [6-5](/training/p6/05-compile) 〔L5 P21〕 |
| 开放视觉推理 | OpenVINO | Intel 的 CPU 推理加速工具 | [6-5](/training/p6/05-compile) 〔L5 P21〕 |
| 表述性状态转移 | RESTful API | 基于 HTTP(S) 的资源式接口 | [6-6](/training/p6/06-api) 〔L5 P22〕 |
| 远程过程调用 | gRPC | 基于 HTTP/2 + Protobuf 的高性能 RPC | [6-6](/training/p6/06-api) 〔L5 P23〕 |
| 协议缓冲区 | Protocol Buffers | gRPC 的二进制序列化格式，比 JSON 快 3–10 倍 | [6-6](/training/p6/06-api) 〔L5 P24〕 |
| 服务器发送事件 | SSE | 单向流式传输协议，服务端推送 | [6-9](/training/p6/09-vllm-fastapi) |
| 统一格式 | GGUF | llama.cpp 定义的模型二进制格式 | [6-7](/training/p6/07-ollama) 〔L5 P33〕 |
| 模型文件 | Modelfile | Ollama 定义自定义模型的配置文件 | [6-7](/training/p6/07-ollama) 〔L5 P34〕 |
| 适配器挂载 | `ADAPTER` | Modelfile 中指定 LoRA 适配器路径的字段 | [6-7](/training/p6/07-ollama) 〔L5 P34〕 |
| 同步爬升 | SGLang | LLM/VLM 快速服务框架，含前端编排语言 | [6-10](/training/p6/10-others) 〔L5 P58〕 |
| 模型仓库 | Model Repository | Triton 的模型组织目录 | [6-10](/training/p6/10-others) 〔L5 P52〕 |
| 水平/垂直扩展 | HPA / Scale | HPA 调 Pod 副本数；节点伸缩调 Node 数 | [6-10](/training/p6/10-others) 〔L5 P61〕 |

## I · MLOps 与工程

| 术语 | 英文 | 一句话定义 | 出处 |
|---|---|---|---|
| 机器学习运维 | MLOps | 把 DevOps 原则用于 ML 全生命周期 | [6-11](/training/p6/11-mlops) 〔L5 P63〕 |
| 自动化训练 | CT | 把数据预处理→训练→评估全流程自动化 | [6-11](/training/p6/11-mlops) 〔L5 P65〕 |
| 持续集成 | CI | 频繁合并 + 自动构建测试 | [6-11](/training/p6/11-mlops) 〔L5 P66〕 |
| 持续交付 | Continuous Delivery | 代码总是处于**可随时发布**的状态 | [6-11](/training/p6/11-mlops)〔原文定义互换〕|
| 持续部署 | Continuous Deployment | 通过测试后**自动部署到生产**，无需人工 | [6-11](/training/p6/11-mlops)〔原文定义互换〕|
| A/B 测试 | A/B Testing | 用业务指标科学比较新旧模型 | [6-1](/training/p6/01-challenges) 〔L5 P8〕 |
| 灰度发布 | Canary Release | 逐步放量，影响可控地验证新模型 | [6-1](/training/p6/01-challenges) 〔L5 P8〕 |
| 性能衰减 | Model Decay | 数据分布变化导致模型预测能力下降 | [6-11](/training/p6/11-mlops) 〔L5 P67〕 |
| 作业主节点 | MASTER_ADDR | torchrun 多机的 rendezvous 端点，**所有节点必须一致** | [4-14](/training/p4/14-optim-practice) |

---

> 返回：[Part 0 导读](/training/) ｜ 下一节：[A2 来源与页码对照](/training/p8/a2-source-map)
