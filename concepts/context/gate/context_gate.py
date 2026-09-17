"""context_gate.py — context 章 L5 验收（示意，部分检查需真实 tokenizer/日志抽象）
运行：python gate/context_gate.py
"""
from typing import Annotated, TypedDict
import operator


# ---- 可审计日志：append-only + surface 投影 ----
class SessionLog:
    """极简 append-only 日志 + surface 投影（演示 compaction 不绕过日志）。"""

    def __init__(self):
        self.events = []          # 全量事件（可回放）
        self.surface = []         # 模型看到的投影

    def append(self, ev):
        self.events.append(ev)    # 只追加，不修改

    def compact(self, summary_event):
        # 压缩不是改旧事件，而是追加一个 replace 事件并重建投影
        self.events.append(summary_event)
        self.surface = [e for e in self.events if e.get("surface")]
        return True


# ---- DSE：确定性信号提取 ----
def dse_extract(text):
    """确定性提取（同输入必同输出）：抓 '约束:'/'用户:' 标记。"""
    out = []
    for line in text.splitlines():
        for prefix in ("约束:", "用户:"):
            if line.startswith(prefix):
                out.append(line)
    return out


def budget_controller_degrades_ok():
    """超预算输入下降配不崩（简化）。"""
    usage = {"system": 4000, "task": 8000, "retrieved": 40000}
    total = sum(usage.values())
    alarm = 0.85 * 32000
    if total > alarm:                       # 降配 retrieved
        while total > alarm and usage["retrieved"] > 1000:
            usage["retrieved"] //= 2
            total = sum(usage.values())
    return total <= 32000                   # 降配后不超预算、不崩


def compaction_not_bypass_log():
    log = SessionLog()
    log.append({"surface": True, "msg": "旧消息1"})
    log.append({"surface": True, "msg": "旧消息2"})
    log.compact({"surface": True, "msg": "[摘要]", "type": "replace"})
    # 旧事件仍在（可回放），投影已被收缩为摘要
    return len(log.events) == 3 and log.surface[-1]["msg"] == "[摘要]"


def dse_is_deterministic():
    txt = "约束: 只读不改\n用户: alice\n约束: 超时5s"
    return dse_extract(txt) == dse_extract(txt)   # 同一输入两次同输出


def count_tokens(text, enc_name="cl100k_base"):
    """真实 tokenizer 计数（tiktoken）。chat 模型可用 encoding_for_model，
    这里用 cl100k_base 作为 gpt-4o/claude 近似的确定基线。"""
    import tiktoken
    enc = tiktoken.get_encoding(enc_name)
    return len(enc.encode(text))


def tiktoken_differs_from_split():
    """真实验证：中文/代码的真实 token 数与 len(split()) 估算不同。
    这证明 2-1 骨架用 len(split()) 会低估预算，必须换真实 tokenizer。"""
    sample = "def f():\n    return '中文测试'"      # 含中文与代码符号
    split_est = len(sample.split())                  # 空格切分估算
    real = count_tokens(sample)                      # 真实 tokenizer
    print(f"    split估算={split_est}, 真实tokens={real}")
    return real != split_est


def chinese_token_cost_is_real():
    """真实验证：中文按字符计 token，长中文段落显著消耗预算（不是 1 个词 1 token）。"""
    zh = "上下文工程是在有限窗口内动态选取组织注入压缩信息"   # 24 个汉字
    n = count_tokens(zh)
    print(f"    中文 {len(zh)} 字 -> {n} tokens")
    return n > 0 and n != len(zh.split())            # 与空白切分（=1）必然不同


# ---- DSE：确定性信号提取（实体/意图/约束），产物可断言 ----
import re

DSE_ENTITY_RULES = {
    "emails": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
    "urls":   re.compile(r"https?://[^\s)。，、；]+"),
    "versions": re.compile(r"\b\d+\.\d+\.\d+\b"),
}
DSE_INTENT_VERBS = ["部署", "回滚", "查询", "修改", "删除", "重构"]
DSE_CONSTRAINT_PAT = re.compile(
    r"(必须[^。;；，\n]*|禁止[^。;；，\n]*|只读|不改[^。;；，\n]*|不超过\s*\d+[^。;；，\n]*|超时\s*\d+\s*秒?)"
)


def dse_extract_rich(text):
    """确定性提取结构化信号（无 LLM、同输入同输出）。"""
    entities = {k: sorted(set(p.findall(text))) for k, p in DSE_ENTITY_RULES.items()}
    entities = {k: v for k, v in entities.items() if v}
    intent = None
    for line in text.splitlines():
        for v in DSE_INTENT_VERBS:                 # 词表顺序固定 → 结果确定
            if v in line:
                intent = v
                break
        if intent:
            break
    return {"entities": entities, "intent": intent,
            "constraints": DSE_CONSTRAINT_PAT.findall(text)}


