---
title: C07 · 单卡实测 + 多卡推演：DDP 与 ZeRO-2 的每卡显存账
---

# C07 · 单卡实测 + 多卡推演：DDP 与 ZeRO-2 的每卡显存账

::: tip 案例信息
**所属 Part**：[Part 4 · 分布式训练](/training/p4/01-basics) ｜ **难度**：基础 ｜ **耗时**：40–70 分钟
**对应讲义**：[4-10 数据并行 DP → DDP](/training/p4/10-ddp)、[4-12 DeepSpeed 与 ZeRO](/training/p4/12-deepspeed-zero)、[4-14 其他优化与实战](/training/p4/14-optim-practice)、[9-B 公式速查卡 · §6 并行摊分](/training/p9/B-formula-card)
**前置**：[C01](/training/p10/c01-llamafactory-env) 已完成（云主机在运行、`llama_env` 可用）
:::

::: warning 成本：本案例只租 1 张卡，约 ¥2–5
**多卡部分不真跑，用账本推演。** 理由见下。

| 项 | 内容 |
|---|---|
| **需要几张卡** | **1 张**（24 GB 档最省，如 RTX 4090 / 3090） |
| **预估费用** | 按量计费 **约 ¥2–5**（取决于卡的档位与你在机时长） |
| **省钱姿势** | ① 用**无卡模式**先配环境、写好配置、做完账本推演，只在"单卡实测"那一步开机<br/>② 单卡实测时**只跑十几步**（`max_steps` 限死），看的是显存读数不是收敛<br/>③ 做完**立刻控制台关机**（`exit` 不算） |
:::

::: info 为什么多卡部分不真跑
真跑 DDP / ZeRO-2 要租 2 张以上卡，成本翻倍；而**这张账本身是可以算出来的**——
[9-B §6](/training/p9/B-formula-card) 给了完整的每卡摊分公式，[4-12](/training/p4/12-deepspeed-zero) 给了 16 B/参数的口径。

**所以本案例把"真跑"和"推演"分开**：
- **单卡**：真跑，拿 `nvidia-smi` 的**实测读数**当地基；
- **多卡**：把 DDP / ZeRO-2 的**启动参数写全**，用账本**推出每卡占用**，再和单卡实测对齐。

这样你练到的是**同一套能力**——配置怎么写、显存怎么摊、结论怎么下，只是不为一张可以算出来的账多付一次租卡钱。
:::

## ① 题目

> 在 **1 张卡**上完成 DDP / ZeRO-2 的完整准备与推演，要求：
>
> 1. **单卡实测**：跑一次 LoRA 微调（限制步数），记录 `nvidia-smi` 的**峰值显存**与训练日志里的步数/耗时；
> 2. **配好多卡**：把单机 2 卡 **DDP** 与 **ZeRO-2** 两套启动参数写全，并能逐个解释每个环境变量/配置项的含义；
> 3. **账本推演**：用 [9-B §6](/training/p9/B-formula-card) 的公式，算出**同一模型在 1 卡 / 2 卡 DDP / 2 卡 ZeRO-2** 三种情况下的每卡静态显存，列表对照；
> 4. **对齐验证**：把账本算出的"1 卡"数字与你实测的峰值显存对照，解释差额来自哪几项；
> 5. **说清边界**：明确说明"哪些结论是实测的、哪些是推演的"——不许把推演结论说成实测结论。

**一句话目标**：把"显存不够就加卡"这句空话，换成**一张能自己算出来的每卡显存账**。

## ② 你会练到什么

| 技能点 | 对应小节 |
|---|---|
| **单机多卡启动参数**：`NNODES` / `NODE_RANK` / `MASTER_ADDR` / `MASTER_PORT` / `FORCE_TORCHRUN` 各自含义 | [4-14](/training/p4/14-optim-practice) · 4.4 四个环境变量 |
| **DDP 的痛点**：为什么纯 DP 一点显存都不省 | [4-10](/training/p4/10-ddp)、[9-B §6](/training/p9/B-formula-card) |
| **ZeRO-2 切什么**：优化器状态 + 梯度，权重不切 | [4-12](/training/p4/12-deepspeed-zero) · 决策表 |
| **每卡摊分公式**：`14/N + 2` 这类式子怎么来的 | [9-B §6](/training/p9/B-formula-card) · 并行摊分 |
| **实测 vs 推演的边界**：怎么诚实地报告结论 | 本案例 ①-5 |

## ③ 前置条件

