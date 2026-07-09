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
BUGS_ARCHIVE = DOC / "bugs-archive.md"
WAIVERS = DOC / "lint-waivers.md"
WAIVERS_ARCHIVE = DOC / "lint-waivers-archive.md"
DESIGN_PROMPT_README = DOC / "design-prompt" / "README.md"

BUG_STATES = ("OPEN", "FIXING", "FIX_READY", "VERIFYING", "CLOSED",
              "TB_BUG", "SPEC_CHANGED", "WONTFIX")
# 终态 = 生命周期已结束，可归档；活跃缺陷永不归档
BUG_DONE_STATES = ("CLOSED", "TB_BUG", "SPEC_CHANGED", "WONTFIX")

# 滚动上限：超限时 --check 报错，提示执行 --archive
STATUS_MAX_LINES = 12
STATUS_KEEP = 8
SUMMARY_MAX_CHARS = 200
LOG_MAX_BLOCKS = 4
LOG_KEEP = 3
BUG_DONE_MAX = 4      # bugs.md 终态行超此数 --check 报错
BUG_DONE_KEEP = 2     # 归档后保留最新 N 条终态行（活跃行全保留）
WAIVER_DONE_MAX = 6   # lint-waivers.md 已批准豁免行超此数 --check 报错
WAIVER_DONE_KEEP = 2  # 归档后保留最新 N 条已批准行（待复核行全保留）

STATUS_EMOJIS = ("✅", "❌", "⚠️", "🔲")
BLOCK_RE = re.compile(r"^## \[")
# 骨架标记精确匹配（整行/整值），避免正文里提到"TODO"一词就误拦
LOG_TODO_RE = re.compile(r"^- TODO$|TODO（一句话标题）", re.M)
BLOCK_VER_RE = re.compile(r"^## \[(\d+\.\d+\.\d+)\]")
SEMVER_RE = re.compile(r"^0\.(\d+)\.(\d+)$")
# 缺陷单进入这些状态时，修复 commit 列必须已回填
BUG_STATES_NEED_COMMIT = ("FIX_READY", "VERIFYING", "CLOSED")

