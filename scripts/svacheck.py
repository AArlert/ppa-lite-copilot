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

## 判定机制（双层互证，任一层命中即判失败）

层 1 —— **VCS SVA 引擎失败行**（对任何 log 都有效，含历史归档 log，无需任何编译/运行选项）::

    "../rtl/packet_proc_core.sv", 326: tb_top.u_packet_proc_core.a_format_ok_consistency: started at 85000ps failed at 85000ps

  该行由断言引擎打印，**与动作块无关**（`$error` / `$fatal` / 无动作块都会打），
  比抓 `Error:` 行更完整，是主锚点。

层 2 —— **VCS 原生结构化计数**（需仿真带 `-assert verbose`，已固化进 sim/Makefile 的 SIM_OPTS）::

    Summary: 91 assertions, 88 with attempts, 2 with failures

  第三个数 >0 即失败。这是工具自己的计数，不依赖任何消息文本，作为层 1 的独立互证。

层 1b —— 动作块严重性行（`Error:` / `Fatal:` 形态），用于 log 被裁剪、只保留严重性行的场合::

    Error: "../tb/sva/packet_proc_core_sva.sv", 56: tb_top...a_format_ok_def: at time 85000 ps

## 为什么不会误伤

三条正则全部锚定**结构**（`"文件", 行号: 层次名:` + 固定短语），不做任何 "error" 词形匹配。
本项目遍地的信号名 `length_error_o` / `chk_error_o` / `type_error_o`（127 处）、状态名
`ERROR_STATE`、UVM 汇总行 `UVM_ERROR :    0`、VCS 编译诊断 `Error-[XXX]` 均不匹配。
`-assert verbose` 会打印的正常尾巴 `... started at 215000ps not finished`（仿真结束时
未完成的尝试）也不匹配——层 1 强制要求 `failed at`。
"""
import re
import sys
from pathlib import Path

# 层 1：SVA 引擎失败行。hier 用 [^\s:]+ —— 层次名不含空格与冒号。
FAIL_LINE_RE = re.compile(
    r'^"(?P<file>[^"]+)",\s*(?P<line>\d+):\s*(?P<hier>[^\s:]+):\s*'
    r'started at \S+\s+failed at (?P<time>\S+)\s*\r?$', re.M)

# 层 1b：动作块严重性行（$error/$fatal 经断言动作块打印时的形态）
SEVERITY_LINE_RE = re.compile(
    r'^(?P<sev>Error|Fatal):\s*"(?P<file>[^"]+)",\s*(?P<line>\d+):\s*(?P<hier>[^\s:]+):\s*'
    r'at time (?P<time>\d[\d.]*\s*\w+)', re.M)

# 层 2：VCS 原生断言汇总计数（-assert verbose）
SUMMARY_RE = re.compile(
    r'^Summary:\s*(?P<total>\d+)\s+assertions?,\s*(?P<attempted>\d+)\s+with attempts,\s*'
    r'(?P<failed>\d+)\s+with failures', re.M)


class SvaResult:
    """一份 log 的断言判定结果。"""

    def __init__(self, failures, severities, summary):
        self.failures = failures      # [{file,line,name,hier,time}] 层 1 命中
        self.severities = severities  # [{sev,file,line,name,hier,time}] 层 1b 命中
        self.summary = summary        # {total,attempted,failed} 或 None（层 2）

    @property
    def has_native_summary(self):
        return self.summary is not None

    @property
    def failed(self):
        """任一层命中即判失败。"""
        return bool(self.failures) or bool(self.severities) or \
            (self.summary is not None and self.summary["failed"] > 0)

    @property
    def n_assert_failed(self):
        """失败的**断言条数**（去重后的断言全路径数），层 2 优先。"""
        if self.summary is not None and self.summary["failed"] > 0:
            return self.summary["failed"]
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
        return f"SVA失败: {self.n_assert_failed} 条断言/{self.n_hits} 次"

    def detail_lines(self, limit=20):
        """逐条明细：断言名 + 源文件:行 + 失败时刻。"""
        out = []
        for f in self.failures[:limit]:
            out.append(f"  {f['name']}  {f['file']}:{f['line']}  @{f['time']}  ({f['hier']})")
        if len(self.failures) > limit:
            out.append(f"  ...（另有 {len(self.failures) - limit} 次，见原始 log）")
        if not self.failures:  # 只命中层 1b/层 2 的场合
            for s in self.severities[:limit]:
                out.append(f"  {s['name']}  {s['file']}:{s['line']}  @{s['time']}  [{s['sev']}]")
            if self.summary and self.summary["failed"] and not self.severities:
                out.append(f"  VCS 原生汇总: {self.summary['failed']} 条断言有失败"
                           f"（共 {self.summary['total']} 条，{self.summary['attempted']} 条被触发）")
        return out


def _name_of(hier):
    """层次路径末段 = 断言名。"""
    return hier.rsplit(".", 1)[-1]


def scan_text(text):
    """扫描 log 文本，返回 SvaResult。"""
    failures = [{"file": m["file"], "line": m["line"], "hier": m["hier"],
                 "name": _name_of(m["hier"]), "time": m["time"]}
                for m in FAIL_LINE_RE.finditer(text)]
    severities = [{"sev": m["sev"], "file": m["file"], "line": m["line"], "hier": m["hier"],
                   "name": _name_of(m["hier"]), "time": m["time"].strip()}
                  for m in SEVERITY_LINE_RE.finditer(text)]
    summary = None
    for m in SUMMARY_RE.finditer(text):  # 多次命中取最后一条（同 log 多次运行时以末次为准）
        summary = {"total": int(m["total"]), "attempted": int(m["attempted"]),
                   "failed": int(m["failed"])}
    return SvaResult(failures, severities, summary)


def scan_file(path):
    p = Path(path)
    return scan_text(p.read_text(encoding="utf-8", errors="replace"))


def main():
    """CLI：批量回扫 log。`python3 scripts/svacheck.py <log>...`

    退出码 0 = 全部干净；1 = 至少一份 log 检出断言失败。
    """
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    quiet = "-q" in sys.argv[1:]
    if not args:
        sys.exit("用法: svacheck.py [-q] <log> [<log>...]")
    n_bad = 0
    for a in args:
        p = Path(a)
        if not p.exists():
            print(f"MISSING   {a}")
            continue
        r = scan_file(p)
        if r.failed:
            n_bad += 1
            print(f"SVA_FAIL  {a}  {r.reason()}")
            for line in r.detail_lines():
                print(line)
        elif not quiet:
            tag = "" if r.has_native_summary else "  [无原生汇总行: 该 log 未带 -assert verbose]"
            print(f"CLEAN     {a}{tag}")
    print(f"\n回扫 {len(args)} 份 log，检出断言失败 {n_bad} 份")
    sys.exit(1 if n_bad else 0)


if __name__ == "__main__":
    main()
