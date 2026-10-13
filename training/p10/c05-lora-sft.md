---
title: C05 · 用 LoRA 对 Qwen3-4B-Base 做一次完整 SFT
---

# C05 · 用 LoRA 对 Qwen3-4B-Base 做一次完整 SFT

::: tip 案例信息
**所属 Part**：[Part 3 · 方法与加速](/training/p3/01-methods-overview) ｜ **难度**：基础 ｜ **耗时**：50–90 分钟
**对应讲义**：[3-2 LoRA 原理与参数](/training/p3/02-lora)、[3-8 实战三则](/training/p3/08-practice)、[1-6 第一个模型微调](/training/p1/06-frameworks)
**前置**：[C02](/training/p10/c02-model-download-webui)（Qwen3-4B-Base 已下到数据盘）、[C03](/training/p10/c03-alpaca-dataset)（有一份自己的数据集）
:::

::: warning 成本：本案例只租 1 张卡，约 ¥3–8
| 项 | 内容 |
|---|---|
| **需要几张卡** | **1 张**（24 GB 档即可，如 RTX 4090 / 3090） |
| **预估费用** | 按量计费 **约 ¥3–8**（LoRA 训 4B，几百条数据、跑几个 epoch 的典型时长） |
| **省钱姿势** | ① **无卡模式**里把 YAML 写全、数据集备好、路径核对完，再开机<br/>② 先用 `max_steps=50` **跑通链路**，确认 loss 在降、能存 adapter，**再决定要不要跑满 epoch**<br/>③ 数据量小时把 `save_steps` 调大、少存 checkpoint<br/>④ 做完**立刻控制台关机**（`exit` 不算） |
:::

::: info LoRA 是"性价比最高的一次微调"
4B 模型 + LoRA，24 GB 单卡**绰绰有余**——可训练参数只有**百分之几**，优化器状态也只按这部分算。
这正是 [C07](/training/p10/c07-ddp-zero2) 说的"LoRA 的账和全参不一样"的前提。**先在单卡上把它跑通。**
:::

## ① 题目

> 用 **LoRA** 对 **Qwen3-4B-Base** 做一次完整的指令微调（SFT），要求：
>
> 1. 写一份训练 YAML，**逐项解释**：`lora_rank` / `lora_alpha` / `lora_dropout` / `lora_target` / 学习率 / epoch 各自选了什么、为什么；
> 2. **先读出 LoRA 参数量**（`print_trainable_parameters()`），确认它在总参数的百分之几；
> 3. 跑一轮训练，日志里**看到 loss 下降**；
> 4. 用 WebUI 加载刚训出的 adapter，**对比微调前 vs 微调后的回答**；
> 5. **综合环节**：把 `lora_rank` 从 8 改成 16 再训一次（限步），对比**可训练参数量**与显存，并解释"r 翻倍，参数量为什么不是简单翻倍"。

**一句话目标**：走通"写配置 → 看参数量 → 训练 → 加载 adapter → 对比效果"这条完整链。

## ② 你会练到什么

| 技能点 | 对应小节 |
|---|---|
| **LoRA 三个参数的含义与取值**：`r` / `alpha` / `dropout` | [3-2](/training/p3/02-lora) · 三参数 |
| **可训练参数量的估算**：`r × (d_in + d_out) × L × 7` | [3-2](/training/p3/02-lora) · 参数量公式 |
| **`lora_target` 挂哪里**：只挂注意力 vs 挂满 7 个线性层 | [3-2](/training/p3/02-lora) · 作用位置 |
| **训练 YAML 的必填项**与 LoRA 专属项 | [1-6](/training/p1/06-frameworks) |
| **用 WebUI 加载 adapter 做前后对比** | [C02 步骤 5](/training/p10/c02-model-download-webui) |

## ③ 前置条件

| 项 | 要求 | 怎么核对 |
|---|---|---|
| 环境 | C01 已完成，`llama_env` 可用 | `conda activate llama_env && llamafactory-cli --help` 有输出 |
| 模型 | Qwen3-4B-Base 已下到数据盘 | `du -sh /root/autodl-tmp/models/hub/models/Qwen/Qwen3-4B-Base` 约 8G |
| 数据集 | 已注册的数据集（用 C03 的 `identity_modify`，或内置 `identity`） | `grep identity data/dataset_info.json` |
| GPU | **≥ 16 GB 显存**（LoRA 训 4B，bf16 + 短序列约 12–18 GB） | `nvidia-smi` |
| 磁盘 | 数据盘 ≥ 10 GB 空闲（adapter + checkpoint 很小，但输出目录要留量） | `df -h` |
| **省钱** | 先无卡模式做完步骤 1–2，再开机做步骤 3 起 | — |

