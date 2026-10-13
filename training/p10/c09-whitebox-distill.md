---
title: C09 · 跑通白盒蒸馏：教师 4B → 学生 1.7B
---

# C09 · 跑通白盒蒸馏：教师 4B → 学生 1.7B

::: tip 案例信息
**所属 Part**：[Part 5 · 知识蒸馏](/training/p5/01-what) ｜ **难度**：基础 ｜ **耗时**：80–150 分钟
**对应讲义**：[5-3 响应式蒸馏](/training/p5/03-response)、[5-9 实战：白盒蒸馏 4B → 1.7B](/training/p5/09-practice)、[5-2 蒸馏技术分类](/training/p5/02-taxonomy)
**前置**：[C05](/training/p10/c05-lora-sft)（会用 LoRA 训 4B）、[C02](/training/p10/c02-model-download-webui)（模型能下能加载）
:::

::: warning 成本：本案例只租 1 张卡，约 ¥8–20
| 项 | 内容 |
|---|---|
| **需要几张卡** | **1 张**（**建议 40 GB 档或更大**——白盒蒸馏要**同时装下教师 + 学生**） |
| **预估费用** | 按量计费 **约 ¥8–20**（四个步骤里有两轮训练，且都要多轮 epoch） |
| **省钱姿势** | ① **本案例是四个步骤中较贵的一道**——请尽量**复用**：教师 4B 若在 [C05](/training/p10/c05-lora-sft) 已微调过，直接合并当教师，**省掉第 1、2 步**<br/>② 先各跑 `max_steps=50` 验证**双模型能同时驻留显存**，再决定是否跑满 epoch<br/>③ 数据量按讲义建议**控制在 10 万条以下**，epoch 相应减小<br/>④ **无卡模式**写完所有脚本再开机<br/>⑤ 做完**立刻控制台关机** |
:::

::: info 本案例为什么比 C05 贵
白盒蒸馏要**同时加载教师和学生两个模型**（[5-9](/training/p5/09-practice) 明确推荐"A800 或其他大显存"）。
这是本册 14 道题里**显存压力最大**的一道——**也因此最该按下面的省钱姿势走**。
:::

## ① 题目

> 按 [5-9 实战](/training/p5/09-practice) 的四步流程，完成一次**白盒蒸馏**（教师 4B → 学生 1.7B），要求：
>
> 1. **第一步**：用 LoRA 微调教师 4B，产出 `lora(4b)` adapter；
> 2. **第二步**：把 adapter **合并**成完整的"微调后 4B"，它就是教师；
> 3. **第三步**：用教师蒸馏学生 1.7B（LoRA），产出 `lora(1.7b)`；
> 4. **第四步**：合并学生权重，做推理验证；
> 5. **解释代码**：`compute_kl_div_loss` 与 `Custom_Trainer.compute_loss` 在干什么；`alpha` / `temperature` 各起什么作用；
> 6. **综合环节**：说清"**异构 logits 对齐**"（教师词表 `V_t` 与学生词表 `V_s` 不等）怎么处理，以及**源码的边界缺陷在哪种情况下会报错**。

**一句话目标**：跑通"教师微调 → 合并 → 蒸馏学生 → 合并验证"这条四段流水线，并看懂 **KL 损失那一行代码**。

## ② 你会练到什么

| 技能点 | 对应小节 |
|---|---|
| **白盒 vs 黑盒**：为什么要用教师的 logits（软标签） | [5-2](/training/p5/02-taxonomy)、[5-3](/training/p5/03-response) |
| **`Total Loss = α·L_distill + (1−α)·L_student`** 的构造 | [5-3](/training/p5/03-response) |
| **温度 T 的软化作用**（T=1 vs T=6 的分布对比） | [5-3](/training/p5/03-response) · 小样例 |
| **`compute_kl_div_loss` 的实现**（`log_softmax` / 掩码 / fp32） | [5-9](/training/p5/09-practice) |
| **异构 logits 对齐**（`V_t > V_s` 补零截断） | [5-9](/training/p5/09-practice) |
| **"教师也要微调"**这个反直觉点 | [5-9](/training/p5/09-practice) 四步流程 |

## ③ 前置条件