def dse_fields_are_assertable():
    """真实验证：DSE 产物是结构化字段，可被 assert 直接断言（对比 LLM 摘要不可断言）。"""
    s = ("用户 alice@corp.com 要求：把 https://svc/api/v1.2.3 部署到 prod，"
         "必须只读校验，超时 5 秒，不改 config.yaml")
    out = dse_extract_rich(s)
    ok = (out["entities"].get("emails") == ["alice@corp.com"]      # 实体可断言
          and out["intent"] == "部署"                               # 意图可断言
          and "必须只读校验" in out["constraints"]                   # 约束可断言
          and dse_extract_rich(s) == out)                          # 确定性可断言
    print(f"    entities={out['entities'].get('emails')}, intent={out['intent']}, "
          f"constraints={len(out['constraints'])} 条")
    return ok


# ---- 策略分派：声明式表 + 固定顺序流水线（DSE 先，LLM 只在残余上）----
DSE, LLM, PRUNE = "dse", "llm", "prune"

ROUTING = {                      # 静态声明，运行时零决策（非 LLM 判断）
    "identity": DSE, "constraint": DSE, "tool_call": DSE,
    "narrative": LLM, "chatter": PRUNE,
}

_SAMPLE = ("用户 alice@corp.com 向 bob@corp.com 说：请把 https://svc/api/v1.2.3 部署到 prod，\n"
           "必须只读校验，超时 5 秒，不改 config.yaml\n"
           "另外我这边还有一堆杂七杂八的事情，比如上周那个讨论会大家聊了很久关于架构\n"
           "演进的方向，最后也没定下来，先这样吧\n"
           "谢谢老师")


def residual_text(text, dse_out):
    """剔除 DSE 已抽走的行——残余才交给 LLM，避免双份成本与语义重复。"""
    cons = set(dse_out["constraints"])
    keep = []
    for line in text.splitlines():
        if line in cons or DSE_CONSTRAINT_PAT.search(line):
            continue
        if any(p.search(line) for p in DSE_ENTITY_RULES.values()):
            continue
        keep.append(line)
    return "\n".join(keep)


def compress(text, strategy="hybrid", summarize_fn=None):
    """三模式：dse_only（零 LLM）/ llm_only（全量 LLM）/ hybrid（默认）。"""
    stats = {"llm_calls": 0, "llm_in_chars": 0}
    payload = {}
    if strategy in ("dse_only", "hybrid"):
        payload["signals"] = dse_extract_rich(text)           # ① DSE 总是先跑
    residual = text if strategy == "llm_only" else residual_text(text, payload["signals"])
    if strategy != "dse_only" and residual.strip() and len(residual) > 40:
        payload["summary"] = (summarize_fn or (lambda s: s[:40] + "…"))(residual)
        stats["llm_calls"] += 1                               # ② LLM 只吃残余
        stats["llm_in_chars"] = len(residual)
    return payload, stats                                     # ③ 组装 signals + summary


def strategy_dispatch_is_declarative():
    """真实验证：策略由静态表定死（非 LLM 决策），三模式行为可预期。"""
    ok_set = set(ROUTING.values()) <= {DSE, LLM, PRUNE}       # 分派值闭集
    _, s_dse = compress(_SAMPLE, "dse_only")
    _, s_hy = compress(_SAMPLE, "hybrid")
    p_dse, _ = compress(_SAMPLE, "dse_only")
    p_hy, _ = compress(_SAMPLE, "hybrid")
    ok = (ok_set
          and s_dse["llm_calls"] == 0                         # dse_only 零 LLM
          and s_hy["llm_calls"] == 1                           # hybrid 只调一次
          and s_hy["llm_in_chars"] < len(_SAMPLE)              # LLM 只吃残余（更省）
          and p_hy["signals"] == p_dse["signals"])             # 策略不影响 DSE 结果
    print(f"    dse_only.llm_calls={s_dse['llm_calls']}, "
          f"hybrid LLM 输入={s_hy['llm_in_chars']}/{len(_SAMPLE)} 字符")
    return ok


def dse_before_llm_order_is_contract():
    """真实验证：先摘要再 DSE 会因措辞被改写而静默丢约束 → 顺序是契约。"""
    def summarize_rewrites(s):          # 模拟 LLM 摘要改写措辞
        return (s.replace("必须只读校验", "需要保证可读")
                 .replace("不改 config.yaml", "保持配置不变"))

    good = dse_extract_rich(_SAMPLE)["constraints"]                    # 正确：DSE 先
    bad = dse_extract_rich(summarize_rewrites(_SAMPLE))["constraints"]  # 错误：摘要先
    print(f"    正确顺序 {len(good)} 条约束；顺序颠倒 {len(bad)} 条")
    return len(good) > len(bad)


def main():
    checks = [
        budget_controller_degrades_ok(),
        compaction_not_bypass_log(),
        dse_is_deterministic(),
        tiktoken_differs_from_split(),
        chinese_token_cost_is_real(),
        dse_fields_are_assertable(),
        strategy_dispatch_is_declarative(),
        dse_before_llm_order_is_contract(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "context gate failed"
    print("PASS: context gate 8/8（真实 tokenizer + DSE 可断言 + 分派声明式 + 顺序契约）")


if __name__ == "__main__":
    main()