::: tip 为什么先做 C03 再来
**训练报错里，九成是数据问题。** [C03](/training/p10/c03-alpaca-dataset) 已经帮你把数据验证过了，
这道题就专注在"**LoRA 配置怎么写、参数量什么样**"上，不重复踩数据的坑。
:::

## ④ 分步操作

### 步骤 1 · 无卡模式：写训练 YAML

```bash
# 控制台切「无卡模式」→ SSH 进去
conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory

# 参照仓库里的示例改写
ls examples/train_lora/
vi examples/train_lora/qwen3_lora_sft.yaml
```

一份可用的 LoRA SFT 配置：

```yaml
### model
model_name_or_path: /root/autodl-tmp/models/hub/models/Qwen/Qwen3-4B-Base
template: qwen3

### method
stage: sft
do_train: true
finetuning_type: lora
lora_rank: 8
lora_alpha: 16          # ⚠️ 不是 256！256 是白盒蒸馏的特殊取值
lora_dropout: 0.1
lora_target: all        # 或 q_proj,v_proj,k_proj,o_proj,...

### dataset
dataset: identity_modify
cutoff_len: 512
max_samples: 1000
overwrite_cache: true
preprocessing_num_workers: 4

### output
output_dir: /root/autodl-tmp/output/qwen3_4b_lora
logging_steps: 5
save_steps: 100
plot_loss: true
overwrite_output_dir: true

### train
per_device_train_batch_size: 1
gradient_accumulation_steps: 8
learning_rate: 2.0e-4
num_train_epochs: 3.0
lr_scheduler_type: cosine
warmup_ratio: 0.1
bf16: true
```

**这一步在选什么**

| 参数 | 含义 | **为什么这么选** |
|---|---|---|
| **`lora_rank: 8`** | 低秩矩阵的秩 r | [3-2](/training/p3/02-lora) 推荐 **4/8/16**。**先从 8 起步**，参数少、够用；效果不够再加 |
| **`lora_alpha: 16`** | 缩放系数，一般 **16–32** | ⚠️ **别照抄讲义里的 256**——那是 [白盒蒸馏 C09](/training/p10/c09-whitebox-distill) 的特殊任务取值。**常规 SFT 用 16 或 32** |
| **`lora_dropout: 0.1`** | 丢弃率 | [3-2](/training/p3/02-lora) 建议 0.2–0.3；**小模型 / 小数据集用 0.1**（讲义 `train.py` 实测也是 0.1） |
| **`lora_target: all`** | 挂到所有线性层（7 个） | 效果更好但参数更多。想省参数 → 只挂注意力 `q_proj,v_proj` 等 4 个 |
| **`learning_rate: 2e-4`** | 学习率 | **LoRA 的推荐区间是 `1e-4`~`5e-4`**（[3-3](/training/p3/03-qlora)）。2e-4 居中稳妥 |
| **`num_train_epochs: 3`** | 训练轮数 | 先 **3 轮**跑通。数据多则减小、数据少可加大——**别一上来就 50 轮** |
| **`finetuning_type: lora`** | 微调方法 | 与 `qlora` 只差**基座是否量化** → [C06](/training/p10/c06-qlora-vs-lora) |
| **`bf16: true`** | 计算精度 | 显存够就用 bf16；不够再考虑 4-bit（就是 QLoRA） |

::: warning `lora_alpha` 是这道题最容易踩的坑
讲义 [3-2](/training/p3/02-lora) 里 `train.py` 用的是 **`lora_alpha=256`**，远高于推荐区间 16–32。
那是**白盒蒸馏特殊任务**（学生要大幅贴合教师分布）的取值，**不是常规 SFT 的默认值**。

本案例用 **16**。**如果照抄 256，学习信号会过强，容易训崩。**
:::

> 🖼 **截图槽 `c05-01`** — 应截：你写好的 YAML（含 `lora_rank` / `lora_alpha` / `lora_target` / `learning_rate` 几行）
> 文件名：`c05/01-yaml.png`

### 步骤 2 · 开机前先确认显存账：LoRA 参数量有多少

先**算**，再跑——这是 Part 9 养成的习惯。

**用 [3-2](/training/p3/02-lora) 的估算式**：

```text
可训练参数 ≈ r × (d_in + d_out) × L × 7        ← 挂满 7 个线性层时
```

**Qwen3-4B + r=8 的粗算**（按 36 层、隐藏维度 2560 估）：

