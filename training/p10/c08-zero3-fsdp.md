---
title: C08 · 单卡 offload 真跑 + FSDP 配置对照
---

# C08 · 单卡 offload 真跑 + FSDP 配置对照

::: tip 案例信息
**所属 Part**：[Part 4 · 分布式训练](/training/p4/01-basics) ｜ **难度**：综合 ｜ **耗时**：50–90 分钟
**对应讲义**：[4-12 DeepSpeed 与 ZeRO](/training/p4/12-deepspeed-zero)、[4-13 FSDP 与 DeepSpeed 对比](/training/p4/13-fsdp)、[4-14 其他优化与实战](/training/p4/14-optim-practice)、[9-B 公式速查卡](/training/p9/B-formula-card)
**前置**：[C07](/training/p10/c07-ddp-zero2) 已完成（知道你那张卡的实测盘子）
:::

::: warning 成本：本案例也只租 1 张卡，约 ¥3–8
**offload 的本职场景就是"单卡装不下"**——所以它在单卡上最好验证，不需要多卡。

| 项 | 内容 |
|---|---|
| **需要几张卡** | **1 张**（建议 24 GB 档；若要做"装不下"的对照，卡小一点反而更容易触发） |
| **预估费用** | 按量计费 **约 ¥3–8**（offload 会慢，但在机时长的绝对值仍不大） |
| **省钱姿势** | ① 无卡模式先改配置、读 `ds_z3_config.json`、算账本<br/>② 真跑只用 `max_steps=10`，看的是**显存能不能撑住**不是收敛<br/>③ offload 训练**很慢**，别跑长——跑长是双倍浪费（卡钱 + 时间）<br/>④ 做完立刻关机 |
:::

::: info 为什么 FSDP 一侧只做"配置对照"
FSDP 与 DeepSpeed 的**内核是同一件事**（都是 ZeRO-3：切片 + AllGather + ReduceScatter）——
这一点 [4-13](/training/p4/13-fsdp) 已用四条相同点讲透。

**所以本案例的取舍是**：
- **DeepSpeed ZeRO-3 + CPU offload 一侧真跑**——因为它是唯一能在单卡上造出"原本装不下"效果的方案（把状态搬到 CPU 内存），真跑有独特价值；
- **FSDP 一侧做配置与机制对照**——它的行为已由 4-13 的八维对照表覆盖，再租一张卡真跑，边际收益远低于成本。

**结论仍然要下**，只是依据从"两套都跑"变成"**一套真跑 + 一套机制/配置对照 + 账本推演**"。
:::

## ① 题目

> 在 **1 张卡**上完成 ZeRO-3 + CPU offload 的真跑，并与 FSDP 做配置级对照，要求：
>
> 1. **说清 offload 解决什么**：用 [4-12](/training/p4/12-deepspeed-zero) 的显存五项，指出 offload 把哪几项搬到了哪里；
> 2. **真跑**：在单卡上开 **ZeRO-3 + CPU offload** 跑一次训练，记录它**能否跑起来**、`nvidia-smi` 峰值、以及训练速度；
> 3. **做对照**：同一模型**关掉 offload**（或降 ZeRO 阶段）再跑一次，对比"能不能跑起来"与"快慢"；
> 4. **FSDP 对照**：给出 FSDP 的等价配置写法，并从 **4-13 的八维**里挑 **4 个**维度说明"这里会不一样"；
> 5. **下结论**：写出一条有条件的选型建议（不是"X 比 Y 好"，而是"**在什么条件下选 X**"）。

**一句话目标**：亲手体验"**用通信和速度换显存**"这笔交易的汇率，而不是背下"ZeRO-3 更省显存"这句话。

## ② 你会练到什么

