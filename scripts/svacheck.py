#!/usr/bin/env python3
"""SVA 断言失败检测（BUG-014）——regress.py / evidence.py 共用的单一判定点。

## 为什么需要它

全仓 49 条断言（rtl/ 32 + tb/sva/ 17）的动作块一律是 `else $error(...)`。`$error` 是
SystemVerilog 系统任务，**不经 UVM report server、不计入 UVM_ERROR**，VCS 默认也不因此
改 simv 退出码。实测（受控破坏 tb/sva/packet_proc_core_sva.sv:56 与
rtl/packet_proc_core.sv:326 各一条断言后跑 ppa_m2_04_test SEED=1）：

    log 内 26 次断言失败，UVM report summary 仍是 `UVM_ERROR : 0` / `UVM_FATAL : 0`，
    simv 退出码 0，make 退出码 0。

故"UVM_ERROR==0 && UVM_FATAL==0 即 PASS"会把**断言失败整类**放过。本模块补上这一层。

## 判定机制（多路互证，任一路命中即判失败）

层 1 —— **VCS SVA 引擎失败行**（`started at … failed at …`）::

    "../rtl/packet_proc_core.sv", 326: tb_top.u_packet_proc_core.a_format_ok: started at 85000ps failed at 85000ps
    "../tb/sva/packet_proc_core_sva.sv", 45: tb_top...a_done_hold: started at 155000ps failed at 165000ps  Offending 'done_o'

  该行由断言引擎打印，**与动作块无关**（`$error` / `$fatal` / 无动作块都会打）。
  层次名段（hier）允许 `::` 与转义标识符里的空格，因此**并发断言的类作用域实例**
  （层次名形如 `p::\chk::check .unnamed$$_0`）也能被锚住——BUG-017 R2 前的 `[^\\s:]+`
  对这类结构性失明，仅靠层 2 兜底，本轮已修。
  尾部允许同行尾随任意文本（如 VCS 真实产出的 `  Offending '<sig>'`）——BUG-017 前的
  `\s*\r?$` 尾锚只放行纯空白/CR，对上面第二条真实形态（BUG-014 登记的 a_done_hold 失败
  行）结构性失明，BUG-018 R2 已放宽为 `(?:\s.*)?$`；`.` 不跨行，尾随文本再长也只吃到本行
  末尾，不会侵入下一行、不会把两条失败行拼成一条误判。

层 2 —— **VCS 原生结构化计数**（需仿真带 `-assert verbose`，已固化进 sim/Makefile 的 SIM_OPTS）::

    Summary: 91 assertions, 88 with attempts, 0 with failures

  三个数依次为：断言实例总数 / 被触发（有 attempt）的条数 / 有失败的条数。
  一份 log 可能出现多条 Summary（拼接 / 多次运行）——**逐条检查、任一条 failures>0 即失败**
  （BUG-017 R3 前取末条，会被"先失败后干净"的拼接 log 骗过）；出现多于一条本身可疑，
  另发 warn。这是工具自己的计数，不依赖任何消息文本，与层 1 互证。

层 1b —— 动作块严重性行（`Error:` / `Fatal:` 形态），用于 log 被裁剪、只保留严重性行的场合::

    Error: "../tb/sva/packet_proc_core_sva.sv", 56: tb_top...a_format_ok_def: at time 85000 ps

  hier 段同层 1 放宽，可锚 `::` 类作用域；但**只在动作块真的调用了 `$error`/`$fatal` 时才会
  存在这一行**——无动作块的断言不打印 `Error:`/`Fatal:` 前缀行，层 1b 对这一类结构性失明
  （不是 bug，是这层的设计范围：它锚的是"动作块打印的严重性行"，不是"断言引擎本身"）。

层 3 —— **断言总数 / 尝试数基线**（BUG-017 R1，sim/regress/sva_baseline.json，默认开启）::

  只看第三个数（failures）会漏掉一整类"真违例但 failures=0"的绕过：
    · `$assertoff(0, tb_top)` → `91 assertions, 0 with attempts, 0 with failures`（total 不变、attempted 掉到 0）；
    · 把 `tb/sva/*.sv` 从 flist 摘掉  → total 从 91 掉下来、failures 仍 0。
  信息就在同一行里却被忽略。层 3 用已登记基线（当前 91/88，floor 语义）兜住：
  total<total_min 或 attempted<attempted_min 即失败。基线只能人工登记维护，脚本永不
  自适应（见基线文件说明）。回扫**旧里程碑** build 的历史 log 时用 `--no-baseline` 关闭本层。
  基线文件自身的 floor 值变更留痕由 `scripts/report.py --check`（第 8 项）机械校验——
  见 sim/regress/sva_baseline.json 说明字段与 report.py 中 check_sva_baseline() 的注释
  （BUG-018 R1）；svacheck.py 本体不做这层校验，只信任传入 / 加载到的基线数值。

## 覆盖矩阵（哪层兜哪类、哪类只有单层兜底——BUG-018 二轮收窄）

**本表是本文件对覆盖范围的唯一权威自述；不再作"全覆盖/fail-closed，对任何 log 都有效"这类
总括声明**（BUG-017 R2 订正过一次"立即断言不成立"，BUG-018 是同类过宽表述第二次在细分形态
上冒头——这次不再补一句订正了事，而是把已知形态逐条列表，新形态发现后只准在表里加行，
不准回到总括式措辞）：

| 断言形态 × 呈现条件 | 层1（started/failed，本行） | 层1b（Error:/Fatal:，动作块） | 层2（Summary，需 -assert verbose） | 层3（floor，需基线） | 唯一兜底 |
| --- | --- | --- | --- | --- | --- |
| 并发断言，带 `$error`/`$fatal`，引擎行无尾随文本 | 命中 | 命中 | 命中 | — | 层1（结构化，不依赖编译选项/动作块） |
| 并发断言，带 `$error`/`$fatal`，引擎行带同行尾巴（如 `Offending '<sig>'`） | 命中（BUG-018 R2 起） | 命中 | 命中 | — | BUG-018 前仅层1b/层2；R2 后层1 亦命中 |
| 并发断言，**无**动作块 | 命中 | **不命中**（无 Error:/Fatal: 行可打） | 命中（需 verbose） | — | 层1（唯一不依赖编译选项的路径） |
| 并发断言，类作用域 hier 含 `::` | 命中（BUG-017 R2 起） | 命中（BUG-017 R2 起） | 命中 | — | 层1 |
| 立即断言 `assert(expr)`，带 `$error`/`$fatal` | **不命中**（不产生 started/failed 行） | 命中 | 命中（需 verbose） | — | 层1b，或依赖 verbose 的层2 |
| 立即断言，**无**动作块 | 不命中 | 不命中 | 命中（**仅当**带 `-assert verbose`） | — | **唯一层2**，硬依赖 `-assert verbose` 这一编译选项 |
| 断言被 `$assertoff` 关断（attempted 掉数，failures 仍 0） | 不命中（未触发不产生 failed 行） | 不命中 | 不命中（failed=0，看不出异常） | 命中（attempted<基线） | **唯一层3** |
| 断言被摘出 flist（total 掉数） | 不命中 | 不命中 | 不命中 | 命中（total<基线） | **唯一层3** |
| 拼接/多次运行 log，先失败后干净 | 命中（失败那一段） | 命中（同上） | 命中（逐条检查取并集，非取末条，BUG-017 R3） | — | 层1/1b/2 均可，任一足够 |

结论：**只有"并发断言 + 有 `$error`/`$fatal` 动作块"这一类同时被三层独立覆盖**；"并发断言无
动作块"只靠层1；"立即断言"整体只靠层1b/层2，其中无动作块的立即断言**唯一**依赖 `-assert
verbose`（regress.py / evidence.py 已把"缺 Summary 行即 FAIL"设为硬条件，使这条依赖显式化，
不是隐藏假设）；"断言被摘除/关断"整体**唯一**依赖层3 基线，而基线本身是人工维护的数值，其
变更留痕由 report.py --check 校验（不在本文件职责内）。**尾锚放宽只解决"同一条真实失败行的
文本变体识别"，不改变上述按断言形态划分的覆盖边界**——本表覆盖的是"已知会出现的行形态"，
VCS 未来版本若换一种全新的失败行措辞，仍需要新增语料并在此表补行，不构成对本表的证伪。

## 为什么不会误伤

层 1/1b/层 2 三条正则全部锚定**结构**（`"文件", 行号: 层次名:` + 固定短语 / `^Summary:`），
不做任何 "error" 词形匹配。本项目遍地的信号名 `length_error_o` / `chk_error_o` /
`type_error_o`、状态名、UVM 汇总行 `UVM_ERROR : 0`、VCS 编译诊断 `Error-[XXX]` 均不匹配；
`… started at 215000ps not finished`（仿真结束未完成的尝试）也不匹配——层 1 强制要求 `failed at`。
层 1/1b 的 `^"` / `^Error:` 行首锚使被前缀顶开的**引用形态**（`UVM_INFO …历史记录: "x", 9: …failed at…`）
不被误判——BUG-018 放宽的尾锚只影响 `failed at` **之后**的文本，不影响这个行首锚，引用形态仍
不在行首、仍不匹配（重放语料见 doc/evidence/v0.5.5/review-bug-015-016-017.md §A2-a 与
doc/evidence/v0.5.3/review-bug-013-014.md §A2-a，本轮改动后已重放确认无回归）。
层 3 基线是数值下限，只对 `^Summary:` 行首的原生计数生效，文档引用形态（`# … Summary: …`）不计入。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE_PATH = ROOT / "sim" / "regress" / "sva_baseline.json"

# 层 1：SVA 引擎失败行。hier 段用非贪婪 .+? —— 允许 `::` 与转义标识符里的空格
# （类作用域实例形如 `p::\chk::check .unnamed$$_0`）。尾部 `: started at … failed at …`
# 是强锚点，非贪婪只会停在真正紧邻 `started at` 的那个冒号处，不会越界（BUG-017 R2）。
# 尾锚 `(?:\s.*)?$` 放行同行任意尾随文本（BUG-018 R2）——VCS 真实产出常带
# `  Offending '<sig>'` 尾巴（BUG-014 登记的 a_done_hold 失败行即此形态），旧尾锚
# `\s*\r?$` 只放行纯空白/CR 对它结构性失明。`.` 不跨行（无 re.S），尾随文本再长也只吃到
# 本行末尾，不会侵入下一行、不会把两条独立失败行拼接误判为一条。
FAIL_LINE_RE = re.compile(
    r'^"(?P<file>[^"]+)",\s*(?P<line>\d+):\s*(?P<hier>.+?):\s*'
    r'started at \S+\s+failed at (?P<time>\S+)(?:\s.*)?$', re.M)

# 层 1b：动作块严重性行（$error/$fatal 经断言动作块打印时的形态），hier 同层 1 放宽。
SEVERITY_LINE_RE = re.compile(
    r'^(?P<sev>Error|Fatal):\s*"(?P<file>[^"]+)",\s*(?P<line>\d+):\s*(?P<hier>.+?):\s*'
    r'at time (?P<time>\d[\d.]*\s*\w+)', re.M)

# 层 2：VCS 原生断言汇总计数（-assert verbose）
SUMMARY_RE = re.compile(
    r'^Summary:\s*(?P<total>\d+)\s+assertions?,\s*(?P<attempted>\d+)\s+with attempts,\s*'
    r'(?P<failed>\d+)\s+with failures', re.M)

_BASELINE_SENTINEL = object()   # scan_text 的 baseline 默认值：表示"加载默认基线文件"
_baseline_cache = _BASELINE_SENTINEL


def load_baseline(path=None):
    """加载 SVA 基线（total_min / attempted_min）。

    缺失 / 损坏 / 字段非法一律 **fail-closed**：直接退出并提示。默认口径拒绝在无基线下
    判定——删掉基线文件不能成为绕过手段。回扫旧 build 的历史 log 走 `--no-baseline`（不经此函数）。
    """
    p = Path(path) if path else DEFAULT_BASELINE_PATH
    if not p.exists():
        sys.exit(f"SVA 基线文件缺失: {p} —— 拒绝在无基线下判定（fail-closed，BUG-017 R1）。"
                 f"回扫旧里程碑 build 的历史 log 请用 svacheck.py --no-baseline。")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        total_min = int(data["total_min"])
        attempted_min = int(data["attempted_min"])
    except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
        sys.exit(f"SVA 基线文件损坏/字段非法: {p}（{e}）—— fail-closed，拒绝判定。")
    return {"total_min": total_min, "attempted_min": attempted_min}


def get_baseline():
    """带缓存的默认基线加载（scan_text 每 log 调用一次，避免反复读盘）。"""
    global _baseline_cache
    if _baseline_cache is _BASELINE_SENTINEL:
        _baseline_cache = load_baseline()
    return _baseline_cache


class SvaResult:
    """一份 log 的断言判定结果。"""

    def __init__(self, failures, severities, summaries, baseline):
        self.failures = failures      # [{file,line,name,hier,time}] 层 1 命中
        self.severities = severities  # [{sev,...}] 层 1b 命中
        self.summaries = summaries    # [{total,attempted,failed}] 层 2 全部命中（不止末条）
        self.baseline = baseline      # {total_min,attempted_min} 或 None（--no-baseline）

    @property
    def has_native_summary(self):
        return bool(self.summaries)

    @property
    def multi_summary(self):
        """出现多于一条 Summary —— 拼接 / 多次运行的 log，本身可疑（BUG-017 R3）。"""
        return len(self.summaries) > 1

    @property
    def summary_failed(self):
        """任一条 Summary 的 failures>0（不取末条，BUG-017 R3）。"""
        return any(s["failed"] > 0 for s in self.summaries)

    @property
    def baseline_violations(self):
        """逐条 Summary 与基线比对，返回违例列表（total/attempted 掉数）。BUG-017 R1。"""
        if self.baseline is None:
            return []
        out = []
        for s in self.summaries:
            why = []
            if s["total"] < self.baseline["total_min"]:
                why.append(f"断言总数 {s['total']}<{self.baseline['total_min']}")
            if s["attempted"] < self.baseline["attempted_min"]:
                why.append(f"尝试数 {s['attempted']}<{self.baseline['attempted_min']}")
            if why:
                out.append({**s, "why": "，".join(why)})
        return out

    @property
    def failed(self):
        """任一路命中即判失败（层 1 / 1b / 层 2 / 层 3 基线）。"""
        return bool(self.failures) or bool(self.severities) or \
            self.summary_failed or bool(self.baseline_violations)

    @property
    def n_assert_failed(self):
        """失败的**断言条数**，层 2 优先（多条 Summary 取失败最多的一条）。"""
        if self.summary_failed:
            return max((s["failed"] for s in self.summaries), default=0)
        return len({f["hier"] for f in self.failures} |
                   {s["hier"] for s in self.severities})

    @property
    def n_hits(self):
        """失败**次数**（同一断言多拍失败计多次）。"""
        return max(len(self.failures), len(self.severities))

    def reason(self):
        """一行式失败原因，用于 result_summary.txt / 证据拒登提示。"""
        if not self.failed:
            return ""
        parts = []
        if self.failures or self.severities or self.summary_failed:
            parts.append(f"SVA失败: {self.n_assert_failed} 条断言/{self.n_hits} 次")
        if self.baseline_violations:
            parts.append("SVA基线不符: " +
                         "；".join(v["why"] for v in self.baseline_violations) +
                         "（断言被摘出编译或 $assertoff 关断）")
        if self.multi_summary and not (self.failures or self.severities):
            parts.append(f"另: 检出 {len(self.summaries)} 条 Summary（拼接/多次运行，可疑）")
        return "；".join(parts)

    def detail_lines(self, limit=20):
        """逐条明细：断言名 + 源文件:行 + 失败时刻 / 基线违例。"""
        out = []
        for f in self.failures[:limit]:
            out.append(f"  {f['name']}  {f['file']}:{f['line']}  @{f['time']}  ({f['hier']})")
        if len(self.failures) > limit:
            out.append(f"  ...（另有 {len(self.failures) - limit} 次，见原始 log）")
        if not self.failures:  # 只命中层 1b/层 2 的场合
            for s in self.severities[:limit]:
                out.append(f"  {s['name']}  {s['file']}:{s['line']}  @{s['time']}  [{s['sev']}]")
            if self.summary_failed and not self.severities:
                worst = max(self.summaries, key=lambda s: s["failed"])
                out.append(f"  VCS 原生汇总: {worst['failed']} 条断言有失败"
                           f"（共 {worst['total']} 条，{worst['attempted']} 条被触发）")
        for v in self.baseline_violations:
            out.append(f"  [基线] Summary: {v['total']}/{v['attempted']}/{v['failed']} —— {v['why']}")
        return out


def _name_of(hier):
    """层次路径末段 = 断言名。"""
    return hier.rsplit(".", 1)[-1]


def scan_text(text, baseline=_BASELINE_SENTINEL):
    """扫描 log 文本，返回 SvaResult。

    baseline 三态：
      · 缺省（哨兵）→ 加载默认基线文件（sim/regress/sva_baseline.json），供 regress.py /
        evidence.py 的当前 build 判定使用（fail-closed，文件缺失即退出）；
      · None        → 不做基线校验（CLI `--no-baseline`，用于回扫旧里程碑 build 的历史 log）；
      · dict        → 直接用给定基线（测试用）。
    """
    if baseline is _BASELINE_SENTINEL:
        baseline = get_baseline()
    failures = [{"file": m["file"], "line": m["line"], "hier": m["hier"],
                 "name": _name_of(m["hier"]), "time": m["time"]}
                for m in FAIL_LINE_RE.finditer(text)]
    severities = [{"sev": m["sev"], "file": m["file"], "line": m["line"], "hier": m["hier"],
                   "name": _name_of(m["hier"]), "time": m["time"].strip()}
                  for m in SEVERITY_LINE_RE.finditer(text)]
    # 收集**全部** Summary 行（不止末条，BUG-017 R3）
    summaries = [{"total": int(m["total"]), "attempted": int(m["attempted"]),
                  "failed": int(m["failed"])} for m in SUMMARY_RE.finditer(text)]
    return SvaResult(failures, severities, summaries, baseline)


def scan_file(path, baseline=_BASELINE_SENTINEL):
    p = Path(path)
    return scan_text(p.read_text(encoding="utf-8", errors="replace"), baseline=baseline)


def main():
    """CLI：批量回扫 log。`python3 scripts/svacheck.py [-q] [--no-baseline] <log>...`

    退出码 0 = 全部干净；1 = 至少一份 log 检出断言失败 / 基线违例。
    `--no-baseline` 关闭层 3 基线校验（回扫旧里程碑 build 的历史 log 用，其 total/attempted
    天然低于当前基线）。
    """
    ap = argparse.ArgumentParser(description="SVA 断言失败/基线回扫（BUG-014 / BUG-017）")
    ap.add_argument("logs", nargs="+", help="待扫描的 log 路径")
    ap.add_argument("-q", "--quiet", action="store_true", help="只打印失败项")
    ap.add_argument("--no-baseline", action="store_true",
                    help="关闭断言总数/尝试数基线校验（回扫旧 build 历史 log 用）")
    args = ap.parse_args()

    bl = None if args.no_baseline else _BASELINE_SENTINEL
    if not args.no_baseline:
        b = get_baseline()
        if not args.quiet:
            print(f"# 基线: total_min={b['total_min']} attempted_min={b['attempted_min']} "
                  f"（{DEFAULT_BASELINE_PATH.relative_to(ROOT)}）")

    n_bad = 0
    for a in args.logs:
        p = Path(a)
        if not p.exists():
            print(f"MISSING   {a}")
            continue
        r = scan_file(p, baseline=bl)
        if r.failed:
            n_bad += 1
            print(f"SVA_FAIL  {a}  {r.reason()}")
            for line in r.detail_lines():
                print(line)
        elif not args.quiet:
            notes = []
            if not r.has_native_summary:
                notes.append("无原生汇总行: 该 log 未带 -assert verbose")
            if r.multi_summary:
                notes.append(f"{len(r.summaries)} 条 Summary")
            tag = f"  [{'; '.join(notes)}]" if notes else ""
            print(f"CLEAN     {a}{tag}")
    print(f"\n回扫 {len(args.logs)} 份 log，检出断言失败/基线违例 {n_bad} 份")
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