| 项 | 要求 | 怎么核对 |
|---|---|---|
| 环境 | C01 已完成，`llama_env` 可用 | `conda activate llama_env && llamafactory-cli --help` 有输出 |
| GPU | **≥ 16 GB 显存**（本案例用 1 张卡） | `nvidia-smi` 看显存总量 |
| 模型 | Qwen3-1.7B 已下载（约 3.4 GB） | `ls /root/autodl-tmp/models/Qwen/Qwen3-1.7B` |
| 数据集 | LLaMA-Factory 内置 `identity` 数据集即可，**不用自备** | `ls LLaMA-Factory/data/*.json` 能看到 `identity.json` |
| 依赖 | 已装 `accelerate`、`deepspeed`（C01 步骤 5 已含） | `python -c "import deepspeed; print(deepspeed.__version__)"` |
| 磁盘 | 数据盘 ≥ 20 GB 空闲 | `df -h`（**看数据盘那一行**） |
| **省钱** | 建议先无卡模式做完步骤 1–3，再开机做步骤 4 | — |

::: tip 为什么选 1.7B 这么小的模型
**推演要干净。** 1.7B 的每卡账是一串能心算的数，不会算错；换成 7B 或 70B 反而干扰你对公式本身的注意力。
**真实模型越大，这套账越省钱**——因为推演的边际成本是 0。
:::

## ④ 分步操作

### 步骤 1 · 先看清一张卡的真实盘子

```bash
nvidia-smi
# 记下：显存总量（MiB）、当前占用、驱动支持的 CUDA 版本
```

**这一步在选什么**：先知道"总量是多少"，后面所有摊分才有分母。

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| 用 `nvidia-smi` 的 **MiB 读数** | `1 MiB = 1/1024 GiB` | 本册统一口径：**MiB ÷ 1024 = GiB**。直接读 "24GB" 会与账本差 7%（GB vs GiB） |
| 看"显存总量"而不是"已用" | 总量是分母，已用是当前进程占用 | 账本算的是"**装不装得下**"，比的是总量 |
| 也看右上角 CUDA Version | 那是**驱动支持的上限** | 与实装 `nvcc -V` 是两回事（[1-5](/training/p1/05-env) 的头号坑） |

> 🖼 **截图槽 `c07-01`** — 应截：`nvidia-smi` 完整输出（含显存总量与 CUDA Version）
> 文件名：`c07/01-nvidia-smi.png`

```bash
# 把总量换算成 GiB，后面账本要用
# 例：24564 MiB ÷ 1024 ≈ 24.0 GiB
```

### 步骤 2 · 用无卡模式先把配置写全（省钱关键）

```bash
# 在 AutoDL 控制台把实例切到"无卡模式"（CPU 模式，几乎免费）
# 然后 SSH 进去做准备 —— 不需要卡
ssh -p <端口号> root@<服务器地址>

cd /root/autodl-tmp/LLaMA-Factory
```

**这一步在选什么**：

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **无卡模式** | 只给 CPU，不开 GPU | **写配置、改 YAML、读源码都不需要卡**。这一步能免费做，就不要花着卡钱做 |
| 直接开卡写配置 | 卡一直在计时 | 除非你要边写边验证，否则是纯浪费 |
| 在本地写好再传上去 | 也行，但要处理行尾/编码 | 云上直接 `vi` 最省事，配置本来就是几行 |

::: tip 判断"这件事需不需要卡"的通用标准
**不跑前向/反向的事，都不需要卡**：改 YAML、读报错日志、翻文档、拉代码、下模型（下模型只吃磁盘和网速）。
**只有 `python train.py` 那一下才需要卡。**
:::

### 步骤 3 · 配好两套多卡启动参数

#### 3.1 DDP（纯数据并行）

**单机 2 卡 DDP**：

```bash
# 单机多卡用 torchrun 更直接（不需要 NNODES/NODE_RANK）
FORCE_TORCHRUN=1 CUDA_VISIBLE_DEVICES=0,1 \
  llamafactory-cli train examples/train_lora/qwen3_lora_sft.yaml
```

**多机多卡 DDP**（本案例只写命令、不执行）：

```bash
# 主节点（node1，NODE_RANK=0）
FORCE_TORCHRUN=1 NNODES=2 NODE_RANK=0 \
  MASTER_ADDR=<node1 的 IP> MASTER_PORT=10000 \
  llamafactory-cli train examples/train_lora/qwen3_lora_sft.yaml

# 从节点（node2，NODE_RANK=1）
FORCE_TORCHRUN=1 NNODES=2 NODE_RANK=1 \
  MASTER_ADDR=<node1 的 IP> MASTER_PORT=10000 \
  llamafactory-cli train examples/train_lora/qwen3_lora_sft.yaml
```