| 技能点 | 对应小节 |
|---|---|
| **offload 搬的是什么**：梯度 / 优化器状态 → CPU 内存 | [4-12](/training/p4/12-deepspeed-zero) · (1) 四项优化 + [4-14](/training/p4/14-optim-practice) · §1 第 4 项 |
| **ZeRO-3 与 ZeRO-2 的区别**：参数也被切 | [4-12](/training/p4/12-deepspeed-zero) · 决策表 |
| **"省显存"的代价**：通信变重、速度变慢 | [4-12](/training/p4/12-deepspeed-zero) · 三条铁律第 2 条 |
| **FSDP ≈ ZeRO-3**：四条相同点 | [4-13](/training/p4/13-fsdp) · (1) FSDP 详解 |
| **选型的真实形态**：带条件的建议 | [4-13](/training/p4/13-fsdp) · (3) 决策树 |

## ③ 前置条件

| 项 | 要求 | 怎么核对 |
|---|---|---|
| 环境 | [C07](/training/p10/c07-ddp-zero2) 已完成，`deepspeed` 可用 | `python -c "import deepspeed; print(deepspeed.__version__)"` |
| GPU | **1 张卡**，≥ 16 GB | `nvidia-smi` |
| 模型 | Qwen3-1.7B（已有） | `ls /root/autodl-tmp/models/Qwen/Qwen3-1.7B` |
| 配置 | `examples/deepspeed/ds_z3_config.json` 存在 | `ls LLaMA-Factory/examples/deepspeed/` |
| **CPU 内存** | **≥ 32 GB**（offload 要往这搬！） | `free -h` 看 `Mem` 那一行 |
| 磁盘 | 数据盘 ≥ 10 GB（offload 也可能落 NVMe） | `df -h` |

::: danger offload 的一个隐藏前提：CPU 内存要够
offload 不是"把显存变没了"，是**把数据搬到 CPU 内存**。
**CPU 内存不够，offload 一样会爆**（只是报错从 OOM 变成被系统 OOM Killer 杀掉）。

开跑前一定先 `free -h`。AutoDL 实例的 CPU 内存通常是显存的几倍，一般都够——但要确认。
:::

## ④ 分步操作

### 步骤 1 · 先算：这个模型原本装得下吗

```text
模型 Qwen3-1.7B，按 1.7 B 参数计，16 B/参数口径（[9-B §4](/training/p9/B-formula-card)）

全参训练静态账 = 1.7 × 16 = 27.2 GB
你那 1 张卡的容量 = <步骤 2 实测的 GiB 数>
```

**这一步在选什么**：

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| 算**全参**还是 **LoRA** | 全参要存全部优化器状态 | **本案例要用全参制造"装不下"**，才能体现 offload 的价值。LoRA 太小，offload 与否都放得下 |
| 用 16 B 还是 12 B 口径 | 见 [9-B §4](/training/p9/B-formula-card) | 无论哪套，1.7B 都在 20–27 GB 区间，**24 GB 卡就是卡在边缘**——这正是我们要的场景 |
| 卡容量按 GiB 还是 GB | `GiB = MiB ÷ 1024` | 账本是 GB、实测是 GiB，**先都换成 GB 再比** |

> 🖼 **截图槽 `c08-01`** — 应截：你的"装得下吗"手算过程（含口径与结论）
> 文件名：`c08/01-fit-calc.png`

### 步骤 2 · 记下单卡盘子与 CPU 内存

```bash
nvidia-smi          # 显存总量
free -h             # CPU 内存总量（offload 的目的地！）
```

| 要记的数 | 为什么 |
|---|---|
| 显存总量（MiB） | 分母，判断"装不装得下" |
| **CPU 内存总量** | offload 的**目的地容量**——它不够，offload 也救不了 |
| 两者比值 | 一般是 2–4 倍，决定了 offload 能搬多少 |

> 🖼 **截图槽 `c08-02`** — 应截：`nvidia-smi` + `free -h` 一并的输出
> 文件名：`c08/02-gpu-cpu-mem.png`

### 步骤 3 · 配好 ZeRO-3 + offload

```bash
cd /root/autodl-tmp/LLaMA-Factory
cat examples/deepspeed/ds_z3_config.json
```

