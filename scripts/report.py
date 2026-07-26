#!/usr/bin/env python3
# PPA-Lite 成果数据机械抽取层：展示材料（doc/report.html / README.md / doc/presentation/）
# 的每一个数字都由本脚本从真值源现算并注入生成区，禁止手写数字入库。
#
# 关于"不落盘现算"与"历史趋势"的矛盾——这个矛盾不存在：
#   历史覆盖率/回归数字本来就已经落盘在 doc/evidence/ 里（里程碑收尾时按 /evidence 规矩归档的
#   一等公民证据），本脚本只是现算地把它们读出来。项目忌讳的"落盘"是指派生状态被抄写成第二份
#   可漂移的真相——趋势数据不属于此类。因此 --json 默认不落盘；唯一允许进仓库的派生产物是
#   HTML/README 的 GEN 生成区（它们本就是要提交的展示件），而 --check 保证它们不漂移。
#   真正的风险不是落盘，是异构格式导致的静默解析错，对策 = 锚点表 + 严格失败 + 漏点守卫。
#
# 第一纪律：任何解析不到就 sys.exit(1) 报错，绝不静默猜测、绝不给默认值。
#           展示材料宁可造不出来，也不能印一个来路不明的数字。
#
# scripts/docs.py 一行不改（pre-commit + CI 硬门禁，BUG-011 前车之鉴），本脚本只 import 复用其解析器。
#
# 用法：
#   python3 scripts/report.py --json [--pretty] [--out PATH]
#   python3 scripts/report.py --summary
#   python3 scripts/report.py --md {kpi|milestones|honesty|evidence-index|data-baseline}
#   python3 scripts/report.py --inject FILE [FILE ...]
#   python3 scripts/report.py --check
import argparse
import hashlib
import json
import re
import signal
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
# 复用 docs.py 的解析器与路径常量（import 无副作用，只注册 SIGPIPE）
from docs import (ROOT, DOC, SPEC, SPEC_SHA, TESTPLAN, FEATURE_MATRIX, BUGS,
                  BUGS_ARCHIVE, WAIVERS, WAIVERS_ARCHIVE, parse_table, row_cells,
                  read_version, status_counts, count_mod_records)

if hasattr(signal, "SIGPIPE"):
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

RTL = ROOT / "rtl"
TB = ROOT / "tb"
SVA_DIR = TB / "sva"
EVIDENCE = DOC / "evidence"
REGRESS_LIST = ROOT / "sim" / "regress" / "regress.list"

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print(f"[warn] {msg}", file=sys.stderr)


def fail(msg):
    print(f"[FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# 内置解析规则常量（**不是数字**：这些是"去哪读、怎么读"的规则；数字一律来自被读文件）
# ---------------------------------------------------------------------------

# 覆盖率摘录锚点表：9 个 evidence 目录只有 4 个含覆盖率摘录，且三种互不兼容的表结构，
# 只能逐版本登记解析锚点。新增里程碑后必须补锚点，否则 --check 的漏点守卫会 FAIL。
COV_ANCHORS = {
    "v0.1.7": dict(file="coverage-summary-M1.md",
                   section=r"^#{2,3}\s*六类结果（复测）",     # 取最终态那张表，非首测表
                   value_col=r"百分比",
                   domain="M1 模块聚合域 (mod5+mod7)",        # 口径与后三点不同，必须外显
                   comparable=False,
                   allow_missing=("score",),
                   note="复测值（同文件另有首测表，不取）；FSM 结构性 N/A；该版本无 SCORE 行；"
                        "域为 M1 两个 RTL 模块聚合，非 tb_top，不可与后三点同轴比较"),
    "v0.2.3": dict(file="coverage-summary.md",
                   section=r"^#{2,3}\s*2\..*设计\+验证环境域",
                   value_col=r"数值", domain="tb_top", comparable=True,
                   allow_missing=(), note=""),
    "v0.3.0": dict(file="coverage-summary.md",
                   section=r"^#{2,3}\s*2\..*设计\+验证环境域",
                   value_col=r"数值", domain="tb_top", comparable=True,
                   allow_missing=(),
                   note="较 v0.2.3 下降（M3 集成路径引入新的未激励代码），非回归劣化"),
    "v0.4.0": dict(file="coverage-summary.md",
                   section=r"^#{2,3}\s*1\..*设计\+验证环境域",
                   value_col=r"闭环", domain="tb_top", comparable=True,
                   allow_missing=(),
                   note="该表同时含基线(v0.3.0)与闭环(v0.4.0)两列，取闭环列"),
}
METRIC_ALIAS = {"LINE": "line", "COND": "cond", "TOGGLE": "toggle", "TGL": "toggle",
                "FSM": "fsm", "BRANCH": "branch", "ASSERT": "assert", "SCORE": "score"}
METRIC_ORDER = ["line", "cond", "toggle", "fsm", "branch", "assert", "score"]
# 六类判据（spec §0 适配 7），score 是综合值不属于六类
SIX_METRICS = ["line", "cond", "toggle", "fsm", "branch", "assert"]
COV_THRESHOLD = 90.0

# 缺陷归属分类：只在"归属列括号前的抬头"上做有序匹配。
# 括号内是解释性文字，常含否定式对照（"infra（…，非 spec 歧义）"、
# "infra（lint 门禁登记遗漏，非 RTL/spec 缺陷）"），拿整格去匹配会被否定式带偏——
# BUG-012 落盘时实测把 infra 误判成 rtl，故改为抬头匹配。
# 这一项归错会直接印错材料上的"spec N / infra N / rtl N / tb N"，属"取错数就印错"，保留严格失败。
# 分类集与 CLAUDE.md §4.3 的疑似归属口径一致（RTL / TB / spec 歧义 / infra），其中 TB 侧
# 对应状态集里的 TB_BUG。BUG-016 落盘时抬头写 TB 而规则只认三类，当场打挂 report-check，
# 属"分类集不完整"而非"分类规则被绕过"，故补全而不是放宽为兜底。
BUG_KIND_RULES = [("rtl", "RTL"), ("tb", "TB"), ("infra", "infra"), ("spec", "spec")]

# rev 审查记录分类：按标题关键字**有序**匹配（文件名早期无统一规范，标题比文件名可靠）。
# 与 BUG_KIND_RULES 不同，这是**开放**分类：项目会持续产生新类型的 rev 记录，归不了类
# 只影响分组呈现、不会印错任何数字，故兜底 other + warn，**绝不 fail()**——
# 否则"写一份新的 rev 审查记录"本身就成了打挂 CI 的动作（review-report-tool.md F10 实测踩过）。
REVIEW_KIND_RULES = [("milestone", "里程碑"), ("gate", "门禁"), ("arbitration", "仲裁"), ("closure", "复验"), ("closure", "关单"),
                     ("waiver", "豁免"), ("tool", "工具"), ("tool", "脚本"),
                     ("tool", "抽取"), ("report", "报告"), ("coverage", "覆盖率")]
REVIEW_KIND_FALLBACK = "other"

# 里程碑 ↔ spec Lab 映射（CLAUDE.md §4.1：M1=Lab1 … M4=Lab4）
MILESTONE_LABS = {"M1": "Lab1", "M2": "Lab2", "M3": "Lab3", "M4": "Lab4"}

# ---------------------------------------------------------------------------
# 源码注释守卫（--check 第 7 项）的规则常量 —— 由来 BUG-013
# ---------------------------------------------------------------------------
# docs.py --check 只守 doc/ 下的文档一致性，**源码注释与交付状态的失步完全没有守卫**，
# 这层腐烂一路带到 0.5.0 收官：tb/ 内 4 处「M3 尚未交付」与 rtl/packet_proc_core.sv
# 已于 0.2.2 交付的事实相反；ppa_scoreboard.sv 的 TODO(M1,DV)/TODO(M3,DV) 描述的比对
# 早已以另一种架构落地却从未被撤销。本项守的不是"注释好不好看"，是**对外陈述的可证伪性**：
# 材料一旦宣称"M1–M4 全部完成"，一次 `git grep 尚未交付` 就能当场推翻它。
#
# 严格失败 vs warn（照 review-report-tool.md F10 的判据自评）：F10 裁定"严格失败该用在
# 取错数会印错材料的地方，不该用在给审查记录贴标签这种装饰性分组上"。本项属**前者**——
# 命中意味着仓库自述与材料结论直接矛盾，不是排版偏好。为避免重演 F10 的失败模式
# （"写一句合法注释成了打挂 CI 的动作"），严格失败被限制在**极窄且可机械判定**的形态上，
# 并配了一个显式逃生口：
#   ① 触发条件必须是"未完成标记"与"具体里程碑编号"**绑定出现**（见 STALE_MARKER_PATTERNS），
#      无期限的开放式留白（`// TODO: …` / `// 占位以便将来加仲裁`）一律不触发，只计数；
#   ② 指向"当前及以后里程碑"的承诺是在途承诺，合法，只计数；
#   ③ 确有必要保留历史措辞时，在同一条注释里写上 STALE_SUPPRESS_TOKEN，降级为 warn 并
#      登记进 --json 的 suppressed 列表供 rev 复核（对齐 lint-waivers 的"登记+复核"文化）。
#
# ★ 召回边界（BUG-017 R6，如实写明；**不扩召回**——精度优先是本守卫已被 rev 认可的刻意取舍）：
#   本守卫**精度优先、召回很窄**，只抓"BUG-013 那几种字面形态"的过期承诺。rev 关单时
#   （doc/evidence/v0.5.3/review-bug-013-014.md §B③(3)）构造的 7 条**真过期承诺全部逃逸**：
#     N01 用模块名不用 M<N> 编号（`packet_proc_core 尚未交付…`）——不含里程碑绑定，无感；
#     N02 句号切断 _NEAR 窗口（`M3 是包处理核。尚未交付…`）；
#     N03 动词不在 _UNDONE_V（`… 尚未补齐`，只认「待补齐」不认「尚未补齐」）；
#     N04 M<N> 与标记间隔 >24 字符（括号里塞了文件路径）；
#     N05 英文措辞（`TODO: M3 not yet implemented`，只计开放式留白，不判过期）；
#     N06 跨两行折行（逐行扫描，不跨行）；
#     N07 「待定」不在词表（`M3 待定，等 Lab2 再说`）。
#   其中 N04/N06 距原始缺陷文本仅一步之遥（原文若多写个路径或换一次行，这道为它而写的
#   守卫就抓不到它）。此外 `sim/flist/rtl.f` 那类过期措辞不是"未完成标记"形态，**天然在
#   射程外**（BUG-013 那处靠人工查出）。
#   → 结论必须显式化：**「report-check 通过」只等于「不存在上述几种字面形态的过期承诺」，
#     绝不等于「仓库里没有过期承诺」。** 对外材料不得把前者表述为后者。
#     扩大召回会重演 F10 的失败模式（合法注释成了打挂 CI 的动作），故本轮**只订正边界表述、
#     不动规则**；真要堵某条逃逸形态，走"登记新缺陷 + 针对性加规则 + 重新自评误报"的正式路径。
STALE_SUPPRESS_TOKEN = "report-check:allow-stale-milestone"

SRC_SCAN_DIRS = ["rtl", "tb", "sim"]
# EDA 产物目录（见 .gitignore）不是本仓库源码，一律跳过
SRC_SCAN_SKIP_DIRS = {"csrc", "out", "urgReport", "verdiLog", "nWaveLog", "DVEfiles",
                      "__pycache__"}
# 注释风格：(行注释起始符, 是否有 /* */ 块注释)
SRC_COMMENT_STYLES = {
    ".sv": (("//",), True), ".svh": (("//",), True), ".v": (("//",), True),
    ".f": (("//", "#"), False),          # VCS filelist：本仓库用 //，# 一并认
    ".list": (("#",), False), ".mk": (("#",), False), ".cfg": (("#",), False),
}
SRC_BASENAME_STYLES = {"Makefile": (("#",), False)}

# 里程碑编号的取值边界：`(?<![A-Za-z0-9_])(?:M|Lab)(\d+)`，且**排除场景 ID 形态**
# `M1-06`/`M4-02b`（后随 -数字）——场景 ID 遍布 tb/，把它当里程碑引用会大面积误伤。
_MS = r"(?<![A-Za-z0-9_])(?:M|Lab)(\d+)(?!\s*-\s*\d)"
# "绑定"的量化定义：同一句内（不跨 。；分句）、间隔 ≤24 个字符。24 这个数是实测定的：
# BUG-013 原文「M3（packet_proc_core）本轮尚未交付」中两者间隔 20 字符，窗口 16 会漏。
_NEAR = r"[^。；;\n]{0,24}?"
_UNDONE_V = r"(?:交付|实现|完成|接入|支持|落地)"
_UNDONE_A = r"(?:尚未|暂未|还未|仍未|未)"

# 每条规则都要求「未完成标记」与「里程碑编号」绑定出现——不是"注释里同时出现 TODO 和 M3"
# 就算数（那会把 `// M1-06：PKT_MEM APB 读回占位行为` 这类正常注释全部误伤）。
STALE_MARKER_PATTERNS = [
    (rf"\b(?:TODO|FIXME|XXX|TBD)\s*[（(]\s*(?:M|Lab)(\d+)",
     "TODO(M<N>, …) —— 挂在具体里程碑上的待办承诺"),
    (rf"{_MS}{_NEAR}{_UNDONE_A}{_UNDONE_V}", "「M<N> … 尚未交付/未实现」"),
    (rf"{_UNDONE_A}{_UNDONE_V}{_NEAR}{_MS}", "「尚未交付 … M<N>」倒装"),
    (rf"{_MS}{_NEAR}(?:待(?:交付|实现|补齐|完成)|骨架阶段)", "「M<N> … 待补齐/骨架阶段」"),
    (rf"(?:待(?:交付|实现|补齐|完成)|骨架阶段){_NEAR}{_MS}", "「待补齐 … M<N>」倒装"),
    (rf"{_MS}{_NEAR}(?:由后续|留待后续|后续){_NEAR}{_UNDONE_V}", "「M<N> … 由后续交付」"),
    # 「M<N> 起…补齐」是排期式承诺：`起` 把动作明确挂到某个里程碑上，语义无歧义。
    # 刻意**不**收录裸的「补齐」——「按 BUG-012 补齐 M3 通路的豁免登记」这类陈述句
    # 会被裸词误伤，而带 `起` 的形态只出现在排期语境里。
    (rf"{_MS}\s*起{_NEAR}(?:补齐|补上|补充|实现|交付|完成)", "「M<N> 起 … 补齐」排期式承诺"),
]
# 无里程碑绑定的开放式留白：只统计、不判失败（apb_sequencer.sv 的"占位以便将来加仲裁"
# 连这一类都不算——它没有任何待办关键字，本守卫对它完全无感）
OPEN_MARKER_RE = re.compile(r"\b(?:TODO|FIXME|XXX|TBD)\b")

# 图表几何常量（R3 的 HTML 定稿后如需微调只改这里，不改生成逻辑）
CHART_GEOM = {
    "coverage": dict(w=680, h=280, pad_l=56, pad_r=28, pad_t=24, pad_b=48,
                     y_min=60.0, y_max=100.0),
    "regress": dict(w=680, h=240, pad_l=56, pad_r=28, pad_t=24, pad_b=48, bar_w=54),
    "pyramid": dict(w=520, h=280, pad_t=16, x_center=260, w_max=440, gap=10),
    "bugs": dict(w=440, h=190, pad_l=96, pad_r=44, pad_t=18, bar_h=30, gap=14),
    "arch": dict(w=680, h=300),
}
# 验证金字塔层次（层名是语义约定，层的数值全部来自现算字段）
PYRAMID_LAYERS = [
    ("SVA 断言（DE 内部 + DV 接口/协议）", "verification.sva.total"),
    ("回归条目 TEST×SEED", "verification.regress.entries"),
    ("testplan 场景", "verification.testplan.rows"),
    ("UVM 场景测试类", "verification.tests.scenario"),
]
# 架构图标签落点（框由 arch 画，本脚本只填标签文本与坐标）
ARCH_LABEL_POS = {
    "ppa_top": (340, 42), "apb_slave_if": (110, 168),
    "packet_sram": (340, 168), "packet_proc_core": (570, 168),
}

# report.py 认识的生成区 key（区外一切由 arch 手写，本脚本不得越界）
GEN_KEYS_HTML = ["kpi-row", "chart-arch-labels", "chart-pyramid", "chart-coverage",
                 "chart-regress", "chart-bugs", "table-modules", "table-testplan",
                 "table-evidence", "footer-stamp", "data-json"]
GEN_KEYS_MD = ["readme-kpi", "readme-milestones"]
GEN_KEYS = GEN_KEYS_HTML + GEN_KEYS_MD

# 生成区禁止内嵌"运行期易变量"（git HEAD / 提交总数 / 今日日期）。理由（rev 审查 F1）：
# 生成区内容一旦提交进仓库，下一次提交就会让 HEAD 变化 → --check 判生成区过期 → CI 硬门禁
# 长红 → 逼出 --no-verify 文化，比不加门禁更糟。对策分两层：
#   (b) 主：生成内容里根本不放这些字段（footer-stamp 改用版本+spec sha+真值源内容摘要；
#          data-json 嵌入前剔除 VOLATILE_JSON_PATHS 子树）——生成区只依赖仓库内容，不依赖
#          git 与挂钟，任何人任何时刻在任何克隆深度下重算都得到同一串字节；
#   (a) 兜底：新鲜度比对前用 VOLATILE_TEXT_PATTERNS 归一化两侧文本，万一 arch 在生成区里
#          写了日期/sha（或将来新增生成器泄漏），也不会误判过期。
VOLATILE_JSON_PATHS = [
    "meta.generated_on",     # date.today()，隔天重跑即变
    "meta.warnings",         # 随环境变化（如 git 不可用会多一条）
    "process",               # 整个子树都是 git 派生：head/commits/tags/date_range/bug_fix_dates
]
# milestones[].tag / tag_date 同样是 git 派生（浅克隆取不到会变 null），逐条剔除
VOLATILE_MILESTONE_KEYS = ["tag", "tag_date"]
# 兜底归一化只认 git 短 sha（7–8 位小写十六进制）。刻意**不**归一化日期与 12 位以上的
# sha：修完 (b) 之后生成内容里剩下的日期/摘要全部是内容派生的稳定值，归一化它们只会
# 削弱过期检测。且该归一化仅在"原文已不一致"时才作为第二判据启用，并一律 warn 外显。
VOLATILE_TEXT_PATTERNS = [(r"\b[0-9a-f]{7,8}\b", "<git-sha>")]

# footer-stamp 的"真值源快照摘要"覆盖范围：任一真值源变动 → 摘要变 → 生成区判过期（正确）；
# 提交 report.html / README 本身不在此列 → 摘要不变 → CI 不会因自身提交而长红（F1 的根治点）
TRUTH_SOURCE_GLOBS = [
    "version.json", "doc/spec.md", "doc/spec.sha256", "doc/testplan.md",
    "doc/feature-matrix.md", "doc/bugs.md", "doc/bugs-archive.md",
    "doc/lint-waivers.md", "doc/lint-waivers-archive.md", "sim/regress/regress.list",
    "rtl/*.sv", "tb/**/*.sv", "doc/evidence/v*/*",
]

# 诚实清单（语义结论由 rev/arch 定，本脚本负责把其中的数字换成现算值并校验锚点文件存在）
HONESTY_ITEMS = [
    dict(id="H1", topic="记分板",
         status="ppa_scoreboard.sv 仅 {sb_lines} 行，只做读写计数，比对不集中在此组件",
         alt="真正的比对在自检序列 chk_eq（tb/ 内 {chk_eq} 处调用）与 core-agent driver 的输出比对——"
             "期望值由**唯一参考模型** predict()（tb/uvm/core_agent/ppa_core_seq_item.sv，"
             "{predict_lines} 行）从 spec 逐条推导（原 ppa_ref_model.sv 死代码已按 BUG-016 删除）",
         cost="检查逻辑分散、非集中式记分板",
         anchors=["tb/uvm/env/ppa_scoreboard.sv", "tb/uvm/core_agent/ppa_core_seq_item.sv"]),
    dict(id="H2", topic="寄存器抽象层",
         status="无 RAL / uvm_reg（tb/ 下 uvm_reg 引用 {uvm_reg} 处）",
         alt="tb/uvm/env/ppa_reg_defs.sv（{reg_defs_lines} 行）地址常量 package 单点定义",
         cost="无自动 mirror / predictor",
         anchors=["tb/uvm/env/ppa_reg_defs.sv"]),
    dict(id="H3", topic="virtual sequence",
         status="无 virtual sequence / p_sequencer（tb/ 下 p_sequencer 引用 {p_seq} 处）",
         alt="ppa_base_test 模板方法 main_seq()",
         cost="多 agent 并发编排能力弱",
         anchors=["tb/uvm/test/ppa_base_test.sv"]),
    dict(id="H4", topic="factory override",
         status="无 factory override（set_type/inst_override {override} 处）",
         alt="场景差异靠独立 test 类",
         cost="test 类数量线性增长（当前 {scenario_tests} 个场景测试类）",
         anchors=["tb/uvm/test"]),
    dict(id="H5", topic="功能覆盖率",
         status="功能覆盖率只有 {cg} 个 covergroup（{cp} coverpoint + {cross} cross）",
         alt="验收口径是 spec §0 适配 7 的代码+断言六类，功能覆盖率不在判据内",
         cost="{score} 是代码域水位，不代表功能空间覆盖（最易被追问）",
         anchors=["tb/uvm/env/ppa_cov.sv"]),
    dict(id="H6", topic="约束随机",
         status="约束随机轻量：无独立 constraint 块（{constraints} 处），靠 $urandom（{urandom} 处）+ 多 seed",
         alt="随机空间靠 seed 数量而非约束建模（回归 {regress_entries} 条 / {unique_tests} 个唯一测试）",
         cost="不是工业级 CRV",
         anchors=["sim/regress/regress.list"]),
]
# 历史不一致注脚（同样由现算结果证实/证伪，见 collect_results 的 signoff_glob_compat）
HONESTY_FOOTNOTES = [
    "M1 签核文件名 {m1_file} 早于 review-m<N>-milestone.md 命名规范，BUG-011 修复后的 "
    "docs.py glob 对它不匹配（内容实质完整，{m1_lines} 行）——docs.py 的 M 完成判据对 M1 已不成立，"
    "属历史遗留，不影响 M1 已签核事实",
    "TOGGLE {toggle} 仅高于门槛 {margin} pt；PRDATA[31:8]+PREADY 的结构性过滤若因设计变更失效需重估",
]


# ---------------------------------------------------------------------------
# 通用解析工具
# ---------------------------------------------------------------------------

def rel(path):
    """仓库内路径转相对；仓库外（如临时目录里的注入目标）原样返回。"""
    p = Path(path).resolve()
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def read(path):
    p = Path(path)
    if not p.exists():
        fail(f"真值源缺失: {rel(p) if p.is_absolute() else p}")
    return p.read_text(encoding="utf-8", errors="replace")


def parse_table_text(text, owner):
    """把一段文本里的第一张 markdown 表解析成 [{列名: 单元格}]（复用 docs.py 的转义处理）。"""
    rows, header = [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            if header is not None and rows:
                break            # 表已结束
            header = None
            continue
        cells = row_cells(line)
        if header is None:
            header = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(dict(zip(header, cells)))
    if not rows:
        fail(f"{owner} 内找不到 markdown 表——表结构变了，解析规则须同步更新（拒绝静默给空值）")
    return header, rows


def slice_section(text, section_re, owner):
    """按标题正则定位章节，切到下一个同级或更高级标题之前。定位不到即 FAIL。"""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines) if re.search(section_re, l)), None)
    if start is None:
        fail(f"{owner} 中定位不到章节 {section_re!r}——文档结构变了，解析规则须同步更新")
    level = len(re.match(r"^#*", lines[start]).group(0)) or 6
    end = len(lines)
    for j in range(start + 1, len(lines)):
        m = re.match(r"^(#{1,6})\s", lines[j])
        if m and len(m.group(1)) <= level:
            end = j
            break
    return "\n".join(lines[start + 1:end])