| 变量 | 含义 | 取值规律 |
|---|---|---|
| `FORCE_TORCHRUN=1` | 强制用 torchrun 多进程启动 | 固定 `1` |
| `NNODES` | 参与训练的总**节点**数 | 单机不填；双机填 `2` |
| `NODE_RANK` | 本机编号 | **主 = 0，从 = 1** |
| `MASTER_ADDR` | **主节点**的 IP | ⚠️ **所有节点必须填同一个值** |
| `MASTER_PORT` | 通信端口 | 两台一致（如 `10000`） |

::: danger `MASTER_ADDR` 是最容易错的一个
**它是"主节点的地址"，不是"本机地址"。** 从节点也必须填 node1 的 IP。

讲义 [4-14](/training/p4/14-optim-practice) 明确指出了原文 docx 的这处错误：
DDP 方案主节点填 `172.19.138.2`、从节点填 `172.20.138.2` —— 两机填了不同地址，
会导致 **rendezvous（汇聚）失败**、进程卡死或报连接错误。
:::

> 🖼 **截图槽 `c07-02`** — 应截：你写好的多卡启动命令（两节点两行，`MASTER_ADDR` 已统一）
> 文件名：`c07/02-multinode-cmd.png`

#### 3.2 ZeRO-2

```bash
# 在 YAML 里指定 DeepSpeed 配置，或命令行覆盖
# 前提：examples/deepspeed/ds_z2_config.json 存在
```

```yaml
# 训练 YAML 中的关键一行
deepspeed: examples/deepspeed/ds_z2_config.json
```

**这一步在选什么**：

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **ZeRO-2** | 切「优化器状态 + 梯度」，**权重不切** | Part 4 实战指定的对照档；显存降幅明显、通信代价还可接受 |
| 为什么不选 ZeRO-1 | 只切优化器状态 | 降得比 ZeRO-2 少；ZeRO-2 是常见默认 |
| 为什么不选 ZeRO-3 | 再切权重，通信最重 | 本模型 1.7B 单卡都放得下，**开 ZeRO-3 是无谓的通信开销**（[4-12 三条铁律](/training/p4/12-deepspeed-zero)第一条） |
| 为什么不用纯 DDP | 不切任何东西 | 作为**对照基线**保留——它就是"什么优化都不做" |

> 🖼 **截图槽 `c07-03`** — 应截：`ds_z2_config.json` 里 `zero_optimization.stage` 的值
> 文件名：`c07/03-zero2-config.png`

### 步骤 4 · 单卡实测：拿真实读数

```bash
conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory

# 限死步数，只为看显存，不为收敛
llamafactory-cli train \
  examples/train_lora/qwen3_lora_sft.yaml \
  max_steps=20
```

开另一个终端窗口盯显存：

```bash
# 每 1 秒刷一次，找峰值
watch -n 1 nvidia-smi
```

**这一步在选什么**：

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| `max_steps=20` | 只跑 20 步就停 | **本步的目的是"量显存"不是"训模型"**，跑满 epoch 是纯烧钱 |
| `watch -n 1 nvidia-smi` | 每秒刷新 | LoRA 显存会在**前几步冲到峰值**然后稳定，1 秒粒度够抓 |
| 为什么不看 `torch.cuda.max_memory_allocated()` | 那是**分配器视角**，不含 CUDA 上下文 | `nvidia-smi` 是**进程真实占用**，和"卡装不装得下"是同一个口径 |
| 记"峰值"不记"稳态" | 峰值才是决定 OOM 与否的数 | 判"装不装得下"永远按峰值算 |

> 🖼 **截图槽 `c07-04`** — 应截：训练跑到峰值时的 `nvidia-smi`（能看清 python 进程的显存占用）
> 文件名：`c07/04-peak-vram.png`

> 🖼 **截图槽 `c07-05`** — 应截：训练日志最后几行（含步数、loss、耗时）
> 文件名：`c07/05-train-log.png`

### 步骤 5 · 账本推演：算三种配置的每卡静态显存

**先确定口径**（这一步必须写出来，否则账算不明白）：

| 口径项 | 取值 | 出处 |
|---|---|---|
| 每参数字节（混合精度 Adam） | **16 B/参数** | [9-B §4](/training/p9/B-formula-card) · CSDN 保守口径（含 fp32 主权重） |
| 权重 | 2 B/参数 | 同上 |
| 梯度 | 2 B/参数 | 同上 |
| 优化器状态 | 12 B/参数 | 同上（AdamW 2×fp32 + 主权重备份） |
| 模型 | Qwen3-1.7B，按 **1.7 B** 参数计 | 简化取值，账本给量级 |