REQUIRED_FILES = [
    VERSION_JSON, STATUS, STATUS_ARCHIVE, LOG, LOG_ARCHIVE,
    TESTPLAN, FEATURE_MATRIX, SPEC, SPEC_SHA, BUGS, BUGS_ARCHIVE,
    WAIVERS, WAIVERS_ARCHIVE, DESIGN_PROMPT_README,
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


def row_cells(line):
    line = line.replace("\\|", ESCAPED_PIPE)
    return [c.strip().replace(ESCAPED_PIPE, "|")
            for c in line.strip().strip("|").split("|")]


def split_table_lines(text):
    """按行拆出文件中第一张 markdown 表：(表前文本, 表头两行, 数据行列表, 表后文本)。
    数据行保持原始文本不动，供归档搬运用。"""
    head, header, rows, tail = [], [], [], []
    state = 0  # 0=表前 1=表内 2=表后
    for line in text.splitlines(keepends=True):
        in_table = line.strip().startswith("|")
        if state == 0:
            (header if in_table else head).append(line)
            state = 1 if in_table else 0
        elif state == 1:
            if in_table:
                (header if len(header) < 2 else rows).append(line)
            else:
                state = 2
                tail.append(line)
        else:
            tail.append(line)
    return "".join(head), "".join(header), rows, "".join(tail)


def waiver_done(row):
    """lint 豁免行是否已完结：结论=豁免 且 rev 复核列已填（未复核的豁免不算数）。"""
    concl = next((v for k, v in row.items() if k.startswith("结论")), "")
    review = next((v for k, v in row.items() if k.startswith("复核")), "")
    return "豁免" in concl and bool(review.strip("-— "))


def archive_table_rows(src, dst, done_fn, keep, label):
    """把 src 表中已完结的数据行（done_fn 为真）归档到 dst，保留最新 keep 条完结行。
    未完结行永不搬动；dst 内新的在上。返回是否有搬动。"""
    head, header, rows, tail = split_table_lines(src.read_text(encoding="utf-8"))
    if not header:
        return False
    cols = row_cells(header.splitlines()[0])
    done_idx = [i for i, r in enumerate(rows) if done_fn(dict(zip(cols, row_cells(r))))]
    movable = set(done_idx[:-keep] if keep else done_idx)
    if not movable:
        return False
    old = [rows[i] for i in sorted(movable)]
    src.write_text(head + header
                   + "".join(r for i, r in enumerate(rows) if i not in movable)
                   + tail, encoding="utf-8")
    ahead, aheader, arows, atail = split_table_lines(dst.read_text(encoding="utf-8"))
    dst.write_text(ahead + aheader + "".join(old) + "".join(arows) + atail,
                   encoding="utf-8")
    print(f"{label}: 归档 {len(old)} 行")
    return True


def status_counts(rows, ms_key="里程碑", st_key="状态"):
    """按里程碑统计各状态数量。"""
    out = {}
    for r in rows:
        ms = r.get(ms_key, "?")
        st = next((e for e in STATUS_EMOJIS if e in r.get(st_key, "")), "?")
        out.setdefault(ms, {e: 0 for e in STATUS_EMOJIS} | {"?": 0})
        out[ms][st] += 1
    return out


def linked_scenes(row):
    return row.get("关联场景", "").replace(",", " ").split()


def testplan_pass_ids(tp_rows):
    return {r.get("ID", "").strip() for r in tp_rows if "✅" in r.get("状态", "")}


def rtl_delivered(mod):
    """交付状态机械推导：rtl/<模块>.sv 是否存在；非单模块条目（如 "(全系统)"）返回 None。"""
    if not re.fullmatch(r"\w+", mod):
        return None
    return (ROOT / "rtl" / f"{mod}.sv").exists()


def fm_stats(fm_rows, tp_pass):
    """feature-matrix 派生统计：交付由 rtl 文件现算，验证由 testplan 现算——均不落盘。"""
    out = {}
    for r in fm_rows:
        d = out.setdefault(r.get("里程碑", "?"), {"total": 0, "rtl_total": 0, "deliv": 0, "verif": 0})
        d["total"] += 1
        dv = rtl_delivered(r.get("模块", ""))
        if dv is not None:
            d["rtl_total"] += 1
            d["deliv"] += dv
        scenes = linked_scenes(r)
        if scenes and any(s in tp_pass for s in scenes):
            d["verif"] += 1
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
    print("\n-- feature-matrix（交付=rtl 文件现算；验证=testplan 现算；均不落盘）--")
    tp_pass = testplan_pass_ids(tp_rows)
    for ms, d in sorted(fm_stats(fm_rows, tp_pass).items()):
        print(f"  {ms}: RTL 交付{d['deliv']}/{d['rtl_total']}  验证✅{d['verif']}/{d['total']}")
    open_bugs = [r for r in parse_table(BUGS)
                 if r.get("状态", "").strip() not in BUG_DONE_STATES]
    print("\n-- bugs --")
    if open_bugs:
        for r in open_bugs:
            print(f"  {r.get('ID', '?')} [{r.get('状态', '?')}] {r.get('现象摘要', '')}")
    else:
        print("  (无未关闭缺陷)")
    print("\n提示: `make next` 查看机械推导的下一步行动；细节用 grep 定位后精读；归档件与 ✅ 条目默认不读。")


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
        if first.get("summary", "").strip() == "TODO":
            errors.append("status.jsonl 首行 summary 仍是 TODO 骨架——收尾时填写实际总览")
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
        if LOG_TODO_RE.search(blocks[0]):
            errors.append("log.md 首块仍含 TODO 骨架——收尾时补全四问（做了什么/没做什么/下一步/如何验证）")

    # testplan 证据链：✅ 必须有真实证据文件（.log 首行含复现命令）+ 带 SEED 的复现命令
    tp_rows = parse_table(TESTPLAN)
    check_dup_ids(tp_rows, "ID", "testplan", errors)
    for r in tp_rows:
        rid = r.get("ID", "?")
        st = r.get("状态", "")
        if not any(e in st for e in STATUS_EMOJIS):
            errors.append(f"testplan {rid} 状态位非法: {st!r}")
        if "✅" in st:
            check_evidence(r.get("证据", ""), f"testplan {rid}", errors)
            if "SEED" not in r.get("复现", "").upper():
                errors.append(f"testplan {rid} 已置 ✅ 但复现列缺少含 SEED 的命令")

    # feature-matrix：纯 arch 工件（无状态位）；守卫只查引用完整性——
    # 关联场景必填且 ID 必须真实存在于 testplan（交付/验证状态由脚本现算，不落盘）
    fm_rows = parse_table(FEATURE_MATRIX)
    check_dup_ids(fm_rows, "编号", "feature-matrix", errors)
    tp_ids = {r.get("ID", "").strip() for r in tp_rows}
    for r in fm_rows:
        fid = r.get("编号", "?")
        scenes = linked_scenes(r)
        if not scenes:
            errors.append(f"feature-matrix {fid} 关联场景为空（每个功能至少映射 1 个 testplan 场景）")
        for s in scenes:
            if s not in tp_ids:
                errors.append(f"feature-matrix {fid} 关联场景 {s} 在 testplan 中不存在（幽灵引用）")

    # bugs.md：状态合法 + FIX_READY/VERIFYING/CLOSED 须回填修复 commit + 关单必须带复验证据
    bug_rows = parse_table(BUGS)
    abug_rows = parse_table(BUGS_ARCHIVE)
    check_dup_ids(bug_rows + abug_rows, "ID", "bugs.md(+归档)", errors)
    done_bugs = [r for r in bug_rows if r.get("状态", "").strip() in BUG_DONE_STATES]
    if len(done_bugs) > BUG_DONE_MAX:
        errors.append(f"bugs.md 终态缺陷行 {len(done_bugs)} > {BUG_DONE_MAX}，请执行: make docs-archive")
    for r in abug_rows:
        if r.get("状态", "").strip() not in BUG_DONE_STATES:
            errors.append(f"bugs-archive.md {r.get('ID', '?')} 状态 {r.get('状态', '')!r} 非终态"
                          "——活跃缺陷不得归档，请移回 bugs.md")
    for r in bug_rows:
        bid = r.get("ID", "?")
        st = r.get("状态", "").strip()
        if st not in BUG_STATES:
            errors.append(f"bugs.md {bid} 状态非法: {st!r}（合法值: {'/'.join(BUG_STATES)}）")
        if st in BUG_STATES_NEED_COMMIT and not r.get("修复 commit", "").strip("-` "):
            errors.append(f"bugs.md {bid} 状态 {st} 但修复 commit 列未回填")
        if st == "CLOSED":
            check_evidence(r.get("复验证据", ""), f"bugs.md {bid} 复验", errors)

    # 缺陷详情页双向校验：表内引用必须存在；doc/bugs/ 下不得有无表行的孤儿页（含归档表行）
    bugs_text = BUGS.read_text(encoding="utf-8") + BUGS_ARCHIVE.read_text(encoding="utf-8")
    for ref in set(re.findall(r"doc/bugs/([A-Za-z0-9_-]+)\.md", bugs_text)):
        if not (DOC / "bugs" / f"{ref}.md").exists():
            errors.append(f"bugs.md 引用的详情页不存在: doc/bugs/{ref}.md")
    bug_ids = {r.get("ID", "").strip() for r in bug_rows + abug_rows}
    if (DOC / "bugs").is_dir():
        for f in sorted((DOC / "bugs").glob("*.md")):
            if f.stem not in bug_ids:
                errors.append(f"doc/bugs/{f.name} 在 bugs.md(+归档) 中无对应 ID 表行（孤儿详情页）")

    # lint-waivers.md：编号唯一（含归档）+ 已批准豁免超限提示归档 + 归档内不得有未批准行
    wv_rows = parse_table(WAIVERS)
    awv_rows = parse_table(WAIVERS_ARCHIVE)
    check_dup_ids(wv_rows + awv_rows, "#", "lint-waivers.md(+归档)", errors)
    done_wv = [r for r in wv_rows if waiver_done(r)]
    if len(done_wv) > WAIVER_DONE_MAX:
        errors.append(f"lint-waivers.md 已批准豁免行 {len(done_wv)} > {WAIVER_DONE_MAX}，"
                      "请执行: make docs-archive")
    for r in awv_rows:
        if not waiver_done(r):
            errors.append(f"lint-waivers-archive.md #{r.get('#', '?')} 未经 rev 批准"
                          "——待复核豁免不得归档，请移回 lint-waivers.md")

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


def cmd_next():
    """机械推导下一步行动：读三张表与守卫状态，按 §4.3 流转规则输出建议清单。
    只做状态机推导，不做语义判断；语义决策（归属判断、卡内容）仍由 orch 完成。"""
    version, milestone = read_version()
    acts = []  # (优先级, 文本)：0=守卫/收尾欠账 1=缺陷与里程碑 2=开发推进

    # 0) 守卫欠账
    actual = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    if actual != SPEC_SHA.read_text(encoding="utf-8").strip():
        acts.append((0, "spec.md 与钉住 sha 不符 → 补修改记录后 python3 scripts/docs.py --pin-spec"))
    first_line = STATUS.read_text(encoding="utf-8").splitlines()[0]
    if json.loads(first_line).get("summary", "").strip() == "TODO":
        acts.append((0, "status.jsonl 首行为 TODO 骨架 → 完成收尾填写（/closeout）"))
    _, blocks = split_log_blocks(LOG.read_text(encoding="utf-8"))
    if blocks and LOG_TODO_RE.search(blocks[0]):
        acts.append((0, "log.md 首块含 TODO 骨架 → 补全四问"))

    # 1) 缺陷推进（§4.3 缺陷闭环）
    for r in parse_table(BUGS):
        bid, st = r.get("ID", "?"), r.get("状态", "").strip()
        owner = r.get("疑似归属", "")
        if st == "OPEN":
            if "spec" in owner.lower():
                acts.append((1, f"{bid} OPEN（spec 歧义）→ 派 rev 仲裁卡"))
            else:
                acts.append((1, f"{bid} OPEN → orch 判归属派单：疑似 RTL→DE 修复卡 / 疑似 TB→DV 自修"))
        elif st == "FIXING":
            acts.append((1, f"{bid} FIXING → 待 DE 回填根因+修复 commit，置 FIX_READY"))
        elif st == "FIX_READY":
            acts.append((1, f"{bid} FIX_READY → 派 DV 复验卡（登记的 TEST+SEED 复跑；关单人≠修复人）"))
        elif st == "VERIFYING":
            acts.append((1, f"{bid} VERIFYING → DV 复跑后用 evidence.py --bug {bid} 回填关单"))

    # 2) 当前里程碑推进（按模块聚合）
    tp_rows = parse_table(TESTPLAN)
    fm_rows = parse_table(FEATURE_MATRIX)
    tp_pass = testplan_pass_ids(tp_rows)
    cur_tp = [r for r in tp_rows if r.get("里程碑") == milestone]
    cur_fm = [r for r in fm_rows if r.get("里程碑") == milestone]
    for r in cur_tp:
        if "❌" in r.get("状态", ""):
            acts.append((1, f"testplan {r.get('ID')} ❌ → DV 先自查激励/checker，仍疑似 RTL 则登 bugs.md"))
    mods = {}
    for r in cur_fm:
        mods.setdefault(r.get("模块", "?"), []).append(r)
    for mod, rows in mods.items():
        deliv = rtl_delivered(mod)  # None = 非单模块条目（如 "(全系统)"），无交付概念
        dp = DOC / "design-prompt" / f"{mod}.md"
        ids = [r.get("编号", "?") for r in rows]
        unverif = sorted({s for r in rows for s in linked_scenes(r) if s not in tp_pass})
        if deliv is False and not dp.exists():
            acts.append((2, f"{mod} 缺 doc/design-prompt/{mod}.md → 派 arch 卡撰写（rev 门禁后才可派 DE）"))
        elif deliv is False:
            acts.append((2, f"{mod} 的 RTL 未交付（条目 {' '.join(ids)}，design-prompt 就绪）→ 派 DE 卡"))
        elif unverif:
            who = "派 DV 场景卡" if deliv else "orch 按条目性质派单（回归/覆盖率类多为 DV）"
            acts.append((2, f"{mod} 场景 {' '.join(unverif)} 未 ✅ → {who}"))

    # 3) 里程碑完成判据（CLAUDE.md §4.1 三条硬条件；交付由 rtl 文件现算）
    if cur_fm and cur_tp and \
       all(rtl_delivered(r.get("模块", "")) is not False for r in cur_fm) and \
       all("✅" in r.get("状态", "") for r in cur_tp):
        mnum = milestone.lstrip("M")
        ev_dirs = list(DOC.glob(f"evidence/v0.{mnum}.*"))
        missing = []
        if not any((d / "result_summary.txt").exists() for d in ev_dirs):
            missing.append("regress 证据（result_summary.txt 复制入 evidence）")
        if not any(d.glob(f"review-M{mnum}*.md") for d in ev_dirs):
            missing.append(f"rev 里程碑签核（review-M{mnum}.md）")
        if missing:
            acts.append((1, f"{milestone} 条目全 ✅，还差：{'；'.join(missing)}"))
        else:
            acts.append((1, f"{milestone} 三条硬条件已齐 → make bump-minor + git tag v0.{int(mnum)+1}.0 进入下一 M"))

    print(f"== 下一步建议（{version} / {milestone}，机械推导，语义决策仍在 orch）==")
    if not acts:
        print("(无建议——若里程碑范围有变，先由 arch 更新 feature-matrix/testplan)")
    for i, (_, text) in enumerate(sorted(acts, key=lambda a: a[0]), 1):
        print(f"{i}. {text}")


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
    # bugs.md：终态行（CLOSED/TB_BUG/SPEC_CHANGED/WONTFIX）超出保留数即归档，活跃行不动
    moved |= archive_table_rows(
        BUGS, BUGS_ARCHIVE,
        lambda r: r.get("状态", "").strip() in BUG_DONE_STATES,
        BUG_DONE_KEEP, "bugs.md")
    # lint-waivers.md：已批准豁免行超出保留数即归档，待复核行不动
    moved |= archive_table_rows(WAIVERS, WAIVERS_ARCHIVE,
                                waiver_done, WAIVER_DONE_KEEP, "lint-waivers.md")
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
    parser.add_argument("--next", action="store_true", help="机械推导下一步行动清单")
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
    if args.next:
        cmd_next()
    if not any(vars(args).values()):
        parser.print_help()


if __name__ == "__main__":
    main()
