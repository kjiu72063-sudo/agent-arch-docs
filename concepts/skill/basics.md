---
title: 6-5 基础实践：物理结构与 skill.md 解剖
---

# 6-5 · 基础实践：物理结构与 skill.md 解剖

::: info 难度分层 · 本页 = L1「动手层」
**读到哪算够**：本页给的是"照抄就能建一个 skill"的最小结构。想先搞清概念见 [6-4 概念定义](/concepts/skill/concept)；想搞清它为什么省 token 见 [6-6 渐进披露](/concepts/skill/disclosure)。
:::

[6-1 机制详解](/concepts/skill/mechanism) 给了一个 `SKILL.md` 的**工程写法**（触发条件、执行步骤、边界、失败处理）。本页换个角度：**先看它在磁盘上长什么样，再逐段拆开这个文件本体**。

## 一、物理结构与环境配置

一个 skill 落在磁盘上，就是**三层**：一条标准路径 → 一个容器文件夹 → 一个核心定义文件。

```
<USER ROOT>/
└─ .cloud/                        ← ① 标准存放路径（约定位置，宿主按此发现 skill）
   └─ scale/
      └─ meeting_summary_assistant/   ← ② Skill 容器文件夹（skill 名 = 目录名）
         └─ skill.md                  ← ③ 核心定义文件（唯一必需文件）
```

| 层级 | 作用 | 约束 |
|---|---|---|
| ① 标准存放路径 | 宿主扫描的根，决定"能不能被发现" | 必须放在约定位置，否则等于不存在 |
| ② Skill 容器文件夹 | 一个 skill 的全部资产边界 | 目录名建议与 `name` 一致 |
| ③ 核心定义文件 | 唯一**必需**文件 | 其余脚本、模板、参考文档都是可选 |

::: warning 文件名大小写
不同平台对核心文件的写法不一致（`skill.md` / `SKILL.md`）。**规范采用全大写 `SKILL.md`**；若你的宿主只认小写，以宿主文档为准。混用时最容易出的问题是"文件明明在，就是不被发现"——先查这一条。
:::

容器文件夹里可以放什么：

```
meeting_summary_assistant/
├─ SKILL.md                # 必需：能力说明（入口）
├─ finance_manual.md       # 可选：外部参考知识（条件触发才加载，见 6-7）
└─ upload.py               # 可选：可执行脚本（见 6-7）
```

这与 [6-1 的目录结构](/concepts/skill/mechanism) 是同一件事：**入口 + 资产**。差别只是本页把"资产分几类"讲得更细——**参考知识**与**可执行脚本**是后面两节的主角。

## 二、解剖 SKILL.md（上）：元数据 = 目录

文件开头的 YAML 前置信息，就是这份手册的**目录**：

```markdown
---
name: meeting_summary_assistant
description: 用于总结会议录音内容，提取关键决策。
---
```

| 字段 | 作用 | 写作要点 |
|---|---|---|
| `name` | 全局唯一标识 | 稳定、可读、与目录名一致 |
| `description` | **决定命中率** | 写"做什么 + 什么时候用"，不是写"这是个总结工具" |

::: tip 为什么元数据这么关键
**模型首先只看到这部分。** 它靠 `name` + `description` 判断"当前任务要不要用这个 skill"。

换句话说：`description` 写得含糊，等于这份 skill 永远不会被选中——正文写得再好也没机会出场。这一点在 [6-6 渐进披露](/concepts/skill/disclosure) 会看到量化后果。
:::

## 三、解剖 SKILL.md（下）：指令 = 正文

元数据之后是**指令正文**，只有在 skill 被选中后才被加载：

```markdown
# Instructions
你必须总结参会人员、议题和决定。

## Example
Input: [Audio Transcript]
Output:
- Attendees: ...
- Decisions: ...
```

| 部分 | 定位 | 何时加载 |
|---|---|---|
| 元数据 | 目录（Menu） | **常驻**——扫一遍就知道有哪些 skill |
| 指令正文 | 正文（Content） | **命中才加载**——详细规则与示例 |

正文里最值钱的是 **`## Example`**：用一组 `Input → Output` 把"输出长什么样"钉死。这比十条形容词都管用，也是 6-4 里"标准化输出格式"的落地手段。

## 四、最小可用示例：会议总结助手

把上面三段拼起来，就是一个完整可用的 skill：

```markdown
---
name: meeting_summary_assistant
description: 用于总结会议录音内容，提取关键决策。
---

# Instructions
你必须总结参会人员、议题和决定。

## Example
Input: [Audio Transcript]
Output:
- Attendees: ...
- Decisions: ...
```

注意它**有多短**。skill 的价值不在篇幅，而在"元数据能被搜到、正文能被照做"。正文里塞不下的东西，交给 6-7 的 Reference 与 Script。

## 五、基础交互流程

一个 skill 被用起来，走的是「**握手确认 → 规则执行**」：

```mermaid
sequenceDiagram
  participant U as 用户
  participant A as Agent
  U->>A: 总结以下会议内容……（粘贴文本）
  A->>U: 检测到 meeting_summary_assistant，请求使用权限
  U->>A: 同意
  A->>U: 按 Instructions 输出<br/>参会人员 / 议题 / 决定
```

两个值得注意的点：

1. **中间那道确认不是多余**。skill 一旦被选中，就等于把一套规则写进上下文并要求模型照做——所以宿主会给用户一次"用不用"的机会。这也是 [6-3 常见坑](/concepts/skill/pitfalls) 里"无版本评审地放行 skill"风险的同一来源。
2. **执行是确定性的**。命中后走的是文件里写死的规则，而不是模型临场发挥——这正是 skill 能"标准化输出"的原因。

典型输出（与上面的 `## Example` 对应）：

```
参会人员：
- 张三 · 李四 · 王五

议题：
- Q4 项目进度
- 新技术调研
- 团队建设活动

决定：
- Q4 项目加速推进，截止日期提前至 11 月 15 日
- 由技术团队在下周三前提交新技术可行性报告
- 12 月中旬安排一次团队 outing，由人事部门组织
```

## 小测验

::: details 点击展开题目与答案
**Q1（选择）**：skill 的"容器文件夹"里，哪一个是唯一必需的文件？  
A. `upload.py`　B. 核心定义文件（`SKILL.md`）　C. `finance_manual.md`  
✅ B。脚本与参考文档都是可选的。

**Q2（判断）**：`description` 只是注释，随便写写不影响效果。  
❌ 错。模型**首先只看到元数据**，它决定 skill 是否被选中；写含糊等于永不命中。

**Q3（选择）**：正文里的 `## Example` 主要价值是？  
A. 凑字数　B. 用 Input→Output 钉死输出格式，实现"标准化输出"　C. 替代元数据  
✅ B。
:::

> 上一节：[6-4 概念定义](/concepts/skill/concept) ｜ 下一节：[6-6 渐进披露与按需加载](/concepts/skill/disclosure)
