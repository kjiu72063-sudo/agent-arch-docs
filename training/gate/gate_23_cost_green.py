"""gate_23_cost_green.py — 成本与绿色 AI：三条换算自洽 + Spot/On-Demand + 电价/碳强度

对应页面：9-11b 成本与绿色 AI

验证什么：
  1. $/百万 token 换算自洽：`租金 ÷ (吞吐 × 3600) × 1e6`
     （T4 → $0.0784；5090 → $0.8755；比值 ≈ 11.17）
  2. 本地电费：`功耗(kW) × 24 × 电价` → 与界面读数在 0.1% 内吻合
     （月按 30 天、年按 365 天，**不是**月×12）
  3. 年度 CO₂：`功耗(kW) × 24 × 365 × 碳强度` → 与界面读数吻合，
     并反推碳强度 475.27 g/kWh（界面显示 475 是取整）
  4. Spot vs On-Demand：溢价倍数 = 2.20 / 1.43 ≈ 1.54（竞价便宜约 35%）
  5. 训练总成本 = 单价 × 时长，与界面 $8.10 / $12.47 吻合

为什么确定：纯算术，无实测成分（读数来自计算器界面）。
运行：python training/gate/gate_23_cost_green.py
"""

import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P9 = os.path.join(HERE, "..", "p9")

# 计算器界面读数（录屏 OCR）
POWER_W = 586.0
ELEC_PRICE = 0.12          # $/kWh
CARBON_G = 475.0           # g/kWh（界面显示值）
UI_DAILY = 1.689
UI_MONTHLY = 50.659
UI_YEARLY = 616.352
UI_CO2_YEAR = 2439.7
UI_HOURS = 5.7
UI_SPOT_RATE = 1.43
UI_ONDEMAND_RATE = 2.20
UI_SPOT_TOTAL = 8.10
UI_ONDEMAND_TOTAL = 12.47
UI_CO2_DAY = 6.68


def check1_cost_per_million_tokens():
    """$/百万 token 换算自洽 + T4 与 5090 的比值。"""
    def cpm(rent, tps):
        return rent / (tps * 3600) * 1e6
    t4 = cpm(0.12, 425)
    g5090 = cpm(1.10, 349)
    ratio = g5090 / t4
    ok = abs(t4 - 0.0784) < 1e-4 and abs(g5090 - 0.8755) < 1e-4
    ok = ok and abs(ratio - 11.17) < 0.02
    print(f"    1x T4 (16GB)   $0.12/hr × 425 t/s → ${t4:.4f}/百万token")
    print(f"    RTX 5090 (32GB) $1.10/hr × 349 t/s → ${g5090:.4f}/百万token")
    print(f"    比值 = {ratio:.2f}x  →  便宜的卡完胜 11 倍")
    return ok


def check2_daily_electricity():
    """每天电费 = 功耗(kW) × 24 × 电价，与界面 0.1% 内吻合。"""
    kwh = POWER_W / 1000 * 24
    daily = kwh * ELEC_PRICE
    ok = abs(daily - UI_DAILY) / UI_DAILY < 0.001
    print(f"    586 W = {POWER_W / 1000:.3f} kW → 每天 {kwh:.3f} kWh"
          f" → {daily:.4f} USD   vs 界面 {UI_DAILY}  偏差 {abs(daily - UI_DAILY) / UI_DAILY * 100:.3f}%")
    return ok


def check3_monthly_yearly_use_30_and_365():
    """月 = 30 天、年 = 365 天（**不是** 月×12）。"""
    kwh = POWER_W / 1000 * 24
    monthly = kwh * 30 * ELEC_PRICE
    yearly = kwh * 365 * ELEC_PRICE
    ok = (abs(monthly - UI_MONTHLY) / UI_MONTHLY < 0.001
          and abs(yearly - UI_YEARLY) / UI_YEARLY < 0.001)
    # 反证：若按 月×12 则与界面不符
    wrong = monthly * 12
    ok = ok and abs(wrong - UI_YEARLY) / UI_YEARLY > 0.01
    print(f"    月(30天) {monthly:.3f} vs 界面 {UI_MONTHLY}")
    print(f"    年(365天) {yearly:.3f} vs 界面 {UI_YEARLY}")
    print(f"    若按『月×12』 = {wrong:.3f} → 与界面差 "
          f"{abs(wrong - UI_YEARLY) / UI_YEARLY * 100:.1f}%  →  排除")
    return ok


