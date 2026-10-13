"""gate_06_lora_galore_exclusive.py — LoRA 与 GaLore/BAdam 配置互斥检测

对应页面：3-4 全参 / Freeze / GaLore / BAdam
讲义依据：L2 P27 原文——
  "注意: 不要将 LoRA 和 GaLore/BAdam一起使用"
  "使用GaLore/ BAdam 时请设置 finetuning_type 为 full 且 pure_bf16 为 True"

验证什么：把这两条硬约束编码成校验器，并对合规/违规配置做布尔断言。
为什么确定：布尔断言。
运行：python training/gate/gate_06_lora_galore_exclusive.py
"""

LORA_FAMILY = {"lora", "qlora"}
GALORE_FAMILY = {"galore", "badam"}


def validate(cfg):
    """返回 (ok, [errors])。cfg 形如:
    {"finetuning_type": "lora"|"full", "use_lora": bool, "optim": "galore"|"badam"|"adamw",
     "pure_bf16": bool}
    """
    errors = []
    ft = cfg.get("finetuning_type")
    use_lora = cfg.get("use_lora", False)
    optim = cfg.get("optim", "adamw")
    pure_bf16 = cfg.get("pure_bf16", False)

    # 规则 1：LoRA 与 GaLore/BAdam 不可同用
    if use_lora and optim in GALORE_FAMILY:
        errors.append("LoRA 与 GaLore/BAdam 不可同用（L2 P27）")

    # 规则 2：用 GaLore/BAdam 时必须 finetuning_type=full
    if optim in GALORE_FAMILY and ft != "full":
        errors.append("使用 GaLore/BAdam 时 finetuning_type 必须为 full（L2 P27）")

    # 规则 3：用 GaLore/BAdam 时必须 pure_bf16=True
    if optim in GALORE_FAMILY and pure_bf16 is not True:
        errors.append("使用 GaLore/BAdam 时 pure_bf16 必须为 True（L2 P27）")

    return (len(errors) == 0), errors


def check1_valid_galore_config_passes():
    cfg = {"finetuning_type": "full", "use_lora": False, "optim": "galore", "pure_bf16": True}
    ok, err = validate(cfg)
    print(f"    合规 GaLore: ok={ok} err={err}")
    return ok and not err


def check2_valid_badam_config_passes():
    cfg = {"finetuning_type": "full", "use_lora": False, "optim": "badam", "pure_bf16": True}
    ok, err = validate(cfg)
    print(f"    合规 BAdam: ok={ok} err={err}")
    return ok and not err


def check3_lora_plus_galore_is_rejected():
    """违反 L2 P27 第一条：LoRA + GaLore 必须被拒。"""
    cfg = {"finetuning_type": "lora", "use_lora": True, "optim": "galore", "pure_bf16": True}
    ok, err = validate(cfg)
    print(f"    违规 LoRA+GaLore: ok={ok} err={err}")
    return (not ok) and any("不可同用" in e for e in err)


def check4_galore_without_full_is_rejected():
    """违反 L2 P27 第二条：GaLore 但 finetuning_type != full。"""
    cfg = {"finetuning_type": "lora", "use_lora": False, "optim": "badam", "pure_bf16": True}
    ok, err = validate(cfg)
    print(f"    违规 finetuning_type=lora: ok={ok} err={err}")
    return (not ok) and any("必须为 full" in e for e in err)


def check5_galore_without_pure_bf16_is_rejected():
    """违反 L2 P27 第三条：GaLore 但 pure_bf16 不为 True。"""
    cfg = {"finetuning_type": "full", "use_lora": False, "optim": "galore", "pure_bf16": False}
    ok, err = validate(cfg)
    print(f"    违规 pure_bf16=False: ok={ok} err={err}")
    return (not ok) and any("pure_bf16" in e for e in err)


def check6_plain_lora_still_ok():
    """普通 LoRA（不混 GaLore）应当通过——约束只针对混用，不是禁用 LoRA。"""
    cfg = {"finetuning_type": "lora", "use_lora": True, "optim": "adamw", "pure_bf16": False}
    ok, err = validate(cfg)
    print(f"    普通 LoRA: ok={ok} err={err}")
    return ok and not err


def main():
    checks = [
        check1_valid_galore_config_passes(),
        check2_valid_badam_config_passes(),
        check3_lora_plus_galore_is_rejected(),
        check4_galore_without_full_is_rejected(),
        check5_galore_without_pure_bf16_is_rejected(),
        check6_plain_lora_still_ok(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_06 failed"
    print("PASS: gate_06 配置互斥 6/6（GaLore/BAdam 合规 + 三种违规被拒 + 普通 LoRA 放行）")


if __name__ == "__main__":
    main()