| 项 | 要求 | 怎么核对 |
|---|---|---|
| 环境 | C01 已完成；**已装 `peft` / `transformers` / `pandas` / `torch`** | `pip list` 里能查到 `peft`、`transformers` |
| 教师模型 | **Qwen3-4B**（或与 C05 同一份微调后 4B） | `ls /root/autodl-tmp/models/.../Qwen3-4B*` |
| 学生模型 | **Qwen3-1.7B** | `ls /root/autodl-tmp/models/.../Qwen3-1.7B` |
| 数据 | 一份 SFT 数据（≤ 10 万条），Alpaca 或自定义 | `wc -l data/xxx.json` |
| **显存** | **建议 ≥ 40 GB**（教师 4B + 学生 1.7B 同时驻留；bf16 下合计约 12 GB 权重，加激活/优化器更高） | `nvidia-smi` 看总量 |
| 依赖版本 | 按 [5-9](/training/p5/09-practice) 的 `requirements.txt` | `peft==0.17.1` / `transformers==4.57.0` / `pandas==2.3.3` / `torch==2.5.1+cu124` |
| **省钱** | 先无卡模式写完四个脚本 | — |

::: warning 显存不够就别硬上
若只有 24 GB 卡，**教师 4B + 学生 1.7B 同时跑可能会 OOM**。
两个可选降级：
1. **教师也用 4-bit 加载**（但白盒蒸馏需要 logits，量化会损精度 → **只能作"跑通链路"用，不能作效果结论**）；
2. 教师换更小（如 1.7B 教师 → 0.6B 学生）先跑通流程。

**哪种都行，但要在报告里写明你用的是哪种**——这正是 [C07](/training/p10/c07-ddp-zero2) 那条"实测 vs 推演"的边界规矩。
:::

## ④ 分步操作

### 步骤 1 · 无卡模式：看懂四步流水线，备好脚本

```bash
# 控制台切「无卡模式」→ SSH 进去
conda activate llama_env
cd /root/autodl-tmp/distill        # 新建一个自己的工作目录
```

**先把四步写下来**（[5-9](/training/p5/09-practice) 的流程）：

| 步骤 | 做什么 | 产出 | 要不要卡 |
|---|---|---|---|
| **①** | LoRA 微调教师 4B（如 epoch=30） | `lora(4b)` adapter | 要（但**可复用 C05**） |
| **②** | 合并 → "微调后 4B 全参" | 教师模型 | 要（合并需卡或 CPU，慢） |
| **③** | 教师蒸馏学生 1.7B（LoRA，epoch=30） | `lora(1.7b)` adapter | 要 |
| **④** | 合并学生权重 + 推理验证 | 学生全参模型 | 要（推理） |

::: tip 第 ① ② 步可以复用！
如果你的 [C05](/training/p10/c05-lora-sft) 已经用**同一份数据**微调过 4B 并保存了 adapter，
**第 ① 步就完成了**。直接用 `llamafactory-cli export`（或 `peft` 的 merge）把它合并成教师即可。
**这一步复用能省掉近一半费用。**
:::

> 🖼 **截图槽 `c09-01`** — 应截：你写的四步流程表（或终端里的目录结构规划）
> 文件名：`c09/01-pipeline.png`

### 步骤 2 · 微调 / 合并教师（步骤 ①②）

**若复用 C05 的 adapter，直接合并**：

