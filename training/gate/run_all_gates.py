#!/usr/bin/env python3
"""run_all_gates.py — 训练·微调·部署模块 验收脚本统一入口

按文件名顺序执行 training/gate/gate_*.py，汇总 PASS/FAIL。
零依赖（纯标准库），直接：

    python training/gate/run_all_gates.py

退出码：0 = 全部通过；1 = 有失败。
"""

import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    scripts = sorted(glob.glob(os.path.join(HERE, "gate_*.py")))
    if not scripts:
        print("未找到 gate 脚本")
        return 1

    results = []
    for path in scripts:
        name = os.path.basename(path)
        print("=" * 68)
        print(f"▶ {name}")
        print("=" * 68)
        proc = subprocess.run([sys.executable, path], capture_output=True, text=True)
        out = (proc.stdout or "") + (proc.stderr or "")
        # 只打印最后一行结论 + 失败时的 traceback 摘要
        lines = [l for l in out.splitlines() if l.strip()]
        tail = lines[-1] if lines else "(无输出)"
        print(f"  {tail}")
        ok = proc.returncode == 0
        if not ok:
            print("  --- 完整输出 ---")
            print(out)
        results.append((name, ok))

    print("=" * 68)
    print("汇总")
    print("=" * 68)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    passed = sum(1 for _, ok in results if ok)
    print(f"\n{passed}/{len(results)} 通过")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
