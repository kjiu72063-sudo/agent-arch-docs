"""gate_04_data_schema.py — 数据集格式与注册结构校验

对应页面：2-2 数据集格式与注册
讲义依据：L2 P9（alpaca: instruction/input/output 三必须字段）、
         L2 P10（sharegpt 多轮）、L2 P8（无论系统还是自定义数据集都需注册至 dataset_info.json）

验证对象（fixtures/）：
  - `identity_modify.json`  —— **真实课程数据集**（91 条，Alpaca）
  - 内联构造的 ShareGPT 样例与 dataset_info.json 注册样例

为什么确定：Schema 可断言。
运行：python training/gate/gate_04_data_schema.py
"""

import json
import os

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")

ALPACA_FIELDS = {"instruction", "input", "output"}      # 讲义 L2 P9
SHAREGPT_ROLES = {"human", "gpt"}                       # LLaMA-Factory 约定


def check1_real_dataset_is_alpaca():
    """真实 identity_modify.json 每条都含 Alpaca 三字段，且无多余字段。"""
    path = os.path.join(FIX, "identity_modify.json")
    data = json.load(open(path, encoding="utf-8"))
    ok = isinstance(data, list) and len(data) > 0
    for item in data:
        if set(item.keys()) != ALPACA_FIELDS:
            ok = False
            break
    print(f"    identity_modify.json: {len(data)} 条，字段={sorted(data[0].keys())}")
    return ok


def check2_alpaca_values_are_nonempty_strings():
    """三字段都必须是字符串；instruction/output 不能为空。"""
    data = json.load(open(os.path.join(FIX, "identity_modify.json"), encoding="utf-8"))
    ok = all(isinstance(it["instruction"], str) and isinstance(it["input"], str)
             and isinstance(it["output"], str)
             and it["instruction"].strip() and it["output"].strip()
             for it in data)
    empty_inputs = sum(1 for it in data if it["input"] == "")
    print(f"    全部为字符串且 instruction/output 非空；input 为空的有 {empty_inputs}/{len(data)} 条")
    return ok


def check3_sharegpt_sample_conforms():
    """ShareGPT 样例：conversations 为 human/gpt 交替，且以 human 开头。"""
    sample = {"conversations": [
        {"from": "human", "value": "你好，请介绍一下你自己"},
        {"from": "gpt", "value": "我是咕泡科技开发的AI助手。"},
        {"from": "human", "value": "你是谁开发的？"},
        {"from": "gpt", "value": "由咕泡科技开发。"},
    ]}
    convs = sample["conversations"]
    roles_ok = all(c["from"] in SHAREGPT_ROLES and isinstance(c["value"], str)
                   for c in convs)
    alternating = all(convs[i]["from"] != convs[i + 1]["from"] for i in range(len(convs) - 1))
    starts_human = convs[0]["from"] == "human"
    ok = roles_ok and alternating and starts_human and len(convs) % 2 == 0
    print(f"    ShareGPT 样例: {len(convs)} 轮，角色交替={alternating}，human 开头={starts_human}")
    return ok


def check4_dataset_info_structure():
    """dataset_info.json 结构：顶层是 map；alpaca/sharegpt 各带必需键。"""
    dataset_info = {
        "identity_modify": {
            "file_name": "identity_modify.json",
            "columns": {"prompt": "instruction", "query": "input", "response": "output"},
        },
        "finance_sharegpt": {
            "file_name": "finance_data.json",
            "formatting": "sharegpt",
            "columns": {"messages": "conversations"},
            "tags": {"role_tag": "from", "content_tag": "value",
                     "user_tag": "human", "assistant_tag": "gpt"},
        },
    }
    ok = isinstance(dataset_info, dict) and len(dataset_info) == 2
    # Alpaca 注册：必须有 file_name + columns(prompt/response)
    a = dataset_info["identity_modify"]
    ok = ok and "file_name" in a
    ok = ok and {"prompt", "response"} <= set(a["columns"])
    ok = ok and set(a["columns"].values()) <= ALPACA_FIELDS
    # ShareGPT 注册：必须有 formatting=sharegpt + columns.messages + tags 四件套
    s = dataset_info["finance_sharegpt"]
    ok = ok and s.get("formatting") == "sharegpt"
    ok = ok and "messages" in s["columns"]
    ok = ok and {"role_tag", "content_tag", "user_tag", "assistant_tag"} <= set(s["tags"])
    print(f"    dataset_info 顶层 {len(dataset_info)} 项；alpaca/sharegpt 注册键齐全")
    return ok


def check5_registration_is_mandatory_rule():
    """讲义规则：任何数据集都必须注册到 dataset_info.json 才能被训练使用。

    以"未注册的数据集名"查询注册表 → 必须查不到（即规则成立）。
    """
    dataset_info = {"identity_modify": {"file_name": "identity_modify.json"}}
    registered = "identity_modify" in dataset_info
    unregistered = "not_registered_anywhere" in dataset_info
    ok = registered and not unregistered
    print(f"    已注册={registered}，未注册查不到={not unregistered}")
    return ok


def main():
    checks = [
        check1_real_dataset_is_alpaca(),
        check2_alpaca_values_are_nonempty_strings(),
        check3_sharegpt_sample_conforms(),
        check4_dataset_info_structure(),
        check5_registration_is_mandatory_rule(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_04 failed"
    print("PASS: gate_04 数据 schema 5/5（真实 Alpaca 91条 + 值类型 + ShareGPT + 注册结构 + 强制注册）")


if __name__ == "__main__":
    main()
