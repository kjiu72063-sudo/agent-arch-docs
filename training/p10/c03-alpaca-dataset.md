---
title: C03 · 制作一份合规的 Alpaca 格式自定义数据集
---

# C03 · 制作一份合规的 Alpaca 格式自定义数据集

::: tip 案例信息
**所属 Part**：[Part 2 · 数据工程](/training/p2/01-data-strategy) ｜ **难度**：基础 ｜ **耗时**：30–50 分钟
**对应讲义**：[2-2 数据集格式与注册](/training/p2/02-data-format)、[2-4 自定义数据集构建](/training/p2/04-custom-dataset)
**前置**：[C01](/training/p10/c01-llamafactory-env) 已完成（云主机在运行、`llama_env` 可用）
:::

::: warning 成本：本案例只租 1 张卡（甚至可以不租卡），约 ¥0–2
| 项 | 内容 |
|---|---|
| **需要几张卡** | **本案例纯数据制作，无需 GPU**。要跑注册验证时租 **1 张**（24 GB 档）即可 |
| **预估费用** | **¥0**（切**无卡模式**做完全部步骤 1–6，注册验证也在无卡模式完成） |
| **省钱姿势** | ① 造数据、改 JSON、注册、查 schema **全是 CPU 活**，无卡模式下全做完<br/>② 只有"真的启动一次训练"才需要卡——那步留给 [C05](/training/p10/c05-lora-sft)<br/>③ 做完**立刻控制台关机** |
:::

::: info 为什么这道题几乎不用花钱
数据工程是**唯一不碰 GPU 的核心环节**——清洗、转格式、注册、校验，全是文本处理。
把它放在**无卡模式**做完，是云上最省钱的习惯之一。
:::

## ① 题目

> 手边有一份**业务数据**（本例用一份 Excel 表格，也可以是自己爬/攒的问答对），要求：
>
> 1. **转成 Alpaca 格式**，写成 `identity_modify.json` 的**同构**文件；
> 2. 放进 LLaMA-Factory 的 `data/` 目录，并**注册到 `dataset_info.json`**；
> 3. 用**加载器实跑一次**，确认数据能被正确读出（不训练，只看"能不能读进来"）；
> 4. **逐个字段解释**：`instruction` / `input` / `output` 各自装什么，`input` 为空合法吗；
> 5. **综合环节**：从原始 Excel 出发，把"收集 → 清洗 → 转格式 → 放 data/ → 注册 → 引用"整条链走完，并说清**每一步失败会是什么症状**。

**一句话目标**：把"我有一份自己的数据"变成"LLaMA-Factory 能用的一份合规数据集"。

## ② 你会练到什么

| 技能点 | 对应小节 |
|---|---|
| **Alpaca 的三字段结构**：`instruction` / `input` / `output` 各装什么 | [2-2](/training/p2/02-data-format) · 字段语义 |
| **`data/` 目录 + `dataset_info.json` 两条铁律** | [2-2](/training/p2/02-data-format) · 两条铁律 |
| **从 Excel / CSV 转 Alpaca 的代码写法**（含 `ensure_ascii=False`） | [2-4](/training/p2/04-custom-dataset) · CSV → Alpaca |
| **注册 JSON 的 `columns` 是映射不是照抄** | [2-2](/training/p2/02-data-format) · 注册示例 |
| **跑加载器验证**：不训练也能确认数据可用 | [2-4](/training/p2/04-custom-dataset) · 完整流程 |

## ③ 前置条件

| 项 | 要求 | 怎么核对 |
|---|---|---|
| 环境 | C01 已完成，`llama_env` 可用 | `conda activate llama_env && python -c "import llava" 2>/dev/null; ls LLaMA-Factory/data/` |
| 源码 | LLaMA-Factory 源码在 `/root/autodl-tmp/LLaMA-Factory` | `ls /root/autodl-tmp/LLaMA-Factory/data/dataset_info.json` |
| 数据 | 自备一份 Excel/CSV(两列：问题、答案) | 也可以先用讲义里的 `finance_data` 抄格式 |
| 依赖 | `pandas`、`openpyxl`（读 xlsx 用） | `python -c "import pandas, openpyxl"` |
| **GPU** | **不需要**——本案例可全程无卡模式 | — |
| 磁盘 | 数据盘 ≥ 1 GB 空闲（数据文件很小） | `df -h` |