```text
r=8  →  8 × (2560 + 2560) × 36 × 7  ≈  10.3 M   ← 量级参考
```

换成 **r=16**，同样的式子翻倍 ≈ **20.6 M**。

| 项目 | r=8 | r=16 | 说明 |
|---|---|---|---|
| 可训练参数（估） | ≈ 10 M | ≈ 20 M | 与 **r 成正比**（其他项不变） |
| 占总参数（4B） | ≈ 0.26% | ≈ 0.52% | 这就是"LoRA 只训一点点"的意思 |
| 梯度 + 优化器 | 只按上面这部分算 | 同上 | **不是按 4B 算！** 参见 [C07](/training/p10/c07-ddp-zero2) |

::: tip 与 Part 9 的数字对齐
[9-15](/training/p9/15-end-to-end) 算过：Qwen3 系列**仅注意力**的 LoRA 参数 ≈ **12.58 M**，**全线性层** ≈ **46.40 M**（差 3.7 倍）。
本步骤的 10 M / 20 M 是**按公式粗算的量级**；真实值以步骤 3 的 `print_trainable_parameters()` 输出为准。
**两者数量级一致即算通过**——账本是给量级用的，不是给小数位用的（[9-B §9](/training/p9/B-formula-card)）。
:::

**预期**：能手算出量级（10 M / 20 M），并能说出"r 翻倍 → 参数翻倍"的依据。

> 🖼 **截图槽 `c05-02`** — 应截：你手写的参数量估算（公式 + 代入 + 结果）
> 文件名：`c05/02-param-calc.png`

### 步骤 3 · 开机训练，读出真实参数量

```bash
# 回控制台开机（本步起需要 GPU）
conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory

# 先只跑 50 步，验证链路
llamafactory-cli train examples/train_lora/qwen3_lora_sft.yaml max_steps=50
```

开另一个终端盯显存：

```bash
watch -n 1 nvidia-smi
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`max_steps=50` 先跑** | 覆盖 epoch 设置，只跑 50 步 | **先验证"链路通不通"，再决定花不花钱跑满**，是云上省钱的标准动作 |
| 看日志里的 `trainable params` | 框架会打印可训练参数量与占比 | **这就是校验步骤 2 粗算的地方** |
| 看 `loss` 是否下降 | 从初始值往下走 | 不降说明学习率 / 数据 / 模板有问题 |
| `watch -n 1 nvidia-smi` | 抓峰值显存 | LoRA 显存很稳，前几步就到位 |

**日志里要找的三样东西**：

```text
trainable params: 10,485,760 || all params: 4,022,000,000 || trainable%: 0.26
{'loss': 2.xxx, 'learning_rate': 2e-4, 'epoch': 0.05}
```

**预期**：日志打印 `trainable params`（**百分之零点几**）、loss 有下降趋势；终端无 OOM。

> 🖼 **截图槽 `c05-03`** — 应截：日志里 `trainable params ... trainable%` 那一行
> 文件名：`c05/03-trainable-params.png`

> 🖼 **截图槽 `c05-04`** — 应截：训练日志前几十行（含 loss 与 learning_rate）
> 文件名：`c05/04-train-log.png`

### 步骤 4 · 跑满 epoch 并存下 adapter

确认链路没问题后，再跑完整训练：

```bash
llamafactory-cli train examples/train_lora/qwen3_lora_sft.yaml
# 输出在 output_dir: /root/autodl-tmp/output/qwen3_4b_lora
ls -la /root/autodl-tmp/output/qwen3_4b_lora/
```

你应该看到：
- `adapter_model.safetensors`——**LoRA 权重本体**（只有几十 MB）
- `adapter_config.json`——记录 r / alpha / target
- `training_args.bin`、`trainer_log.jsonl` 等训练产物

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **存 adapter 不存整模型** | LoRA 只存新增的小矩阵 | **几十 MB vs 8 GB**，这是 LoRA 最大的实惠 |
| `save_steps` 调大 | 少存中间 checkpoint | 省钱又省盘；最终产物在训练结束时也会存 |
| 输出放**数据盘** | `output_dir` 指向 `/root/autodl-tmp/...` | 放系统盘重开机可能丢 |
| 要不要合并权重 | `llamafactory-cli export` | **本案例先不合并**——直接加载 adapter 更省时省盘；C09 才需要合并 |

**预期**：输出目录里有 `adapter_model.safetensors`（约几十 MB）+ `adapter_config.json`。

> 🖼 **截图槽 `c05-05`** — 应截：`ls -la` 输出目录，能看到 `adapter_model.safetensors` 与 `adapter_config.json`
> 文件名：`c05/05-adapter-files.png`

### 步骤 5 · 加载 adapter，对比微调前后

```bash
GRADIO_SERVER_PORT=6006 llamafactory-cli webui
# 需要时在本地开隧道：ssh -L 6006:127.0.0.1:6006 -p <端口> root@<地址>
```

在 WebUI 里配两项（其余同 [C02 步骤 5](/training/p10/c02-model-download-webui)）：

| 配置 | 值 | 说明 |
|---|---|---|
| **模型路径** | Qwen3-4B-Base 的绝对路径 | 与训练时**同一基座** |
| **微调方法** | **`lora`** | 关键一步：这次要加载 adapter |
| **LoRA 路径** | `/root/autodl-tmp/output/qwen3_4b_lora` | 指到你刚训出的目录 |

然后**同一个问题问两遍**：

1. **不加载 adapter**（微调方法选 `none`）→ 记录回答；
2. **加载 adapter** → 记录回答。

```text
问题：你是谁？请用一句话自我介绍。
微调前：<贴原模型回答>
微调后：<贴 adapter 回答>
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **对比要"同题同参"** | 同一个问题、同样解码参数 | 否则差异说不清是 adapter 带来的还是采样随机性 |
| 只挂 adapter 不改基座 | LoRA 推理时把 ΔW 加上 | **基座没动过**，所以能随意切回 `none` 对照 |
| 效果不明显也正常 | 数据集小、只训 3 轮 | **本步骤验证的是"改动能被观察到"**，不是刷榜 |