```bash
# 用 peft 合并 LoRA 到基座（示意，实际按你的脚本）
python - <<'PY'
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = "/root/autodl-tmp/models/hub/models/Qwen/Qwen3-4B-Base"
adapter = "/root/autodl-tmp/output/qwen3_4b_lora"
out = "/root/autodl-tmp/models/teacher_4b"

m = AutoModelForCausalLM.from_pretrained(base, torch_dtype="auto", device_map="cpu")
m = PeftModel.from_pretrained(m, adapter).merge_and_unload()
m.save_pretrained(out, safe_serialization=True)
print("教师已保存到", out)
PY
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **复用 C05 的 adapter** | 不重跑第 ① 步 | **同样的数据+同样的模型，重跑纯浪费钱** |
| **`merge_and_unload()`** | 把 LoRA 的 ΔW 合进基座，得到完整模型 | 蒸馏需要**完整教师模型**（要它的全量 logits），不能只给 adapter |
| 合并放到 **CPU** | `device_map="cpu"` | 合并不吃算力，**放 CPU 省显存给后面的蒸馏** |
| `safe_serialization=True` | 存 safetensors | 标准格式，后续加载无坑 |

**预期**：`/root/autodl-tmp/models/teacher_4b` 生成，含 `config.json` 与 `*.safetensors`。

> 🖼 **截图槽 `c09-02`** — 应截：合并脚本的输出 + `ls` 教师目录
> 文件名：`c09/02-teacher-merged.png`

### 步骤 3 · 看懂 KL 损失那一行

在写蒸馏训练脚本前，**先把损失函数读懂**（[5-9](/training/p5/09-practice) 给了完整实现）：

```python
def compute_kl_div_loss(logits, teacher_logits, target, padding_id, reduction="sum"):
    # 1) 都转 fp32 —— 软化分布需要精度
    logits = logits.float()
    teacher_logits = teacher_logits.float()

    # 2) 温度 T 软化：p_i = softmax(z_i / T)
    T = 6
    student_log_probs = torch.log_softmax(logits / T, dim=-1)     # log Q
    teacher_probs = torch.softmax(teacher_logits / T, dim=-1)     # P

    # 3) KL(P‖Q) = Σ P · (log P − log Q)
    kl = (teacher_probs * (torch.log(teacher_probs + 1e-8) - student_log_probs)).sum(-1)

    # 4) 掩码：padding 位不计入
    pad_mask = (target == padding_id)
    kl = kl.masked_fill_(pad_mask, 0.0)

    return kl.sum() if reduction == "sum" else kl.mean()
```

**这一步在选什么**

| 代码片段 | 作用 | 为什么这么写 |
|---|---|---|
| **`.float()`** | 转 fp32 | 软化后的分布很"平"，**低精度下 KL 会算出噪声** |
| **`T = 6`** | 温度 | [5-3](/training/p5/03-response)：T=1 时分布尖锐、T=6 时差异才显出来。**范围 3–20** |
| **`log_softmax(logits/T)`** | 学生的 log 概率 | 数值稳定写法（不先 softmax 再 log） |
| **`teacher_probs · (logP − logQ)`** | KL 的逐项定义 | 与 [5-3 的公式](/training/p5/03-response) 逐字对应 |
| **`+ 1e-8`** | 防 log(0) | 数值保险 |
| **`masked_fill_(pad_mask, 0.0)`** | 屏蔽 padding | **padding 位没有监督意义**，计进去会污染损失 |
| `reduction="sum"` | 求和 | 与后续 `loss_total` 的加权配套 |

::: warning 讲义代码与本课程约定的一个差异
标准做法里 KL 项还要乘 **`T²`**（补偿温度导致的梯度缩放）。
[5-3](/training/p5/03-response) 明确说了：**本课程代码未乘 `T²`**，靠**较大的 α + 学习率**来平衡。
**你可以不乘，但要知道标准做法是乘的**——面试/生产里这是个常见考点。
:::

**预期**：能逐行解释这段代码，并说出 `T` 与 `masked_fill_` 的作用。

> 🖼 **截图槽 `c09-03`** — 应截：`compute_kl_div_loss` 的代码（或你对它的批注）
> 文件名：`c09/03-kl-code.png`

### 步骤 4 · 看懂 `compute_loss` 与异构 logits 对齐

`Custom_Trainer.compute_loss` 是蒸馏的"总调度"（[5-9](/training/p5/09-practice)）：

```python
class Custom_Trainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        # 1) 学生前向
        outputs = model(**inputs)
        student_logits = outputs.logits

        # 2) 教师前向 —— 不要梯度！
        with torch.no_grad():
            teacher_logits = self.teacher(**inputs).logits

        # 3) 异构对齐：词表不一致时补零/截断
        V_t, V_s = teacher_logits.size(-1), student_logits.size(-1)
        if V_t > V_s:
            # 教师词表更大 → 学生补零到 V_t
            student_logits = F.pad(student_logits, (0, V_t - V_s))
        elif V_t < V_s:
            raise ValueError(...)   # ⚠️ 源码边界缺陷：不支持这种情形
        # V_t == V_s（同系列 Qwen3）→ 直接走，无需对齐

        # 4) 两项损失加权
        kl = compute_kl_div_loss(student_logits, teacher_logits,
                                 inputs["labels"], self.padding_id)
        loss_total = self.alpha * kl + (1 - self.alpha) * outputs.loss
        return (loss_total, outputs) if return_outputs else loss_total
