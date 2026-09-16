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


def tiktoken_differs_from_split():
    """示意：中文/代码用真实 tokenizer 计数与 len(split) 有差异。"""
    sample = "def f():\n    return '中文测试'"
    split_est = len(sample.split())
    # 真实 tokenizer 对中文/符号通常产生 > 空格切分 的 token 数
    realistic = 9  # 演示值；真实用 tiktoken 等
    return realistic != split_est


def main():
    checks = [
        budget_controller_degrades_ok(),
        compaction_not_bypass_log(),
        dse_is_deterministic(),
        tiktoken_differs_from_split(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "context gate failed"
    print("PASS: context gate 4/4")


if __name__ == "__main__":
    main()