::: tip 为什么用 Excel 举例
**开发人员手里最常见的就是 Excel**。`data_finetune.xlsx` 这种两列表（一列问、一列答）转 Alpaca 是最典型的一条路径，
[2-4](/training/p2/04-custom-dataset) 给的代码就是照它写的。
:::

## ④ 分步操作

### 步骤 1 · 切无卡模式，进项目目录

```bash
# AutoDL 控制台 → 把实例切到「无卡模式」（CPU，几乎免费）
ssh -p <端口号> root@<服务器地址>

conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory
ls data/ | head
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **无卡模式** | 只给 CPU，不开 GPU | **本案例 100% 是文本处理**，用卡等于烧钱。无卡模式下 `python` 照样能跑 |
| 直接开卡做 | 卡一直计时 | 除非你要顺带跑一次训练，否则纯浪费 |
| 在本地做好再上传 | 也行，但云上数据盘路径要一致 | 云上直接改更省事——数据文件也就几百 KB |

> 🖼 **截图槽 `c03-01`** — 应截：无卡模式下 SSH 进去、`ls data/` 能看到 `dataset_info.json` 与若干 `*.json`
> 文件名：`c03/01-workdir.png`

**预期**：终端在 `(llama_env)` 里，`data/` 目录下列出 `dataset_info.json`、`identity.json` 等文件。

### 步骤 2 · 看清"目标长什么样"：Alpaca 的定式

先读一遍参照文件，别急着写自己的：

```bash
cat data/identity.json
```

你应该看到**一个 JSON 数组**，每个元素三个键：

```json
[
  {
    "instruction": "请你介绍一下你自己。",
    "input": "",
    "output": "我是一个由 ... 训练的语言模型 ..."
  }
]
```

**这一步在选什么**

| 字段 | 装什么 | 注意事项 |
|---|---|---|
| **`instruction`** | **指令/问题本身**——你要模型做什么 | 必填。是模型看到的"任务描述" |
| **`input`** | **补充材料**——指令里要引用的那段文本 | **可以为空字符串**（本例就是空）。它不等于"第二个问题" |
| **`output`** | **期望的回答**——模型该学的东西 | 必填，是监督信号（label）的来源 |

::: warning 最容易搞错的一点：`input` 到底是什么
`input` 是**给指令当输入材料**用的，不是"第二句话"。
- 翻译任务：`instruction` = "把下面这句话翻译成英文"，`input` = 要翻译的原句，`output` = 译文 ✅
- 普通问答：`instruction` = 问题，`input` = `""`，`output` = 答案 ✅

把第二个问题塞进 `input`、答案是 `output`，模型会学错——它以为你永远会给一段"补充材料"。
:::

::: tip JSON 数组还是 JSONL？
`identity.json` 用的是 **JSON 数组**（整个文件一个 `[...]`）。
LLaMA-Factory 也支持 **JSONL**（一行一条、无外层括号）——见 [2-2 的 `Traditional_Chinese.jsonl` 样例](/training/p2/02-data-format)。
**本案例统一用 JSON 数组**，与 `identity_modify.json` 保持一致。
:::

> 🖼 **截图槽 `c03-02`** — 应截：`cat data/identity.json` 的输出（能看到三字段结构）
> 文件名：`c03/02-alpaca-sample.png`

### 步骤 3 · 把 Excel 转成 Alpaca

把业务表格（两列：问题、答案）转成 Alpaca。新建一个转换脚本：

```python
# make_alpaca.py —— 放在项目根目录
import json
import pandas as pd

# 3.1 读源表（xlsx 需 openpyxl；csv 用 pd.read_csv）
df = pd.read_excel("data_finetune.xlsx")