**代入公式**（[9-B §6](/training/p9/B-formula-card)）：

```text
每卡权重   = Φ × 权重字节 / (TP × PP × [1 或 DP])     ← 仅 ZeRO-3 乘 DP
每卡梯度   = Φ × 2 B / (TP × PP × [1 或 DP])          ← ZeRO-2/3 乘 DP
每卡优化器 = Φ × opt_B / (TP × PP × DP)               ← ZeRO-1 起乘 DP
```

**三种配置的账**（Φ = 1.7 B，fp16 权重 2 B、梯度 2 B、优化器 12 B）：

| 配置 | 每卡权重 | 每卡梯度 | 每卡优化器 | 静态合计/卡 |
|---|---|---|---|---|
| **1 卡**（基线） | `1.7×2 = 3.4 GB` | `1.7×2 = 3.4 GB` | `1.7×12 = 20.4 GB` | **≈ 27.2 GB** |
| **2 卡 DDP**（不切） | `3.4 GB` | `3.4 GB` | `20.4 GB` | **≈ 27.2 GB** ⚠ 一点没省 |
| **2 卡 ZeRO-2** | `3.4 GB`（不切） | `3.4 ÷ 2 = 1.7 GB` | `20.4 ÷ 2 = 10.2 GB` | **≈ 15.3 GB** ✅ |

**这一步在选什么**：

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| 用哪套口径 | 12 B（阿里云）/ 16 B（CSDN） | **选 16 B 并在纸上写明**。两套差 24.6 GB/7B，不声明就是耍流氓（[9-B §4](/training/p9/B-formula-card)） |
| 算"静态"还是"含激活" | 静态 = 权重+梯度+优化器 | 本案例**先算静态**（可复现），激活值单列到步骤 6 讲 |
| GB 还是 GiB | `1 GB = 10⁹ B`；`1 GiB ≈ 1.074 GB` | 账本用 **GB**（与公式出处一致），实测的 MiB 要**除以 1024** 变 GiB。**两者差 7%，不许混着比** |

::: warning 这张表最重要的一行是「2 卡 DDP 一点没省」
**DP 是复制不是切分**——2 张卡各存一份完整的权重+梯度+优化器状态。
所以 `2 卡 DDP = 1 卡`，显存扛不住还是扛不住。

**想省显存，DP 必须配 ZeRO。** 这是 [9-B §6](/training/p9/B-formula-card) 反复强调的一条。
:::

### 步骤 6 · 对齐：把推演和实测接上

```text
实测峰值（GiB）        = <填你 nvidia-smi 读到的数>
静态账本（GB）         = 27.2 GB
差额 = 实测 − 静态     = ? GB
```

差额由这几项构成（对着填）：

| 差额来源 | 典型量级 | 说明 |
|---|---|---|
| **激活值** | 与 `s·b·h·L` 正相关 | 训练账本的大头，**短序列时不算大** |
| **框架开销** | **1–2 GB** | CUDA 上下文 + 框架自身 + 输入缓冲（[9-B §5](/training/p9/B-formula-card)） |
| **临时 Buffer / 碎片** | 不定 | 计算中间缓冲与显存碎片 |
| **GB → GiB 换算** | **约 +7%** | 账本是 GB，实测是 GiB，**别忘了这一步** |
| **LoRA 只训少量参数** | **负向**（实测更小） | LoRA 的梯度/优化器**只算可训练参数**（约 0.1–1%），不是 1.7 B！ |

::: danger 这里有个必须自己发现的坑
上面那张账表按**全参微调**算的（梯度/优化器 = 1.7 B × 字节数）。
但你实际跑的是 **LoRA** —— 可训练参数只有零点几个百分点。

**所以：**
- 如果你实测的峰值**远小于 27 GB**，是对的，因为 LoRA 不存 1.7B 的优化器状态；
- 如果你要算**全参**场景的账，才用上面那张表。

**两种都对，但必须说清你算的是哪种。** 混用会导致"账本说 27 GB、实测 9 GB"这种看起来像算错了的结果。
:::

> 🖼 **截图槽 `c07-06`** — 应截：你手写的"实测 vs 推演"对照表（或 Excel 截图）
> 文件名：`c07/06-reconcile.png`

### 步骤 7 · 关机

```bash
exit
# ⚠️ 这只是断开 SSH —— 必须回 AutoDL 控制台点「关机」
```

