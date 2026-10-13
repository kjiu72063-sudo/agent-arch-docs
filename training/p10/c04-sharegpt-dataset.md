---
title: C04 · 多轮对话 → ShareGPT 格式 → 接入 LLaMA-Factory
---

# C04 · 多轮对话 → ShareGPT 格式 → 接入 LLaMA-Factory

::: tip 案例信息
**所属 Part**：[Part 2 · 数据工程](/training/p2/01-data-strategy) ｜ **难度**：综合 ｜ **耗时**：40–70 分钟
**对应讲义**：[2-2 数据集格式与注册](/training/p2/02-data-format)、[2-4 自定义数据集构建](/training/p2/04-custom-dataset)
**前置**：[C01](/training/p10/c01-llamafactory-env) 已完成；建议先做 [C03](/training/p10/c03-alpaca-dataset)（单轮 Alpaca）
:::

::: warning 成本：本案例只租 1 张卡（也可以不租），约 ¥0–2
| 项 | 内容 |
|---|---|
| **需要几张卡** | **纯数据处理，不需要 GPU**。要验证"训练能读到多轮数据"时租 **1 张** |
| **预估费用** | **¥0**（无卡模式做完全部核心步骤） |
| **省钱姿势** | ① 转换 + 注册 + 读一遍**全在无卡模式做**<br/>② 只在"跑起来看几行渲染结果"时才需要考虑开卡，且**限死 `max_steps=2`**<br/>③ 做完**立刻控制台关机** |
:::

::: info 为什么多轮要单独一道题
Alpaca 只能装**一问一答**。真实的客服、助手场景都是**多轮**——用户追问、模型记住上文。
ShareGPT 就是为多轮设计的格式，**注册方式与 Alpaca 完全不同**（多一层 `tags`），这是本案例的核心考点。
:::

## ① 题目

> 有一批**多轮对话**（用户与助手的来回，可能超过 3 轮），要求：
>
> 1. 转成 **ShareGPT 格式**的 `finance_data.json`，结构参照讲义样例；
> 2. 注册到 `dataset_info.json`——**注意 ShareGPT 必须写 `formatting` 与 `tags`**，并解释每个 `tag` 的含义；
> 3. 实跑加载器，确认多轮对话被**完整读出**（不是只剩最后一轮）；
> 4. **说清 Alpaca 与 ShareGPT 的取舍**：什么时候必须用 ShareGPT；
> 5. **综合环节**：故意把 `tags.role_tag` 改成与数据不一致的值，看报什么错，并说明**为什么 `from` 的取值必须与 `role_tag` 严格一致**。

**一句话目标**：把"一段多轮聊天记录"变成"框架认得的多轮训练数据"。

## ② 你会练到什么

| 技能点 | 对应小节 |
|---|---|
| **ShareGPT 结构**：`conversations` 数组 + `from` / `value` 二元组 | [2-2](/training/p2/02-data-format) · ShareGPT 真实样例 |
| **多轮对话转 ShareGPT 的代码写法** | [2-4](/training/p2/04-custom-dataset) · 多轮对话 → ShareGPT |
| **注册里 `formatting: sharegpt` + `tags` 的作用** | [2-2](/training/p2/02-data-format) · 注册示例 |
| **`role_tag` 必须与数据一致**（最常见坑） | [2-4](/training/p2/04-custom-dataset) · ⚠ 提示 |
| **两种格式怎么选** | [2-2](/training/p2/02-data-format) · 两种格式怎么选 |

## ③ 前置条件

| 项 | 要求 | 怎么核对 |
|---|---|---|
| 环境 | C01 已完成，`llama_env` 可用 | `conda activate llama_env && ls data/` |
| 源码 | LLaMA-Factory 在 `/root/autodl-tmp/LLaMA-Factory` | `ls data/dataset_info.json` |
| 数据 | 一份多轮对话原始记录（Python 列表 / CSV 都行） | 讲义 `finance_data.json` 可直接当参照 |
| 依赖 | `pandas`（若源是表格） | `python -c "import pandas"` |
| **GPU** | **不需要**（可选：验证渲染时租 1 张） | — |
| 磁盘 | 数据盘 ≥ 1 GB 空闲 | `df -h` |

::: tip 多轮数据的常见来源形态
1. **嵌套列表**：`[[("human", "..."), ("gpt", "...")], ...]`（讲义 [2-4](/training/p2/04-custom-dataset) 用的就是这种）
2. **客服日志表**：一行一条会话，列里存着多段文本
3. **现成 JSON**：已经有 `conversations` 结构的

**本案例用第 1 种**，因为它最直观、也最容易改。
:::

## ④ 分步操作

### 步骤 1 · 无卡模式进场，看 ShareGPT 长什么样