```

**这一步在选什么**

| 代码片段 | 作用 | 为什么这么写 |
|---|---|---|
| **`with torch.no_grad()`** | 教师不建计算图 | 教师是"老师"不是"学生"，**除了前向什么都不做**。不关梯度会白吃显存 |
| **`V_t > V_s` → 补零** | 学生词表小，补到教师大小 | 补的位概率为 0，KL 里自然不起作用（配合掩码） |
| **`V_t == V_s` → 直接走** | Qwen3 同系列词表一致 | **本案例正是这种**（4B 与 1.7B 同词表），所以最省心 |
| **`V_t < V_s` → 报错** | 源码不支持 | ⚠️ **这是源码的边界缺陷**：教师词表比学生小时会直接抛错。遇到就得自己改 |
| **`alpha * kl + (1-alpha) * loss`** | 总损失 | [5-3](/training/p5/03-response)：`α=0.5`，一半学教师、一半学真标签 |

::: danger `V_t < V_s` 这个边界你必须知道
[5-9](/training/p5/09-practice) 的源码只处理了"教师词表 ≥ 学生词表"。
**如果教师词表比学生小，代码会直接报错**——这是实现上的取舍，不是物理定律。
**工程上怎么做**：要么先生成学生 logits 的子集，要么对教师 logits 补零。
**关键是你知道它的存在**——生产里遇到就会卡住。
:::

**预期**：能说清 `no_grad`、三种词表关系、`alpha` 加权各自的作用。

> 🖼 **截图槽 `c09-04`** — 应截：`compute_loss` 里异构对齐那一段代码
> 文件名：`c09/04-hetero-align.png`

### 步骤 5 · 蒸馏学生（步骤 ③）

关键超参（[5-9](/training/p5/09-practice)）：

```python
alpha = 0.5
temperature = 6          # 范围 3–20
lr = 5e-4
num_train_epochs = 10    # ⚠️ 讲义正文写 30，代码是 10 —— 以代码为准，但要知道讲义说 30
r = 8
lora_alpha = 256         # ⚠️ 蒸馏确实用了 256（与常规 SFT 的 16–32 不同）
lora_dropout = 0.1
gradient_accumulation_steps = 16
max_seq_len = 512
per_device_train_batch_size = 1
```

```bash
# 回控制台开机，限步先验证"双模型能共存"
python train_distill.py --max_steps 50
# 另开终端盯显存
watch -n 1 nvidia-smi
```

**这一步在选什么**

| 超参 | 取值 | 为什么这么选 |
|---|---|---|
| **`alpha=0.5`** | 教师项与真标签项各半 | [5-3](/training/p5/03-response) 的默认平衡点 |
| **`temperature=6`** | 软化程度 | 范围 **3–20**；太小分布太尖、太大过于均匀 |
| **`lora_alpha=256`** | ⚠️ **这里确实是 256** | 与 [C05](/training/p10/c05-lora-sft) 的 16 **不同**！蒸馏要学生**大幅贴合教师分布**，所以缩放更强 |
| **`num_train_epochs`** | 代码 **10** / 讲义 **30** | **以你手上的代码为准**；讲义建议"数据量大则 epoch 小些（如 10）" |
| **`labels` prompt 置 `-100`** | 只对回答部分算损失 | 避免模型学"复述问题" |
| **`V_t == V_s`** | Qwen3 同系列 | 无需对齐处理，直接跑 |

::: tip 这里正好呼应 C05 的坑
[C05](/training/p10/c05-lora-sft) 强调"常规 SFT 别照抄 `alpha=256`"；
**蒸馏这道题恰恰要用 256**。同一个参数、两个任务、两个取值——
**关键不是记数值，是记"为什么"**（蒸馏要更强的贴合信号）。
:::

**预期**：教师与学生同时驻留显存、无 OOM；日志有 KL 相关 loss 输出且下降。

> 🖼 **截图槽 `c09-05`** — 应截：蒸馏训练日志（含 loss 输出）
> 文件名：`c09/05-distill-log.png`

> 🖼 **截图槽 `c09-06`** — 应截：蒸馏时 `nvidia-smi`（能看到双模型占用，明显高于单模型）
> 文件名：`c09/06-dual-vram.png`

### 步骤 6 · 合并学生并推理验证（步骤 ④）

```python
# 合并学生 LoRA
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

