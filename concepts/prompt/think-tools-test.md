---
title: 1-5 策略④⑤⑥ 思考/工具/测试
---

# 1-5 · 策略④ 让模型思考 · ⑤ 使用外部工具 · ⑥ 系统测试

这三条把"写提示词"升级为**搭系统**：推理、工具、验证。

## 策略④ · 给模型时间"思考"

> ✕ "直接告诉我：3.9 和 3.11 谁大？" —— 模型"急着答"，常被带偏。

> ✓ "请先列出推理步骤，再给出结论。" —— **先想后答**，正确率更高。

### 三种常见形态

| 形态 | 做法 | 适用 |
|---|---|---|
| 显式思维链（CoT） | prompt 里要求"先分步推理再作答" | 数学、多步逻辑、需要审计推理过程 |
| 扩展思考（extended thinking） | 由模型侧分配独立"思考预算"（如 Anthropic extended thinking） | 复杂规划、长链推理 |
| 让模型先自评再改 | "先写初稿 → 自我批判 → 修订" | 写作、代码 review 前置 |

> 关键区别：**CoT 是"把思考写进输出"**（你能看到、能审计）；**extended thinking 是"思考在独立通道里"**（不污染最终输出，更适合长推理）。两者都服务于同一个目的：**别让模型边想边答**。

::: tip 落点
这是 [04 loop](/concepts/loop) 里"先规划再执行"的雏形。
:::

## 策略⑤ · 使用外部工具（Tool Use）

模型自己不会算、不会查、不会执行代码，但它能**请求调用工具**，拿到结果再继续。这就是工具调用。

### 一次工具调用的完整往返

```text
① 模型输出：{"tool_call": "read_file", "args": {"path": "package.json"}}
② harness 校验参数（是否越权？路径是否在工作区？）→ 执行 → 拿到内容
③ harness 把结果作为 tool 消息回灌
④ 模型基于结果继续（提取 scripts.test / 决定下一步）
```
> 第②步的**参数校验与权限拦截**是 [03 harness](/concepts/harness) 的职责——工具不是"模型想调就能调"。

### 最小样例：工具 + 程序化验证

任务："读 package.json，找出 scripts.test，**只读不改**"。

```python
# 验证不靠人眼，靠断言
import json, subprocess
out = run_agent("读 package.json 找出 scripts.test，只读不改")
data = json.loads(open("package.json", encoding="utf-8").read())
assert data["scripts"]["test"], "scripts.test 不能为空"        # ① 结果非空
assert not git_dirty(["package.json"]), "任务要求只读，文件不应被改"  # ② 不变量未被破坏
```
> 注意 ②：验证不只是"结果对不对"，还要验**不变量**（"只读"承诺有没有被破坏）。这是 [harness 机械化执行](/concepts/harness/mechanism) 的思想。

## 策略⑥ · 系统地测试改动（Eval）

- **攒一组固定问题（评估集）**：每次改 prompt 都整组重跑；
- **看回归**：改好了 A，别弄坏 B；
- **量化**：用"通过率"而不是"感觉更好了"。

### 最小可运行评估集

```python
# eval.py —— 每次改 prompt 都跑一遍，输出通过率
CASES = [
    {"in": "总结公司年假政策",           "check": lambda r: has_n_items(r, 5) and no_outside_info(r)},
    {"in": "读取 package.json 找 test", "check": lambda r: r.strip() == expected_test_cmd()},
    {"in": "把 for 改成 map",          "check": lambda r: behavior_unchanged(r) and has_comment(r)},
]

def run_eval(prompt_version):
    passed = sum(1 for c in CASES if c["check"](agent(c["in"], prompt_version)))
    rate = passed / len(CASES)
    print(f"{prompt_version}: {passed}/{len(CASES)} = {rate:.0%}")
    return rate

# 回归门禁：新版本通过率不得低于旧版本
assert run_eval("v2") >= run_eval("v1"), "prompt 改动造成回归，拒绝合并"
```

> **评估集就是 prompt 的测试套件**：有了它，"改 prompt"从玄学变成有红线的工程动作。这直接呼应 [04 loop 的 Verifier](/concepts/loop/design)——**独立、可量化、可回归**。

::: info 【事实·直译归纳】
六条策略名称为 OpenAI 提示工程指南内容的直译归纳；该官方页本次抓取被 403、正文未直读，另参考 DeepLearning.AI 课程。详见 [事实源](/practice/compare)。
:::

## 小测验

::: details 点击展开题目与答案
**Q1（选择）**：CoT 与 extended thinking 的核心区别是？  
A. 没有区别　B. CoT 把推理写进输出（可审计），extended thinking 在独立通道（不污染输出）　C. 后者更便宜  
✅ B。

**Q2（判断）**：验证只看"结果对不对"就够了。  
❌ 错。还要验不变量（如"只读"承诺是否被破坏）。

**Q3（选择）**：评估集（eval）对 prompt 改动的意义是？  
A. 让 prompt 更长　B. 把"改 prompt"变成有回归红线的工程动作　C. 替代模型  
✅ B。
:::

> 上一节：[1-4 策略②③](/concepts/prompt/ref-split) ｜ 下一节：[1-6 实例里的 prompt](/concepts/prompt/instances)