```bash
# 控制台切「无卡模式」→ SSH 进去
conda activate llama_env
cd /root/autodl-tmp/LLaMA-Factory

# 找一个 ShareGPT 样例看结构（若仓库里没有，就照着讲义样例建一个）
ls data/*.json | head
```

ShareGPT 的定式长这样（讲义 [2-2](/training/p2/02-data-format) 的 `finance_data.json` 样例）：

```json
[
  {
    "conversations": [
      { "from": "human", "value": "你好，我想咨询一下理财产品。" },
      { "from": "gpt",   "value": "您好，请问您更看重收益还是流动性？" },
      { "from": "human", "value": "收益高一点吧。" },
      { "from": "gpt",   "value": "那可以关注一下……" }
    ]
  }
]
```

**这一步在选什么**

| 结构 | Alpaca | **ShareGPT** |
|---|---|---|
| **外层** | 一条 = 一个对象，三个平铺字段 | 一条 = 一个对象，**只有一个 `conversations` 键** |
| **内容形态** | 单轮（一进一出） | **数组**，可放任意多轮 |
| **每轮怎么表示** | 三个固定键 | `{"from": 角色, "value": 文本}` |
| **角色取值** | 无（隐含） | **必须与注册里的 `tags` 一致**（如 `human` / `gpt`） |

> 🖼 **截图槽 `c04-01`** — 应截：一份 ShareGPT 样例的结构（能看到 `conversations` 与多个 `from/value`）
> 文件名：`c04/01-sharegpt-sample.png`

### 步骤 2 · 把多轮记录转成 ShareGPT

```python
# make_sharegpt.py
import json

# 2.1 原始多轮数据：每条会话是一个 (角色, 文本) 列表
raw_dialogues = [
    [
        ("human", "你好，我想咨询一下理财产品。"),
        ("gpt",   "您好，请问您更看重收益还是流动性？"),
        ("human", "收益高一点吧。"),
        ("gpt",   "那可以关注一下……"),
    ],
    [
        ("human", "帮我看看这个合同有没有坑。"),
        ("gpt",   "请把合同关键条款贴出来。"),
    ],
]

records = []
for dialogue in raw_dialogues:
    records.append({
        "conversations": [
            {"from": role, "value": text} for role, text in dialogue
        ]
    })

with open("data/finance_data.json", "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"已写出 {len(records)} 条会话")
```

```bash
python make_sharegpt.py
head -c 500 data/finance_data.json
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **`from` 用 `human` / `gpt`** | 与讲义样例一致的角色名 | **这是默认约定**。写成 `user` / `assistant` 也行，但**注册里的 `tags` 必须跟着改** |
| **一条记录一个会话** | 整个多轮放在同一对象的 `conversations` 里 | **关键**：拆成多条会丢掉上下文，模型学不到"记住上文" |
| `ensure_ascii=False` | 中文原样输出 | 同 [C03](/training/p10/c03-alpaca-dataset)——不设就变 `\uXXXX` |
| **`indent=2`** | 缩进 | 多轮嵌套较深，缩进后**肉眼能核对轮次顺序** |
| 角色顺序：human → gpt | 交替出现 | **顺序即上下文**。多轮里先 human 后 gpt；别把两条 gpt 连在一起 |

::: warning 多轮数据最容易犯的两个错
1. **把会话拆成多条**：一条记录只留最后一轮 → 模型永远学不会上下文。
2. **角色名与注册不一致**：数据里写 `user`，注册里写 `human` → **会报错或把整段对话当成一个人的话**。
:::

**预期**：`data/finance_data.json` 生成；`head` 能看到 `conversations` 里**四轮都在**、中文正常。

> 🖼 **截图槽 `c04-02`** — 应截：`python make_sharegpt.py` 输出 + `head -c 500` 显示的多轮结构
> 文件名：`c04/02-convert.png`

### 步骤 3 · 注册（ShareGPT 必须写 `formatting` 和 `tags`）

```json
{
  "finance_data": {
    "file_name": "finance_data.json",
    "formatting": "sharegpt",
    "columns": {
      "messages": "conversations"
    },
    "tags": {
      "role_tag": "from",
      "content_tag": "value",
      "user_tag": "human",
      "assistant_tag": "gpt"
    }
  }
}
```

**这一步在选什么**

| 键 | 含义 | Alpaca 时有吗 |
|---|---|---|
| **`formatting: "sharegpt"`** | 告诉框架"这是多轮格式" | ❌ 可省略（默认 alpaca）；**ShareGPT 不写就会按 Alpaca 解析，直接失败** |
| **`columns.messages`** | 哪一列装着对话数组 | 对应 `conversations`。Alpaca 是 `prompt/query/response` 三个，**这里只有一个** |
| **`tags.role_tag`** | **数据里表示"角色"的键名** | ⭐ 取值 `"from"`——因为数据里就是 `{"from": ..., "value": ...}` |
| **`tags.content_tag`** | **数据里表示"内容"的键名** | 取值 `"value"` |
| **`tags.user_tag`** | **哪个角色名代表"用户"** | 取值 `"human"`——**必须与数据里写的角色名逐字一致** |
| **`tags.assistant_tag`** | 哪个角色名代表"助手" | 取值 `"gpt"`——同上 |

::: danger `role_tag` / `user_tag` / `assistant_tag` 三者最容易混
分两组记：
- **`role_tag` / `content_tag`** 回答"**键叫什么**"——`from` 还是别的？`value` 还是 `content`？
- **`user_tag` / `assistant_tag`** 回答"**值的字面是什么**"——用户叫 `human` 还是 `user`？助手叫 `gpt` 还是 `assistant`？

**改数据里的角色名，就要同步改 `user_tag`/`assistant_tag`。**
[2-4](/training/p2/04-custom-dataset) 明确提醒：`from` 的取值必须与 `tags.role_tag` 对应关系保持一致。
:::

> 🖼 **截图槽 `c04-03`** — 应截：`dataset_info.json` 里的条目（`formatting` + `columns` + 四个 `tags` 全可见）
> 文件名：`c04/03-register.png`

### 步骤 4 · 实跑加载器，确认轮次没丢

```python
# check_sharegpt.py
from datasets import load_dataset