关键字段（对着自己的文件核）：

```json
{
  "zero_optimization": {
    "stage": 3,
    "offload_optimizer": { "device": "cpu" },
    "offload_param":     { "device": "cpu" }
  }
}
```

**这一步在选什么**：

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| `stage: 3` | 切优化器状态 + 梯度 + **参数** | 单卡装不下时必须切参数；ZeRO-2 的参数每卡一份，帮不上忙 |
| `offload_optimizer.device` | 优化器状态搬到哪 | `cpu` = 搬到内存。也有 `nvme`（ZeRO-Infinity），更省显存但更慢 |
| `offload_param.device` | 参数搬到哪 | 同理。**这一项是"能跑起来"的关键** |
| 为什么不 offload 梯度 | 梯度按需产生、随用随丢 | 通常不必单独 offload；优化器状态和参数才是常驻大头 |
| `nvme` vs `cpu` | NVMe 容量更大但**慢一个量级** | 先试 `cpu`；真放不下再上 `nvme` |

::: warning offload 的代价是"慢"
`offload_optimizer` + `offload_param` 一起开，每一步都要**把参数从内存搬到显存、算完再搬回去**。
PCIe 带宽远低于显存带宽 → **训练会明显变慢**（常见慢数倍）。

**这就是这笔交易的汇率：拿"慢"换"能跑"。** 步骤 5 要把这个汇率量出来。
:::

> 🖼 **截图槽 `c08-03`** — 应截：`ds_z3_config.json` 里 `stage` 与两个 `offload_*` 字段
> 文件名：`c08/03-z3-offload-config.png`

### 步骤 4 · 真跑：开 offload

```bash
conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory

# 记开始时间
date +%s

llamafactory-cli train \
  examples/train_lora/qwen3_lora_sft.yaml \
  deepspeed=examples/deepspeed/ds_z3_config.json \
  max_steps=10

date +%s        # 记结束时间，相减 = 总耗时
```

**这一步在选什么**：

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| `max_steps=10` | 只跑 10 步 | 看"能不能跑起来"和"多慢"，10 步足够；**跑长是双倍烧钱** |
| **前后各 `date +%s`** | 拿总秒数 | 要和步骤 5 关掉 offload 的耗时对比 → **必须量** |
| 盯着显存 | offload 状态下峰值应**明显低于**不做 offload | 这是"省显存"的直接证据 |
| 用 `watch -n 1 nvidia-smi` | 每秒刷新 | offload 时显存**波动大**（搬来搬去），要多看几次取峰值 |

> 🖼 **截图槽 `c08-04`** — 应截：开着 offload 训练时 `nvidia-smi` 的显存占用
> 文件名：`c08/04-offload-vram.png`

> 🖼 **截图槽 `c08-05`** — 应截：训练日志最后几行 + 你记的耗时秒数
> 文件名：`c08/05-offload-time.png`

### 步骤 5 · 对照：关掉 offload 再跑一次

```bash
date +%s

llamafactory-cli train \
  examples/train_lora/qwen3_lora_sft.yaml \
  deepspeed=examples/deepspeed/ds_z3_config.json \
  max_steps=10
  # 注意：这次用的是"不带 offload"的 ZeRO-3 配置（或 ZeRO-2）

date +%s
```

**这一步在选什么**：

| 对照方案 | 含义 | 适合观察什么 |
|---|---|---|
| **ZeRO-3 不带 offload** | 只切片、都留在显存 | **最干净的单变量对照**：只改 offload 一项 |
| ZeRO-2（不带 offload） | 参数不切 | 看"切参数"本身值多少显存 |
| 纯 DDP | 什么都不切 | 大概率直接 OOM —— **本身就是结论**（"不做优化根本跑不了"） |

