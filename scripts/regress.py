#!/usr/bin/env python3
# 一键回归：读取回归列表，逐条调用 make run，解析 UVM log，生成 sim/result_summary.txt
# 列表格式（sim/regress/regress.list）：每行 "<TEST> <SEED>"，# 开头为注释
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIM = ROOT / "sim"
DEFAULT_LIST = SIM / "regress" / "regress.list"
SUMMARY = SIM / "result_summary.txt"

UVM_ERR_RE = re.compile(r"UVM_(ERROR|FATAL)\s*:?\s+(\d+)")


def parse_log(log_path):
    """UVM report summary 中 ERROR/FATAL 均为 0 才算 PASS。"""
    if not log_path.exists():
        return "NOLOG"
    text = log_path.read_text(encoding="utf-8", errors="replace")
    counts = {kind: int(num) for kind, num in UVM_ERR_RE.findall(text)}
    if not counts:
        return "NOSUMMARY"
    return "PASS" if counts.get("ERROR", 0) == 0 and counts.get("FATAL", 0) == 0 else "FAIL"


def main():
    cov = "1" if "COV=1" in sys.argv[1:] else "0"
    pos = [a for a in sys.argv[1:] if not a.startswith("COV=")]
    list_file = Path(pos[0]) if pos else DEFAULT_LIST
    entries = []
    for lineno, line in enumerate(list_file.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            sys.exit(f"回归列表第 {lineno} 行格式错误（应为 '<TEST> <SEED>'）: {line}")
        entries.append((parts[0], parts[1]))
    if not entries:
        sys.exit("回归列表为空")

    results = []
    for test, seed in entries:
        print(f"== 回归: {test} SEED={seed} ==", flush=True)
        rc = subprocess.run(
            ["make", "-C", str(SIM), "run", f"TEST={test}", f"SEED={seed}", f"COV={cov}"],
        ).returncode
        verdict = parse_log(SIM / "out" / f"{test}_{seed}.log")
        if rc != 0 and verdict == "PASS":
            verdict = "FAIL"  # 仿真进程异常退出不算通过
        results.append((test, seed, verdict))

    passed = sum(1 for _, _, v in results if v == "PASS")
    lines = [f"PPA-Lite 回归结果  日期={date.today()}  通过={passed}/{len(results)}"]
    lines += [f"{v:6s} {t} SEED={s}" for t, s, v in results]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))
    print(f"\n摘要已写入 {SUMMARY.relative_to(ROOT)}")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
