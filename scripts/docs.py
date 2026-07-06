#!/usr/bin/env python3
# 文档记忆系统的机械层：接手摘要 / 结构守卫 / 滚动归档 / spec 钉住
# 原则：机械交脚本、语义留 Agent。本脚本只做计数、校验、搬运，不生成语义内容。
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "doc"

VERSION_JSON = ROOT / "version.json"
STATUS = DOC / "status.jsonl"
STATUS_ARCHIVE = DOC / "status-archive.jsonl"
LOG = DOC / "log.md"
LOG_ARCHIVE = DOC / "log-archive.md"
TESTPLAN = DOC / "testplan.md"
FEATURE_MATRIX = DOC / "feature-matrix.md"
SPEC = DOC / "spec.md"
SPEC_SHA = DOC / "spec.sha256"
BUGS = DOC / "bugs.md"
DESIGN_PROMPT_README = DOC / "design-prompt" / "README.md"

BUG_STATES = ("OPEN", "FIXING", "FIX_READY", "VERIFYING", "CLOSED",
              "TB_BUG", "SPEC_CHANGED", "WONTFIX")

# 滚动上限：超限时 --check 报错，提示执行 --archive
STATUS_MAX_LINES = 12
STATUS_KEEP = 8
SUMMARY_MAX_CHARS = 200
LOG_MAX_BLOCKS = 4
LOG_KEEP = 3

STATUS_EMOJIS = ("✅", "❌", "⚠️", "🔲")
BLOCK_RE = re.compile(r"^## \[")
SEMVER_RE = re.compile(r"^0\.(\d+)\.(\d+)$")

REQUIRED_FILES = [
    VERSION_JSON, STATUS, STATUS_ARCHIVE, LOG, LOG_ARCHIVE,
    TESTPLAN, FEATURE_MATRIX, SPEC, SPEC_SHA, BUGS, DESIGN_PROMPT_README,
    ROOT / "CLAUDE.md", ROOT / "Makefile",
]


def read_version():
    data = json.loads(VERSION_JSON.read_text(encoding="utf-8"))
    return data["version"], data.get("milestone", "")


def split_log_blocks(text):
    """返回 (头部文本, [块文本列表])，块以 '## [' 开头。"""
    lines = text.splitlines(keepends=True)
    head, blocks, cur = [], [], None
    for line in lines:
        if BLOCK_RE.match(line):
            if cur is not None:
                blocks.append(cur)
            cur = [line]
        elif cur is None:
            head.append(line)
        else:
            cur.append(line)
    if cur is not None:
        blocks.append(cur)
    return "".join(head), ["".join(b) for b in blocks]


ESCAPED_PIPE = "\x00"


