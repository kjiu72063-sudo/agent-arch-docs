---
title: C06 · QLoRA(4-bit) vs LoRA：显存与效果对照
---

# C06 · QLoRA(4-bit) vs LoRA：显存与效果对照

::: tip 案例信息
**所属 Part**：[Part 3 · 方法与加速](/training/p3/01-methods-overview) ｜ **难度**：综合 ｜ **耗时**：60–100 分钟
**对应讲义**：[3-3 QLoRA 与 bitsandbytes](/training/p3/03-qlora)、[3-8 实战三则](/training/p3/08-practice)、[1-9 调参难点（上）· 量化](/training/p1/09-tuning-quant)
**前置**：[C05](/training/p10/c05-lora-sft) 已完成（LoRA 的 YAML 与 adapter 已产出）
:::

::: warning 成本：本案例只租 1 张卡，约 ¥4–10
| 项 | 内容 |
|---|---|
| **需要几张卡** | **1 张**（24 GB 档；若想更真实地体现 QLoRA 的"省"，用 **16 GB 档**对比更明显） |
| **预估费用** | 按量计费 **约 ¥4–10**（**两轮**训练：LoRA 一轮 + QLoRA 一轮） |
| **省钱姿势** | ① 两轮都用 `max_steps=50` **限步对照**，只比**显存读数与参数量**，不为收敛跑满<br/>② **无卡模式**写 YAML、改 `quantization_bit`，只在这两轮真跑时开卡<br/>③ 复用 [C05](/training/p10/c05-lora-sft) 的数据集与模型，**不重新下载**<br/>④ LoRA 那一轮若 C05 已跑过，**可直接引用它的读数**，只真跑 QLoRA 一轮 → 费用减半<br/>⑤ 做完**立刻控制台关机** |
:::

::: info 这道题的"对照"有一半可以复用
**LoRA 的读数来自 [C05](/training/p10/c05-lora-sft)**（你刚跑过）。
本案例**只需要真跑 QLoRA 那一轮**，然后把两者的**显存、参数量、文件大小**放一起比。
这就是"降本"的核心思路：**对照项能复用/能算，就不重复花钱。**
:::

## ① 题目

> 在同一模型（Qwen3-4B-Base）、同一数据集上，**分别**用 **LoRA** 和 **QLoRA(4-bit)** 做一次微调（各限步），要求：
>
> 1. **说清 QLoRA 的三件事**：4-bit 量化 / 混合精度"存 4-bit 算 16-bit" / 双量化；
> 2. **写出 YAML 的关键差异**（`quantization_bit` 等），并说明**为什么只差这么一点**；
> 3. 两轮训练各记一次**峰值显存**与 `trainable params`，列表对照；
> 4. 解释：**为什么 QLoRA 省的是"基座"，不是"adapter"**；
> 5. **综合环节**：把两轮训出的 adapter 都加载做同题对比，给出"什么场景选哪个"的结论——**并说明哪些结论是实测的、哪些是推断的**。

**一句话目标**：把"QLoRA 更省显存"这句口号，换成**一张有读数的对照表 + 一句敢下结论的取舍建议**。

## ② 你会练到什么

| 技能点 | 对应小节 |
|---|---|
| **QLoRA 三机制**：4-bit 量化 / 混合精度 / 双量化 | [3-3](/training/p3/03-qlora) · 三机制 |
| **学习率差异**：LoRA `1e-4~5e-4` vs QLoRA `5e-5~2e-4` | [3-3](/training/p3/03-qlora) · 学习率 |
| **bitsandbytes 三步**：归一化 / 量化 NF4 / 反量化 | [3-3](/training/p3/03-qlora) |
| **`quantization_bit` 与 `finetuning_type` 的关系** | [1-9](/training/p1/09-tuning-quant) |
| **实测 vs 推断的边界**（诚实报告） | [C07](/training/p10/c07-ddp-zero2) · ①-5 |

## ③ 前置条件