::: tip 单变量实验原则
**一次只改一个东西。** 想比较 offload 的效果，就只改 offload；
如果同时把 ZeRO-3 换成 ZeRO-2，就说不清差异是哪个原因造成的。
这是 [4-14](/training/p4/14-optim-practice) 那个"同模型同数据只改 ZeRO 阶段"实验的同一条原则。
:::

> 🖼 **截图槽 `c08-06`** — 应截：两次训练的对照表（能否跑起来 / 峰值显存 / 耗时）
> 文件名：`c08/06-compare-table.png`

### 步骤 6 · FSDP 对照：写配置 + 挑 4 个维度说差异

FSDP 在 LLaMA-Factory 里的等价入口：

```bash
# 讲义里给出的 FSDP 路径
ls /root/autodl-tmp/LLaMA-Factory/examples/extras/fsdp_qlora
cat /root/autodl-tmp/LLaMA-Factory/examples/extras/fsdp_qlora/train.sh
```

**从 [4-13 的八维](/training/p4/13-fsdp) 里挑这 4 个维度做对照**（其余 4 个可略）：

| 维度 | DeepSpeed（你刚跑的） | FSDP |
|---|---|---|
| **配置方式** | 独立 JSON 文件（`ds_z3_config.json`） | 几行代码包装模型，像用 DDP |
| **可切粒度** | 可配 ZeRO-1/2/3 三档 | **默认就是 ZeRO-3**（"唯一切片"） |
| **能否 offload** | ✅ 有 ZeRO-Offload / Infinity（**能到 CPU/NVMe**） | ❌ 无等价能力 |
| **学习曲线** | 要了解众多 JSON 参数 | API 干净，上手快 |

**这一步在选什么**：

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| 挑 4 个而不是全 8 个 | 八维里有些（如"性能"）需要真跑才分得出 | **不真跑就不该断言性能差异**——只对照"配置形态与能力有无" |
| 挑"能/不能"，不挑"好/坏" | 能力有无是**确定的** | `能否 offload` 是二元事实；`谁更快` 要实测（我们没跑 FSDP） |
| FSDP 写法和 DeepSpeed 的对照重点 | 配置入口在哪 | 目的不是会用 FSDP，是**知道它长什么样、什么时候该选它** |

> 🖼 **截图槽 `c08-07`** — 应截：`fsdp_qlora/train.sh` 的内容（看它的启动方式）
> 文件名：`c08/07-fsdp-train-sh.png`

### 步骤 7 · 下一条"带条件的"结论

把结论写成这个形状（不要写"ZeRO-3 比 FSDP 好"）：

```text
当【条件】时，选【方案】，因为【代价可接受 / 不可接受】。
```

参考句式：

> 当**单卡放不下、且没有多卡可用**时，选 **ZeRO-3 + CPU offload**——
> 代价是训练明显变慢，换来"能跑起来"。
>
> 当**团队想少写配置、单机多卡够用**时，选 **FSDP**——
> 它默认就是 ZeRO-3，几行代码像 DDP，代价是没有 offload 能力。
>
> 当**模型单卡放得下**时，**两者都别开 ZeRO-3**——
> 通信开销白付（[4-12 三条铁律](/training/p4/12-deepspeed-zero)第一条）。

> 🖼 **截图槽 `c08-08`** — 应截：你写的条件式结论
> 文件名：`c08/08-conclusion.png`

### 步骤 8 · 关机

```bash
exit
# ⚠️ 回 AutoDL 控制台点「关机」
```

## ⑤ 预期结果（判定标准）