ds = load_dataset("json", data_files="data/finance_data.json", split="train")
print("会话数:", len(ds))
print("字段:", ds.column_names)
first = ds[0]["conversations"]
print("第一条轮数:", len(first))
for turn in first:
    print(f"  [{turn['from']}] {turn['value'][:20]}")
```

```bash
python check_sharegpt.py
```

**这一步在选什么**

| 选项 / 判断 | 含义 | 为什么这么选 |
|---|---|---|
| **数"轮数"而不是只数"条数"** | 会话数 ≠ 轮数 | **会话数是 2 但每条只剩 1 轮**，说明转换时把多轮压平了 |
| 打印每轮的 `from` | 核对角色名 | **这就是 `tags` 要对上的东西**——打印出来才能确认真实取值 |
| 看首轮 `value` 是否完整 | 检查是否有截断 | 清洗阶段若按行切过，可能把一句话切断 |

**预期**：会话条数正确；第一条轮数 = 原始轮数（如 4）；角色名是 `human` / `gpt`。

> 🖼 **截图槽 `c04-04`** — 应截：`check_sharegpt.py` 输出（会话数 / 字段 / 逐轮打印）
> 文件名：`c04/04-verify.png`

### 步骤 5 · 综合环节：故意改坏 `role_tag`，看报错

```bash
# 把 dataset_info.json 里 finance_data 的 role_tag 从 "from" 改成 "role"（数据里并没有 role 这个键）
# 然后重跑加载检查
python check_sharegpt.py
```

再改回去，把 `user_tag` 从 `"human"` 改成 `"user"`（数据里写的是 `human`），重跑。

**这一步在选什么**

| 你改了什么 | 会发生什么 | 说明 |
|---|---|---|
| `role_tag` 改成数据里不存在的键 | 框架取不到角色 → **报错或整段被当成同一个人** | 证明 `role_tag` 必须指向真实键名 |
| `user_tag` 改成数据里不存在的角色名 | 框架认为"没有用户轮" → **报错或标签错位** | 证明"值"层面也必须逐字一致 |
| 改回正确值 | 恢复正常 | 反证前面的错确实来自这一处 |

::: warning 这类错误的症状很"远"
数据错了，报错可能出现在**训练中途的 collator 里**，而不是数据加载时。
**所以要在数据阶段就把它试出来**——这就是本步骤存在的意义。
:::

**预期**：能观察到"改坏 → 报错/异常 → 改回 → 恢复"的完整对照，并能说出报错来自哪一层。

> 🖼 **截图槽 `c04-05`** — 应截：改坏后的报错信息 + 改回后的正常输出（两张并排）
> 文件名：`c04/05-break-fix.png`

### 步骤 6 · 综合环节：把两种格式的取舍写清楚

| 场景 | 选哪个 | 理由 |
|---|---|---|
| 单轮问答、指令跟随、格式转换 | **Alpaca** | 结构最简单，三字段一目了然 |
| 多轮客服、助手、需要"记住上文" | **ShareGPT** | 唯一能装多轮的格式 |
| 数据里混着单轮和多轮 | **ShareGPT** | 单轮也能塞进 `conversations`（就一对），统一格式省事 |
| 想要最少的注册配置 | **Alpaca** | 不用写 `formatting` / `tags` |

::: tip 一句话决策
**只有一条判断：要不要保留"上下文"。**
要 → ShareGPT；不要 → Alpaca。
:::

**预期**：能给出"我这份数据该选哪种"的明确结论 + 理由。

> 🖼 **截图槽 `c04-06`** — 应截：你写的 Alpaca vs ShareGPT 取舍表
> 文件名：`c04/06-choose.png`

## ⑤ 预期结果与判定标准

| # | 检查项 | 判定标准（必须看到） |
|---|---|---|
| 1 | 结构说得出 | 能说清 `conversations` + `from`/`value` 的结构 |
| 2 | **多轮未被压平** | 一条记录的轮数与原始一致（不是只剩 1 轮） |
| 3 | 文件已生成 | `data/finance_data.json` 存在，中文不转义 |
| 4 | **`formatting` 写了** | 注册里明确写了 `"sharegpt"` |
| 5 | **四个 `tags` 写全** | `role_tag` / `content_tag` / `user_tag` / `assistant_tag` 都在 |
| 6 | **两组合义分得清** | 能分别解释 `role_tag/content_tag`（键名）与 `user_tag/assistant_tag`（值名） |
| 7 | **加载器读出多轮** | 打印出正确会话数、正确轮数、正确角色名 |
| 8 | **破坏性验证做过** | 有"改坏 → 报错 → 改回"的对照记录 |
| 9 | **能说清为什么** | 能解释"角色名与注册不一致为什么会导致失败" |
| 10 | **取舍有结论** | 能对"该用 Alpaca 还是 ShareGPT"给出明确判断标准 |
| 11 | **理解性目标：顺序即上下文** | 能说清多轮的角色交替顺序就是模型要学的上下文 |
| 12 | 实例状态 | 确认未无谓占用 GPU |

> 第 2、6、8、11 项是重点：**转换是体力活；"轮次不能丢""两层 tag 各管什么""一致性的后果"才是这道题要带走的东西。**

## ⑥ 常见报错

| 报错 | 原因 | 处置 |
|---|---|---|
| **数据只剩最后一轮** | 转换时把会话拆成了多条记录 | 一个会话只放一个 `conversations`，别拆 |
| **`KeyError` / 角色取不到** | `tags.role_tag` 指向的键名与数据不符 | 数据里是 `from`，`role_tag` 就得是 `"from"` |
| **报错说找不到用户轮 / 标签错位** | `user_tag`/`assistant_tag` 与数据里的角色名不一致 | 数据写 `human` 就填 `"human"`，改数据要同步改注册 |
| **按 Alpaca 解析多轮失败** | 忘了写 `"formatting": "sharegpt"` | 加上它 |
| **`columns.messages` 写成了 `prompt/query/response`** | 沿用了 Alpaca 的三键 | ShareGPT 只有 `messages` 一个，指到 `conversations` |
| `Unknown dataset: finance_data` | 没注册或 JSON 语法错 | 用 `python -m json.tool` 验语法 |
| `FileNotFoundError` | 文件没在 `data/` 或 `file_name` 写了路径 | 只写文件名 |
| 中文变 `\uXXXX` | 没加 `ensure_ascii=False` | 加上重写 |
| 训练中 loss 异常震荡 | 多轮里出现了连续两条同角色 | 检查角色是否 human/gpt 交替 |
| 验证集拆分后样本变少很多 | 一条=一个会话，会话数本来就少 | 正常。会话数少时别切太大验证集 |

## ⑦ 延伸

1. **加一个 `system` 角色**：在 `conversations` 开头插一条 `{"from": "system", "value": "你是..."}`，注册里加 `system_tag`。**系统提示词怎么进数据？**
2. **混合数据**：把 [C03](/training/p10/c03-alpaca-dataset) 的单轮 Alpaca 转成 ShareGPT（一对 `human`/`gpt` 即可），和本案例的多轮数据**合并成一个文件**，用同一个注册条目。**这样做有什么好处？**
3. **多轮 + 截断**：在 `check_sharegpt.py` 里统计每种长度的会话占比。**超长会话会不会被 `cutoff_len` 截掉上下文？** → 想想 [Part 1 的 cutoff_len](/training/p1/09-tuning-quant)。
4. **把角色名整个换掉**：数据里改成 `user`/`assistant`，注册里也改。**改动是否彻底？还有哪里有隐藏耦合？**
5. **接入训练**：把 `finance_data` 用在 [C05](/training/p10/c05-lora-sft) 的 YAML 里 `dataset: finance_data`，体会"多轮 SFT"和"单轮 SFT"在训练日志上的差别。
6. **写一份自己的数据规范**：把本案例的"必须项"（三字段或 conversations、role 一致、不许拆会话、不许空 output）固化成团队规范文档。

---

> 上一案例：[C03 制作一份合规的 Alpaca 格式自定义数据集](/training/p10/c03-alpaca-dataset) ｜ [案例库总览](/training/p10/) ｜ [Part 2 末页题目](/training/p2/04-custom-dataset)