| 做法 | 结果 |
|---|---|
| **关机（不释放）** | 停止计费，数据盘保留 → 下次继续用 |
| 只关 SSH 窗口 | ⚠️ **实例仍在跑、仍在计费** |

## ⑤ 预期结果（判定标准）

| # | 判定项 | 通过标准 |
|---|---|---|
| 1 | 单卡实测有数 | `nvidia-smi` 记录到**峰值显存**（MiB 读数），并已换算为 GiB |
| 2 | 训练确已跑起来 | 日志有 step 推进（≥ 10 步）与 loss 输出 |
| 3 | 两套参数写全 | DDP 与 ZeRO-2 的启动命令/配置都能贴出，且 `MASTER_ADDR` 两节点一致 |
| 4 | 五个变量说得清 | 能解释 `FORCE_TORCHRUN` / `NNODES` / `NODE_RANK` / `MASTER_ADDR` / `MASTER_PORT` |
| 5 | **账本算对** | 三种配置的每卡静态显存表算出，且 **2 卡 DDP 与 1 卡数值相同** |
| 6 | **口径已声明** | 明确写出用了 12 B 还是 16 B 口径；明确 GB 与 GiB 的处理方式 |
| 7 | **理解性目标：LoRA 的账不同** | 能说清"LoRA 只训少量参数，所以优化器状态不按 1.7B 算"——这是本案例最容易错的一点 |
| 8 | **理解性目标：为什么 DDP 不省** | 能说清"DP 是复制不是切分"，所以纯 DP 的每卡占用与单卡相同 |
| 9 | **理解性目标：实测与推演的边界** | 明确区分了哪些数字来自实测、哪些来自推演，未把推演说成实测 |
| 10 | 已关机 | 回控制台确认实例状态为「已关机」而非仅断开 SSH |

按标准表逐项打勾……

## ⑥ 常见报错

| 报错 | 原因 | 处置 |
|---|---|---|
| `Address already in use`（MASTER_PORT） | 端口被占（上次进程没退干净） | `pkill -f torchrun`，或换 `MASTER_PORT=10001` |
| 进程卡住不动、无日志 | `MASTER_ADDR` 两节点填了不同地址 | 统一改成 **node1 的 IP**（[4-14](/training/p4/14-optim-practice) 指出的原文错误） |
| `torch.distributed.DistNetworkError` | 防火墙/安全组没放开端口 | 云控制台开入方向端口；或确认两机内网互通 |
| `CUDA out of memory` | 显存真不够 | 降 `batch_size`、加 `gradient_accumulation`、或上 ZeRO-2 |
| `deepspeed` 相关 import 失败 | 没装 deepspeed | `pip install deepspeed`（[C01 步骤 5](/training/p10/c01-llamafactory-env)） |
| `No space left on device` | 模型/日志写到系统盘 | 确认 `MODELSCOPE_CACHE` 指向数据盘；`df -h` 看数据盘 |
| 训练日志显示"使用了 N 张卡"但只有 1 张在忙 | `CUDA_VISIBLE_DEVICES` 没设对 | 检查卡号是否写成 `0,1` 而机器只有 1 张卡 |
| **实测显存远小于账本** | 跑的是 LoRA，账本按全参算 | **不是错**。要么把账本改成按可训练参数算，要么明确声明算的是全参 |
| 忘记关机被扣费 | `exit` 不等于关机 | 回控制台点「关机」；养成做完即关的习惯 |

## ⑦ 延伸

1. **把模型从 1.7B 换成 7B**：账本所有数字乘以约 4.1，看什么时候 24 GB 单卡开始装不下。
2. **给账本加上激活值**：按 [9-B §3](/training/p9/B-formula-card) 的 `34 × s × b × h × 2B × L` 算一遍，看激活占多少比例。
3. **换成 ZeRO-3 再推一遍**：每卡权重也 ÷ 2，合计会降到多少？再想想"通信代价变重"值不值。
4. **真的租 2 张卡跑一次**：如果哪天手头宽裕，用同一份配置真跑 DDP 与 ZeRO-2，核对推演准不准。
5. **把 `MASTER_ADDR` 故意填错**：在两节点上填各自的 IP，亲眼看 rendezvous 怎么失败——比读十遍文档印象深。
6. **算一次成本**：按 [9-B §7](/training/p9/B-formula-card) 的 `$/百万 token` 或"每小时单价 × 时长"，算算"真跑多卡"比"推演"贵多少。

---

> 下一节：[C08 单卡 offload 真跑 + FSDP 配置对照](/training/p10/c08-zero3-fsdp) ｜ [案例库总览](/training/p10/) ｜ [Part 4 末页题目](/training/p4/14-optim-practice)