| # | 判定项 | 通过标准 |
|---|---|---|
| 1 | 算过"装得下吗" | 有全参静态账（≈ 27 GB，1.7B × 16 B）与卡的容量对照 |
| 2 | 记了 CPU 内存 | `free -h` 的 `Mem` 总量已记录（offload 的目的地） |
| 3 | **offload 真跑起来了** | 开着 `offload_optimizer` + `offload_param`，训练确实跑出 step |
| 4 | 有显存证据 | 记录了开 offload 时的峰值显存 |
| 5 | 有耗时证据 | 前后 `date +%s`，两次（开/关 offload）耗时都记下 |
| 6 | **对照是单变量的** | 开/关 offload 两次之间，只有 offload 这一项变了 |
| 7 | FSDP 配置看到了 | 能看到 `fsdp_qlora/train.sh` 的启动方式 |
| 8 | 挑了 4 个维度对照 | 4 个维度都是"配置形态 / 能力有无"这类**不需要真跑就能断言**的 |
| 9 | **理解性目标：offload 搬什么** | 能说清 offload 搬的是**优化器状态与参数**，目的地是 **CPU 内存**（或 NVMe） |
| 10 | **理解性目标：代价是慢** | 能用自己两次的耗时数据说明 offload 更慢，并解释原因是 PCIe 带宽远低于显存带宽 |
| 11 | **理解性目标：没跑的不瞎断言** | 未对"FSDP 与 DeepSpeed 谁更快"下结论——因为我们只跑了 DeepSpeed 一侧 |
| 12 | **理解性目标：结论带条件** | 结论是"当…时选…"的形状，不是"A 比 B 好" |
| 13 | 已关机 | 控制台确认「已关机」 |

按标准表逐项打勾……

## ⑥ 常见报错

| 报错 | 原因 | 处置 |
|---|---|---|
| `RuntimeError: CUDA out of memory`（开着 offload 还爆） | **CPU 内存不够**，或被系统 OOM Killer 杀 | `free -h` 确认；升级实例内存规格，或改 `nvme` |
| 进程被 kill、日志无报错就中断 | 系统 OOM Killer（内存打满） | `dmesg \| tail` 看有没有 OOM 记录；减少 `batch_size` |
| 训练极慢（每步几十秒） | **这是 offload 的正常代价**，不是 bug | 确认数值量级是否合理；跑长训练时考虑 `nvme` 或干脆换大卡 |
| `offload_param` 设了但显存没降 | 配置文件没被加载 | 确认命令行 `deepspeed=` 指向了正确文件，且 `stage: 3` |
| `deepspeed` 版本相关报错 | 版本与 LLaMA-Factory 不匹配 | 按 [C01 步骤 5](/training/p10/c01-llamafactory-env) 的版本装 |
| FSDP 路径不存在 | 仓库版本差异 | `find . -path "*fsdp*" -name "*.sh"` 找实际路径；或只读 [4-13](/training/p4/13-fsdp) 的对照表 |
| `No space left on device` | offload 到 NVMe 时吃磁盘 | `df -h`；换回 `cpu`，或清数据盘 |
| 忘记关机被扣费 | `exit` 不等于关机 | 回控制台点「关机」 |

## ⑦ 延伸

1. **把 `offload_optimizer` 单独开、`offload_param` 不开**：哪个对显存贡献更大？各开一次看差异。
2. **改用 `nvme` 卸载**：显存更省，但耗时再翻多少？（注意 `df -h` 确认磁盘够）
3. **把模型换成 7B**：算算单卡 + offload 还能不能跑；CPU 内存够不够。
4. **真租 2 张卡做 FSDP 对照**：如果哪天要写选型报告，用同一份数据真跑 FSDP，把 [4-13](/training/p4/13-fsdp) 的"性能"那一维也补上实测。
5. **做一次"不做任何优化"的对照**：纯 DDP 或单卡全参，看它是不是直接 OOM——OOM 本身就是"为什么需要 ZeRO"的最好论据。
6. **算成本**：把"单卡 + offload 跑 T 小时"与"多卡不带 offload 跑 T/N 小时"按 [9-B §7](/training/p9/B-formula-card) 算一遍，看哪个更划算——**答案取决于卡价与慢多少**。

---

> 上一节：[C07 单卡实测 + 多卡推演](/training/p10/c07-ddp-zero2) ｜ [案例库总览](/training/p10/) ｜ [Part 4 末页题目](/training/p4/14-optim-practice)