base = "/root/autodl-tmp/models/hub/models/Qwen/Qwen3-1.7B"
adapter = "/root/autodl-tmp/output/qwen3_1_7b_distill"
out = "/root/autodl-tmp/models/student_1_7b"

m = AutoModelForCausalLM.from_pretrained(base, torch_dtype="auto", device_map="cpu")
m = PeftModel.from_pretrained(m, adapter).merge_and_unload()
m.save_pretrained(out, safe_serialization=True)
```

```python
# inference.py —— 验证（注意 fp16）
tok = AutoTokenizer.from_pretrained(out)
model = AutoModelForCausalLM.from_pretrained(out, torch_dtype=torch.float16, device_map="auto")

messages = [{"role": "user", "content": "你是谁？"}]
ids = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt").to(model.device)
out_ids = model.generate(ids, max_new_tokens=128)
print(tok.decode(out_ids[0][ids.shape[1]:], skip_special_tokens=True))   # 切片掉 prompt
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`add_generation_prompt=True`** | 按对话模板补齐"该助手说话了"的前缀 | 不加 → 模型不知道该接着谁说话，输出会怪 |
| **输出切片 `[ids.shape[1]:]`** | 只要新生成的部分 | 否则会把输入问题也打印出来 |
| **`dtype=torch.float16`** | 推理用 fp16 | [5-9](/training/p5/09-practice) 的 `inference.py` 就是这样；推理不需要 bf16 的动态范围 |
| 合并也放 CPU | 省显存 | 同步骤 2 |

**预期**：学生模型能正常回答；输出不是原样复述问题。

> 🖼 **截图槽 `c09-07`** — 应截：`inference.py` 的输出（学生的回答）
> 文件名：`c09/07-student-infer.png`

### 步骤 7 · 综合环节：说清异构对齐与边界缺陷

| 情形 | 代码行为 | 你该怎么做 |
|---|---|---|
| **`V_t > V_s`**（教师词表大） | 学生 logits 补零到 V_t | 源码已处理，直接用 |
| **`V_t == V_s`**（同系列，**本案例**） | 无需对齐 | 直接用 |
| **`V_t < V_s`**（教师词表小） | **抛错**（源码边界缺陷） | 需自己改：教师补零 or 学生截断 |

**为什么同系列（Qwen3-4B 与 Qwen3-1.7B）这么省事**：
它们**共用同一个 tokenizer / 词表**，`V_t == V_s`，跳过整个对齐分支。
**这也是讲义选 "4B → 1.7B" 而不是跨系列蒸馏的原因之一。**

**预期**：能画出三种词表关系的分支，并说清源码只覆盖前两种。

> 🖼 **截图槽 `c09-08`** — 应截：你画的"词表大小 → 代码行为"三分支图
> 文件名：`c09/08-vocab-cases.png`

### 步骤 8 · 关机

```bash
exit
# ⚠️ 回 AutoDL 控制台点「关机」
```

> 🖼 **截图槽 `c09-09`** — 应截：控制台显示「已关机」
> 文件名：`c09/09-shutdown.png`

## ⑤ 预期结果与判定标准