records = []
for _, row in df.iterrows():
    records.append({
        "instruction": str(row["问题"]),
        "input": "",                     # 普通问答留空
        "output": str(row["回答"]),
    })

# 3.2 必须 ensure_ascii=False，否则中文会变成 \uXXXX
with open("data/identity_modify.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"已写出 {len(records)} 条")
```

```bash
python make_alpaca.py
head -c 400 data/identity_modify.json
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`ensure_ascii=False`** | 让中文按原样写出，而不是 `\u4f60\u597d` | **不设这个，文件会变成一串转义码**。虽然模型也能读，但人没法核对，出问题极难排查 |
| `indent=2` | 缩进 2 空格，便于阅读 | 数据量小时无所谓；大文件可去掉省空间 |
| **JSON 数组 vs 逐行 JSONL** | 数组一次性 `json.dump`；JSONL 每行 `f.write(json.dumps(...) + "\n")` | 数组写法更直观；**JSONL 适合流式追加**。本案例用数组 |
| **`input` 留空 vs 塞内容** | 留空 = 纯问答 | 除非你的任务真需要"指令 + 材料"两段式，否则留空 |
| **列名映射** | 源表列名 ≠ Alpaca 字段名 | **这一步就是在做映射**：`问题 → instruction`、`回答 → output`。后面注册时还要再做一次映射，别搞混 |

::: warning 两种"映射"不要混
1. **转换时**：把源表列名映射成 Alpaca 的三个键（本步骤）。
2. **注册时**：告诉 LLaMA-Factory"你的文件里哪列对应哪个键"（步骤 4）。

**如果你已经转成标准 Alpaca 三字段，注册时 `columns` 就写 1:1 映射**（`prompt→instruction`）。
如果跳过转换、直接注册原始表，就得写真实列名。**两种都行，但要清楚自己在哪一层。**
:::

**预期**：`data/identity_modify.json` 生成，`head` 能看到**中文原样显示**（不是 `\u`）。

> 🖼 **截图槽 `c03-03`** — 应截：`python make_alpaca.py` 的输出 + `head -c 400` 显示的中文内容
> 文件名：`c03/03-convert.png`

### 步骤 4 · 注册到 `dataset_info.json`

打开 `data/dataset_info.json`，加入你的数据集条目：

```json
{
  "identity_modify": {
    "file_name": "identity_modify.json",
    "columns": {
      "prompt": "instruction",
      "query": "input",
      "response": "output"
    }
  }
}
```

```bash
# 确认已写入（jq 没装就直接 cat 找关键字）
grep -A6 '"identity_modify"' data/dataset_info.json
```

**这一步在选什么**

| 键 | 含义 | 为什么这么写 |
|---|---|---|
| **`file_name`** | 数据文件的**文件名**（相对 `data/` 目录） | **只写文件名，不写路径**。写了 `./data/...` 反而会找不到 |
| **`columns.prompt`** | 你的文件里**哪一列**是指令 | 值是 `"instruction"`——因为我们的文件就叫这名。**这是映射，不是固定值** |
| **`columns.query`** | 哪一列是输入材料 | 对应 `"input"` |
| **`columns.response`** | 哪一列是回答 | 对应 `"output"` |
| **`formatting`** | 不写 = 默认 `alpaca` | Alpaca 格式可省略；**ShareGPT 必须写 `"sharegpt"`** → [C04](/training/p10/c04-sharegpt-dataset) |

::: danger `columns` 是"映射"，不是"照抄"
最常见的错误：**以为 `columns` 的值必须固定写 `prompt/query/response`**。
不是的——`columns` 说的是"**我文件里的列名 → 框架内部的键**"。

如果源文件列名是 `question` / `answer`，这里就该写 `"prompt": "question", "response": "answer"`。
写错的表现是：**训练一开始就报 `KeyError` 或读到空数据**。
:::

> 🖼 **截图槽 `c03-04`** — 应截：`dataset_info.json` 里你的条目（`file_name` + `columns` 三段映射）
> 文件名：`c03/04-register.png`

### 步骤 5 · 实跑加载器：确认数据真能读出来

不训练，只让框架**读一遍**你的数据集：

```python
# check_dataset.py
from datasets import load_dataset

ds = load_dataset(
    "json",
    data_files="data/identity_modify.json",
    split="train",
)
print("条数:", len(ds))
print("字段:", ds.column_names)
print("样例:", ds[0])
```

```bash
python check_dataset.py
# 或用 LLaMA-Factory 自己的预览：python src/llamafactory/data/... （版本差异大，用上面的通用法最稳）
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **用 `datasets` 直接读 JSON** | 通用、与框架版本无关 | **最稳的验证方式**：绕开框架，先确认文件本身合法 |
| 用框架内部预览脚本 | 更贴近真实训练路径 | 但脚本路径随版本变，容易找不到文件 |
| **看"条数"和"字段名"** | 条数对不对、字段是不是 `instruction/input/output` | **条数对不上 = 转换漏了行；字段名不对 = 注册映射会失败** |
| 打印 `ds[0]` | 看第一条真实内容 | 中文是否乱码、字段是否错位，一眼可见 |

::: tip 这一步为什么能替代"跑训练"
训练要卡、要时间；而**数据对不对，读一遍就知道**。
九成的"训练报错"其实是数据问题——**先在这一步拦住，别等到发车才发现**。
:::

**预期**：打印出正确的条数、`column_names` 含三字段、第一条内容中文正常。

> 🖼 **截图槽 `c03-05`** — 应截：`check_dataset.py` 的三行输出（条数 / 字段 / 样例）
> 文件名：`c03/05-verify.png`

### 步骤 6 · 综合环节：说清整条链与失败症状

把这条链画出来，并**给每一步配一个"失败症状"**：

| 环节 | 做对的表现 | **做错的症状** |
|---|---|---|
| 收集 | 有原始 Excel/CSV | — |
| 清洗 | 去重、去空行、格式统一 | 训练 loss 抖动大、模型学会答空话 |
| **转格式** | 三字段齐全、中文不转义 | `KeyError: 'instruction'` / 文件里全是 `\u4e2d` |
| **放 `data/`** | 文件在 `data/` 目录下 | `FileNotFoundError`（放错目录最常见） |
| **注册** | `dataset_info.json` 有条目、`columns` 映射对 | `KeyError` 或读到的条数 = 0 |
| **引用** | 训练 YAML 里 `dataset: identity_modify` | `Unknown dataset: xxx` |

```bash
# 最后再自查一遍（对应 2-4 的自检清单）
ls -la data/identity_modify.json
grep -c '"instruction"' data/identity_modify.json
```

::: tip 配套门禁
[2-4](/training/p2/04-custom-dataset) 的自检清单提到 `gate/data_schema.py`——
**实际脚本名是 `gate_04_data_schema.py`**（5 项检查）。如果你手上有这个门禁脚本，直接跑它比手查更省事。
:::

**预期**：能用自己的话把六个环节 + 六种症状说全，并能现场演示"故意把 `file_name` 写错"→ 报什么错。

> 🖼 **截图槽 `c03-06`** — 应截：你整理的"环节 → 失败症状"对照表（手写或 Excel）
> 文件名：`c03/06-chain.png`

### 步骤 7 · 收工（本案例无卡，无需关机也行，但要确认实例状态）

```bash
exit    # 断开 SSH
```

**注意**：
- 若你**全程用无卡模式**，实例本身是"关机"状态下的无卡运行，**费用极低**；
- 若你为验证注册**临时开过卡**，做完记得**回控制台关机**。

## ⑤ 预期结果与判定标准

| # | 检查项 | 判定标准（必须看到） |
|---|---|---|
| 1 | 目录就位 | 在 `(llama_env)` 且 `LLaMA-Factory/data/` 可见 |
| 2 | **结构说得出** | 能说清 `instruction` / `input` / `output` 各装什么 |
| 3 | **`input` 用法对** | 明确说出"`input` 可为空、它不是第二个问题" |
| 4 | 文件已生成 | `data/identity_modify.json` 存在 |
| 5 | **中文不转义** | `head` 看到中文原样，**不是 `\uXXXX`** |
| 6 | **注册条目在** | `dataset_info.json` 里能看到你的条目 |
| 7 | **映射说得出** | 能说明 `columns` 是"映射不是照抄" |
| 8 | **能读出来** | 加载器打印出正确条数与三字段名 |
| 9 | 内容正确 | 第一条样例中文正常、字段不错位 |
| 10 | **失败症状能对上** | 能给出"放错目录 / 忘注册 / 映射错"各自的报错 |
| 11 | **理解性目标：数据先行** | 能说清"九成训练报错是数据问题，先验证数据再上卡" |
| 12 | 实例状态 | 确认未在无谓地占用 GPU（无卡模式或已关机） |

> 第 2、3、7、8、11 项是重点：**转个格式不难，难的是"知道字段之间什么关系、注册为什么是映射、为什么要先验证数据"。**

## ⑥ 常见报错

| 报错 | 原因 | 处置 |
|---|---|---|
| 文件里全是 `\u4e2d\u6587` | `json.dump` 没加 `ensure_ascii=False` | 加上参数重写一遍 |
| **`Unknown dataset: identity_modify`** | 忘了注册，或 `dataset_info.json` 语法错（多了个逗号） | 检查条目；用 `python -m json.tool data/dataset_info.json` 验语法 |
| **`FileNotFoundError: identity_modify.json`** | 文件没放 `data/`，或 `file_name` 写成了路径 | 文件放 `data/`；`file_name` **只写文件名** |
| **`KeyError: 'instruction'`** | `columns` 映射与文件真实列名不一致 | 打开文件确认键名，再改 `columns` 的值 |
| 读出来条数 = 0 | 文件是空数组，或 JSON 结构不对（外层不是数组） | `check_dataset.py` 打印 `len(ds)`；确认文件以 `[` 开头 |
| `ModuleNotFoundError: openpyxl` | 读 `.xlsx` 需要它 | `pip install openpyxl` |
| `ModuleNotFoundError: pandas` | 没装 pandas | `pip install pandas` |
| 训练时 loss 不动 / 输出全是空 | `output` 列大面积为空 | 清洗阶段没过滤空行 |
| `json.decoder.JSONDecodeError` | JSON 语法错（尾逗号 / 引号不配对） | `python -m json.tool <file> ` 定位报错行 |
| 中文乱码（not `\u`，是真乱码） | 写文件时 encoding 不是 utf-8 | `open(..., "w", encoding="utf-8")` |
| 注册后仍读不到 | `dataset_info.json` 被改坏了 | 保留备份，或从 LLaMA-Factory 原本的示例里对照格式 |

## ⑦ 延伸

1. **换成 JSONL**：把 `json.dump` 改成逐行 `f.write(json.dumps(r, ensure_ascii=False) + "\n")`，注册时加 `"formatting": "alpaca"` 或直接沿用。**两种格式在什么场景下更顺手？**
2. **故意写错 `file_name`**：写成 `./data/identity_modify.json`，看报什么错。**认得这个错，比背"只写文件名"有用。**
3. **做一次真实清洗**：给 `make_alpaca.py` 加去重（`df.drop_duplicates()`）与去空（`df.dropna()`），再对比条数变化。**脏数据怎么影响训练？**
4. **多轮对话怎么装**：Alpaca 装不下多轮 → [C04 ShareGPT 格式](/training/p10/c04-sharegpt-dataset) 会解决这个问题。
5. **写一个自己的门禁脚本**：把步骤 5 的检查固化成一个脚本（条数 > 0、三字段齐全、无空 output），以后每份数据都先跑它。
6. **接入 C05**：把本案例的数据集拿去 [C05](/training/p10/c05-lora-sft) 的 YAML 里 `dataset: identity_modify`，真正训一次——**这才是"数据工程 → 微调"的完整闭环**。

---

> 下一案例：[C04 多轮对话 → ShareGPT 格式](/training/p10/c04-sharegpt-dataset) ｜ [案例库总览](/training/p10/) ｜ [Part 2 末页题目](/training/p2/04-custom-dataset)
