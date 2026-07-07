#!/usr/bin/env python3
# 证据机械生成：从仿真 log 抽取摘录写入 doc/evidence/，并回填 testplan/bugs 状态。
# 目的：证据文件不再由 agent 手写（防抄录错误与幻觉手笔）；agent 只做一个语义决策——
# 这次 run 对应哪个场景 ID / BUG-ID。防伪锚点仍是"仿真在本地真实跑过"。
#
# 用法（本地 VM，仿真跑完后执行）：
#   python3 scripts/evidence.py --scen M1-01 --test ppa_smoke_test --seed 42
#   python3 scripts/evidence.py --bug BUG-003 --test ppa_err_test --seed 7   # 复验关单
#   可选 --log <路径> 覆盖默认的 sim/out/<TEST>_<SEED>.log
import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "doc"
TESTPLAN = DOC / "testplan.md"
BUGS = DOC / "bugs.md"

UVM_CNT_RE = re.compile(r"UVM_(ERROR|FATAL)\s*:?\s+(\d+)")
SUMMARY_MARK = "UVM Report Summary"
KEY_LINE_RE = re.compile(r"(?i)\b(pass|match|compare ok|check ok)\b")
KEY_LINES_MAX = 30
ESC = "\x00"


def read_version():
    return json.loads((ROOT / "version.json").read_text(encoding="utf-8"))["version"]


def extract(log_path, scen_id):
    """机械抽取：UVM Report Summary 段 + 关键 PASS/比对行 + 含场景ID 的行。"""
    text = log_path.read_text(encoding="utf-8", errors="replace")
    counts = {k: int(v) for k, v in UVM_CNT_RE.findall(text)}
    if not counts:
        sys.exit(f"log 中找不到 UVM report summary，无法判定结果: {log_path}")
    if counts.get("ERROR", 0) or counts.get("FATAL", 0):
        sys.exit(f"log 判定 FAIL（UVM_ERROR={counts.get('ERROR', 0)} "
                 f"UVM_FATAL={counts.get('FATAL', 0)}）——FAIL 不登证据，去 bugs.md 登缺陷")
    lines = text.splitlines()
    idx = next((i for i, l in enumerate(lines) if SUMMARY_MARK in l), None)
    summary = lines[max(0, idx - 1):idx + 14] if idx is not None else []
    keys = [l for l in lines if KEY_LINE_RE.search(l) or scen_id in l]
    return summary, keys[:KEY_LINES_MAX]


def update_row(path, id_val, updates):
    """按首列 ID 定位 markdown 表格行，更新指定列（支持 \\| 转义）。"""
    out, header, found = [], None, False
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s.startswith("|"):
            header = None
            out.append(line)
            continue
        cells = [c.strip().replace(ESC, "|")
                 for c in s.replace("\\|", ESC).strip("|").split("|")]
        if header is None:
            header = cells
        elif not all(set(c) <= set("-: ") for c in cells) and cells[0] == id_val and not found:
            found = True
            row = dict(zip(header, cells))
            row.update(updates)
            out.append("| " + " | ".join(row.get(h, "").replace("|", "\\|") for h in header) + " |")
            continue
        out.append(line)
    if not found:
        sys.exit(f"{path.name} 中未找到 ID 为 {id_val} 的表行")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="证据机械生成与状态回填")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scen", help="testplan 场景 ID（置 ✅）")
    g.add_argument("--bug", help="bugs.md 缺陷 ID（复验关单置 CLOSED）")
    ap.add_argument("--test", required=True, help="UVM 测试名")
    ap.add_argument("--seed", required=True, help="仿真种子")
    ap.add_argument("--log", help="仿真 log 路径（默认 sim/out/<TEST>_<SEED>.log）")
    args = ap.parse_args()

    rid = args.scen or args.bug
    log_path = Path(args.log) if args.log else ROOT / "sim" / "out" / f"{args.test}_{args.seed}.log"
    if not log_path.exists():
        sys.exit(f"仿真 log 不存在: {log_path}（没有 log 就没有证据）")

    summary, keys = extract(log_path, rid)
    cmd = f"make run TEST={args.test} SEED={args.seed}"
    ev_dir = DOC / "evidence" / f"v{read_version()}"
    ev_dir.mkdir(parents=True, exist_ok=True)
    ev_path = ev_dir / f"{rid}.log"
    body = [cmd,
            f"# 由 scripts/evidence.py 于 {date.today()} 机械生成，源 log: {log_path.relative_to(ROOT)}",
            "", "## UVM Report Summary", *summary, "", "## 关键检查行", *keys, ""]
    ev_path.write_text("\n".join(body), encoding="utf-8")
    rel = str(ev_path.relative_to(ROOT))
    print(f"证据已生成: {rel}")

    if args.scen:
        update_row(TESTPLAN, args.scen, {"状态": "✅", "证据": rel, "复现": f"`{cmd}`"})
        print(f"testplan {args.scen} 已回填（✅/证据/复现）")
    else:
        update_row(BUGS, args.bug, {"状态": "CLOSED", "复验证据": rel})
        print(f"bugs.md {args.bug} 已回填（CLOSED/复验证据）——注意关单人≠修复人")

    rc = subprocess.run([sys.executable, str(ROOT / "scripts" / "docs.py"), "--check"]).returncode
    sys.exit(rc)


if __name__ == "__main__":
    main()