**预期**：两次回答有可观察的差异；能说清差异来自 adapter。

> 🖼 **截图槽 `c05-06`** — 应截：**同一问题的前后两次回答**（一张图里含微调前、微调后）
> 文件名：`c05/06-before-after.png`

### 步骤 6 · 综合环节：r=8 → r=16 对照

把 YAML 里 `lora_rank: 8` 改成 `16`（`output_dir` 换个新目录），**限步再训一次**：

```bash
llamafactory-cli train examples/train_lora/qwen3_lora_sft.yaml \
  output_dir=/root/autodl-tmp/output/qwen3_4b_lora_r16 \
  max_steps=50
```

对比两次日志：

| 项 | r=8 | r=16 | 规律 |
|---|---|---|---|
| `trainable params` | 屏幕读数 A | 屏幕读数 B | **B ≈ 2A** |
| `trainable%` | ≈ 0.26% | ≈ 0.52% | 同样翻倍 |
| 峰值显存 | 读数 C | 读数 D | D 略大于 C，**但远不到翻倍** |
| adapter 文件大小 | ≈ X MB | ≈ 2X MB | 与参数量同比例 |

::: danger 这里有个必须想明白的问题
**"r 翻倍，参数量翻倍"——但为什么显存不是翻倍？**

因为 LoRA 的显存里，**大头是基座权重（4B，好几个 GB）**，
LoRA 参数那部分（10 M → 20 M，才几十 MB）只占零头。
**所以 r 加倍，参数量加倍，总显存只涨一点点。**

这正是 [9-15](/training/p9/15-end-to-end) 说的"LoRA 只动一小块账"的直观体现。
:::

**预期**：能给出"参数量翻倍 / 显存只微涨"的对照，并能解释原因。

> 🖼 **截图槽 `c05-07`** — 应截：r=8 与 r=16 两次日志的 `trainable params` 对照
> 文件名：`c05/07-rank-compare.png`

### 步骤 7 · 关机

```bash
exit
# ⚠️ 这只是断开 SSH —— 必须回 AutoDL 控制台点「关机」
```

| 做法 | 结果 |
|---|---|
| **关机（不释放）** | 停止计费，数据盘与模型保留 → 下次继续 |
| 只关 SSH 窗口 | ⚠️ **实例仍在跑、仍在计费** |

> 🖼 **截图槽 `c05-08`** — 应截：AutoDL 控制台显示实例「已关机」
> 文件名：`c05/08-shutdown.png`

## ⑤ 预期结果与判定标准

