#!/usr/bin/env python3
# 一键回归：读取回归列表，逐条调用 make run，解析 UVM log，生成 sim/result_summary.txt
# 列表格式（sim/regress/regress.list）：每行 "<TEST> <SEED>"，# 开头为注释
#
# 判定两条腿（BUG-014 后，BUG-017 加固）：
#   ① UVM report summary 的 UVM_ERROR/UVM_FATAL 均为 0；
#   ② SVA 断言零失败 + 未被静默关断（scripts/svacheck.py：引擎失败行[含 :: 类作用域] +
#      原生汇总逐条 + 断言总数/尝试数基线，任一命中即失败）。
# 任一不满足即 FAIL。断言失败**不计入 UVM_ERROR**，故必须独立判定，不能混为一谈。
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import svacheck  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SIM = ROOT / "sim"
DEFAULT_LIST = SIM / "regress" / "regress.list"
SUMMARY = SIM / "result_summary.txt"

UVM_ERR_RE = re.compile(r"UVM_(ERROR|FATAL)\s*:?\s+(\d+)")


def parse_log(log_path):
    """返回 (verdict, reason)。verdict ∈ {PASS,FAIL,NOLOG,NOSUMMARY}。

    首列 token 保持在既有集合内，新增的失败原因走 reason 后缀——这样
    scripts/report.py 对 result_summary.txt 的逐行统计（^PASS/^FAIL...）不受影响，
    同时又能把"断言失败"和"UVM_ERROR"两类原因如实分开呈现。
    """
    if not log_path.exists():
        return "NOLOG", ""
    text = log_path.read_text(encoding="utf-8", errors="replace")

    # —— 腿 ①：UVM report summary ——
    counts = {kind: int(num) for kind, num in UVM_ERR_RE.findall(text)}
    if not counts:
        return "NOSUMMARY", ""

    # —— 腿 ②：SVA 断言 ——
    sva = svacheck.scan_text(text)

    reasons = []
    if counts.get("ERROR", 0) or counts.get("FATAL", 0):
        reasons.append(f"UVM_ERROR={counts.get('ERROR', 0)} UVM_FATAL={counts.get('FATAL', 0)}")
    if sva.failed:
        reasons.append(sva.reason())
    elif not sva.has_native_summary:
        # 本流程的 make run 固定带 -assert verbose（见 sim/Makefile），必然有原生汇总行。
        # 缺失说明仿真选项被绕过/工具行为变了 —— 失效即失败（fail-closed），不放行。
        reasons.append("缺 VCS 断言汇总行（-assert verbose 未生效？）")
    if reasons:
        return "FAIL", "; ".join(reasons)
    return "PASS", ""


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

    # 先清理再回归：VCS 对 out/ 下 .daidir/csrc 等构建产物做增量复用判断，跨会话残留
    # （尤其与 make lint 等不同选项集的产物混存同一 out/ 目录）会导致构建数据库损坏，
    # 产生假失败（如 constraint.sdb 报 VFS_SDB_ERROR，见 BUG-007）。回归证据的可信度
    # 要求每次从干净状态起跑，不依赖调用者记得先手动 make clean。
    subprocess.run(["make", "-C", str(SIM), "clean"], check=True)

    results = []
    for test, seed in entries:
        print(f"== 回归: {test} SEED={seed} ==", flush=True)
        rc = subprocess.run(
            ["make", "-C", str(SIM), "run", f"TEST={test}", f"SEED={seed}", f"COV={cov}"],
        ).returncode
        log_path = SIM / "out" / f"{test}_{seed}.log"
        verdict, reason = parse_log(log_path)
        if rc != 0 and verdict == "PASS":
            verdict, reason = "FAIL", "仿真进程异常退出"  # 退出码非 0 不算通过
        if verdict != "PASS":
            print(f"   -> {verdict} {reason}", flush=True)
            for line in svacheck.scan_file(log_path).detail_lines() if log_path.exists() else []:
                print(line, flush=True)
        results.append((test, seed, verdict, reason))

    passed = sum(1 for _, _, v, _ in results if v == "PASS")
    n_sva = sum(1 for _, _, _, r in results if "SVA失败" in r)
    head = f"PPA-Lite 回归结果  日期={date.today()}  通过={passed}/{len(results)}"
    if n_sva:
        head += f"  （其中 {n_sva} 条因 SVA 断言失败）"
    lines = [head]
    lines += [f"{v:6s} {t} SEED={s}" + (f"  [{r}]" if r else "") for t, s, v, r in results]
    SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n" + "\n".join(lines))
    print(f"\n摘要已写入 {SUMMARY.relative_to(ROOT)}")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