| 项 | 要求 | 怎么核对 |
|---|---|---|
| 环境 | C01 已完成，`llama_env` 可用 | `conda activate llama_env && llamafactory-cli --help` |
| **bitsandbytes** | **必须已装**（QLoRA 的 4-bit 靠它） | `python -c "import bitsandbytes as bnb; print(bnb.__version__)"` |
| 模型 | Qwen3-4B-Base 在数据盘 | `du -sh .../Qwen3-4B-Base` 约 8G |
| 数据集 | C05 用的那套（`identity_modify` 或内置 `identity`） | `grep identity data/dataset_info.json` |
| **C05 的读数** | LoRA 那一轮的峰值显存 + `trainable params` | 翻 [C05 步骤 3、6 的截图](/training/p10/c05-lora-sft) |
| GPU | **≥ 16 GB 显存**（QLoRA 训 4B 约 6–10 GB，比 LoRA 明显低） | `nvidia-smi` |
| **省钱** | 无卡模式写完两套 YAML 再开机 | — |

::: tip 为什么建议用 16 GB 的卡来对比
**在 24 GB 卡上跑 QLoRA，省显存的感受不明显**（本来 LoRA 就跑得下）。
若目标就是体会 QLoRA 的价值，**用 16 GB 档的卡**——LoRA 会紧、QLoRA 会松，差别一眼可见。
:::

## ④ 分步操作

### 步骤 1 · 无卡模式：看清两套配置只差什么

```bash
# 控制台切「无卡模式」→ SSH 进去
conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory
cp examples/train_lora/qwen3_lora_sft.yaml examples/train_lora/qwen3_qlora_sft.yaml
vi examples/train_lora/qwen3_qlora_sft.yaml
```

**两套 YAML 的差异**（其余全部相同）：

| 参数 | LoRA | **QLoRA** | 为什么 |
|---|---|---|---|
| `finetuning_type` | `lora` | `lora` | **不变**——QLoRA 仍是 LoRA 方法，只是基座被量化了 |
| **`quantization_bit`** | 不写（或 `none`） | **`4`** | ⭐ **唯一的核心差异**：让 bitsandbytes 把基座权重压到 4-bit |
| `quantization_method` | 不写 | 通常默认 `bnb` | 也可选 `hqq` / `eetq`，见 [1-9](/training/p1/09-tuning-quant) |
| **`learning_rate`** | `2e-4` | **`1e-4`** | [3-3](/training/p3/03-qlora)：**QLoRA 推荐 `5e-5`~`2e-4`，比 LoRA 更低**——量化后信号更"粗"，步子要小 |
| `lora_rank` / `alpha` / `dropout` | 8 / 16 / 0.1 | **同左** | adapter 部分完全一样，**不受量化影响** |
| `output_dir` | `.../lora` | `.../qlora` | **必须分开**，否则产物互相覆盖 |

对应的关键几行：

```yaml
### method
stage: sft
do_train: true
finetuning_type: lora
quantization_bit: 4        # ⭐ QLoRA 就靠这一行
lora_rank: 8
lora_alpha: 16
lora_dropout: 0.1
lora_target: all

### train
learning_rate: 1.0e-4      # QLoRA 用更低的学习率
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`quantization_bit: 4`** | 基座权重 4-bit（NF4） | QLoRA 的定义性配置。**写 `8` 就是 8-bit 量化**（3-8 实战用过 8-bit） |
| **`finetuning_type` 保持 `lora`** | 方法不变 | **这是理解 QLoRA 的关键**：它不是新方法，是"LoRA + 量化基座" |
| **学习率降一档** | 1e-4 vs 2e-4 | 量化引入误差，学习率太高会震荡 |
| 其余项不动 | r / alpha / target 一致 | **对照实验要控制变量**——只有量化这一项变，差异才能归因 |

> 🖼 **截图槽 `c06-01`** — 应截：两套 YAML 并排（或 `diff` 输出），**突出 `quantization_bit` 与 `learning_rate` 两行**
> 文件名：`c06/01-yaml-diff.png`

### 步骤 2 · 先想清楚：QLoRA 到底省了哪一块

在跑之前**先把账说清**，否则读数出来也解释不了：

| 显存组成 | LoRA | **QLoRA(4-bit)** | 变化 |
|---|---|---|---|
| **基座权重** | bf16：4B × 2 B ≈ **8 GB** | 4-bit：4B × 0.5 B ≈ **2 GB** | ⭐ **降 4 倍——省的就是这块** |
| **LoRA adapter 参数** | bf16（16-bit） | **同样 bf16（16-bit）** | **不变** ⚠️ |
| **梯度（adapter 的）** | 按可训练参数算 | 按可训练参数算 | **不变** ⚠️ |
| **优化器状态（adapter 的）** | 按可训练参数算 | 按可训练参数算 | **不变** ⚠️ |
| **激活值** | 与序列/batch 相关 | 与序列/batch 相关 | 基本不变 |

::: danger 最关键的认知：QLoRA 省的是"存权重"，不是"算"
[3-3](/training/p3/03-qlora) 的三机制里有一条：**"存 4-bit，算 16-bit"**——
基座权重以 **4-bit 存放**，但**参与矩阵乘法前会被反量化回 16-bit**。
所以：
- **省**：静态的权重占用（8 GB → 2 GB）
- **不省**：adapter 的参数/梯度/优化器（它们**始终是 16-bit**）
- **代价**：反量化有计算开销 + 量化损失精度

**一句话**：QLoRA 用"一点点计算开销 + 一点精度损失"，换来"基座权重降到 1/4"。
:::

**预期**：能说出"省的是基座权重那块（约 8 GB → 2 GB），adapter 部分不变"。

> 🖼 **截图槽 `c06-02`** — 应截：你手写的"显存组成 → 哪块变、哪块不变"表格
> 文件名：`c06/02-ledger-split.png`

### 步骤 3 · 真跑 QLoRA 那一轮（LoRA 的读数直接用 C05 的）

```bash
# 回控制台开机
conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory

# 限步跑 QLoRA
llamafactory-cli train examples/train_lora/qwen3_qlora_sft.yaml max_steps=50
```

另开终端盯峰值：

```bash
watch -n 1 nvidia-smi
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **只真跑 QLoRA 这一轮** | LoRA 那一轮 C05 已做过 | **对照实验的"控制组"可以复用**，不必重跑（除非你的卡/数据变了） |
| `max_steps=50` | 限步 | 重演上文：**目的是量显存，不是训收敛** |
| 两轮**同样步数、同样 batch** | 50 步、batch=1 | **控制变量**，否则显存差异说不清是谁造成的 |
| 抓"峰值" | 峰值决定 OOM 与否 | 与 C05 / C07 同口径 |

**预期**：QLoRA 这轮的峰值显存**明显低于 C05 记录的 LoRA 峰值**；`trainable params` 与 LoRA 那轮**几乎相同**（因为 adapter 结构一样）。

> 🖼 **截图槽 `c06-03`** — 应截：QLoRA 训练的 `nvidia-smi` 峰值（能看清 python 进程占用）
> 文件名：`c06/03-qlora-peak.png`

> 🖼 **截图槽 `c06-04`** — 应截：QLoRA 日志里 `trainable params` 那一行（与 C05 对照）
> 文件名：`c06/04-qlora-params.png`

### 步骤 4 · 把两轮的读数拼成对照表

把 [C05](/training/p10/c05-lora-sft) 的 LoRA 读数与本轮的 QLoRA 读数填进同一张表：

| 项 | **LoRA**（C05 读数） | **QLoRA 4-bit**（本轮读数） | 差异 |
|---|---|---|---|
| 基座权重占用（理论） | ≈ 8 GB（bf16） | ≈ 2 GB（4-bit） | **↓ 约 4 倍** |
| `trainable params` | A | ≈ A | **基本不变** |
| `trainable%` | ≈ 0.26% | ≈ 0.26% | 不变 |
| **峰值显存（实测）** | C GB | D GB | **D < C** |
| 训练耗时（同样 50 步） | X s | Y s | 常略慢（反量化开销） |
| adapter 文件大小 | ≈ M MB | ≈ M MB | 不变 |
| 学习率 | 2e-4 | 1e-4 | 更低 |

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **"峰值显存差"要解释** | 差值应大致等于"基座权重省下的量" | 若差值远小于理论，说明**还有别的项在占大头**（激活值？CUDA 上下文？） |
| **耗时也记** | 反量化有计算开销 | QLoRA **通常略慢**——省显存不是白来的 |
| 声明口径：GB / GiB | 实测 MiB ÷ 1024 = GiB | 与 [C07](/training/p10/c07-ddp-zero2) 同规矩 |