def ver_tuple(name):
    m = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", name.strip())
    if not m:
        fail(f"版本目录名不符合 v0.M.P 格式: {name}")
    return tuple(int(x) for x in m.groups())


def ver_milestone(name):
    """版本 → 里程碑：minor 号即 M 号（CLAUDE.md §4.1 bump-minor 进下一 Milestone）。"""
    return f"M{ver_tuple(name)[1]}"


def evidence_dirs():
    dirs = sorted(EVIDENCE.glob("v*"), key=lambda p: ver_tuple(p.name))
    if not dirs:
        fail("doc/evidence/ 下没有 v0.M.P 目录")
    return dirs


def sv_files(base):
    return sorted(Path(base).rglob("*.sv"))


RE_ASSERT_PROP = re.compile(r"\bassert\s+property\b")
RE_PORT = re.compile(r"^\s*(?:input|output|inout)\b", re.M)
RE_INST = re.compile(r"^\s*(\w+)\s+(u_\w+)\s*\(", re.M)
RE_MODULE_HEAD = re.compile(r"^\s*module\b", re.M)
RE_PORTLIST_END = re.compile(r"^\s*\)\s*;", re.M)


def count_ports(text, owner):
    """端口数只在 module 头的端口清单范围内统计（F9）：从 `module` 行切到端口表结束的
    `);` 行为止。全文件统计会把 task/function 的 input/output 一并算进去而虚高。"""
    m = RE_MODULE_HEAD.search(text)
    if not m:
        fail(f"{owner} 内找不到 module 声明——端口统计拒绝退化为全文件扫描")
    end = RE_PORTLIST_END.search(text, m.end())
    if not end:
        fail(f"{owner} 的 module 端口清单找不到结束的 ');' 行——结构变了，拒绝猜范围")
    head = text[m.start():end.start()]
    return len(RE_PORT.findall(head)), len(RE_PORT.findall(text))


# ---------------------------------------------------------------------------
# A. project
# ---------------------------------------------------------------------------

def truth_digest():
    """真值源快照摘要：对所有真值源文件的 (相对路径, sha256) 排序后再取 sha256。
    纯内容派生——不依赖 git、不依赖挂钟，任何克隆深度下重算都相同（F1 的确定性来源）。"""
    items = []
    for pat in TRUTH_SOURCE_GLOBS:
        for f in sorted(ROOT.glob(pat)):
            if f.is_file():
                items.append((str(f.relative_to(ROOT)),
                              hashlib.sha256(f.read_bytes()).hexdigest()))
    if not items:
        fail("真值源快照为空——TRUTH_SOURCE_GLOBS 与仓库结构不符")
    h = hashlib.sha256()
    for name, sha in sorted(set(items)):
        h.update(f"{name} {sha}\n".encode())
    return h.hexdigest(), len(set(items))


def collect_project():
    version, milestone = read_version()
    if ver_milestone(version) != milestone:
        warn(f"version.json 的 milestone={milestone} 与版本号推导的 {ver_milestone(version)} 不符——"
             "里程碑映射规则（minor 号=M 号）在本仓库首次失效，milestones 派生字段请人工复核")

    spec_text = read(SPEC)
    actual = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    pinned = read(SPEC_SHA).strip()
    if actual != pinned:
        fail("doc/spec.md 现算 sha256 与 doc/spec.sha256 不符——展示材料宣称的\"spec 被钉住\"当场不成立，"
             "拒绝出数（先补修改记录再 python3 scripts/docs.py --pin-spec）")

    _, rev_rows = parse_table_text(slice_section(spec_text, r"^##\s*修改记录", "doc/spec.md"),
                                   "doc/spec.md 修改记录")
    n_declared = count_mod_records(spec_text)
    if n_declared != len(rev_rows):
        fail(f"spec 修改记录行数解析不一致（docs.py={n_declared} / report.py={len(rev_rows)}）")
    revisions = []
    for r in rev_rows:
        content = r.get("内容", "")
        m = re.search(r"BUG-\d{3}", content)
        # 闭环修订的锚点是"rev 裁决落地"这句固定措辞（r4–r11 均有；r3 只是提到"lint 门禁"，不是裁决）
        arb = bool(re.search(r"rev\s*裁决", content))
        revisions.append({
            "rev": r.get("版次", ""), "date": r.get("日期", ""), "author": r.get("修改人", ""),
            "linked_bug": m.group(0) if m else None,
            "closed_loop": bool(m) or arb,
            "origin": "bugs.md 缺陷闭环" if m else
                      ("rev 门禁附带仲裁" if arb else "项目基线/适配"),
            "summary": content,
        })
    closed_loop = [r for r in revisions if r["closed_loop"]]

    _, csr_rows = parse_table_text(slice_section(spec_text, r"^##\s*5\.2\s", "doc/spec.md"),
                                   "doc/spec.md §5.2 寄存器表")
    offsets = [r for r in csr_rows if r.get("偏移", "").strip()]
    if not offsets:
        fail("doc/spec.md §5.2 表中解析不到\"偏移\"列——表结构变了")

    digest, n_files = truth_digest()
    return {
        "version": version,
        "milestone": milestone,
        "spec_file": rel(SPEC),
        "spec_lines": len(spec_text.splitlines()),
        "spec_sha256": actual,
        "spec_pinned": True,
        "truth_digest": digest,
        "truth_files": n_files,
        "truth_digest_rule": "对 TRUTH_SOURCE_GLOBS 命中的全部真值源文件按 (路径, sha256) "
                             "排序后再取 sha256；不含 git 与挂钟，克隆深度无关",
        "spec_revisions": revisions,
        "spec_revision_count": len(revisions),
        "spec_closed_loop_count": len(closed_loop),
        "spec_closed_loop_via_bugs": sum(1 for r in closed_loop if r["linked_bug"]),
        "spec_closed_loop_via_gate": sum(1 for r in closed_loop if not r["linked_bug"]),
        "spec_closed_loop_note": "闭环修订 = 由 bugs.md 缺陷裁决或 rev 门禁附带仲裁驱动的 spec 修订；"
                                 "其中经 rev 门禁仲裁的两条无 BUG-ID，材料不得笼统称\"N 个 BUG\"",
        "csr_count": len(offsets),
        "csr_field_rows": len(csr_rows),
    }


# ---------------------------------------------------------------------------
# B. design
# ---------------------------------------------------------------------------

def collect_design(features_rows):
    modules = []
    for f in sv_files(RTL):
        text = read(f)
        ports, ports_whole = count_ports(text, rel(f))
        if ports != ports_whole:
            warn(f"{rel(f)} 端口清单外另有 {ports_whole - ports} 处 input/output/inout"
                 "（task/function 参数等），端口数只计清单内的")
        modules.append({
            "name": f.stem, "file": rel(f),
            "lines": len(text.splitlines()),
            "sva": len(RE_ASSERT_PROP.findall(text)),
            "ports": ports,
        })
    if not modules:
        fail("rtl/ 下没有 .sv 文件")

    top = RTL / "ppa_top.sv"
    hierarchy = [{"module": m, "instance": i} for m, i in RE_INST.findall(read(top))]
    if not hierarchy:
        fail(f"{rel(top)} 内解析不到例化关系（^<module> u_<inst> (）——顶层结构变了")

    core = RTL / "packet_proc_core.sv"
    m = re.search(r"typedef\s+enum\b[^;]*?\{(.*?)\}", read(core), re.S)
    if not m:
        fail(f"{rel(core)} 内解析不到 typedef enum 状态机定义")
    states = []
    for part in m.group(1).split(","):
        part = re.sub(r"//.*", "", part)
        name = part.split("=")[0].strip()
        if name:
            states.append(name)

    return {
        "modules": modules,
        "module_count": len(modules),
        "rtl_lines": sum(x["lines"] for x in modules),
        "rtl_sva": sum(x["sva"] for x in modules),
        "rtl_ports": sum(x["ports"] for x in modules),
        "hierarchy": hierarchy,
        "fsm": {"file": rel(core), "states": states, "count": len(states)},
        "features": [{"id": r.get("编号", ""), "milestone": r.get("里程碑", ""),
                      "module": r.get("模块", ""), "feature": r.get("功能", ""),
                      "spec_ref": r.get("spec 依据", ""),
                      "scenes": r.get("关联场景", "").replace(",", " ").split()}
                     for r in features_rows],
        "feature_count": len(features_rows),
        "src": {"modules": "rtl/*.sv", "features": rel(FEATURE_MATRIX)},
    }


