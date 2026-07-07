#!/usr/bin/env python3
# 文档记忆系统的机械层：接手摘要 / 结构守卫 / 滚动归档 / spec 钉住
# 原则：机械交脚本、语义留 Agent。本脚本只做计数、校验、搬运，不生成语义内容。
import argparse
import hashlib
import json
import re
import signal
import subprocess
import sys
from pathlib import Path

# 输出常被管到 head/grep（token 纪律），恢复默认 SIGPIPE 行为避免 BrokenPipeError
if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

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
BLOCK_VER_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]")
SEMVER_RE = re.compile(r"^0\.(\d+)\.(\d+)$")
# 缺陷单进入这些状态时，修复 commit 列必须已回填
BUG_STATES_NEED_COMMIT = ("FIX_READY", "VERIFYING", "CLOSED")

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


def check_evidence(cell, owner, errors):
    """证据单元格三重校验：路径前缀、文件存在、.log 首行含复现命令（TEST+SEED）。"""
    ev = cell.strip("` ")
    if not ev.startswith("doc/evidence/"):
        errors.append(f"{owner} 证据未指向 doc/evidence/ 路径")
        return
    p = ROOT / ev
    if not p.exists():
        errors.append(f"{owner} 证据文件不存在: {ev}")
        return
    if ev.endswith(".log"):
        first = next((l for l in p.read_text(encoding="utf-8", errors="replace").splitlines()
                      if l.strip()), "")
        up = first.upper()
        if "TEST" not in up or "SEED" not in up:
            errors.append(f"{owner} 证据文件首行不是复现命令（须含 TEST 与 SEED）: {ev}")


def check_dup_ids(rows, key, name, errors):
    seen = set()
    for r in rows:
        rid = r.get(key, "").strip()
        if rid and rid in seen:
            errors.append(f"{name} 存在重复 {key}: {rid}")
        seen.add(rid)