::: warning 别把"峰值差"直接说成"省了 6 GB"
实测峰值差可能**小于**理论权重差（8 − 2 = 6 GB），也可能**接近**。原因：
- 权重省了 6 GB，但 `trainable%` 那点开销不变；
- 更可能是**别的项（激活值、CUDA 上下文）占比变了**，稀释了相对差异。

**要写的是"实测差 = ? GB"，并用"权重理论差 ≈ 6 GB"作参照，然后解释为什么两者不完全相等。**
:::

**预期**：对照表填完，且能说出"实测差与权重理论差的关系"。

> 🖼 **截图槽 `c06-05`** — 应截：你的 LoRA vs QLoRA 对照表（含峰值显存与参数量）
> 文件名：`c06/05-compare-table.png`

### 步骤 5 · 综合环节：加载两个 adapter 做同题对比

沿用 [C05 步骤 5](/training/p10/c05-lora-sft) 的两轮问答法，这次是**三方**对比：

| 配置 | 微调方法 | LoRA 路径 |
|---|---|---|
| 基座（对照） | `none` | — |
| **LoRA** | `lora` | `.../output/qwen3_4b_lora` |
| **QLoRA** | `lora` | `.../output/qwen3_qlora` |

```text
问题：给"退改签"写一句客服口径的说明。
基座：<贴回答>
LoRA：<贴回答>
QLoRA：<贴回答>
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **三方对比而不是两方** | 加一个"未微调"基线 | **没有基线，"微调有没有用"就说不清** |
| 同题同解码参数 | 控制变量 | 否则差异可能只是采样随机 |
| **效果差异要诚实** | 50 步的短训，两 adapter 差异可能很小 | **不要为了下结论而夸大**——短训不是为了比效果 |

::: danger 这一节的诚实边界
**你只跑了 50 步。** 在这个前提下：
- **可以说**："在本配置下，QLoRA 的峰值显存低于 LoRA，且两者 adapter 结构一致。"
- **不可以说**："QLoRA 效果不如 LoRA"——**训练步数太少，两者都远未收敛**，任何效果结论都不成立。

**这正是 [C07](/training/p10/c07-ddp-zero2) 那条规矩：不许把没跑过的结论说成实测结论。**
:::

**预期**：三方回答都拿到；能明确说出"哪些是实测、哪些不能下结论"。

> 🖼 **截图槽 `c06-06`** — 应截：三方的同题回答（一张图三栏，或两图对照）
> 文件名：`c06/06-three-way.png`

### 步骤 6 · 综合环节：给出取舍结论

| 场景 | 选哪个 | 理由 |
|---|---|---|
| 显存充足（≥ 24 GB）、追求训练稳定 | **LoRA** | 无反量化开销、精度无损，训练更快更稳 |
| **显存紧张（16 GB 甚至更小）** | **QLoRA** | 基座权重降到 1/4，是**跑得起来 vs 跑不起来**的分界 |
| 要训更大的模型（7B+）而卡不大 | **QLoRA** | 同上，这是 QLoRA 最主要的价值场景 |
| 追求最高最终效果、不计成本 | **LoRA / 全参** | 量化毕竟有精度损失 |

::: tip 一句话决策
**QLoRA 不是"更好的 LoRA"，是"显存不够时的 LoRA"。**
能全精度跑就用 LoRA；跑不起来才上 QLoRA。**这是工程取舍，不是优劣排序。**
:::

**预期**：能给出带条件的结论（什么卡、什么模型用哪个），而非笼统的"QLoRA 更好"。

> 🖼 **截图槽 `c06-07`** — 应截：你写的"场景 → 选哪个 → 理由"取舍表
> 文件名：`c06/07-decision.png`

### 步骤 7 · 关机

```bash
exit
# ⚠️ 回 AutoDL 控制台点「关机」
```

> 🖼 **截图槽 `c06-08`** — 应截：控制台显示「已关机」
> 文件名：`c06/08-shutdown.png`

## ⑤ 预期结果与判定标准

| # | 检查项 | 判定标准（必须看到） |
|---|---|---|
| 1 | **三机制说得出** | 能说清 4-bit 量化 / 存4算16 / 双量化 |
| 2 | **YAML 差异最小化** | 能指出两套配置只差 `quantization_bit`（+学习率） |
| 3 | **理解为什么只差这一点** | 能说清"QLoRA = LoRA + 量化基座，方法本身不变" |
| 4 | **账本拆分正确** | 有"哪块变、哪块不变"的表：变的是基座权重 |
| 5 | **QLoRA 真跑了** | 有 QLoRA 的峰值显存读数 + 日志 |
| 6 | **参数量几乎相同** | 两轮 `trainable params` 基本一致 |
| 7 | **对照表完整** | 权重/参数量/峰值/耗时/adapter 大小五列都有 |
| 8 | **差值会解释** | 能解释"实测差"与"权重理论差（≈6 GB）"的关系 |
| 9 | **三方对比做了** | 基座 / LoRA / QLoRA 同题回答都有 |
| 10 | **取舍有结论** | 给出带条件的场景化建议 |
| 11 | **理解性目标：省的不是 adapter** | 能说清 adapter 始终 16-bit，QLoRA 省的是基座 |
| 12 | **实测与推断分开** | 明确声明哪些结论成立、哪些因步数太少不能下 |
| 13 | 已关机 | 控制台显示「已关机」 |

> 第 3、4、11、12 项是重点：**跑两轮不难；难的是"知道省在哪、知道什么话不能说"。**

## ⑥ 常见报错

| 报错 | 原因 | 处置 |
|---|---|---|
| **`ModuleNotFoundError: bitsandbytes`** | 没装 / 环境不对 | `pip install bitsandbytes`（[C01 步骤 5](/training/p10/c01-llamafactory-env)） |
| `CUDA out of memory` | 卡太小或 batch 大 | 降 batch / `cutoff_len`；确认 `quantization_bit: 4` 已生效 |
| **QLoRA 显存没降多少** | `quantization_bit` 没写对（如写了 8，或写在了错位置） | 确认在 method 段写 `quantization_bit: 4`；看启动日志是否加载 bnb |
| **loss 震荡 / NaN** | 学习率没降，仍用 LoRA 的 2e-4 | QLoRA 用 `1e-4` 或更低 |
| **两轮产物混在一起** | `output_dir` 没分开 | LoRA / QLoRA 各一个目录 |
| QLoRA 报"权重加载失败" | bnb 与 torch/CUDA 版本不匹配 | 用 [C01](/training/p10/c01-llamafactory-env) 那套已验证的版本组合 |
| adapter 加载后无变化 | 微调方法选错（选了 `qlora` 而不是 `lora` 加载） | 加载 adapter 时**微调方法仍选 `lora`**；量化只影响训练时的基座 |
| 训练比 LoRA 慢很多 | 反量化开销 | **正常**。省显存的代价就是这点头开销 |
| `trainable%` 与 LoRA 不一致 | 两轮 r/target 改了 | 对照实验要控制变量，只改量化这一项 |
| 显存省了但效果差很多 | 步数太少 / lr 过低 | 短训不作为效果依据；要评效果得跑满 |

## ⑦ 延伸

1. **换成 8-bit**：`quantization_bit: 8` 再跑一轮，看显存落在 LoRA 与 4-bit 之间哪个位置。**为什么 8-bit 省得不多？**
2. **换成 `hqq` / `eetq`**：`quantization_method` 换一档（[1-9](/training/p1/09-tuning-quant)），对比显存与速度。**不同量化后端差别在哪？**
3. **上 7B 试一次**：在 16 GB 卡上用 QLoRA 跑 7B，看是否跑得起来；再用 LoRA 跑一次，多半会 OOM。**这就是 QLoRA 的真实价值场景。**
4. **合并导出**：把 QLoRA 的 adapter `export` 出来，确认合并后的模型是 **bf16 完整模型**。**为什么 4-bit 只在训练时？**
5. **把差值算进账本**：用 [9-B 的字节表](/training/p9/B-formula-card)（INT4 = 0.5 B/参数）手算基座权重，与实测差对照。
6. **跑满再比效果**：把两轮都跑满 epoch，再做三方对比。**这才是"效果对照"的合法前提**——本案例的短训结论不可外推。

---

> 上一案例：[C05 用 LoRA 对 Qwen3-4B-Base 做一次完整 SFT](/training/p10/c05-lora-sft) ｜ [案例库总览](/training/p10/) ｜ [Part 3 末页题目](/training/p3/08-practice)