def check4_yearly_co2_and_carbon_intensity():
    """年度 CO₂ 与反推的碳强度 475.27 g/kWh。"""
    kwh_year = POWER_W / 1000 * 24 * 365
    co2 = kwh_year * (CARBON_G / 1000)
    ok = abs(co2 - UI_CO2_YEAR) / UI_CO2_YEAR < 0.001
    implied = UI_CO2_YEAR / kwh_year * 1000
    ok = ok and abs(implied - 475.27) < 0.1
    print(f"    年耗电 {kwh_year:.2f} kWh × 0.475 kg/kWh = {co2:.2f} kg"
          f"  vs 界面 {UI_CO2_YEAR}  偏差 {abs(co2 - UI_CO2_YEAR) / UI_CO2_YEAR * 100:.3f}%")
    print(f"    反推碳强度 = {implied:.2f} g/kWh  →  界面显示的 475 是取整值 ✓")
    return ok


def check5_co2_per_day_selfconsistent():
    """CO₂/天 = 日耗电 × 碳强度，与界面 6.68 kg 吻合。"""
    kwh = POWER_W / 1000 * 24
    co2d = kwh * (CARBON_G / 1000)
    ok = abs(co2d - UI_CO2_DAY) / UI_CO2_DAY < 0.01
    print(f"    {kwh:.3f} kWh × 0.475 kg/kWh = {co2d:.3f} kg  vs 界面 {UI_CO2_DAY}")
    return ok


def check6_spot_vs_ondemand():
    """Spot vs On-Demand：溢价 1.54 倍；总成本 = 单价 × 时长，且反推时长一致。

    注意：界面 `5.7h` 是**取整显示**——两个单价各自反推出的时长
    （8.10/1.43 = 5.664h、12.47/2.20 = 5.668h）彼此一致，
    但都略小于显示的 5.7h。这与碳强度 475 的取整是同一种现象。
    """
    premium = UI_ONDEMAND_RATE / UI_SPOT_RATE
    saving = 1 - UI_SPOT_RATE / UI_ONDEMAND_RATE
    ok = abs(premium - 1.5385) < 0.001 and abs(saving - 0.35) < 0.005

    h_spot = UI_SPOT_TOTAL / UI_SPOT_RATE
    h_ondemand = UI_ONDEMAND_TOTAL / UI_ONDEMAND_RATE
    # 两条独立反推的时长必须彼此一致（差 < 0.01h）
    ok = ok and abs(h_spot - h_ondemand) < 0.01
    # 且两者都应 ≤ 界面显示的 5.7h（说明 5.7 是上取整）
    ok = ok and h_spot <= UI_HOURS and h_ondemand <= UI_HOURS
    # 界面显示的 5.7h 与之差 < 0.05
    ok = ok and abs(UI_HOURS - h_spot) < 0.05
    print(f"    溢价 {premium:.3f}x  →  Spot 便宜 {saving * 100:.1f}%")
    print(f"    8.10 / 1.43 = {h_spot:.4f} h     12.47 / 2.20 = {h_ondemand:.4f} h"
          f"   ← 两条独立反推一致")
    print(f"    界面显示 {UI_HOURS} h → 取整值（真实 ≈ {h_spot:.3f} h）")
    return ok


def check7_all_three_formulas_documented():
    """9-11b 正文必须载有三条换算公式与全部读数。"""
    txt = io.open(os.path.join(P9, "12-cost-green.md"), encoding="utf-8").read()
    need = ["租金($/hr) ÷ (吞吐(tokens/s) × 3600) × 1,000,000",
            "功耗(kW) × 24 × 电价($/kWh)",
            "功耗(kW) × 24 × 365 × 电网碳强度",
            "1.689", "50.659", "616.352", "2439.7", "1.43", "2.20",
            "0.0784", "0.8755", "475"]
    missing = [n for n in need if n not in txt]
    ok = not missing
    print(f"    9-11b 关键词/读数命中 {len(need) - len(missing)}/{len(need)}"
          f"{'  缺失: ' + str(missing) if missing else ''}")
    return ok


def main():
    checks = [
        check1_cost_per_million_tokens(),
        check2_daily_electricity(),
        check3_monthly_yearly_use_30_and_365(),
        check4_yearly_co2_and_carbon_intensity(),
        check5_co2_per_day_selfconsistent(),
        check6_spot_vs_ondemand(),
        check7_all_three_formulas_documented(),
    ]
    for i, ok in enumerate(checks, 1):
        print(f"check{i}: {'PASS' if ok else 'FAIL'}")
    assert all(checks), "gate_23 failed"
    print("PASS: gate_23 成本与绿色 AI 7/7（$/百万token + 日电费 + 月30日年365 + 年CO2与碳强度 + CO2/天 + Spot对比 + 正文）")


if __name__ == "__main__":
    main()