def count_mod_records(text):
    """统计 spec '## 修改记录' 表的数据行数；无该表返回 None。"""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if l.strip().startswith("## 修改记录")), None)
    if start is None:
        return None
    n, seen_header = 0, False
    for l in lines[start + 1:]:
        s = l.strip()
        if s.startswith("#"):
            break
        if not s.startswith("|"):
            continue
        if not seen_header:
            seen_header = True
            continue
        if set(s.replace("|", "").strip()) <= set("-: "):
            continue
        n += 1
    return n


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
    todo = [r.get("ID", "?") for r in tp_rows if "✅" not in r.get("状态", "")]
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

    # log.md：块数上限 + 首块版本与 version.json 同步（堵"bump 了不写交接块"）
    _, blocks = split_log_blocks(LOG.read_text(encoding="utf-8"))
    if len(blocks) > LOG_MAX_BLOCKS:
        errors.append(f"log.md 共 {len(blocks)} 块 > {LOG_MAX_BLOCKS}，请执行: make docs-archive")
    if blocks:
        m = BLOCK_VER_RE.match(blocks[0])
        if not m:
            errors.append("log.md 首块块头格式非法（应为 '## [版本] 日期 标题'）")
        elif m.group(1) != version:
            errors.append(f"log.md 首块版本 {m.group(1)} ≠ version.json {version}"
                          "（收尾时 bump 后需在 log.md 顶部加新块）")

    # testplan 证据链：✅ 必须有真实证据文件（.log 首行含复现命令）+ 带 SEED 的复现命令
    tp_rows = parse_table(TESTPLAN)
    check_dup_ids(tp_rows, "ID", "testplan", errors)
    tp_pass = {r.get("ID", "").strip() for r in tp_rows if "✅" in r.get("状态", "")}
    for r in tp_rows:
        rid = r.get("ID", "?")
        st = r.get("状态", "")
        if not any(e in st for e in STATUS_EMOJIS):
            errors.append(f"testplan {rid} 状态位非法: {st!r}")
        if "✅" in st:
            check_evidence(r.get("证据", ""), f"testplan {rid}", errors)
            if "SEED" not in r.get("复现", "").upper():
                errors.append(f"testplan {rid} 已置 ✅ 但复现列缺少含 SEED 的命令")

    # feature-matrix：状态位合法 + ✅ 联动（口径：至少 1 条关联场景已在 testplan ✅）
    fm_rows = parse_table(FEATURE_MATRIX)
    check_dup_ids(fm_rows, "编号", "feature-matrix", errors)
    for r in fm_rows:
        fid = r.get("编号", "?")
        if not any(e in r.get("状态", "") for e in STATUS_EMOJIS):
            errors.append(f"feature-matrix {fid} 状态位非法: {r.get('状态')!r}")
        if "✅" in r.get("状态", ""):
            scenes = r.get("关联场景", "").replace(",", " ").split()
            if not scenes:
                errors.append(f"feature-matrix {fid} 已置 ✅ 但关联场景为空")
            elif not any(s in tp_pass for s in scenes):
                errors.append(f"feature-matrix {fid} 已置 ✅ 但关联场景（{' '.join(scenes)}）"
                              "无一在 testplan 置 ✅")

    # bugs.md：状态合法 + FIX_READY/VERIFYING/CLOSED 须回填修复 commit + 关单必须带复验证据
    bug_rows = parse_table(BUGS)
    check_dup_ids(bug_rows, "ID", "bugs.md", errors)
    for r in bug_rows:
        bid = r.get("ID", "?")
        st = r.get("状态", "").strip()
        if st not in BUG_STATES:
            errors.append(f"bugs.md {bid} 状态非法: {st!r}（合法值: {'/'.join(BUG_STATES)}）")
        if st in BUG_STATES_NEED_COMMIT and not r.get("修复 commit", "").strip("-` "):
            errors.append(f"bugs.md {bid} 状态 {st} 但修复 commit 列未回填")
        if st == "CLOSED":
            check_evidence(r.get("复验证据", ""), f"bugs.md {bid} 复验", errors)

    # 缺陷详情页双向校验：表内引用必须存在；doc/bugs/ 下不得有无表行的孤儿页
    bugs_text = BUGS.read_text(encoding="utf-8")
    for ref in set(re.findall(r"doc/bugs/([A-Za-z0-9_-]+)\.md", bugs_text)):
        if not (DOC / "bugs" / f"{ref}.md").exists():
            errors.append(f"bugs.md 引用的详情页不存在: doc/bugs/{ref}.md")
    bug_ids = {r.get("ID", "").strip() for r in bug_rows}
    if (DOC / "bugs").is_dir():
        for f in sorted((DOC / "bugs").glob("*.md")):
            if f.stem not in bug_ids:
                errors.append(f"doc/bugs/{f.name} 在 bugs.md 中无对应 ID 表行（孤儿详情页）")

    # spec.md 变更守卫（修改需登记修改记录并重新 pin）
    spec_text = SPEC.read_text(encoding="utf-8")
    actual = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    pinned = SPEC_SHA.read_text(encoding="utf-8").strip()
    if actual != pinned:
        errors.append("doc/spec.md 与钉住的 sha256 不符——修改 spec 必须在其\"修改记录\"表加条目，"
                      "然后执行: python3 scripts/docs.py --pin-spec")
    if count_mod_records(spec_text) is None:
        errors.append("doc/spec.md 缺少 '## 修改记录' 表（spec 守卫依赖该表）")

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
    # 防悄改：spec 相对 git HEAD 有实质改动时，"修改记录"表必须新增条目才允许重新钉住
    cur = SPEC.read_text(encoding="utf-8")
    head = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD:doc/spec.md"],
                          capture_output=True, text=True)
    if head.returncode == 0 and head.stdout != cur:
        old_n, new_n = count_mod_records(head.stdout), count_mod_records(cur)
        if old_n is not None and new_n is not None and new_n <= old_n:
            sys.exit("拒绝钉住: doc/spec.md 相对 HEAD 有改动，但\"修改记录\"表未新增条目——"
                     "先补修改记录，再执行 --pin-spec")
    elif head.returncode != 0:
        print("[warn] 无法读取 git HEAD 的 spec.md，跳过修改记录增量校验")
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