# ---------------------------------------------------------------------------
# C. verification
# ---------------------------------------------------------------------------

def count_pattern(base, pattern, flags=0):
    """在 base 下所有 .sv 中统计正则命中次数（用于诚实清单的机械锚点）。"""
    rx = re.compile(pattern, flags)
    return sum(len(rx.findall(read(f))) for f in sv_files(base))


def collect_verification(tp_rows, rtl_lines):
    files = sv_files(TB)
    if not files:
        fail("tb/ 下没有 .sv 文件")
    tb_lines = sum(len(read(f).splitlines()) for f in files)

    groups = {}
    for f in files:
        groups[rel(f.parent)] = groups.get(rel(f.parent), 0) + 1

    # 测试文件三分类 + package（package 不是测试，单列，保证四类之和 == 文件数）
    test_dir = TB / "uvm" / "test"
    scenario, base_cls, seq_lib, pkg = [], [], [], []
    for f in sorted(test_dir.glob("*.sv")):
        n = f.stem
        entry = {"name": n, "file": rel(f), "lines": len(read(f).splitlines())}
        if n.endswith("_pkg"):
            pkg.append(entry)
        elif n.endswith("base_test"):
            base_cls.append(entry)
        elif n.endswith("_seq_lib"):
            seq_lib.append(entry)
        else:
            scenario.append(entry)
    if len(scenario) + len(base_cls) + len(seq_lib) + len(pkg) != len(list(test_dir.glob("*.sv"))):
        fail("tb/uvm/test/ 文件分类未穷尽——分类规则须更新")

    de_sva = {f.stem: len(RE_ASSERT_PROP.findall(read(f))) for f in sv_files(RTL)}
    dv_sva = {f.stem: len(RE_ASSERT_PROP.findall(read(f))) for f in sorted(SVA_DIR.glob("*.sv"))}
    if not dv_sva:
        fail("tb/sva/ 下没有 .sv 断言文件")

    cov_file = TB / "uvm" / "env" / "ppa_cov.sv"
    cov_text = read(cov_file)
    cgs = re.findall(r"^\s*covergroup\s+(\w+)", cov_text, re.M)
    cps = re.findall(r"^\s*(\w+)\s*:\s*coverpoint\b", cov_text, re.M)
    crosses = re.findall(r"^\s*(\w+)\s*:\s*cross\b", cov_text, re.M)
    if not cgs:
        fail(f"{rel(cov_file)} 内解析不到 covergroup")

    tp_counts = status_counts(tp_rows)
    tp_pass = sum(1 for r in tp_rows if "✅" in r.get("状态", ""))

    # 回归列表：与 scripts/regress.py 同款解析规则
    entries, seeds_of = [], {}
    for lineno, line in enumerate(read(REGRESS_LIST).splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            fail(f"regress.list 第 {lineno} 行格式错误（应为 '<TEST> <SEED>'）: {line}")
        entries.append({"test": parts[0], "seed": parts[1]})
        seeds_of.setdefault(parts[0], []).append(parts[1])
    if not entries:
        fail("regress.list 为空")
    multi_seed = [{"test": t, "seeds": s} for t, s in seeds_of.items() if len(s) > 1]

    scen_names = {e["name"] for e in scenario}
    regress_only = sorted(set(seeds_of) - scen_names)
    if regress_only:
        warn(f"regress.list 中有 {len(regress_only)} 个测试在 tb/uvm/test/ 找不到同名文件: "
             f"{', '.join(regress_only)}")

    return {
        "tb_files": len(files),
        "tb_lines": tb_lines,
        "rtl_tb_ratio": round(tb_lines / rtl_lines, 2) if rtl_lines else None,
        "groups": dict(sorted(groups.items())),
        "tests": {
            "files": len(list(test_dir.glob("*.sv"))),
            "scenario": len(scenario), "scenario_names": [e["name"] for e in scenario],
            "base": len(base_cls), "base_names": [e["name"] for e in base_cls],
            "seq_lib": seq_lib, "seq_lib_count": len(seq_lib),
            "package": len(pkg),
        },
        "sva": {
            "de": sum(de_sva.values()), "dv": sum(dv_sva.values()),
            "total": sum(de_sva.values()) + sum(dv_sva.values()),
            "de_by_file": de_sva, "dv_by_file": dv_sva,
            "note": "DE = rtl/ 内部不变量断言；DV = tb/sva/ 接口/协议断言（bind 挂接），职责分工见 CLAUDE.md §0",
        },
        "functional_coverage": {
            "file": rel(cov_file), "covergroups": cgs, "covergroup_count": len(cgs),
            "coverpoints": cps, "coverpoint_count": len(cps),
            "crosses": crosses, "cross_count": len(crosses),
        },
        "testplan": {
            "file": rel(TESTPLAN),
            "rows": len(tp_rows), "passed": tp_pass,
            "pass_rate": round(100.0 * tp_pass / len(tp_rows), 2) if tp_rows else None,
            "by_milestone": {ms: {"total": sum(c.values()), "pass": c["✅"], "fail": c["❌"],
                                  "warn": c["⚠️"], "todo": c["🔲"]}
                             for ms, c in sorted(tp_counts.items())},
            "entries": [{"id": r.get("ID", ""), "milestone": r.get("里程碑", ""),
                         "scenario": r.get("场景", ""), "status": r.get("状态", ""),
                         "spec_ref": r.get("spec 依据", ""),
                         "evidence": r.get("证据", ""),
                         "repro": r.get("复现", "").strip("` ")}
                        for r in tp_rows],
        },
        "regress": {
            "file": rel(REGRESS_LIST),
            "entries": len(entries), "unique_tests": len(seeds_of),
            "multi_seed": multi_seed, "multi_seed_tests": len(multi_seed),
            "list": entries,
        },
    }


# ---------------------------------------------------------------------------
# D. results — 回归历史
# ---------------------------------------------------------------------------

RES_HEAD = re.compile(r"日期=(\d{4}-\d{2}-\d{2})\s+通过=(\d+)/(\d+)")
RES_ROW = re.compile(r"^(PASS|FAIL|NOLOG|NOSUMMARY)\b")


def collect_regress_history():
    history, missing = [], []
    for d in evidence_dirs():
        f = d / "result_summary.txt"
        if not f.exists():
            missing.append({"version": d.name, "milestone": ver_milestone(d.name),
                            "artifacts": sorted(p.name for p in d.iterdir())})
            continue
        lines = read(f).splitlines()
        head = RES_HEAD.search(lines[0] if lines else "")
        if not head:
            fail(f"{rel(f)} 首行不含 '日期=YYYY-MM-DD 通过=N/N'——回归摘要格式变了")
        d_date, passed, total = head.group(1), int(head.group(2)), int(head.group(3))
        rows = [l for l in lines[1:] if RES_ROW.match(l)]
        n_pass = sum(1 for l in rows if l.startswith("PASS"))
        # 交叉校验：首行声明 ⇄ 逐行结果，不等即 FAIL（防抄录/截断）
        if n_pass != passed or len(rows) != total:
            fail(f"{rel(f)} 首行声明 {passed}/{total} 与逐行统计 {n_pass}/{len(rows)} 不符")
        history.append({"version": d.name, "milestone": ver_milestone(d.name), "date": d_date,
                        "passed": passed, "total": total, "pass_rate": round(100.0 * passed / total, 2),
                        "pass_lines": n_pass, "result_lines": len(rows), "src": rel(f)})
    if not history:
        fail("doc/evidence/ 下没有任何 result_summary.txt")

    # 同批归档合并：同日期 + 同 通过/总数 的相邻记录判为同一批（防趋势图画成两次增长）
    series = []
    for h in history:
        if series and series[-1]["date"] == h["date"] and \
           series[-1]["passed"] == h["passed"] and series[-1]["total"] == h["total"]:
            series[-1]["versions"].append(h["version"])
            series[-1]["milestones"].append(h["milestone"])
            series[-1]["src"].append(h["src"])
            continue
        series.append({"versions": [h["version"]], "milestones": [h["milestone"]],
                       "date": h["date"], "passed": h["passed"], "total": h["total"],
                       "src": [h["src"]]})
    merged = [s for s in series if len(s["versions"]) > 1]
    last = series[-1]
    # F3：说明性注记里的数字一律由现算字段填入，不手写——手写的注记不会随数据更新，
    # 而 data-json 会把它原样带进 HTML，等于在展示材料里埋一个不会自更新的数字。
    n_dirs = len(evidence_dirs())
    note = (f"{n_dirs} 个 evidence 目录 ≠ {n_dirs} 次测量：只有含 result_summary.txt 的目录"
            f"才是一次归档回归，实际 {len(history)} 次（缺摘要的 {len(missing)} 个目录见 "
            f"missing_result_summary）。未归档的轮次即便在别处文中被提及，也不得补进曲线。"
            + (f" series 已按'同日期同结果'合并同批归档："
               + "；".join("+".join(s["versions"]) + f" 同为 {s['passed']}/{s['total']}"
                          for s in merged) + "。" if merged else ""))
    return {
        "history": history, "points": len(history),
        "latest": {"versions": last["versions"], "date": last["date"],
                   "passed": last["passed"], "total": last["total"],
                   "text": f"{last['passed']}/{last['total']}",
                   "pass_rate": round(100.0 * last["passed"] / last["total"], 2),
                   "src": last["src"]},
        "series": series, "series_points": len(series),
        "merged_batches": merged,
        "missing_result_summary": missing,
        "note": note,
    }


# ---------------------------------------------------------------------------
# D. results — 覆盖率历史（锚点表 + 严格失败 + 漏点守卫）
# ---------------------------------------------------------------------------

RE_COV_PASS = re.compile(r"(\d+)\s*/\s*(\d+)\s*PASS")


def norm_metric_label(label):
    return re.sub(r"[*（）()\s]|综合|六类", "", label).upper()


def clean_cell(cell):
    """单元格清洗：去 * % 空白；含 → 取右段（首测→复测）；N/A、— 等 → None。"""
    v = re.sub(r"[*%\s]", "", cell)
    if "→" in v:
        v = v.split("→")[-1]
    if v in ("", "N/A", "NA", "—", "-", "--", "n/a"):
        return None
    try:
        return float(v)
    except ValueError:
        fail(f"覆盖率单元格无法解析为数值: {cell!r}")


def pick_value_col(header, version, value_col, owner):
    """列选择：优先取列头含本目录版本号的列（一条规则同时覆盖 v0.4.0 的"闭环(v0.4.0)"），
    否则回退到锚点登记的 value_col 正则。命中数 != 1 即 FAIL。"""
    bare = version.lstrip("v")
    hits = [i for i, h in enumerate(header) if bare in h]
    how = f"列头含版本号 {bare}"
    if not hits:
        hits = [i for i, h in enumerate(header) if re.search(value_col, h)]
        how = f"列头匹配 {value_col!r}"
    if len(hits) != 1:
        fail(f"{owner} 值列定位失败（{how} 命中 {len(hits)} 列，表头={header}）——"
             "表结构变了，拒绝猜列（取错列会把基线当成结论）")
    return hits[0], how


def collect_coverage_history():
    history = []
    anchor_dirs = set()
    for d in evidence_dirs():
        if not list(d.glob("coverage-summary*.md")):
            continue
        anchor_dirs.add(d.name)
        anchor = COV_ANCHORS.get(d.name)
        if anchor is None:
            fail(f"{d.name} 有覆盖率摘录但 COV_ANCHORS 未登记解析规则——"
                 "新增里程碑后必须补锚点，否则趋势曲线会静默漏点")
        f = d / anchor["file"]
        if not f.exists():
            fail(f"COV_ANCHORS[{d.name}] 指向的 {anchor['file']} 不存在于 {rel(d)}")
        owner = rel(f)
        text = read(f)
        header, rows = parse_table_text(slice_section(text, anchor["section"], owner), owner)
        col, how = pick_value_col(header, d.name, anchor["value_col"], owner)

        vals = {}
        for r in rows:
            key = METRIC_ALIAS.get(norm_metric_label(r.get(header[0], "")))
            if key is None:
                continue
            if key in vals:
                fail(f"{owner} 中类别 {key} 出现多行——章节切片可能跨了两张表")
            vals[key] = clean_cell(r.get(header[col], ""))
        missing = [m for m in METRIC_ORDER
                   if m not in vals and m not in anchor["allow_missing"]]
        if missing:
            fail(f"{owner} 的表中缺少类别行 {missing}——表结构变了，拒绝用 0/默认值补位")

        point = {"version": d.name, "milestone": ver_milestone(d.name),
                 "domain": anchor["domain"], "comparable": anchor["comparable"],
                 "value_col": header[col], "col_rule": how,
                 "src": owner, "note": anchor["note"]}
        point.update({m: vals.get(m) for m in METRIC_ORDER})
        point["six_pass"] = [m for m in SIX_METRICS
                             if vals.get(m) is not None and vals[m] >= COV_THRESHOLD]
        point["six_measured"] = [m for m in SIX_METRICS if vals.get(m) is not None]
        history.append(point)

    if not history:
        fail("doc/evidence/ 下没有任何 coverage-summary*.md")
    stale = sorted(set(COV_ANCHORS) - anchor_dirs)
    if stale:
        warn(f"COV_ANCHORS 登记了但 evidence 下已无对应覆盖率摘录: {', '.join(stale)}")

    comparable = [p for p in history if p["comparable"]]
    latest = comparable[-1] if comparable else None
    return {
        "history": history, "points": len(history),
        "comparable_points": len(comparable),
        "latest": latest,
        "threshold": COV_THRESHOLD,
        "metrics": SIX_METRICS,
        "note": "M1 点口径为模块聚合域（非 tb_top）且无 SCORE 行、FSM 结构性 N/A → comparable=false，"
                "画图不得用 0 补位连线；M2→M3 的 SCORE 是真实下降（集成路径引入新未激励代码），"
                "必须画出来并注解。",
    }


def cov_pass_crosscheck(cov_hist, regress_hist):
    """每个 coverage-summary 的 N/N PASS ⇄ 同目录 result_summary（--check 第 2 项）。"""
    errors, notes = [], []
    res_by_ver = {h["version"]: h for h in regress_hist}
    for p in cov_hist:
        ver = p["version"]
        pairs = {(int(a), int(b)) for a, b in RE_COV_PASS.findall(read(ROOT / p["src"]))}
        res = res_by_ver.get(ver)
        if not pairs:
            notes.append(f"{p['src']} 中找不到 'N/N PASS' 声明，跳过交叉校验")
            continue
        if len(pairs) > 1:
            notes.append(f"{p['src']} 中有 {len(pairs)} 个互不相同的 N/N PASS 声明 "
                         f"{sorted(pairs)}（首测/复测并存）→ 降级为 warn，不做等值比对")
            continue
        got = pairs.pop()
        if res is None:
            notes.append(f"{ver} 有覆盖率摘录但同目录无 result_summary.txt，无法交叉校验")
        elif got != (res["passed"], res["total"]):
            errors.append(f"{p['src']} 声明 {got[0]}/{got[1]} PASS 与 "
                          f"{res['src']} 的 {res['passed']}/{res['total']} 不符")
    return errors, notes


# ---------------------------------------------------------------------------
# E-bis. sva_baseline —— svacheck.py 层 3 信任锚的留痕校验（--check 第 8 项，BUG-018 A）
# ---------------------------------------------------------------------------
# svacheck.py 层 3（sim/regress/sva_baseline.json 的 total_min/attempted_min）此前不受任何
# 机械守卫（全仓只有 spec.md 被 sha-pin）——rev 实测把 floor 静默改成 0/0 后，`$assertoff`
# 向量（91/0/0）重新判 CLEAN（BUG-018 登记语料，doc/evidence/v0.5.5/review-bug-015-016-017.md
# §C-③新绕过A）。
#
# 不做 sha-pin：那会把"任何改动"（含合法抬高 floor）都逼进 `--pin-spec` 那套额外命令的心智
# 模型，且与 spec.md 的"钉住=禁止修改除非走修改记录"语义不同——floor 本来就允许随规模增长
# 而上调，做成 sha-pin 会变成没有必要的死门禁（违反卡内判据③）。改走"值必须自描述"：
# **当前 total_min/attempted_min 必须与 changelog 数组末行文本里声明的
# `total_min=N attempted_min=N` 逐字一致**。效果：
#   · 只改两个数字字段、不追 changelog 行（rev 的攻击构造）→ 末行仍是旧值 → 不一致 → FAIL；
#   · 按基线文件自身"维护纪律"要求的正当程序改值 + 在 changelog 追一行新值 → 一致 → 绿，
#     不阻断合法变更（判据③）。
# 这不是密码学意义上的防篡改——changelog 与数值字段同在一份 git 版本文件里，存心作恶的提交
# 者可以两处一起改掉（判据①测的是"只改一处"这类静默/疏忽式编辑，不是杜绝一切恶意提交）。
# 它把"这次动了 floor"从只能靠 /closeout 的人工 git diff 才看得见，变成本脚本能自动读出来的
# 显式声明，git 历史仍是恶意场景下的最终人工兜底。
SVA_BASELINE = ROOT / "sim" / "regress" / "sva_baseline.json"
RE_SVA_BASELINE_LOG_VALUES = re.compile(
    r"total_min\s*=\s*(\d+).*?attempted_min\s*=\s*(\d+)", re.S)


def check_sva_baseline():
    """sva_baseline.json 的 total_min/attempted_min ⇄ changelog 末行留痕比对。

    返回 (errors, note)：errors 非空即 --check FAIL；note 是给人读的现算摘要 dict
    （errors 非空时 note=None，避免把校验失败中途的半成品数字印进 note）。
    """
    if not SVA_BASELINE.exists():
        return [f"{rel(SVA_BASELINE)} 缺失——svacheck.py 层 3（断言总数/尝试数基线）的信任锚不存在"], None
    try:
        raw = json.loads(SVA_BASELINE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"{rel(SVA_BASELINE)} JSON 解析失败: {e}"], None
    missing = [k for k in ("total_min", "attempted_min", "changelog") if k not in raw]
    if missing:
        return [f"{rel(SVA_BASELINE)} 缺少字段 {missing}"], None
    total_min, attempted_min, changelog = raw["total_min"], raw["attempted_min"], raw["changelog"]
    if isinstance(total_min, bool) or isinstance(attempted_min, bool) or \
       not isinstance(total_min, int) or not isinstance(attempted_min, int):
        return [f"{rel(SVA_BASELINE)} total_min/attempted_min 必须是整数（现为 "
                f"{type(total_min).__name__}={total_min!r} / "
                f"{type(attempted_min).__name__}={attempted_min!r}）"], None
    if not isinstance(changelog, list) or not changelog:
        return [f"{rel(SVA_BASELINE)} changelog 为空或非数组——floor 值的变更留痕缺失，"
                "拒绝在无留痕记录下信任基线文件（BUG-018 判据①，fail-closed）"], None
    last = changelog[-1]
    m = RE_SVA_BASELINE_LOG_VALUES.search(str(last))
    if not m:
        return [f"{rel(SVA_BASELINE)} changelog 末行未按 'total_min=N attempted_min=N' 格式声明"
                f"新值：「{last}」——floor 变更必须在 changelog 末行显式写出新值（BUG-018 判据②）"], None
    log_total, log_attempted = int(m.group(1)), int(m.group(2))
    if (log_total, log_attempted) != (total_min, attempted_min):
        return [f"{rel(SVA_BASELINE)} 当前 floor（total_min={total_min}, "
                f"attempted_min={attempted_min}）与 changelog 末行声明值（total_min={log_total}, "
                f"attempted_min={log_attempted}）不符——floor 被改动但未同步在 changelog 追行留痕"
                "（静默改动，BUG-018 判据①命中）"], None
    return [], {"total_min": total_min, "attempted_min": attempted_min,
               "changelog_entries": len(changelog), "changelog_last": str(last)}


# ---------------------------------------------------------------------------
# F. results — 缺陷 / 豁免 / 审查
# ---------------------------------------------------------------------------

RE_SHA = re.compile(r"\b[0-9a-f]{7}\b")


def collect_bugs():
    rows = parse_table(BUGS) + parse_table(BUGS_ARCHIVE)
    if not rows:
        fail("bugs.md(+归档) 解析不到任何缺陷行")
    entries = []
    for r in rows:
        owner = r.get("疑似归属", "")
        head = re.split(r"[（(]", owner.strip("* 　"))[0]      # 括号前的抬头才是归属本身
        kind = next((k for k, pat in BUG_KIND_RULES if pat.lower() in head.lower()), None)
        if kind is None:
            fail(f"bugs.md {r.get('ID', '?')} 的归属列抬头 {head[:40]!r} 无法归入 rtl/tb/infra/spec——"
                 "分类规则须更新（拒绝静默归入\"其他\"）")
        commits = RE_SHA.findall(r.get("修复 commit", ""))
        entries.append({
            "id": r.get("ID", ""), "date": r.get("日期", ""), "version": r.get("版本", ""),
            "state": r.get("状态", "").strip(), "kind": kind, "owner_raw": owner,
            "fix_commits": commits, "rounds": len(commits),
            "evidence": r.get("复验证据", "").strip("` "),
            "summary": r.get("现象摘要", "")[:120],
            "repro": r.get("最小复现", "")[:160], "spec_ref": r.get("spec 依据", "")[:120],
        })
    by_kind, by_state = {}, {}
    for e in entries:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
        by_state[e["state"]] = by_state.get(e["state"], 0) + 1
    multi = [e for e in entries if e["rounds"] > 1]
    return {
        "total": len(entries), "by_kind": by_kind, "by_state": by_state,
        "multi_round": [{"id": e["id"], "rounds": e["rounds"], "commits": e["fix_commits"]}
                        for e in multi],
        "entries": sorted(entries, key=lambda e: e["id"]),
        "src": [rel(BUGS), rel(BUGS_ARCHIVE)],
        "kind_rule": "有序匹配归属列：含 RTL→rtl；含 infra→infra；含 spec→spec"
                     "（infra 行原文含\"非 spec 歧义\"，spec 必须排最后）",
        "rounds_rule": "rounds = 修复 commit 列中 7 位 sha 的个数（\"两轮闭环\"的唯一机械证据）",
    }


# 豁免登记行号的**语义**核对：对应告警类别的代码特征。行号是登记时刻的快照，
# 文件后续改动会漂移；本表用于把"处数可信 / 行号已漂移"两件事分开如实呈现。
SITE_ANCHOR_PATTERNS = {
    "SVA-DIU": r"disable\s+iff",
    "NS": r"@\s*\(|wait\s*\(|repeat\s*\(",
    "WMIA-L": r"uvm_field_",
}

# 豁免"处数"抽取：<文件>:<行号表>，行号表允许 , / 分隔与 N-M 区间
RE_WAIVER_SITE = re.compile(
    r"([\w./]+\.(?:sv|svh)):"
    r"(\d+(?:\s*[-–]\s*\d+)?(?:\s*[,/]\s*\d+(?:\s*[-–]\s*\d+)?)*)")
RE_DECLARED_SITES = re.compile(r"(?:全\s*)?(\d+)\s*处")


def count_sites(spec_str):
    n = 0
    for part in re.split(r"[,/]", spec_str):
        m = re.fullmatch(r"\s*(\d+)\s*[-–]\s*(\d+)\s*", part)
        n += (int(m.group(2)) - int(m.group(1)) + 1) if m else 1
    return n


def collect_waivers():
    rows = parse_table(WAIVERS) + parse_table(WAIVERS_ARCHIVE)
    if not rows:
        fail("lint-waivers.md(+归档) 解析不到任何豁免行")
    entries, by_cat = [], {}
    total_sites, mismatches, stale_lines = 0, [], []
    for r in rows:
        cat_m = re.search(r"Lint-\[([A-Z-]+)\]", r.get("告警类别", ""))
        if not cat_m:
            fail(f"lint-waivers #{r.get('#', '?')} 的告警类别列解析不到 Lint-[XXX]")
        cat = cat_m.group(1)
        obj = r.get("对象（文件:行）", "")
        pat = SITE_ANCHOR_PATTERNS.get(cat)
        if pat is None:
            warn(f"lint 豁免 #{r.get('#', '?')} 的类别 {cat} 未登记行号语义特征，"
                 "该行跳过行号漂移核对（新类别请补 SITE_ANCHOR_PATTERNS）")
        sites, files = 0, []
        for f, spec_str in RE_WAIVER_SITE.findall(obj):
            n = count_sites(spec_str)
            # 展开行号（含 N-M 区间），逐行核对是否仍命中该类别的代码特征
            nums = []
            for part in re.split(r"[,/]", spec_str):
                rg = re.fullmatch(r"\s*(\d+)\s*[-–]\s*(\d+)\s*", part)
                nums += (list(range(int(rg.group(1)), int(rg.group(2)) + 1)) if rg
                         else [int(x) for x in re.findall(r"\d+", part)])
            p = ROOT / f
            hit = None
            if p.exists() and pat:
                src = p.read_text(encoding="utf-8", errors="replace").splitlines()
                hit = sum(1 for x in nums
                          if x <= len(src) and re.search(pat, src[x - 1]))
                if hit != len(nums):
                    stale_lines.append(f"#{r.get('#', '?')} {f}: 登记 {len(nums)} 行，"
                                       f"现文件仍命中 {hit} 行（行号已漂移，处数不受影响）")
            elif not p.exists():
                stale_lines.append(f"#{r.get('#', '?')} {f}: 文件已不存在")
            files.append({"file": f, "sites": n, "exists": p.exists(),
                          "lines_still_matching": hit})
            sites += n
        if sites == 0:
            fail(f"lint-waivers #{r.get('#', '?')} 的对象列解析不出任何 <文件>:<行号>——"
                 "登记格式变了，处数拒绝给默认值")
        # 交叉校验：结论/原因列若自述"N 处"，逐行号解析的总数必须命中其中之一。
        # 收集全部自述值而非只取第一个——一条豁免可能写成"其中 3 处…，全 10 处"，
        # 只取首个会因措辞变化误报（这个校验挂在 CI 上，误报的代价是把 CI 打红）。
        # 取数优先级：结论列的"全 N 处"是权威自述；结论列没写才退到原因列。
        # 不把两列混在一起取并集——那样一列被改坏、另一列碰巧还对，就会被放过（实测漏检过）。
        # 同一列内允许多个数（如原因列"首批 8 处；追加 4 处"），命中其一即可。
        declared = [int(x) for x in RE_DECLARED_SITES.findall(r.get("结论（豁免/待修）", ""))] \
            or [int(x) for x in RE_DECLARED_SITES.findall(r.get("原因", ""))]
        if declared and sites not in declared:
            mismatches.append(f"#{r.get('#', '?')} 自述 {declared} 处 ≠ 行号解析 {sites} 处")
        # 已复核 = 复核列非空**且**明示"批准"。docs.py 的 waiver_done() 只判非空，
        # 那是给归档决策用的宽口径；这里的结果会印成"N/N 全部经 rev 复核批准"，
        # 把"待 rev 复核"算成已复核就是在对外材料上作假（#12 落盘时实测会被算进去）。
        rv = r.get("复核（rev/日期）", "").strip("-— ")
        reviewed = bool(rv) and "批准" in rv and not rv.lstrip().startswith("待")
        entries.append({"id": r.get("#", ""), "category": cat, "sites": sites,
                        "sites_declared": declared, "files": files,
                        "reviewed": reviewed,
                        "conclusion": r.get("结论（豁免/待修）", "")[:80],
                        "review": r.get("复核（rev/日期）", "")[:80],
                        "object": obj[:160]})
        by_cat[cat] = by_cat.get(cat, 0) + 1
        total_sites += sites
    if mismatches:
        fail("lint 豁免处数自述与行号解析不一致: " + "；".join(mismatches) +
             "（登记表内部矛盾，拒绝出数）")
    reviewed = sum(1 for e in entries if e["reviewed"])
    pending = [e["id"] for e in entries if not e["reviewed"]]
    if pending:
        warn(f"lint 豁免 #{'/#'.join(pending)} 尚未经 rev 复核批准——"
             "展示材料不得写\"全部经 rev 复核\"（CLAUDE.md §7）")
    declared_rows = [e for e in entries if e["sites_declared"]]
    return {
        "total": len(entries), "by_category": by_cat,
        "reviewed": reviewed, "all_reviewed": reviewed == len(entries),
        "pending_review": pending,
        "reviewed_rule": "复核列须非空、含\"批准\"、且不以\"待\"开头；"
                         "\"待 rev 复核\"计为未复核（比 docs.py waiver_done 的归档口径严）",
        "sites_total": total_sites,
        "sites_rule": "逐条解析对象列的 <文件>:<行号表>（行号表按 , 与 / 分隔，N-M 计为 M-N+1 行）后求和",
        "sites_crosscheck": f"{len(declared_rows)}/{len(entries)} 条豁免在结论/原因列自述了\"N 处\"，"
                            f"全部与行号解析一致（0 处矛盾）",
        "sites_caveat": "处数 = 登记时刻的 lint 告警条数，可机械抽取且已交叉校验；"
                        "但对象列里的绝对行号是登记时刻的快照，文件后续改动会漂移"
                        "（见 sites_line_drift），漂移不影响处数本身",
        "sites_line_drift": sorted(set(stale_lines)),
        "sites_line_drift_rule": "按告警类别的代码特征逐行核对现文件对应行"
                                 f"（{SITE_ANCHOR_PATTERNS}）",
        "entries": sorted(entries, key=lambda e: int(e["id"]) if e["id"].isdigit() else 0),
        "src": [rel(WAIVERS), rel(WAIVERS_ARCHIVE)],
    }


def collect_reviews():
    seen, entries = set(), []
    for d in evidence_dirs():
        for f in sorted(list(d.glob("rev-*.md")) + list(d.glob("review*.md"))):
            if f in seen:
                continue
            seen.add(f)
            text = read(f)
            title = next((l.lstrip("# ").strip() for l in text.splitlines()
                          if l.startswith("#")), f.stem)
            kind = next((k for k, pat in REVIEW_KIND_RULES if pat in title), None)
            if kind is None:
                # 开放分类：归不了类只是分组标签缺失，不影响任何会印出去的数字 → 兜底 + warn
                kind = REVIEW_KIND_FALLBACK
                warn(f"{rel(f)} 标题 {title!r} 未命中已知分类关键字，归入 "
                     f"{REVIEW_KIND_FALLBACK}（如需单独分组，补 REVIEW_KIND_RULES）")
            entries.append({"path": rel(f), "version": d.name,
                            "milestone": ver_milestone(d.name), "title": title,
                            "kind": kind, "lines": len(text.splitlines())})
    if not entries:
        fail("doc/evidence/ 下没有任何 rev 审查记录")
    by_kind = {}
    for e in entries:
        by_kind[e["kind"]] = by_kind.get(e["kind"], 0) + 1
    return {"count": len(entries), "lines": sum(e["lines"] for e in entries),
            "by_kind": by_kind, "entries": entries,
            "kind_rule": "按标题关键字有序匹配：里程碑→milestone / 门禁→gate / 仲裁→arbitration / 豁免→waiver"}


def collect_evidence_inventory():
    dirs, logs = [], 0
    for d in evidence_dirs():
        files = sorted(p for p in d.iterdir() if p.is_file())
        n_log = sum(1 for p in files if p.suffix == ".log")
        logs += n_log
        dirs.append({
            "version": d.name, "milestone": ver_milestone(d.name),
            "files": len(files), "logs": n_log,
            "has_result_summary": (d / "result_summary.txt").exists(),
            "has_coverage_summary": bool(list(d.glob("coverage-summary*.md"))),
            "reviews": len(list(d.glob("rev-*.md")) + list(d.glob("review*.md"))),
            "names": [p.name for p in files],
        })
    return {
        "dirs": len(dirs), "log_files": logs,
        "result_summaries": sum(1 for d in dirs if d["has_result_summary"]),
        "coverage_summaries": sum(1 for d in dirs if d["has_coverage_summary"]),
        "total_files": sum(d["files"] for d in dirs),
        "detail": dirs,
        "note": "evidence 目录数 ≠ 测量次数：只有含 result_summary / coverage-summary 的目录才是一次归档测量",
    }


# ---------------------------------------------------------------------------
# G-bis. source_markers —— 源码注释 ⇄ 交付状态（--check 第 7 项，BUG-013）
# ---------------------------------------------------------------------------

RE_SV_STRING = re.compile(r'"(?:\\.|[^"\\])*"')
RE_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def comment_style(path):
    return SRC_BASENAME_STYLES.get(path.name) or SRC_COMMENT_STYLES.get(path.suffix)


def iter_comments(path):
    """产出 [(行号, 注释文本)]。先屏蔽字符串字面量再取注释，`"http://…"` 之类不会被当注释。
    已知边界（如实记录，不假装完备）：不解析宏与 `ifdef——被条件编译排除的代码里的注释
    同样会被扫到。这是刻意的：一条注释是否陈述事实，与它当前是否参与编译无关。"""
    style = comment_style(path)
    if style is None:
        return []
    tokens, has_block = style
    text = RE_SV_STRING.sub('""', read(path))
    out = []
    if has_block:
        def _blank(m):
            first = text.count("\n", 0, m.start()) + 1   # m.start() 是原文偏移，行号稳定
            for i, l in enumerate(m.group(0).splitlines()):
                out.append((first + i, l.strip()))
            return "\n" * m.group(0).count("\n")
        text = RE_BLOCK_COMMENT.sub(_blank, text)
    for lineno, line in enumerate(text.splitlines(), 1):
        idx = [i for i in (line.find(t) for t in tokens) if i >= 0]
        if idx:
            out.append((lineno, line[min(idx):].strip()))
    return sorted(out)


def scan_source_markers(milestone):
    """扫 rtl/ tb/ sim/ 的源码注释，找"引用了具体里程碑的未完成标记"，与当前里程碑对照。

    收官判据（机械、无歧义）：**N < 当前里程碑编号即视为已收官**。依据 CLAUDE.md §4.1——
    `make bump-minor` 进下一个 M 的前提是上一个 M 的三条硬条件（RTL 就绪 + 场景全 ✅、
    regress 100% PASS 且证据归档、rev 审查记录归档）全部达成，故"当前 M 之前的 M"必然已收官。
    另注：本仓库的 `M<N>` 有两种含义——spec §2.3 的**模块编号**（M1 apb_slave_if /
    M2 packet_sram / M3 packet_proc_core）与项目**里程碑编号**。二者在 N < 当前 M 这一
    判据下结论一致（模块 M1–M3 分别在里程碑 M1/M1/M2 交付完毕），故本守卫不区分，
    但因此**只在"该编号已经没有任何未交付内容"这一层面成立**，不试图区分二者语义。"""
    m = re.fullmatch(r"M(\d+)", str(milestone).strip())
    if not m:
        fail(f"version.json 的 milestone={milestone!r} 不是 M<N> 形态——"
             "源码注释守卫拒绝猜测当前里程碑（宁可不出数，也不放过一条过期承诺）")
    cur = int(m.group(1))

    files, comment_lines = [], 0
    stale, suppressed, live, open_ended = [], [], [], []
    for d in SRC_SCAN_DIRS:
        base = ROOT / d
        if not base.is_dir():
            fail(f"源码注释守卫的扫描目录不存在: {d}/ —— 仓库结构变了，拒绝静默跳过")
        for p in sorted(base.rglob("*")):
            if not p.is_file() or comment_style(p) is None:
                continue
            if set(p.relative_to(ROOT).parts[:-1]) & SRC_SCAN_SKIP_DIRS:
                continue
            files.append(rel(p))
            for lineno, ctext in iter_comments(p):
                comment_lines += 1
                base_rec = {"file": rel(p), "line": lineno, "text": ctext[:200]}
                hits = []
                for pat, desc in STALE_MARKER_PATTERNS:
                    for mm in re.finditer(pat, ctext):
                        hits.append({**base_rec, "milestone": f"M{int(mm.group(1))}",
                                     "rule": desc, "match": mm.group(0).strip()})
                seen = set()
                for h in hits:
                    key = (h["milestone"], h["match"])
                    if key in seen:            # 多条规则命中同一处，只记一次
                        continue
                    seen.add(key)
                    if int(h["milestone"][1:]) >= cur:
                        live.append(h)                       # 在途承诺，合法
                    elif STALE_SUPPRESS_TOKEN in ctext:
                        suppressed.append(h)                 # 已登记豁免，降级 warn
                    else:
                        stale.append(h)                      # 过期承诺 → 严格失败
                if not hits and OPEN_MARKER_RE.search(ctext):
                    open_ended.append(base_rec)              # 开放式留白，只计数

    return {
        "scanned_dirs": SRC_SCAN_DIRS,
        "files": len(files), "comment_lines": comment_lines,
        "current_milestone": f"M{cur}",
        "closed_rule": f"N < {cur} 视为已收官（CLAUDE.md §4.1：进下一个 M 的前提是上一个 M "
                       f"三条硬条件全部达成）",
        "stale": stale, "stale_count": len(stale),
        "suppressed": suppressed, "suppressed_count": len(suppressed),
        "open_milestone": live, "open_milestone_count": len(live),
        "open_ended": open_ended, "open_ended_count": len(open_ended),
        "suppress_token": STALE_SUPPRESS_TOKEN,
        "patterns": [{"regex": p, "desc": d} for p, d in STALE_MARKER_PATTERNS],
        "severity": "stale=错误（exit 1）；suppressed=warn；open_milestone/open_ended=仅计数",
        "note": "stale=引用已收官里程碑的未完成标记（源码自述与交付事实相反，会让材料结论"
                "被 git grep 当场证伪）；open_ended=无里程碑绑定的开放式留白，属正常设计留白，"
                "不判失败也不 warn。判定只看注释文本，不看代码语义。",
    }


# ---------------------------------------------------------------------------
# G. process（git，允许降级：CI 浅克隆拿不到时置 null + warn，--check 只 warn 不 error）
# ---------------------------------------------------------------------------

def git(*args):
    try:
        r = subprocess.run(["git", "-C", str(ROOT), *args],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)
    if r.returncode != 0:
        return None, (r.stderr or "").strip()
    return r.stdout.strip(), None


def collect_process(bugs):
    out, err = git("rev-parse", "--short", "HEAD")
    if out is None:
        warn(f"git 不可用（{err}），process.git 字段全部降级为 null（CI 浅克隆属正常）")
        return {"available": False, "head": None, "commits": None, "tags": None,
                "date_range": None, "bug_fix_dates": None,
                "note": "git 元数据不可用，展示材料的 git 相关数字必须留空，不得填历史值"}
    head = out
    n, _ = git("rev-list", "--count", "HEAD")
    tags_raw, _ = git("for-each-ref",
                      "--format=%(refname:short) %(creatordate:short) %(objectname:short)",
                      "refs/tags")
    tags = []
    for line in (tags_raw or "").splitlines():
        parts = line.split()
        if len(parts) >= 3:
            tags.append({"tag": parts[0], "date": parts[1], "commit": parts[2]})
    dates_raw, _ = git("log", "--format=%ad", "--date=short")
    dates = (dates_raw or "").splitlines()
    if not dates:
        warn("git log 为空，date_range 置 null")
    fix_dates = {}
    for b in bugs["entries"]:
        for sha in b["fix_commits"]:
            d, _ = git("show", "-s", "--format=%ad", "--date=short", sha)
            fix_dates.setdefault(b["id"], []).append({"commit": sha, "date": d})
    return {
        "available": True, "head": head,
        "commits": int(n) if n and n.isdigit() else None,
        "tags": tags, "tag_count": len(tags),
        "date_range": {"first": dates[-1], "last": dates[0]} if dates else None,
        "bug_fix_dates": fix_dates,
        "note": "tag 约定：里程碑完成时打 v0.M.P（CLAUDE.md §4.1），bump-minor 后的 v0.{M+1}.0 "
                "即上一个 M 的收官 tag",
    }


# ---------------------------------------------------------------------------
# 里程碑汇总（全部字段由上面各 collector 的现算结果派生）
# ---------------------------------------------------------------------------

def derive_milestones(data):
    tp = data["verification"]["testplan"]["by_milestone"]
    fm = data["design"]["features"]
    reg = {h["version"]: h for h in data["results"]["regress"]["history"]}
    # F5：同一 M 可能有多份 coverage-summary。规则显式化为"取该 M 内版本号最大的一份"，
    # 并在 >1 时 warn + 在条目里带出全部候选——不静默只留最后一份。
    cov, cov_cands = {}, {}
    for p in sorted(data["results"]["coverage"]["history"], key=lambda x: ver_tuple(x["version"])):
        cov_cands.setdefault(p["milestone"], []).append(p["version"])
        cov[p["milestone"]] = p
    for ms, cands in cov_cands.items():
        if len(cands) > 1:
            warn(f"{ms} 有 {len(cands)} 份覆盖率摘录（{', '.join(cands)}），"
                 f"里程碑表按显式规则取版本号最大的 {cands[-1]}")
    reviews = data["results"]["reviews"]["entries"]
    tags = {t["tag"]: t for t in (data["process"].get("tags") or [])}

    out = []
    for ms in sorted(tp, key=lambda m: int(m.lstrip("M"))):
        mnum = int(ms.lstrip("M"))
        mods = []
        for f in fm:
            if f["milestone"] == ms and f["module"] not in mods:
                mods.append(f["module"])
        vers = sorted((v for v in reg if ver_tuple(v)[1] == mnum), key=ver_tuple)
        last = reg[vers[-1]] if vers else None
        sign = [r for r in reviews if r["milestone"] == ms and r["kind"] == "milestone"]
        # docs.py 的 M 完成判据用 glob review-m<N>*.md（BUG-011 修复后），此处机械核对兼容性
        compat = [r for r in sign if Path(r["path"]).name.lower().startswith(f"review-m{mnum}")]
        tag = tags.get(f"v0.{mnum + 1}.0")
        out.append({
            "id": ms, "lab": MILESTONE_LABS.get(ms),
            "modules": mods,
            "scenarios": tp[ms]["total"], "scenarios_pass": tp[ms]["pass"],
            "regress": f"{last['passed']}/{last['total']}" if last else None,
            "regress_src": last["src"] if last else None,
            "coverage_score": cov[ms]["score"] if ms in cov else None,
            "coverage_domain": cov[ms]["domain"] if ms in cov else None,
            "coverage_comparable": cov[ms]["comparable"] if ms in cov else None,
            "coverage_src": cov[ms]["src"] if ms in cov else None,
            "coverage_candidates": cov_cands.get(ms, []),
            "regress_candidates": vers,
            "signoff": [r["path"] for r in sign],
            "signoff_glob_compat": bool(compat),
            "tag": tag["tag"] if tag else None,
            "tag_date": tag["date"] if tag else None,
        })
    return out


def derive_honesty(data):
    v = data["verification"]
    cov = data["results"]["coverage"]
    latest = cov["latest"]
    ctx = {
        "sb_lines": len(read(TB / "uvm/env/ppa_scoreboard.sv").splitlines()),
        "predict_lines": len(read(TB / "uvm/core_agent/ppa_core_seq_item.sv").splitlines()),
        "reg_defs_lines": len(read(TB / "uvm/env/ppa_reg_defs.sv").splitlines()),
        "chk_eq": count_pattern(TB, r"\bchk_eq\b"),
        "uvm_reg": count_pattern(TB, r"\buvm_reg\b"),
        "p_seq": count_pattern(TB, r"\bp_sequencer\b"),
        "override": count_pattern(TB, r"set_(?:type|inst)_override"),
        "constraints": count_pattern(TB, r"^\s*constraint\s+\w+", re.M),
        "urandom": count_pattern(TB, r"\$urandom"),
        "scenario_tests": v["tests"]["scenario"],
        "cg": v["functional_coverage"]["covergroup_count"],
        "cp": v["functional_coverage"]["coverpoint_count"],
        "cross": v["functional_coverage"]["cross_count"],
        "score": fmt_num(latest["score"]) if latest else "N/A",
        "regress_entries": v["regress"]["entries"],
        "unique_tests": v["regress"]["unique_tests"],
    }
    items = []
    for it in HONESTY_ITEMS:
        for a in it["anchors"]:
            if not (ROOT / a).exists():
                fail(f"诚实清单 {it['id']} 的锚点文件不存在: {a}")
        items.append({"id": it["id"], "topic": it["topic"],
                      "status": it["status"].format(**ctx),
                      "alternative": it["alt"].format(**ctx),
                      "cost": it["cost"].format(**ctx),
                      "anchors": it["anchors"]})

    m1 = next((m for m in data["milestones"] if m["id"] == "M1"), None)
    notes = []
    if m1 and m1["signoff"] and not m1["signoff_glob_compat"]:
        f = Path(m1["signoff"][0])
        notes.append(HONESTY_FOOTNOTES[0].format(
            m1_file=f.name, m1_lines=next(r["lines"] for r in data["results"]["reviews"]["entries"]
                                          if r["path"] == m1["signoff"][0])))
    if latest and latest.get("toggle") is not None:
        notes.append(HONESTY_FOOTNOTES[1].format(
            toggle=fmt_num(latest["toggle"]),
            margin=fmt_num(round(latest["toggle"] - COV_THRESHOLD, 2))))
    return {"items": items, "footnotes": notes,
            "note": "语义结论由 rev/arch 定；其中每个数字均由本脚本现算填入，锚点文件存在性已校验"}


# ---------------------------------------------------------------------------
# 图表几何：坐标由本脚本算好，浏览器不算（无 JS / 严格 CSP 下也成立）
# ---------------------------------------------------------------------------

def fmt_num(v):
    if v is None:
        return "N/A"
    if isinstance(v, bool):
        return "是" if v else "否"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


def xy(i, n, val, g, vmin, vmax):
    w, h = g["w"], g["h"]
    span = (n - 1) or 1
    x = g["pad_l"] + i * (w - g["pad_l"] - g["pad_r"]) / span
    y = h - g["pad_b"] - (val - vmin) / (vmax - vmin) * (h - g["pad_t"] - g["pad_b"])
    return round(x, 1), round(y, 1)


def derive_charts(data):
    charts = {}

    # 覆盖率折线：只对 comparable 点连线；不可比点单独出 marker；null 不补 0、不连线
    g = CHART_GEOM["coverage"]
    hist = data["results"]["coverage"]["history"]
    pts = []
    for i, p in enumerate(hist):
        item = {"version": p["version"], "milestone": p["milestone"],
                "comparable": p["comparable"], "score": p["score"], "domain": p["domain"]}
        if p["score"] is not None:
            item["x"], item["y"] = xy(i, len(hist), p["score"], g, g["y_min"], g["y_max"])
        else:
            # SCORE 缺失：只给 x（供 arch 标注缺失点位置），y 置 null，绝不用 0 补位
            item["x"] = xy(i, len(hist), g["y_min"], g, g["y_min"], g["y_max"])[0]
            item["y"] = None
        pts.append(item)
    line = [p for p in pts if p["comparable"] and p["score"] is not None]
    deltas = [{"from": line[i]["version"], "to": line[i + 1]["version"],
               "delta": round(line[i + 1]["score"] - line[i]["score"], 2)}
              for i in range(len(line) - 1)]
    charts["coverage"] = {
        "geom": g, "scale": {"y_min": g["y_min"], "y_max": g["y_max"], "unit": "%"},
        "points": pts,
        "polyline": " ".join(f"{p['x']},{p['y']}" for p in line),
        "threshold_y": round(g["h"] - g["pad_b"] - (COV_THRESHOLD - g["y_min"]) /
                             (g["y_max"] - g["y_min"]) * (g["h"] - g["pad_t"] - g["pad_b"]), 1),
        "deltas": deltas,
        "note": "polyline 只串 comparable 点；M1 点口径不同，须单独 marker + 注解，不得并入折线",
    }

    # 回归柱状：用合并同批后的 series（v0.4.0/v0.4.1 同批不画成两次增长）
    g = CHART_GEOM["regress"]
    ser = data["results"]["regress"]["series"]
    vmax = max(s["total"] for s in ser) or 1
    bars, step = [], (g["w"] - g["pad_l"] - g["pad_r"]) / (len(ser) or 1)
    for i, s in enumerate(ser):
        h = (s["passed"] / vmax) * (g["h"] - g["pad_t"] - g["pad_b"])
        bars.append({"label": "/".join(s["versions"]), "milestones": s["milestones"],
                     "passed": s["passed"], "total": s["total"], "date": s["date"],
                     "x": round(g["pad_l"] + i * step + (step - g["bar_w"]) / 2, 1),
                     "y": round(g["h"] - g["pad_b"] - h, 1),
                     "w": g["bar_w"], "h": round(h, 1)})
    n_missing = len(data["results"]["regress"]["missing_result_summary"])
    charts["regress"] = {
        "geom": g, "scale": {"y_max": vmax}, "bars": bars,
        "note": f"{len(data['results']['regress']['history'])} 条归档记录合并同批后画 {len(ser)} 根柱；"
                f"另有 {n_missing} 个 evidence 目录无归档回归摘要，其轮次不入图"}

    # 验证金字塔
    g = CHART_GEOM["pyramid"]
    vals = [(label, resolve(data, path)) for label, path in PYRAMID_LAYERS]
    nmax = max(v for _, v in vals) or 1
    lay_h = (g["h"] - g["pad_t"]) / len(vals) - g["gap"]
    layers = []
    for i, (label, n) in enumerate(vals):
        w = g["w_max"] * (0.35 + 0.65 * n / nmax)
        layers.append({"label": label, "n": n,
                       "x": round(g["x_center"] - w / 2, 1),
                       "y": round(g["pad_t"] + i * (lay_h + g["gap"]), 1),
                       "w": round(w, 1), "h": round(lay_h, 1)})
    charts["pyramid"] = {"geom": g, "layers": layers,
                         "width_rule": "w = w_max * (0.35 + 0.65 * n / n_max)"}

    # 缺陷分类条形
    g = CHART_GEOM["bugs"]
    bk = data["results"]["bugs"]["by_kind"]
    order = [k for k, _ in BUG_KIND_RULES if k in bk]
    nmax = max(bk.values()) or 1
    charts["bugs"] = {"geom": g, "bars": [
        {"kind": k, "n": bk[k],
         "x": g["pad_l"], "y": g["pad_t"] + i * (g["bar_h"] + g["gap"]),
         "w": round((g["w"] - g["pad_l"] - g["pad_r"]) * bk[k] / nmax, 1), "h": g["bar_h"]}
        for i, k in enumerate(order)]}

    # 架构图标签（框由 arch 画，这里只给文本与落点）
    g = CHART_GEOM["arch"]
    mods = {m["name"]: m for m in data["design"]["modules"]}
    charts["arch"] = {"geom": g, "labels": [
        {"name": n, "x": pos[0], "y": pos[1],
         "lines": mods[n]["lines"], "sva": mods[n]["sva"], "ports": mods[n]["ports"]}
        for n, pos in ARCH_LABEL_POS.items() if n in mods],
        "hierarchy": data["design"]["hierarchy"]}
    return charts


# ---------------------------------------------------------------------------
# 顶层装配
# ---------------------------------------------------------------------------

def resolve(data, path):
    """按 a.b[0].c 形式取值；取不到即 FAIL（provenance/图表引用的路径必须都存在）。"""
    cur = data
    for token in path.split("."):
        m = re.fullmatch(r"(\w+)((?:\[\d+\])*)", token)
        if not m:
            fail(f"字段路径非法: {path}")
        key, idx = m.group(1), m.group(2)
        if not isinstance(cur, dict) or key not in cur:
            fail(f"字段路径解析不到: {path}（断在 {key}）")
        cur = cur[key]
        for i in re.findall(r"\[(\d+)\]", idx):
            if not isinstance(cur, list) or int(i) >= len(cur):
                fail(f"字段路径下标越界: {path}")
            cur = cur[int(i)]
    return cur


def collect():
    tp_rows = parse_table(TESTPLAN)
    fm_rows = parse_table(FEATURE_MATRIX)
    if not tp_rows or not fm_rows:
        fail("testplan.md / feature-matrix.md 解析不到表行")

    project = collect_project()
    design = collect_design(fm_rows)
    verification = collect_verification(tp_rows, design["rtl_lines"])
    bugs = collect_bugs()
    regress_hist = collect_regress_history()
    cov_hist = collect_coverage_history()

    data = {
        "meta": {
            "generated_by": "scripts/report.py",
            "generated_on": str(date.today()),
            "discipline": "所有数字现算于真值源；解析不到即报错退出，不给默认值",
            # rev 审计用：区分"脚本内置的解析规则"与"从文件读出的数字"。
            # 下面列出的全部是规则（去哪读、怎么读、怎么排版），其中不含任何成果数字。
            "builtin_rules": {
                "COV_ANCHORS": {v: {k: (str(x) if not isinstance(x, (bool, tuple)) else x)
                                    for k, x in a.items()} for v, a in COV_ANCHORS.items()},
                "METRIC_ALIAS": METRIC_ALIAS,
                "COV_THRESHOLD": COV_THRESHOLD,
                "COV_THRESHOLD_src": "spec §0 适配 7（六类 ≥90% 合格）——判据来自 spec，非实测值",
                "BUG_KIND_RULES": [k for k, _ in BUG_KIND_RULES],
                "BUG_KIND_RULES_strict": "归不了类即 FAIL（会印错 spec/infra/rtl 分布）",
                "REVIEW_KIND_RULES": [{"kind": k, "keyword": p} for k, p in REVIEW_KIND_RULES],
                "REVIEW_KIND_FALLBACK": REVIEW_KIND_FALLBACK,
                "REVIEW_KIND_RULES_strict": "开放分类：归不了类兜底 other + warn，不 FAIL",
                "VOLATILE_JSON_PATHS": VOLATILE_JSON_PATHS,
                "TRUTH_SOURCE_GLOBS": TRUTH_SOURCE_GLOBS,
                "SITE_ANCHOR_PATTERNS": SITE_ANCHOR_PATTERNS,
                "MILESTONE_LABS": MILESTONE_LABS,
                "MILESTONE_LABS_src": "CLAUDE.md §4.1（M1=Lab1 … M4=Lab4）",
                "CHART_GEOM": CHART_GEOM,
                "PYRAMID_LAYERS": [l for l, _ in PYRAMID_LAYERS],
                "ARCH_LABEL_POS": {k: list(v) for k, v in ARCH_LABEL_POS.items()},
                "HONESTY_topics": [h["topic"] for h in HONESTY_ITEMS],
                "note": "以上均为解析/排版规则；展示材料里的每个数字都不来自此处，"
                        "而来自 provenance[] 指向的真值源文件",
            },
            "warnings": WARNINGS,
        },
        "project": project,
        "design": design,
        "verification": verification,
        "results": {
            "regress": regress_hist,
            "coverage": cov_hist,
            "bugs": bugs,
            "waivers": collect_waivers(),
            "reviews": collect_reviews(),
            "evidence": collect_evidence_inventory(),
        },
        "process": collect_process(bugs),
        "source_markers": scan_source_markers(project["milestone"]),
    }
    data["milestones"] = derive_milestones(data)
    data["honesty"] = derive_honesty(data)
    data["charts"] = derive_charts(data)
    data["kpi"] = derive_kpi(data)
    data["provenance"] = derive_provenance(data)
    data["meta"]["warnings"] = list(WARNINGS)
    return data


# KPI 卡片：(展示名, 字段路径, 单位)。值一律 resolve 现算，脚本内不写死任何数字
KPI_SPEC = [
    ("六类综合覆盖率", "results.coverage.latest.score", "%"),
    ("最新回归通过", "results.regress.latest.text", ""),
    ("testplan 场景", "verification.testplan.passed", " ✅"),
    ("SVA 断言", "verification.sva.total", " 条"),
    ("RTL 代码", "design.rtl_lines", " 行"),
    ("TB 代码", "verification.tb_lines", " 行"),
    ("缺陷闭环", "results.bugs.total", " 条"),
    ("lint 豁免", "results.waivers.total", " 条"),
    ("rev 审查记录", "results.reviews.count", " 份"),
    ("spec 修订", "project.spec_revision_count", " 次"),
]


def derive_kpi(data):
    out = []
    for label, path, unit in KPI_SPEC:
        p = path.replace("[-1]", f"[{len(resolve(data, path.split('[')[0])) - 1}]") \
            if "[-1]" in path else path
        out.append({"label": label, "path": p, "value": resolve(data, p),
                    "text": fmt_num(resolve(data, p)), "unit": unit})
    return out


# provenance：每个会出现在展示材料里的数字 → 出处文件 + 定位规则。
# rev 按这张表逐条核，无需通读脚本。
PROVENANCE_SPEC = [
    ("project.version", "version.json", "docs.py read_version()"),
    ("project.spec_sha256", "doc/spec.sha256", "现算 spec.md sha256 并与钉住值比对，不符即 FAIL"),
    ("project.spec_revision_count", "doc/spec.md", "'## 修改记录' 章节首表数据行数（与 docs.py count_mod_records 交叉校验）"),
    ("project.spec_closed_loop_count", "doc/spec.md",
     "修改记录中措辞含 'rev 裁决' 或含 BUG-\\d{3} 的条目数（r3 只提到 'lint 门禁' 不算裁决，已排除）"),
    ("project.csr_count", "doc/spec.md", "§5.2 章节切片内表格中'偏移'列非空的行数"),
    ("design.rtl_lines", "rtl/*.sv", "各文件 splitlines() 求和"),
    ("design.rtl_sva", "rtl/*.sv", "正则 \\bassert\\s+property\\b 命中数求和（DE 内部断言）"),
    ("design.module_count", "rtl/*.sv", "文件数"),
    ("design.fsm.count", "rtl/packet_proc_core.sv", "typedef enum {...} 内按逗号切分的枚举项数"),
    ("design.feature_count", "doc/feature-matrix.md", "docs.py parse_table 行数"),
    ("verification.tb_files", "tb/**/*.sv", "rglob 文件数"),
    ("verification.tb_lines", "tb/**/*.sv", "各文件 splitlines() 求和"),
    ("verification.rtl_tb_ratio", "rtl/ + tb/", "tb_lines / rtl_lines，保留 2 位"),
    ("verification.sva.de", "rtl/*.sv", "assert property 命中数"),
    ("verification.sva.dv", "tb/sva/*.sv", "assert property 命中数"),
    ("verification.sva.total", "rtl/ + tb/sva/", "de + dv"),
    ("verification.tests.scenario", "tb/uvm/test/*.sv", "排除 *base_test / *_seq_lib / *_pkg 后的文件数"),
    ("verification.testplan.rows", "doc/testplan.md", "docs.py parse_table 行数"),
    ("verification.testplan.passed", "doc/testplan.md", "状态列含 ✅ 的行数"),
    ("verification.regress.entries", "sim/regress/regress.list", "非注释非空行数（regress.py 同款规则）"),
    ("verification.regress.unique_tests", "sim/regress/regress.list", "去重后的测试名个数"),
    ("verification.functional_coverage.covergroup_count", "tb/uvm/env/ppa_cov.sv", "^\\s*covergroup\\s+(\\w+) 命中数"),
    ("results.regress.points", "doc/evidence/v*/result_summary.txt", "含该文件的目录数；首行 通过=N/N 与 ^PASS 行数交叉校验"),
    ("results.regress.latest.text", "doc/evidence/v0.4.1/result_summary.txt",
     "最新一批归档回归（同日期同结果的相邻版本已合并为一批）的 通过/总数"),
    ("results.coverage.points", "doc/evidence/v*/coverage-summary*.md", "COV_ANCHORS 逐版本锚点定位章节+值列后取数"),
    ("results.coverage.latest.score", "doc/evidence/v0.4.0/coverage-summary.md",
     "最新 comparable=true 的覆盖率点的 SCORE 行（tb_top 域，取'闭环(v0.4.0)'列）"),
    ("results.bugs.total", "doc/bugs.md + doc/bugs-archive.md", "两表 parse_table 行数之和"),
    ("results.waivers.total", "doc/lint-waivers.md + 归档", "两表 parse_table 行数之和"),
    ("results.waivers.sites_total", "doc/lint-waivers.md + 归档", "对象列 <文件>:<行号表> 逐条求和，与自述'N 处'交叉校验"),
    ("results.reviews.count", "doc/evidence/v*/rev-*.md + review*.md", "glob 去重文件数"),
    ("results.reviews.lines", "doc/evidence/v*/rev-*.md + review*.md", "各文件行数求和"),
    ("results.evidence.log_files", "doc/evidence/v*/*.log", "后缀为 .log 的文件数"),
    ("process.commits", "git", "git rev-list --count HEAD（不可用则 null）"),
]


def derive_provenance(data):
    # 两个"最新值"字段的出处随归档推进而变，用现算 src 覆盖静态登记，避免写死版本号
    overrides = {
        "results.regress.latest.text": ", ".join(data["results"]["regress"]["latest"]["src"]),
        "results.coverage.latest.score": (data["results"]["coverage"]["latest"] or {}).get("src", ""),
    }
    out = []
    for path, source, rule in PROVENANCE_SPEC:
        out.append({"path": path, "value": resolve(data, path),
                    "text": fmt_num(resolve(data, path)),
                    "source": overrides.get(path) or source, "rule": rule})
    # 历史序列的每个点自带 src，单独列出，保证"任一数字都能指到文件"
    for p in data["results"]["coverage"]["history"]:
        out.append({"path": f"results.coverage.history[{p['version']}]",
                    "value": p["score"], "text": fmt_num(p["score"]),
                    "source": p["src"],
                    "rule": f"章节 {COV_ANCHORS[p['version']]['section']} / 值列 {p['value_col']}（{p['col_rule']}）"})
    for h in data["results"]["regress"]["history"]:
        out.append({"path": f"results.regress.history[{h['version']}]",
                    "value": h["passed"], "text": f"{h['passed']}/{h['total']}",
                    "source": h["src"], "rule": "首行 通过=N/N，与 ^PASS 行数交叉校验"})
    return out


# ---------------------------------------------------------------------------
# 生成区内容（HTML / README）
# ---------------------------------------------------------------------------

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def metric_span(data, path, unit=""):
    return f'<span data-metric="{path}">{esc(fmt_num(resolve(data, path)))}</span>{esc(unit)}'


def gen_kpi_row(data):
    out = []
    for k in data["kpi"]:
        out.append(f'  <div class="kpi"><span class="kpi-label">{esc(k["label"])}</span>'
                   f'<span class="kpi-value">{metric_span(data, k["path"], k["unit"])}</span></div>')
    return "\n".join(out)


def gen_chart_arch_labels(data):
    c = data["charts"]["arch"]
    out = [f'  <!-- viewBox 建议 0 0 {c["geom"]["w"]} {c["geom"]["h"]}；框线/连线由 arch 手绘 -->']
    for l in c["labels"]:
        out.append(f'  <text class="arch-name" x="{l["x"]}" y="{l["y"]}" '
                   f'text-anchor="middle">{esc(l["name"])}</text>')
        out.append(f'  <text class="arch-meta" x="{l["x"]}" y="{l["y"] + 16}" '
                   f'text-anchor="middle">{l["lines"]} 行 · SVA {l["sva"]} · 端口 {l["ports"]}</text>')
    for h in c["hierarchy"]:
        out.append(f'  <!-- 例化: ppa_top.{h["instance"]} = {h["module"]} -->')
    return "\n".join(out)


def gen_chart_pyramid(data):
    c = data["charts"]["pyramid"]
    out = [f'  <!-- 层宽规则 {c["width_rule"]}；viewBox 建议 0 0 {c["geom"]["w"]} {c["geom"]["h"]} -->']
    for l in c["layers"]:
        out.append(f'  <rect class="pyr" x="{l["x"]}" y="{l["y"]}" width="{l["w"]}" '
                   f'height="{l["h"]}" rx="4"/>')
        out.append(f'  <text class="pyr-label" x="{c["geom"]["x_center"]}" '
                   f'y="{round(l["y"] + l["h"] / 2 + 5, 1)}" text-anchor="middle">'
                   f'{esc(l["label"])} · {l["n"]}</text>')
    return "\n".join(out)


def gen_chart_coverage(data):
    c = data["charts"]["coverage"]
    g = c["geom"]
    out = [f'  <!-- y 轴刻度 {g["y_min"]}..{g["y_max"]}%（轴/图例由 arch 手绘）；'
           f'viewBox 建议 0 0 {g["w"]} {g["h"]} -->',
           f'  <line class="cov-threshold" x1="{g["pad_l"]}" y1="{c["threshold_y"]}" '
           f'x2="{g["w"] - g["pad_r"]}" y2="{c["threshold_y"]}"/>',
           f'  <polyline class="cov-line" fill="none" points="{c["polyline"]}"/>']
    for p in c["points"]:
        if p["y"] is None:
            out.append(f'  <!-- {p["version"]} SCORE 缺失（该版本无 SCORE 行），不绘点、不补 0 -->')
            continue
        cls = "cov-dot" if p["comparable"] else "cov-dot cov-dot-alt"
        out.append(f'  <circle class="{cls}" cx="{p["x"]}" cy="{p["y"]}" r="4">'
                   f'<title>{esc(p["version"])} {esc(p["milestone"])} '
                   f'{fmt_num(p["score"])}% · 域={esc(p["domain"])}</title></circle>')
        out.append(f'  <text class="cov-val" x="{p["x"]}" y="{round(p["y"] - 10, 1)}" '
                   f'text-anchor="middle">{fmt_num(p["score"])}</text>')
        out.append(f'  <text class="cov-x" x="{p["x"]}" y="{g["h"] - g["pad_b"] + 20}" '
                   f'text-anchor="middle">{esc(p["milestone"])} {esc(p["version"])}</text>')
    for d in c["deltas"]:
        out.append(f'  <!-- Δ {d["from"]}→{d["to"]}: {d["delta"]:+} pt -->')
    return "\n".join(out)


def gen_chart_regress(data):
    c = data["charts"]["regress"]
    g = c["geom"]
    out = [f'  <!-- viewBox 建议 0 0 {g["w"]} {g["h"]}；y 轴 0..{c["scale"]["y_max"]} 条 -->']
    for b in c["bars"]:
        out.append(f'  <rect class="reg-bar" x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" '
                   f'height="{b["h"]}" rx="3"><title>{esc(b["label"])} {b["passed"]}/{b["total"]} '
                   f'@{esc(b["date"])}</title></rect>')
        out.append(f'  <text class="reg-val" x="{round(b["x"] + b["w"] / 2, 1)}" '
                   f'y="{round(b["y"] - 8, 1)}" text-anchor="middle">'
                   f'{b["passed"]}/{b["total"]}</text>')
        out.append(f'  <text class="reg-x" x="{round(b["x"] + b["w"] / 2, 1)}" '
                   f'y="{g["h"] - g["pad_b"] + 20}" text-anchor="middle">'
                   f'{esc("/".join(b["milestones"]))}</text>')
    return "\n".join(out)


def gen_chart_bugs(data):
    c = data["charts"]["bugs"]
    out = [f'  <!-- viewBox 建议 0 0 {c["geom"]["w"]} {c["geom"]["h"]} -->']
    for b in c["bars"]:
        out.append(f'  <text class="bug-label" x="{b["x"] - 8}" y="{b["y"] + 20}" '
                   f'text-anchor="end">{esc(b["kind"])}</text>')
        out.append(f'  <rect class="bug-bar bug-{esc(b["kind"])}" x="{b["x"]}" y="{b["y"]}" '
                   f'width="{b["w"]}" height="{b["h"]}" rx="3"/>')
        out.append(f'  <text class="bug-val" x="{round(b["x"] + b["w"] + 8, 1)}" '
                   f'y="{b["y"] + 20}">{b["n"]}</text>')
    return "\n".join(out)


def gen_table_modules(data):
    rows = ["  <tr><th>模块</th><th>行数</th><th>端口</th><th>内部断言</th><th>里程碑</th></tr>"]
    ms_of = {}
    for f in data["design"]["features"]:
        ms_of.setdefault(f["module"], f["milestone"])
    for m in data["design"]["modules"]:
        rows.append(f'  <tr><td><code>{esc(m["file"])}</code></td><td>{m["lines"]}</td>'
                    f'<td>{m["ports"]}</td><td>{m["sva"]}</td>'
                    f'<td>{esc(ms_of.get(m["name"], "-"))}</td></tr>')
    return "\n".join(rows)


def gen_table_testplan(data):
    rows = ["  <tr><th>ID</th><th>里程碑</th><th>场景</th><th>状态</th><th>证据</th></tr>"]
    for e in data["verification"]["testplan"]["entries"]:
        rows.append(f'  <tr><td>{esc(e["id"])}</td><td>{esc(e["milestone"])}</td>'
                    f'<td>{esc(e["scenario"])}</td><td>{esc(e["status"])}</td>'
                    f'<td><code>{esc(e["evidence"])}</code></td></tr>')
    return "\n".join(rows)


def gen_table_evidence(data):
    rows = ["  <tr><th>版本</th><th>里程碑</th><th>文件</th><th>仿真 log</th>"
            "<th>回归摘要</th><th>覆盖率摘录</th><th>rev 记录</th></tr>"]
    for d in data["results"]["evidence"]["detail"]:
        rows.append(f'  <tr><td>{esc(d["version"])}</td><td>{esc(d["milestone"])}</td>'
                    f'<td>{d["files"]}</td><td>{d["logs"]}</td>'
                    f'<td>{"✅" if d["has_result_summary"] else "—"}</td>'
                    f'<td>{"✅" if d["has_coverage_summary"] else "—"}</td>'
                    f'<td>{d["reviews"]}</td></tr>')
    return "\n".join(rows)


def gen_footer_stamp(data):
    """确定性落款（F1）：只用仓库内容派生的量——版本、spec 钉住 sha、真值源快照摘要。
    **刻意不含** git HEAD / 提交总数 / 生成日期，否则提交本 HTML 之后 CI 立刻判过期。"""
    p = data["project"]
    return (f'  <p class="stamp">版本 {esc(p["version"])}（{esc(p["milestone"])}） · '
            f'spec sha256 <code>{esc(p["spec_sha256"][:12])}…</code>（已钉住） · '
            f'真值源快照 <code>{esc(p["truth_digest"][:12])}…</code> · '
            f'由 <code>scripts/report.py --inject</code> 生成，禁止手改'
            f'（落款不含 git HEAD/提交数/生成日期：它们随每次提交变动，'
            f'内嵌会使生成区新鲜度门禁恒假）</p>')


def stable_view(data):
    """data-json 入库前剔除运行期易变子树（F1）。被剔除的字段不是不可信，
    而是"随每次提交/每天变化"，内嵌进仓库就会让 --check 第 5 项永久判过期。"""
    out = json.loads(json.dumps(data, ensure_ascii=False))
    for path in VOLATILE_JSON_PATHS:
        cur, *rest = path.split(".")
        if not rest:
            out.pop(cur, None)
        elif isinstance(out.get(cur), dict):
            out[cur].pop(rest[0], None)
    for m in out.get("milestones", []):
        for k in VOLATILE_MILESTONE_KEYS:
            m.pop(k, None)
    # provenance 里也有指向易变字段的条目（如 process.commits），同样剔除，否则
    # "提交一次 → commits+1 → data-json 变化 → 判过期"的链条依然成立（实测踩到）
    dropped = [p["path"] for p in out.get("provenance", [])
               if any(p["path"] == v or p["path"].startswith(v + ".")
                      for v in VOLATILE_JSON_PATHS)]
    out["provenance"] = [p for p in out.get("provenance", []) if p["path"] not in dropped]
    out["_excluded_volatile"] = {
        "paths": VOLATILE_JSON_PATHS + [f"milestones[].{k}" for k in VOLATILE_MILESTONE_KEYS],
        "provenance_paths": dropped,
        "why": "git 派生量与生成日期随每次提交/每天变化，内嵌入库会让生成区新鲜度门禁恒假"
               "（提交展示材料这一动作本身就会打挂 CI）；需要实时值请跑 make report-json（不落盘）",
    }
    return out


def gen_data_json(data):
    return ('  <script type="application/json" id="report-data">\n'
            + json.dumps(stable_view(data), ensure_ascii=False, indent=1)
            + "\n  </script>")


def gen_readme_kpi(data):
    lines = ["| 指标 | 数值 | 出处 |", "| --- | --- | --- |"]
    prov = {p["path"]: p["source"] for p in data["provenance"]}
    for k in data["kpi"]:
        src = prov.get(k["path"], "scripts/report.py --json 现算")
        lines.append(f'| {k["label"]} | {k["text"]}{k["unit"]} | `{src}` |')
    return "\n".join(lines)


def gen_readme_milestones(data):
    lines = ["| 里程碑 | Lab | 模块 | 场景 | 回归 | 六类综合 | 签核记录 |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for m in data["milestones"]:
        cov = fmt_num(m["coverage_score"])
        if m["coverage_score"] is not None and not m["coverage_comparable"]:
            cov += f'（{m["coverage_domain"]}，口径不同）'
        elif m["coverage_score"] is None and m["coverage_src"]:
            cov = f'N/A（{m["coverage_domain"]}，该版本无 SCORE 行）'
        sign = "、".join(f"`{s}`" for s in m["signoff"]) or "—"
        lines.append(f'| {m["id"]} | {m["lab"] or "—"} | {"、".join(m["modules"])} | '
                     f'{m["scenarios_pass"]}/{m["scenarios"]} ✅ | {m["regress"] or "—"} | '
                     f'{cov} | {sign} |')
    return "\n".join(lines)


GENERATORS = {
    "kpi-row": gen_kpi_row,
    "chart-arch-labels": gen_chart_arch_labels,
    "chart-pyramid": gen_chart_pyramid,
    "chart-coverage": gen_chart_coverage,
    "chart-regress": gen_chart_regress,
    "chart-bugs": gen_chart_bugs,
    "table-modules": gen_table_modules,
    "table-testplan": gen_table_testplan,
    "table-evidence": gen_table_evidence,
    "footer-stamp": gen_footer_stamp,
    "data-json": gen_data_json,
    "readme-kpi": gen_readme_kpi,
    "readme-milestones": gen_readme_milestones,
}
assert set(GENERATORS) == set(GEN_KEYS), "GENERATORS 与 GEN_KEYS 不一致"


# ---------------------------------------------------------------------------
# 生成区注入 / 新鲜度校验
# ---------------------------------------------------------------------------

def gen_re(key):
    return re.compile(r"(<!--\s*GEN:" + re.escape(key) + r"\b[^>]*-->)(.*?)"
                      r"(<!--\s*/GEN:" + re.escape(key) + r"\s*-->)", re.S)


def scan_gen_keys(text):
    return [k for k in GEN_KEYS if gen_re(k).search(text)]


def devolatile(text):
    for pat, repl in VOLATILE_TEXT_PATTERNS:
        text = re.sub(pat, repl, text)
    return text


def compare_gen(old, new):
    """生成区内容三态比较（F1 的 (a) 兜底层）：
    same          原文一致；
    volatile-only 原文不一致，但归一化掉 git 短 sha 后一致 → 不判过期，但 warn 外显；
    different     实质不一致 → 判过期。"""
    if old.strip("\n") == new:
        return "same"
    if devolatile(old.strip("\n")) == devolatile(new):
        return "volatile-only"
    return "different"


def inject_file(path, data, dry_run=False):
    """注入/比对生成区。文件不存在或无生成区 → warn 并跳过（返回 None）。
    仅当实质变化才改写文件——"只差易变量"不重写，避免 make report-sync 每跑一次就脏一次。"""
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        warn(f"{path} 不存在，跳过注入（R3 尚未交付展示材料时属正常）")
        return None
    text = p.read_text(encoding="utf-8")
    keys = scan_gen_keys(text)
    if not keys:
        warn(f"{rel(p)} 中没有任何 report.py 认识的生成区标记，跳过"
             f"（可用 key: {', '.join(GEN_KEYS)}）")
        return None
    changed, same, volatile, new_text = [], [], [], text
    for k in keys:
        body = GENERATORS[k](data)
        verdict = compare_gen(gen_re(k).search(new_text).group(2), body)
        if verdict == "same":
            same.append(k)
            continue
        if verdict == "volatile-only":
            volatile.append(k)
            warn(f"{rel(p)} 生成区 {k} 与现算内容仅差 git 短 sha，按未过期处理、不重写"
                 "（若确需刷新，先修掉泄漏易变量的生成器）")
            continue
        changed.append(k)
        new_text = gen_re(k).sub(
            lambda mm: mm.group(1) + "\n" + body + "\n" + mm.group(3), new_text, count=1)
    if changed and not dry_run:
        p.write_text(new_text, encoding="utf-8")
    return {"file": rel(p), "changed": changed, "same": same,
            "volatile_only": volatile, "keys": keys}


RE_DATA_METRIC = re.compile(r'data-metric="([^"]+)"[^>]*>([^<]*)<')


def check_static_metrics(path, data):
    """HTML 中每个 data-metric 元素的静态文本必须等于 JSON 对应值（无 JS 时页面也是对的）。"""
    p = Path(path) if Path(path).is_absolute() else ROOT / path
    if not p.exists():
        return None, f"{path} 不存在，跳过静态数字比对"
    errs = []
    n = 0
    for mpath, text in RE_DATA_METRIC.findall(p.read_text(encoding="utf-8")):
        n += 1
        want = fmt_num(resolve(data, mpath))
        if text.strip() != want:
            errs.append(f"{rel(p)} data-metric={mpath} 页面文本 {text.strip()!r} ≠ 现算值 {want!r}")
    return (errs, f"{rel(p)} 共比对 {n} 个 data-metric") if n else (
        errs, f"{rel(p)} 无 data-metric 元素，跳过静态数字比对")


# ---------------------------------------------------------------------------
# 输出：--summary / --md
# ---------------------------------------------------------------------------

def cmd_summary(data):
    p, v, r = data["project"], data["verification"], data["results"]
    cov = r["coverage"]["latest"]
    print("== PPA-Lite 成果数据（scripts/report.py 现算，无手写数字）==")
    print(f"版本 {p['version']}（{p['milestone']}） · spec {p['spec_lines']} 行 / "
          f"修订 {p['spec_revision_count']} 次（闭环 {p['spec_closed_loop_count']}："
          f"{p['spec_closed_loop_via_bugs']} 条走 bugs.md、{p['spec_closed_loop_via_gate']} 条走 rev 门禁仲裁）")
    print(f"spec sha256 {p['spec_sha256'][:16]}… 已钉住并现算校验通过")
    print("\n-- 设计 --")
    for m in data["design"]["modules"]:
        print(f"  {m['name']:<20} {m['lines']:>4} 行  端口 {m['ports']:>2}  内部断言 {m['sva']:>2}")
    print(f"  合计 {data['design']['rtl_lines']} 行 / 内部断言 {data['design']['rtl_sva']} 条 / "
          f"CSR {p['csr_count']} 个寄存器 / FSM {data['design']['fsm']['count']} 态")
    print("\n-- 验证 --")
    print(f"  tb {v['tb_files']} 个文件 / {v['tb_lines']} 行（TB:RTL = {v['rtl_tb_ratio']}:1）")
    print(f"  SVA {v['sva']['total']} 条 = DE {v['sva']['de']}（rtl/）+ DV {v['sva']['dv']}（tb/sva/）")
    print(f"  UVM 测试类 {v['tests']['scenario']} 个场景 + {v['tests']['base']} 基类 + "
          f"{v['tests']['seq_lib_count']} 序列库")
    print(f"  testplan {v['testplan']['passed']}/{v['testplan']['rows']} ✅  "
          f"回归 {v['regress']['entries']} 条 / {v['regress']['unique_tests']} 唯一测试")
    sm = data["source_markers"]
    print(f"  源码注释守卫（{'/'.join(sm['scanned_dirs'])}，{sm['files']} 文件 / "
          f"{sm['comment_lines']} 行注释）: 过期里程碑承诺 {sm['stale_count']} 处 / "
          f"登记豁免 {sm['suppressed_count']} 处 / 在途承诺 {sm['open_milestone_count']} 处 / "
          f"开放式留白 {sm['open_ended_count']} 处")
    print("\n-- 结果 --")
    print(f"  回归历史（{r['regress']['points']} 次归档）: " +
          "  ".join(f"{h['milestone']}/{h['version']} {h['passed']}/{h['total']}"
                    for h in r["regress"]["history"]))
    print(f"  覆盖率历史（{r['coverage']['points']} 次测量）:")
    for c in r["coverage"]["history"]:
        flag = "" if c["comparable"] else "  ← 口径不同，不可同轴比较"
        print(f"    {c['milestone']}/{c['version']} SCORE={fmt_num(c['score'])} "
              f"[{'/'.join(f'{m}={fmt_num(c[m])}' for m in SIX_METRICS)}] 域={c['domain']}{flag}")
    if cov:
        print(f"  最新可比水位: {fmt_num(cov['score'])}%（{cov['version']}，域 {cov['domain']}，"
              f"六类达标 {len(cov['six_pass'])}/{len(cov['six_measured'])}）")
    multi = ", ".join("{} ({} 轮)".format(b["id"], b["rounds"]) for b in r["bugs"]["multi_round"])
    print(f"  缺陷 {r['bugs']['total']} 条 " +
          "（" + " / ".join(f"{k} {n}" for k, n in sorted(r["bugs"]["by_kind"].items())) + "）" +
          f"；多轮修复: {multi or '无'}")
    print(f"  lint 豁免 {r['waivers']['total']} 条 / {r['waivers']['sites_total']} 处 " +
          "（" + " / ".join(f"{k} {n}" for k, n in sorted(r["waivers"]["by_category"].items())) + "）" +
          f"；rev 复核 {r['waivers']['reviewed']}/{r['waivers']['total']}")
    print(f"  rev 审查记录 {r['reviews']['count']} 份 / {r['reviews']['lines']} 行 " +
          "（" + " / ".join(f"{k} {n}" for k, n in sorted(r["reviews"]["by_kind"].items())) + "）")
    print(f"  证据 {r['evidence']['dirs']} 个版本目录 / {r['evidence']['total_files']} 个文件"
          f"（仿真 log {r['evidence']['log_files']}、回归摘要 {r['evidence']['result_summaries']}、"
          f"覆盖率摘录 {r['evidence']['coverage_summaries']}）")
    g = data["process"]
    if g["available"]:
        print(f"\n-- 过程 --\n  提交 {g['commits']} 次 / tag {g['tag_count']} 个 / "
              f"{g['date_range']['first']} → {g['date_range']['last']} / HEAD {g['head']}")
    else:
        print("\n-- 过程 --\n  git 元数据不可用（已降级为 null）")
    if WARNINGS:
        print(f"\n[{len(WARNINGS)} 条 warn，见 stderr]")


def md_kpi(data):
    return gen_readme_kpi(data)


def md_milestones(data):
    return gen_readme_milestones(data)


def md_honesty(data):
    h = data["honesty"]
    out = ["| # | 主题 | 现状 | 替代方案 | 代价 |", "| --- | --- | --- | --- | --- |"]
    for it in h["items"]:
        out.append(f'| {it["id"]} | {it["topic"]} | {it["status"]} | {it["alternative"]} | {it["cost"]} |')
    if h["footnotes"]:
        out.append("")
        out += [f"{i}. {t}" for i, t in enumerate(h["footnotes"], 1)]
    return "\n".join(out)


def md_evidence_index(data):
    out = ["| 版本 | 里程碑 | 类型 | 文件 | 说明 |", "| --- | --- | --- | --- | --- |"]
    tp = {e["evidence"]: e for e in data["verification"]["testplan"]["entries"] if e["evidence"]}
    bug = {b["evidence"]: b for b in data["results"]["bugs"]["entries"] if b["evidence"]}
    rev = {r["path"]: r for r in data["results"]["reviews"]["entries"]}
    for d in data["results"]["evidence"]["detail"]:
        for name in d["names"]:
            path = f"doc/evidence/{d['version']}/{name}"
            if path in tp:
                kind, desc = "场景证据", f'{tp[path]["id"]} {tp[path]["scenario"]}'
            elif path in bug:
                kind, desc = "缺陷复验", f'{bug[path]["id"]} 关单'
            elif path in rev:
                kind, desc = f'rev/{rev[path]["kind"]}', rev[path]["title"]
            elif name == "result_summary.txt":
                h = next((x for x in data["results"]["regress"]["history"]
                          if x["version"] == d["version"]), None)
                kind, desc = "回归摘要", f'{h["passed"]}/{h["total"]} @{h["date"]}' if h else ""
            elif name.startswith("coverage-summary"):
                c = next((x for x in data["results"]["coverage"]["history"]
                          if x["version"] == d["version"]), None)
                kind = "覆盖率摘录"
                desc = f'SCORE={fmt_num(c["score"])} 域={c["domain"]}' if c else ""
            elif name.startswith("coverage-"):
                kind, desc = "覆盖率过滤/缺口", ""
            elif name.endswith(".log"):
                kind, desc = "仿真 log 摘录（未被引用）", ""
            else:
                kind, desc = "其他", ""
            out.append(f'| {d["version"]} | {d["milestone"]} | {kind} | `{path}` | {desc} |')
    return "\n".join(out)


def md_data_baseline(data):
    out = ["| 字段路径 | 数值 | 出处 | 定位规则 |", "| --- | --- | --- | --- |"]
    for p in data["provenance"]:
        out.append(f'| `{p["path"]}` | {p["text"]} | `{p["source"]}` | {p["rule"]} |')
    out.append("")
    out.append("> 以上每个数字均由 `scripts/report.py` 现算；讲稿/材料引用时以本表为唯一基线。")
    out.append("> 内置的是解析规则（COV_ANCHORS 锚点表、分类关键字表、图表几何常量），不是数字。")
    return "\n".join(out)


MD_FRAGMENTS = {"kpi": md_kpi, "milestones": md_milestones, "honesty": md_honesty,
                "evidence-index": md_evidence_index, "data-baseline": md_data_baseline}


# ---------------------------------------------------------------------------
# --check：八项校验（git 字段只 warn 不 error；目标文件不存在时 5/6 跳过并 warn；
#           第 8 项为 BUG-018 新增的 sva_baseline.json floor⇄changelog 留痕校验）
# ---------------------------------------------------------------------------

# 注入与校验共用同一份目标清单（F2）：分成两份必然漂移——rev 审查发现 report-sync 只注入
# 前两个而 --check 检查三个，讲稿"检查得到、同步不到"。--inject 不带参数即取本清单。
TARGETS = ["doc/report.html", "README.md", "doc/presentation/defense.md"]


def cmd_check(data):
    errors, notes = [], []

    # 1. spec sha256：**在此处重算一次**，不复述 collect() 的结论（F4）。
    #    BUG-011 的教训是"看起来在校验、其实恒真"，故这一项必须是本函数自己的断言。
    actual = hashlib.sha256(SPEC.read_bytes()).hexdigest()
    pinned = read(SPEC_SHA).strip()
    if actual != pinned:
        errors.append(f"doc/spec.md 现算 sha256 {actual[:16]}… ≠ 钉住值 {pinned[:16]}…")
    notes.append(f"[1/8] spec.md sha256 现算比对（本函数独立重算）: "
                 f"{'一致' if actual == pinned else '不一致'} {actual[:16]}…")

    # 2. coverage-summary 的 N/N PASS ⇄ 同目录 result_summary
    errs, ns = cov_pass_crosscheck(data["results"]["coverage"]["history"],
                                   data["results"]["regress"]["history"])
    errors += errs
    for n in ns:
        warn(n)
    notes.append(f"[2/8] 覆盖率摘录 ⇄ 回归摘要 交叉校验：{len(data['results']['coverage']['history'])} 份，"
                 f"{len(errs)} 处不符，{len(ns)} 处降级 warn")

    # 3. regress.list 条目数 == 最新 result_summary 结果行数
    n_list = data["verification"]["regress"]["entries"]
    latest = data["results"]["regress"]["latest"]
    if n_list != latest["total"]:
        errors.append(f"regress.list 条目 {n_list} ≠ 最新回归摘要 "
                      f"{'/'.join(latest['versions'])} 的结果行数 {latest['total']}"
                      "——回归列表改过但未重跑归档，或摘要过期")
    notes.append(f"[3/8] regress.list {n_list} 条 == 最新回归摘要 {latest['total']} 条结果行")

    # 4. 漏点守卫：**在此处重扫目录**，不复述 collect() 的结论（F4）
    have, missing = [], []
    for d in evidence_dirs():
        if list(d.glob("coverage-summary*.md")):
            have.append(d.name)
            if d.name not in COV_ANCHORS:
                missing.append(d.name)
    if missing:
        errors.append(f"以下目录有覆盖率摘录但 COV_ANCHORS 未登记解析规则: {', '.join(missing)}")
    if len(have) != data["results"]["coverage"]["points"]:
        errors.append(f"覆盖率摘录目录数 {len(have)} ≠ 已解析的覆盖率点数 "
                      f"{data['results']['coverage']['points']}——有摘录被静默漏读")
    notes.append(f"[4/8] COV_ANCHORS 漏点守卫（本函数独立重扫）: {len(have)} 份摘录，"
                 f"{len(missing)} 份缺锚点")

    # 5. 生成区新鲜度
    fresh, skipped = [], []
    for t in TARGETS:
        res = inject_file(t, data, dry_run=True)
        if res is None:
            skipped.append(t)
            continue
        if res["changed"]:
            errors.append(f"{res['file']} 生成区已过期（{', '.join(res['changed'])}）"
                          "——执行 make report-sync 重新注入")
        fresh.append(f"{res['file']}({len(res['keys'])} 区"
                     + (f"，{len(res['volatile_only'])} 区仅差易变量" if res["volatile_only"] else "")
                     + ")")
    notes.append(f"[5/8] 生成区新鲜度：已校验 {', '.join(fresh) or '无'}；"
                 f"跳过 {', '.join(skipped) or '无'}")

    # 6. HTML 静态数字比对
    checked = []
    for t in TARGETS:
        res = check_static_metrics(t, data)
        if res[0] is None:
            warn(res[1])
            continue
        errors += res[0]
        checked.append(res[1])
    notes.append(f"[6/8] 静态 data-metric 比对：{'；'.join(checked) or '无目标文件'}")

    # 7. 源码注释 ⇄ 交付状态（BUG-013）：**在此处重扫**，不复述 collect() 的结论（F4）。
    #    严格失败的理由与误报边界见 STALE_MARKER_PATTERNS 上方的长注释。
    sm = scan_source_markers(data["project"]["milestone"])
    for h in sm["stale"]:
        errors.append(
            f"{h['file']}:{h['line']} 注释里有引用已收官 {h['milestone']} 的未完成标记"
            f"（{h['rule']}）：「{h['match']}」——{sm['closed_rule']}；"
            f"该说的话已过期，请按事实改写；确需保留原措辞请在同一条注释里写 "
            f"{STALE_SUPPRESS_TOKEN} 并说明理由（登记后降级为 warn，交 rev 复核）")
    for h in sm["suppressed"]:
        warn(f"{h['file']}:{h['line']} 的过期里程碑标记（{h['milestone']}）已被 "
             f"{STALE_SUPPRESS_TOKEN} 登记豁免，降级为 warn——请 rev 复核该豁免是否仍成立")
    notes.append(f"[7/8] 源码注释 ⇄ 交付状态（本函数独立重扫 {'/'.join(sm['scanned_dirs'])}，"
                 f"{sm['files']} 个文件 / {sm['comment_lines']} 行注释，当前 "
                 f"{sm['current_milestone']}）：过期承诺 {sm['stale_count']}、"
                 f"登记豁免 {sm['suppressed_count']}、在途承诺 {sm['open_milestone_count']}、"
                 f"开放式留白 {sm['open_ended_count']}（后两类不判失败）")

    # 8. sva_baseline.json floor ⇄ changelog 末行留痕（BUG-018 A，svacheck.py 层 3 信任锚加固）
    sb_errors, sb_note = check_sva_baseline()
    errors += sb_errors
    if sb_note:
        notes.append(f"[8/8] sva_baseline.json floor⇄changelog 留痕校验：一致（total_min="
                     f"{sb_note['total_min']}, attempted_min={sb_note['attempted_min']}，"
                     f"changelog 共 {sb_note['changelog_entries']} 条，末行「"
                     f"{sb_note['changelog_last'][:60]}…」）")
    else:
        notes.append(f"[8/8] sva_baseline.json floor⇄changelog 留痕校验："
                     f"{'；'.join(sb_errors)}")

    # git 字段只 warn
    if not data["process"]["available"]:
        warn("git 元数据不可用（CI 浅克隆属正常）——git 相关字段为 null，不判 FAIL")

    for n in notes:
        print(n)
    if errors:
        for e in errors:
            print(f"[FAIL] {e}", file=sys.stderr)
        print(f"\nreport-check 未通过：{len(errors)} 个问题", file=sys.stderr)
        return 1
    print(f"\nreport-check 通过（{len(WARNINGS)} 条 warn）")
    return 0


# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="PPA-Lite 成果数据机械抽取层（展示材料的唯一取数口）")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--json", action="store_true", help="输出结构化 JSON（默认 stdout，不落盘）")
    g.add_argument("--summary", action="store_true", help="人读速查（handover 风格）")
    g.add_argument("--md", choices=sorted(MD_FRAGMENTS), help="输出 markdown 片段")
    g.add_argument("--inject", nargs="*", metavar="FILE", default=None,
                   help=f"把生成区内容注入目标文件；不带参数 = 注入全部默认目标"
                        f"（{' '.join(TARGETS)}，与 --check 同一份清单）")
    g.add_argument("--check", action="store_true",
                   help="八项校验（含生成区新鲜度、源码注释⇄交付状态、sva_baseline.json 留痕校验）")
    ap.add_argument("--pretty", action="store_true", help="--json 缩进输出")
    ap.add_argument("--out", metavar="PATH", help="--json 另存到文件（发布 Artifact 用，日常不需要）")
    args = ap.parse_args()

    if not any((args.json, args.summary, args.md, args.check)) and args.inject is None:
        ap.print_help()
        return 0

    data = collect()

    if args.json:
        text = json.dumps(data, ensure_ascii=False, indent=2 if args.pretty else None)
        if args.out:
            Path(args.out).write_text(text + "\n", encoding="utf-8")
            print(f"JSON 已写入 {args.out}", file=sys.stderr)
        else:
            print(text)
        return 0
    if args.summary:
        cmd_summary(data)
        return 0
    if args.md:
        print(MD_FRAGMENTS[args.md](data))
        return 0
    if args.inject is not None:
        targets = args.inject or TARGETS       # 不带参数 = 全部默认目标（与 --check 同源）
        touched = 0
        for t in targets:
            res = inject_file(t, data)
            if res is None:
                continue
            touched += len(res["changed"])
            print(f"{res['file']}: 更新 {len(res['changed'])} 区"
                  f"{'（' + ', '.join(res['changed']) + '）' if res['changed'] else ''}，"
                  f"未变 {len(res['same'])} 区"
                  + (f"，仅差易变量 {len(res['volatile_only'])} 区" if res["volatile_only"] else ""))
        print(f"共更新 {touched} 个生成区（目标: {', '.join(targets)}）")
        return 0
    if args.check:
        return cmd_check(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
