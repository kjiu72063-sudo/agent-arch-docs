"""gate_12_deploy_config.py — Ollama Modelfile / vLLM yaml 字段合法性

对应页面：6-7 Ollama 部署全流程 · 6-8 vLLM 与 PagedAttention · 6-9 vLLM+FastAPI
代码依据：fixtures/Modelfile（ollama相关代码/Modulefile）
          fixtures/qwen3_1_7b.yaml（vllm相关代码，LLaMA-Factory 推理配置）

验证什么：
  A. Modelfile——指令白名单、FROM 必须首行、PARAMETER 键合法且值类型正确、
     取值范围合理、TEMPLATE 花括号配对且含 {{ .System }}/{{ .Prompt }}、
     SYSTEM 三引号闭合。
  B. qwen3_1_7b.yaml——顶层必填键、infer_backend 枚举、trust_remote_code 布尔、
     vllm_config 子键、dtype 枚举、gpu_memory_utilization ∈ (0,1]、max_model_len 正整数。
  C. 源材料提醒：dtype: float32 对 vLLM 非常罕见（推理一般 bf16/fp16），
     且 model_name_or_path 指向目录而非具体模型——显式标注为源配置可改进点。

为什么确定：Schema 可断言，纯结构校验，不做任何实测。
运行：python training/gate/gate_12_deploy_config.py
"""

import os
import re

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
MODELFILE = os.path.join(FIX, "Modelfile")
YAMLFILE = os.path.join(FIX, "qwen3_1_7b.yaml")

# --- Modelfile 语法约定 ---
INSTRUCTIONS = {"FROM", "PARAMETER", "SYSTEM", "TEMPLATE", "LICENSE",
                "MESSAGE", "ADAPTER", "PROJECTOR"}
NUM_PARAMS = {"num_ctx", "num_predict", "num_gpu", "num_thread", "top_k",
              "seed", "repeat_last_n", "num_batch", "main_gpu"}
FLOAT_PARAMS = {"temperature", "top_p", "repeat_penalty", "min_p", "typical_p",
                "tfs_z", "mirostat_eta", "mirostat_tau"}


def read_modelfile():
    with open(MODELFILE, "r", encoding="utf-8") as f:
        return f.read()


def parse_modelfile(text):
    """返回 (instructions, params, has_system, template_ok)。"""
    lines = text.splitlines()
    instrs, params = [], {}
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        head = stripped.split(None, 1)[0].upper()
        instrs.append(head)
        if head == "PARAMETER":
            _, rest = stripped.split(None, 1)
            key, _, val = rest.partition(" ")
            params[key.strip()] = val.strip()
        if head in ("SYSTEM", "TEMPLATE"):
            # 三引号块可能跨多行
            if '"""' in stripped and stripped.count('"""') % 2 == 1:
                i += 1
                while i < n and '"""' not in lines[i]:
                    i += 1
        i += 1
    return instrs, params, text


def check_a1_from_first():
    instrs, _, _ = parse_modelfile(read_modelfile())
    ok = instrs and instrs[0] == "FROM"
    print(f"    Modelfile 指令序列 = {instrs}  ⇒ 首条为 FROM={ok}")
    return ok


def check_a2_instruction_whitelist():
    instrs, _, _ = parse_modelfile(read_modelfile())
    unknown = [x for x in instrs if x not in INSTRUCTIONS]
    ok = not unknown
    print(f"    未知指令 = {unknown or '无'}  ⇒ 全部合法={ok}")
    return ok


def check_a3_param_types():
    _, params, _ = parse_modelfile(read_modelfile())
    ok = True
    for k, v in params.items():
        if k in NUM_PARAMS:
            if not re.fullmatch(r"-?\d+", v):
                ok = False
        elif k in FLOAT_PARAMS:
            try:
                float(v)
            except ValueError:
                ok = False
        elif k not in INSTRUCTIONS:
            # 未登记键不判错，只提示
            print(f"    (未登记参数 {k}={v}，不做类型断言)")
    print(f"    PARAMETER 类型检查：{params}  ⇒ 合法={ok}")
    return ok


def check_a4_param_ranges():
    _, params, _ = parse_modelfile(read_modelfile())
    ok = True
    if "temperature" in params:
        t = float(params["temperature"]); ok &= (0.0 <= t <= 2.0)
        print(f"    temperature={t} ∈ [0,2] = {0.0<=t<=2.0}")
    if "top_p" in params:
        p = float(params["top_p"]); ok &= (0.0 < p <= 1.0)
        print(f"    top_p={p} ∈ (0,1] = {0.0<p<=1.0}")
    if "num_ctx" in params:
        c = int(params["num_ctx"]); ok &= c > 0 and (c & (c - 1)) == 0
        print(f"    num_ctx={c} 为正且为 2 的幂 = {c>0 and (c&(c-1))==0}")
    if "num_predict" in params:
        np_ = int(params["num_predict"]); ok &= np_ > 0
        print(f"    num_predict={np_} > 0 = {np_>0}")
    return bool(ok)


