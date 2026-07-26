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

  该行由断言引擎打印，**与动作块无关**（`$error` / `$fatal` / 无动作块都会打）。
  层次名段（hier）允许 `::` 与转义标识符里的空格，因此**并发断言的类作用域实例**
  （层次名形如 `p::\chk::check .unnamed$$_0`）也能被锚住——BUG-017 R2 前的 `[^\\s:]+`
  对这类结构性失明，仅靠层 2 兜底，本轮已修。

层 2 —— **VCS 原生结构化计数**（需仿真带 `-assert verbose`，已固化进 sim/Makefile 的 SIM_OPTS）::

    Summary: 91 assertions, 88 with attempts, 0 with failures

  三个数依次为：断言实例总数 / 被触发（有 attempt）的条数 / 有失败的条数。
  一份 log 可能出现多条 Summary（拼接 / 多次运行）——**逐条检查、任一条 failures>0 即失败**
  （BUG-017 R3 前取末条，会被"先失败后干净"的拼接 log 骗过）；出现多于一条本身可疑，
  另发 warn。这是工具自己的计数，不依赖任何消息文本，与层 1 互证。

层 1b —— 动作块严重性行（`Error:` / `Fatal:` 形态），用于 log 被裁剪、只保留严重性行的场合::

    Error: "../tb/sva/packet_proc_core_sva.sv", 56: tb_top...a_format_ok_def: at time 85000 ps

  hier 段同层 1 放宽，可锚 `::` 类作用域。

层 3 —— **断言总数 / 尝试数基线**（BUG-017 R1，sim/regress/sva_baseline.json，默认开启）::

  只看第三个数（failures）会漏掉一整类"真违例但 failures=0"的绕过：
    · `$assertoff(0, tb_top)` → `91 assertions, 0 with attempts, 0 with failures`（total 不变、attempted 掉到 0）；
    · 把 `tb/sva/*.sv` 从 flist 摘掉  → total 从 91 掉下来、failures 仍 0。
  信息就在同一行里却被忽略。层 3 用已登记基线（当前 91/88，floor 语义）兜住：
  total<total_min 或 attempted<attempted_min 即失败。基线只能人工登记维护，脚本永不
  自适应（见基线文件说明）。回扫**旧里程碑** build 的历史 log 时用 `--no-baseline` 关闭本层。

## 层 1 的 fail-closed 到底覆盖到哪（订正 BUG-017 R2 的过宽自述）

BUG-017 前本文件头称"层 1 …不依赖任何编译选项、fail-closed，对任何 log 都有效"。**这句对
立即断言不成立**，如实订正：

- 层 1 的 `started at … failed at …` 是**并发（时序）断言**的引擎行。修好 `::` 正则后，
  并发断言的模块作用域与类作用域实例都能被层 1 锚住，**这部分**确实不依赖任何编译选项。
- **立即断言**（`assert(expr)`，如 UVM-1.2 库里的 `assert($cast(...))`、DV 未来写在 UVM
  组件里的 `assert(...)`）**不产生** `started at/failed at` 引擎行。它的失败只经由：
  层 1b（当且仅当动作块是 `$error`/`$fatal`）、或层 2 的原生汇总计数（依赖 `-assert verbose`）。
  故对立即断言这一类，"不依赖编译选项的 fail-closed" **不成立**——兜底落在层 2，需 `-assert verbose`。
  regress.py / evidence.py 已把"缺汇总行即 FAIL"设为硬条件（fail-closed），使这条依赖显式化。

## 为什么不会误伤

层 1/1b/层 2 三条正则全部锚定**结构**（`"文件", 行号: 层次名:` + 固定短语 / `^Summary:`），
不做任何 "error" 词形匹配。本项目遍地的信号名 `length_error_o` / `chk_error_o` /
`type_error_o`、状态名、UVM 汇总行 `UVM_ERROR : 0`、VCS 编译诊断 `Error-[XXX]` 均不匹配；
`… started at 215000ps not finished`（仿真结束未完成的尝试）也不匹配——层 1 强制要求 `failed at`。
层 1/1b 的 `^"` / `^Error:` 行首锚使被前缀顶开的**引用形态**（`UVM_INFO …历史记录: "x", 9: …failed at…`）
不被误判。层 3 基线是数值下限，只对 `^Summary:` 行首的原生计数生效，文档引用形态（`# … Summary: …`）不计入。
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BASELINE_PATH = ROOT / "sim" / "regress" / "sva_baseline.json"

# 层 1：SVA 引擎失败行。hier 段用非贪婪 .+? —— 允许 `::` 与转义标识符里的空格
# （类作用域实例形如 `p::\chk::check .unnamed$$_0`）。尾部 `: started at … failed at …$`
# 是强锚点，非贪婪只会停在真正紧邻 `started at` 的那个冒号处，不会越界（BUG-017 R2）。
FAIL_LINE_RE = re.compile(
    r'^"(?P<file>[^"]+)",\s*(?P<line>\d+):\s*(?P<hier>.+?):\s*'
    r'started at \S+\s+failed at (?P<time>\S+)\s*\r?$', re.M)

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