| # | 检查项 | 判定标准（必须看到） |
|---|---|---|
| 1 | YAML 完整 | 含 model / method / dataset / output / train 五段关键项 |
| 2 | **三参数能解释** | 能说清 `r` / `alpha` / `dropout` 各是什么、为什么取这值 |
| 3 | **没照抄 alpha=256** | 用的是 16–32 区间，并能说明 256 是蒸馏特例 |
| 4 | **参数估算做了** | 有手算的量级（10 M / 20 M） |
| 5 | **参数量读到了** | 日志里 `trainable params` 与手算**同数量级** |
| 6 | **占比说得出** | 能说出可训练参数占总参数的百分之几 |
| 7 | 训练跑通 | 日志有 loss 输出，且呈下降趋势 |
| 8 | adapter 已存 | `adapter_model.safetensors` + `adapter_config.json` 在位，几十 MB |
| 9 | **前后对比做了** | 同题两次回答，有可观察差异 |
| 10 | **r 对照做了** | 有 r=8 vs r=16 的参数/显存对照 |
| 11 | **理解性目标：显存不翻倍** | 能解释"参数量翻倍但显存只微涨"的原因 |
| 12 | **理解性目标：只训一点点** | 能说清"LoRA 的梯度/优化器只按可训练参数算，不按 4B 算" |
| 13 | **路径都在数据盘** | 模型、输出、数据集都在 `/root/autodl-tmp` |
| 14 | 已关机 | 控制台显示「已关机」 |

> 第 2、6、11、12 项是重点：**会跑训练只是入门，会解释"参数为什么这么少、显存为什么不翻倍"才是这道题的目标。**

## ⑥ 常见报错

| 报错 | 原因 | 处置 |
|---|---|---|
| **`CUDA out of memory`** | batch/序列太大，或选了 bf16 但卡小 | 降 `per_device_train_batch_size`、加 `gradient_accumulation_steps`、降 `cutoff_len`；或改走 [C06 QLoRA](/training/p10/c06-qlora-vs-lora) |
| `Unknown dataset: identity_modify` | 数据集没注册 | 回 [C03 步骤 4](/training/p10/c03-alpaca-dataset) 注册 |
| `KeyError: 'instruction'` | 注册 `columns` 映射与文件不符 | 核对列名 |
| **loss 不降 / NaN** | `lora_alpha` 照抄了 256，或 lr 过大 | 把 alpha 改回 16–32；lr 降到 1e-4 |
| `RANK` / `alpha` 没生效 | 忘了 `output_dir` 换新目录，被覆盖 | 每次改参**换一个输出目录**，否则产物混在一起 |
| 加载 adapter 报"找不到权重" | 微调方法选了 `lora` 但 LoRA 路径没填 / 填错 | 路径指到含 `adapter_config.json` 的那一层 |
| 微调前后**完全一样** | adapter 没真正加载 | 确认微调方法 = `lora`、LoRA 路径正确；重启一次 WebUI |
| 输出目录在系统盘 | `output_dir` 用了相对路径 | 写成绝对路径且指向 `/root/autodl-tmp` |
| `No space left on device` | checkpoint 存太多 / 输出在系统盘 | 调大 `save_steps`；输出移数据盘 |
| `ModuleNotFoundError: peft` | 环境不全 | 回 [C01 步骤 5](/training/p10/c01-llamafactory-env) 补装 |
| 重开机后找不到 adapter | 输出写在了系统盘 | 迁到数据盘；检查 `output_dir` |

## ⑦ 延伸

1. **改成只挂注意力**：`lora_target: q_proj,v_proj`（4 个），对比参数量与效果。**为什么 [9-15](/training/p9/15-end-to-end) 说 `12.58 M` 和 `46.40 M` 差 3.7 倍？**
2. **调 `lora_dropout`**：从 0.1 提到 0.3，观察小数据集上的过拟合是否缓解。**dropout 什么时候该调大？**
3. **换数据集**：用 [C04](/training/p10/c04-sharegpt-dataset) 的多轮 `finance_data` 再训一次，体会多轮 SFT 的 loss 曲线差异。
4. **合并权重**：`llamafactory-cli export` 把 adapter 合进基座，得到一个完整的 4B 模型。**什么时候必须合并？** → 提示：[C09 蒸馏](/training/p10/c09-whitebox-distill) 拿它当教师。
5. **训久一点**：把 epoch 从 3 提到 10，看 loss 与回答质量怎么变。**过拟合长什么样？**
6. **把 LoRA 与全参对比**：用 `finetuning_type: full` 再跑一次（限步），对比显存与参数量——**这就是 [C07](/training/p10/c07-ddp-zero2) 那张账的现实版**。

---

> 下一案例：[C06 QLoRA(4-bit) vs LoRA：显存与效果对照](/training/p10/c06-qlora-vs-lora) ｜ [案例库总览](/training/p10/) ｜ [Part 3 末页题目](/training/p3/08-practice)