def parse_table(path):
    """解析 markdown 表格，返回 [ {列名: 单元格}, ... ]（跳过表头/分隔行，支持 \\| 转义）。"""
    rows, header = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith("|"):
            header = None
            continue
        line = line.replace("\\|", ESCAPED_PIPE)
        cells = [c.strip().replace(ESCAPED_PIPE, "|")
                 for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def status_counts(rows, ms_key="里程碑", st_key="状态"):
    """按里程碑统计各状态数量。"""
    out = {}
    for r in rows:
        ms = r.get(ms_key, "?")
        st = next((e for e in STATUS_EMOJIS if e in r.get(st_key, "")), "?")
        out.setdefault(ms, {e: 0 for e in STATUS_EMOJIS} | {"?": 0})
        out[ms][st] += 1
    return out


def fmt_counts(counts):
    lines = []
    for ms in sorted(counts):
        c = counts[ms]
        total = sum(c.values())
        lines.append(f"  {ms}: ✅{c['✅']}/{total}  ❌{c['❌']} ⚠️{c['⚠️']} 🔲{c['🔲']}")
    return "\n".join(lines)


def cmd_handover():
    version, milestone = read_version()
    first = STATUS.read_text(encoding="utf-8").splitlines()[0]
    st = json.loads(first)
    _, blocks = split_log_blocks(LOG.read_text(encoding="utf-8"))
    tp_rows = parse_table(TESTPLAN)
    fm_rows = parse_table(FEATURE_MATRIX)

    print("== PPA-Lite 接手摘要 ==")
    print(f"版本: {version} ({milestone})")
    print(f"状态[{st['date']}]: {st['summary']}")
    print("\n-- log.md 最新块 --")
    print(blocks[0].rstrip() if blocks else "(空)")
    print("\n-- testplan --")
    print(fmt_counts(status_counts(tp_rows)))
    todo = [r["ID"] for r in tp_rows if "✅" not in r.get("状态", "")]
    print(f"  未完成场景: {', '.join(todo) if todo else '(无)'}")
    print("\n-- feature-matrix --")
    print(fmt_counts(status_counts(fm_rows)))
    open_bugs = [r for r in parse_table(BUGS)
                 if r.get("状态", "") not in ("CLOSED", "TB_BUG", "SPEC_CHANGED", "WONTFIX")]
    print("\n-- bugs --")
    if open_bugs:
        for r in open_bugs:
            print(f"  {r.get('ID', '?')} [{r.get('状态', '?')}] {r.get('现象摘要', '')}")
    else:
        print("  (无未关闭缺陷)")
    print("\n提示: 细节用 grep 定位后精读；归档件与 ✅ 条目默认不读。")


def cmd_check():
    errors, warns = [], []

    for f in REQUIRED_FILES:
        if not f.exists():
            errors.append(f"缺少必需文件: {f.relative_to(ROOT)}")
    if errors:
        return report(errors, warns)

    # version.json
    version, _ = read_version()
    if not SEMVER_RE.match(version):
        errors.append(f"version.json 版本号不符合 0.M.P 格式: {version}")

    # status.jsonl
    lines = [l for l in STATUS.read_text(encoding="utf-8").splitlines() if l.strip()]
    for i, line in enumerate(lines, 1):
        try:
            rec = json.loads(line)
            for key in ("date", "version", "summary"):
                if key not in rec:
                    errors.append(f"status.jsonl 第{i}行缺少字段 {key}")
        except json.JSONDecodeError:
            errors.append(f"status.jsonl 第{i}行不是合法 JSON")
    if lines:
        first = json.loads(lines[0])
        if len(first.get("summary", "")) > SUMMARY_MAX_CHARS:
            errors.append(f"status.jsonl 首行 summary 超过 {SUMMARY_MAX_CHARS} 字符，请精简并把细节放进 log.md")
        if first.get("version") != version:
            errors.append(f"status.jsonl 首行版本 {first.get('version')} ≠ version.json {version}（收尾时先 bump 再写状态）")
    if len(lines) > STATUS_MAX_LINES:
        errors.append(f"status.jsonl 共 {len(lines)} 行 > {STATUS_MAX_LINES}，请执行: make docs-archive")

    # log.md
    _, blocks = split_log_blocks(LOG.read_text(encoding="utf-8"))
    if len(blocks) > LOG_MAX_BLOCKS:
        errors.append(f"log.md 共 {len(blocks)} 块 > {LOG_MAX_BLOCKS}，请执行: make docs-archive")

    # testplan 证据链：✅ 必须有存在的证据文件 + 带 SEED 的复现命令
    for r in parse_table(TESTPLAN):
        rid = r.get("ID", "?")
        st = r.get("状态", "")
        if not any(e in st for e in STATUS_EMOJIS):
            errors.append(f"testplan {rid} 状态位非法: {st!r}")
        if "✅" in st:
            ev = r.get("证据", "").strip("` ")
            if not ev.startswith("doc/evidence/"):
                errors.append(f"testplan {rid} 已置 ✅ 但证据列未指向 doc/evidence/ 路径")
            elif not (ROOT / ev).exists():
                errors.append(f"testplan {rid} 证据文件不存在: {ev}")
            if "SEED" not in r.get("复现", "").upper():
                errors.append(f"testplan {rid} 已置 ✅ 但复现列缺少含 SEED 的命令")

    # feature-matrix 状态位合法性
    for r in parse_table(FEATURE_MATRIX):
        if not any(e in r.get("状态", "") for e in STATUS_EMOJIS):
            errors.append(f"feature-matrix {r.get('编号', '?')} 状态位非法: {r.get('状态')!r}")

    # bugs.md：状态合法 + 关单必须带复验证据
    for r in parse_table(BUGS):
        bid = r.get("ID", "?")
        st = r.get("状态", "").strip()
        if st not in BUG_STATES:
            errors.append(f"bugs.md {bid} 状态非法: {st!r}（合法值: {'/'.join(BUG_STATES)}）")
        if st == "CLOSED":
            ev = r.get("复验证据", "").strip("` ")
            if not ev.startswith("doc/evidence/"):
                errors.append(f"bugs.md {bid} 已 CLOSED 但复验证据未指向 doc/evidence/ 路径")
            elif not (ROOT / ev).exists():
                errors.append(f"bugs.md {bid} 复验证据文件不存在: {ev}")

    # spec.md 变更守卫（修改需登记修改记录并重新 pin）
    actual = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    pinned = SPEC_SHA.read_text(encoding="utf-8").strip()
    if actual != pinned:
        errors.append("doc/spec.md 与钉住的 sha256 不符——修改 spec 必须在其\"修改记录\"表加条目，"
                      "然后执行: python3 scripts/docs.py --pin-spec")

    return report(errors, warns)


def report(errors, warns):
    for w in warns:
        print(f"[warn] {w}")
    if errors:
        for e in errors:
            print(f"[FAIL] {e}")
        print(f"\ndocs-check 未通过：{len(errors)} 个问题")
        return 1
    print("docs-check 通过")
    return 0


def cmd_archive():
    moved = False
    # log.md：保留最新 LOG_KEEP 块，其余移入归档（归档内也是新的在上）
    head, blocks = split_log_blocks(LOG.read_text(encoding="utf-8"))
    if len(blocks) > LOG_KEEP:
        keep, old = blocks[:LOG_KEEP], blocks[LOG_KEEP:]
        LOG.write_text(head + "".join(keep), encoding="utf-8")
        ahead, ablocks = split_log_blocks(LOG_ARCHIVE.read_text(encoding="utf-8"))
        LOG_ARCHIVE.write_text(ahead + "".join(old) + "".join(ablocks), encoding="utf-8")
        print(f"log.md: 归档 {len(old)} 块")
        moved = True
    # status.jsonl：保留最新 STATUS_KEEP 行，其余移入归档
    lines = [l for l in STATUS.read_text(encoding="utf-8").splitlines() if l.strip()]
    if len(lines) > STATUS_KEEP:
        keep, old = lines[:STATUS_KEEP], lines[STATUS_KEEP:]
        STATUS.write_text("\n".join(keep) + "\n", encoding="utf-8")
        alines = [l for l in STATUS_ARCHIVE.read_text(encoding="utf-8").splitlines() if l.strip()]
        STATUS_ARCHIVE.write_text("\n".join(old + alines) + "\n", encoding="utf-8")
        print(f"status.jsonl: 归档 {len(old)} 行")
        moved = True
    if not moved:
        print("无需归档")


def cmd_pin_spec():
    sha = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    SPEC_SHA.write_text(sha + "\n", encoding="utf-8")
    print(f"已钉住 doc/spec.md: {sha}")


def main():
    parser = argparse.ArgumentParser(description="PPA-Lite 文档机械层")
    parser.add_argument("--handover", action="store_true", help="打印接手摘要")
    parser.add_argument("--check", action="store_true", help="文档结构与证据链守卫")
    parser.add_argument("--archive", action="store_true", help="滚动归档 log/status")
    parser.add_argument("--pin-spec", action="store_true", help="重新钉住 spec.md 的 sha256")
    args = parser.parse_args()
    if args.pin_spec:
        cmd_pin_spec()
    if args.archive:
        cmd_archive()
    if args.check:
        sys.exit(cmd_check())
    if args.handover:
        cmd_handover()
    if not any(vars(args).values()):
        parser.print_help()


if __name__ == "__main__":
    main()