def check_a5_template_balanced():
    text = read_modelfile()
    opens = len(re.findall(r"\{\{", text))
    closes = len(re.findall(r"\}\}", text))
    has_sys = "{{ .System }}" in text
    has_prompt = "{{ .Prompt }}" in text
    ok = opens == closes and opens > 0 and has_sys and has_prompt
    print(f"    花括号开={opens} 闭={closes}；.System={has_sys}；.Prompt={has_prompt}  ⇒ 合法={ok}")
    return ok


def check_a6_system_triple_quoted():
    text = read_modelfile()
    sys_line = [l for l in text.splitlines() if l.strip().upper().startswith("SYSTEM")]
    ok = bool(sys_line) and sys_line[0].count('"""') == 2
    print(f"    SYSTEM 行三引号闭合 = {ok}")
    return ok


# --- YAML 最小子集解析（两level，支持 # 注释与 key: value） ---

def parse_yaml(text):
    top, nested, cur = {}, {}, None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            v = v.strip()
            if v == "":
                cur = k.strip(); nested[cur] = {}
            else:
                top[k.strip()] = v; cur = None
        else:
            if cur is not None and ":" in line:
                k, _, v = line.partition(":")
                nested[cur][k.strip()] = v.split("#")[0].strip()
    return top, nested


def read_yaml():
    with open(YAMLFILE, "r", encoding="utf-8") as f:
        return parse_yaml(f.read())


def check_b1_required_keys():
    top, _ = read_yaml()
    need = {"model_name_or_path", "template", "infer_backend", "trust_remote_code"}
    missing = need - set(top)
    ok = not missing
    print(f"    yaml 顶层键 = {sorted(top)}  缺={missing or '无'}")
    return ok


def check_b2_backend_enum():
    top, _ = read_yaml()
    allowed = {"huggingface", "vllm", "sglang"}
    v = top.get("infer_backend", "")
    ok = v in allowed
    print(f"    infer_backend='{v}' ∈ {sorted(allowed)} = {ok}")
    return ok


def check_b3_trust_remote_code_bool():
    top, _ = read_yaml()
    v = top.get("trust_remote_code", "").lower()
    ok = v in ("true", "false")
    print(f"    trust_remote_code='{v}' 是布尔字面量 = {ok}")
    return ok


def check_b4_vllm_config():
    _, nested = read_yaml()
    cfg = nested.get("vllm_config", {})
    need = {"dtype", "gpu_memory_utilization", "max_model_len"}
    missing = need - set(cfg)
    ok = not missing
    print(f"    vllm_config = {cfg}  缺={missing or '无'}")
    return ok


def check_b5_vllm_values():
    _, nested = read_yaml()
    cfg = nested.get("vllm_config", {})
    ok = True
    dt = cfg.get("dtype", "")
    ok &= dt in {"float16", "bfloat16", "float32", "half", "auto"}
    print(f"    dtype='{dt}' 属合法枚举 = {dt in {'float16','bfloat16','float32','half','auto'}}")
    try:
        g = float(cfg.get("gpu_memory_utilization", "0"))
        ok &= (0.0 < g <= 1.0)
        print(f"    gpu_memory_utilization={g} ∈ (0,1] = {0.0<g<=1.0}")
    except ValueError:
        ok = False
    try:
        m = int(cfg.get("max_model_len", "0"))
        ok &= m > 0
        print(f"    max_model_len={m} > 0 = {m>0}")
    except ValueError:
        ok = False
    return bool(ok)


def check_c_source_caveats():
    """源配置可改进点：显式记录而非静默通过。"""
    top, nested = read_yaml()
    cfg = nested.get("vllm_config", {})
    dt = cfg.get("dtype", "")
    path = top.get("model_name_or_path", "")
    warns = []
    if dt == "float32":
        warns.append("vLLM 推理用 float32 罕见（一般 bfloat16/float16），显存与时延代价大")
    if path.endswith("/"):
        warns.append(f"model_name_or_path='{path}' 指向目录而非具体模型名")
    ok = True   # 只提醒，不判失败（这是源材料的可改进点，不是我们的断言）
    for w in warns:
        print(f"    [!] {w}")
    print(f"    记录 {len(warns)} 条源配置提醒 ⇒ 本检查只披露不拦截")
    return ok


def main():
    checks = [
        check_a1_from_first(),
        check_a2_instruction_whitelist(),
        check_a3_param_types(),
        check_a4_param_ranges(),
        check_a5_template_balanced(),
        check_a6_system_triple_quoted(),
        check_b1_required_keys(),
        check_b2_backend_enum(),
        check_b3_trust_remote_code_bool(),
        check_b4_vllm_config(),
        check_b5_vllm_values(),
        check_c_source_caveats(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_12 failed"
    print("PASS: gate_12 部署配置 12/12（Modelfile 6 项 + yaml 5 项 + 源提醒 1 项）")


if __name__ == "__main__":
    main()