| # | 检查项 | 判定标准（必须看到） |
|---|---|---|
| 1 | 四步流程说得出 | 能依次说出 ①教师微调 ②合并 ③蒸馏学生 ④合并验证 |
| 2 | **教师已就绪** | `teacher_4b` 目录存在，是**完整模型**（非 adapter） |
| 3 | **复用做对了** | 若复用 C05 的 adapter，能说明省掉了第 ① 步 |
| 4 | **KL 代码能解释** | 能说清 `.float()` / `T` / `log_softmax` / `masked_fill_` 的作用 |
| 5 | **T 的作用说得出** | 能说出 T=1 与 T=6 分布差异（尖锐 vs 平缓） |
| 6 | **知道标准做法乘 T²** | 能指出本课程代码未乘，标准做法要乘 |
| 7 | **`no_grad` 说得出** | 能解释教师为什么不需要梯度 |
| 8 | **异构对齐三分支** | 能说清 `V_t`/`V_s` 三种关系及各自行为 |
| 9 | **边界缺陷知道** | 能指出 `V_t < V_s` 会报错，以及怎么改 |
| 10 | **alpha=256 有理由** | 能说清为什么蒸馏用 256 而常规 SFT 用 16 |
| 11 | 蒸馏跑通 | 日志有 loss，双模型共存不 OOM |
| 12 | **学生已合并** | `student_1_7b` 完整模型存在 |
| 13 | **推理验证做了** | 学生能回答问题，输出非复述 |
| 14 | **理解性目标：教师为什么要微调** | 能说清"教师也得先在目标任务上训过，才能教出对口的知识" |
| 15 | 已关机 | 控制台显示「已关机」 |

> 第 4、8、9、14 项是重点：**四段流水线照着做能跑通；"KL 那一行在算啥""词表不一致怎么办""教师为什么也得微调"才是蒸馏真正要带走的东西。**

## ⑥ 常见报错

| 报错 | 原因 | 处置 |
|---|---|---|
| **`CUDA out of memory`** | 教师 + 学生同驻，显存不够 | 换更大显存卡；或教师用 4-bit 加载（**只作链路验证**）；或换更小学生 |
| **`V_t < V_s` 相关 ValueError** | 教师词表比学生小（源码边界缺陷） | 换同系列模型（`V_t == V_s`）；或自己改对齐逻辑 |
| 词表不一致时维度报错 | 忘了做异构对齐 | 确认走的是 `V_t ≥ V_s` 分支 |
| `loss` 是 `nan` | KL 算了 log(0) 或温度/精度问题 | 确认 `.float()` 与 `+1e-8`；降 lr |
| 学生输出复述问题 | `labels` 没把 prompt 置 `-100` | 处理标签掩码 |
| 学生输出怪 / 不停 | 推理时没加 `add_generation_prompt=True` | 加上；或对话模板不匹配 |
| 推理打印出问题原文 | 忘了切片 `[ids.shape[1]:]` | 切片后再 decode |
| `ModuleNotFoundError: peft` | 版本缺失 | 按 `requirements.txt` 装 `peft==0.17.1` |
| 合并时报 shape 不匹配 | adapter 与基座不是同一次训练的 | 确认 adapter 对应的是同一个基座 |
| 训练非常慢 | 双模型前向 + `gradient_accumulation=16` | 正常；可先限步验证链路 |
| 显存够但报 OOM 于推理 | 合并后模型 + 分词器占位 | 合并放 CPU，推理再 `device_map="auto"` |

## ⑦ 延伸

1. **教师不微调直接蒸馏**：跳过第 ①② 步，用原始 4B 当教师，对比学生效果。**为什么讲义坚持先微调教师？** → [5-2](/training/p5/02-taxonomy)
2. **调 `temperature`**：从 6 改成 3 和 12 各跑一次（限步），看 KL 项量级怎么变。**T 太大为什么反而不好？**
3. **补上 `T²`**：把 KL 项乘 `T²` 再跑，对比"乘 vs 不乘"的 loss 曲线。**这印证了 [5-3](/training/p5/03-response) 的哪句话？**
4. **换成跨系列蒸馏**：用一个**词表不同**的教师（如别的系列），亲手触发一次异构对齐，甚至触发 `V_t < V_s` 的报错。**亲身踩坑比读代码印象深。**
5. **做黑盒对照**：只用教师的**输出文本**（不看 logits）训学生，对比白盒/黑盒差别。**白盒多的信息值多少钱？**
6. **接 [C10](/training/p10/c10-distill-vs-sft)**：把学生模型拿去做"蒸馏 vs 直接 SFT"的效果对比——**那才是这道题的完整闭环**。

---

> 下一案例：[C10 蒸馏 vs 小模型直接 SFT：效果对比](/training/p10/c10-distill-vs-sft) ｜ [案例库总览](/training/p10/) ｜ [Part 5 末页题目](/training/p5/09-practice)
