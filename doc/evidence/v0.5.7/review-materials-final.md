# 审查记录：三件展示材料终审（三方核对）+ BUG-018 复验关单

## 0. 身份、范围与纪律声明

- **审查人 = rev（本会话全新实例）**，与三件材料的两个 arch 作者、BUG-018 的 DV 修复人（commit `59c07f1`）均为不同实例，满足实例隔离与「关单人 ≠ 修复人」（CLAUDE.md §4.3）。
- **被审 HEAD = `a12ae7b`**（v0.5.7 / M5，工作区起点干净）——即「docs: 回填 BUG-018 修复 commit，状态 FIXING → FIX_READY」那一笔。
- **被审工件**：`doc/report.html`、`README.md`、`doc/presentation/defense.md`；`doc/bugs.md` BUG-018 条目；`sim/regress/sva_baseline.json`（守卫机制）、`scripts/svacheck.py`（层 1 尾锚 + docstring）。
- 环境：本地 VM，`vcs = /home/synopsys/vcs-mx/O-2018.09-SP2/bin/vcs`（已探测，真跑闭环）。全程显式 `export VCS_HOME/VERDI_HOME/LM_LICENSE_FILE`。
- **纪律：零 git 写操作**（无 checkout/restore/stash/reset/clean）。临时篡改一律「字节备份 + 还原 + sha256 校验」：`sim/regress/sva_baseline.json` 三次改动后 sha256 均还原为 `15efabf1…41cb98`；`doc/report.html` 的注入实验全部在 scratchpad **副本**上跑，真文件 sha256 `3d96b991…5199e` 未变。写入域仅本文件与 `doc/bugs.md` BUG-018 终态格。
- 判据出处：`doc/spec.md`（§0 适配表优先、§11.5）、CLAUDE.md §4.2/§4.3/§7；措辞红线以 `doc/evidence/v0.5.3/review-bug-013-014.md` §C 与 `doc/evidence/v0.5.0/review-report-tool.md` §B/C3 为准。

---

## A. 三件材料终审

### A0. 取数口径与「第三方」方法

`report.py --check` 的 [6/8] 已机械做过一轮「span 文本 ⇄ 现算 JSON」的静态比对。我做的是**第三方**：把 JSON 值本身按 provenance 回**证据原文/源码**独立复算，专抓「JSON 本身抽错但 span==JSON 比对仍自洽」的共谋态。基准 JSON 取自 `python3 scripts/report.py --json --pretty`（现算，107 KB）。

### A1. data-metric 三方核对（抽查 ≥15，实为 18 项回原文复算）

先跑一遍全量自洽核对：report.html 98 个 + README 5 个 data-metric span，逐个 `resolve(现算JSON, path)` 比对——**0 处不符**（我脚本报的 5 处「100 vs 100.00」是我的 fmt 助手未按百分比补两位小数所致，非真差异；report.py 自带 fmt_num 输出 100.00，[6/8] 亦通过）。据此确认 span==JSON 自洽层无洞，随后逐项回原文：

| # | 字段 | JSON 值 | 独立复算（命令/原文） | 一致 |
| --- | --- | --- | --- | --- |
| 1 | design.rtl_lines | 939 | `wc -l rtl/*.sv`：313+332+85+209=939 | 是 |
| 2 | design.rtl_sva | 32 | `grep -cE '\bassert\s+property\b' rtl/*.sv` 求和=32 | 是 |
| 3 | verification.sva.dv | 17 | tb/sva 三文件 4+6+7=17 | 是 |
| 4 | verification.sva.total | 49 | 32+17 | 是 |
| 5 | verification.tb_files | 62 | `find tb -name '*.sv' \| wc -l`=62（v0.5.0 时 63，BUG-016 删 ppa_ref_model.sv → 62） | 是 |
| 6 | verification.tb_lines | 3514 | splitlines 求和=3514 | 是 |
| 7 | verification.rtl_tb_ratio | 3.74 | 3514/939=3.742 | 是 |
| 8 | results.bugs.total | 18 | bugs.md 3 行（016/017/018）+ archive 15 行（001–015），无重号 | 是 |
| 9 | results.waivers.total | 12 | 活跃 2（#11/#12）+ 归档 10（#1–#10） | 是 |
| 10 | results.waivers.sites_total | 81 | 逐条对象列求和（含 `/` 分隔、区间）=81；且见 A5 实跑 lint | 是 |
| 11 | results.reviews.count | 13 | `ls doc/evidence/v*/{rev-*,review*}.md` 去重=13 | 是 |
| 12 | results.evidence.log_files | 33 | `find doc/evidence/v* -maxdepth 1 -name '*.log' \| wc -l`=33 | 是 |
| 13 | project.spec_lines | 903 | `splitlines(doc/spec.md)`=903 | 是 |
| 14 | project.spec_revision_count | 11 / 8闭环=6+2 | spec 修改记录 r1–r11=11；`grep 'rev 裁决'`=8；via_bugs=6=SPEC_CHANGED 缺陷数 | 是 |
| 15 | results.coverage.latest.* | line100/cond94.35/tgl90.42/fsm100/branch100/assert100/score97.46 | `doc/evidence/v0.4.0/coverage-summary.md` 闭环列逐格 | 是 |
| 16 | results.coverage.history[1/2].score | 86.16 / 82.05 | v0.2.3 / v0.3.0 coverage-summary | 是 |
| 17 | charts.coverage.deltas[0].delta | -4.11 | 82.05−86.16=−4.11 | 是 |
| 18 | results.bugs.multi_round[0] | 2 轮 / 9c28fea,b8a1890 | bugs-archive BUG-009 行两个 sha | 是 |

结论：**18/18 一致，0 条对不上**。无「JSON 抽错但比对自洽」的共谋态。

### A2. 五张 SVG 图表数据正确性（从 GEN 区 points 反算）

- **覆盖率爬坡（chart-coverage）**：y 轴 60→100% 映射 y=232→24（40% / 208px）。反算门槛线 90%→y=76.0 ✓；M2 86.16→95.97≈96.0 ✓；M3 82.05→117.34≈117.3 ✓；M4 97.46→37.21≈37.2 ✓。polyline `254.7,96.0 453.3,117.3 652.0,37.2` 只串这三个 comparable 点。**M2→M3 如实画出下降**（y 96.0→117.3，屏幕上更低=值更低）。**M1 点**（手绘区 L625–629）：`<circle class="cov-m1" r=5>` + `<line class="cov-m1">`，CSS L205 `fill:var(--surface);stroke:var(--muted);stroke-dasharray:3 2` = **空心 + 虚线**；域注记「M1：模块聚合域(mod5+mod7) · 无 SCORE 行 · 不同轴，不连线」齐全；置于 y 轴 x=56（脱离折线绘图区），不入 polyline。全部符合红线（review-report-tool §B.2）。
- **回归增长（chart-regress）**：y 轴 0→32 映射 y=192→24（32 / 168px）。反算高度：10→52.5 ✓、17→89.2 ✓、22→115.5 ✓、32→168.0 ✓；y 起点对应。四根柱 10/17/22/32，5 份 result_summary 合并 v0.4.0/v0.4.1 同批为一柱。**cosmetic：M4 柱 x 标签「M4/M4」**（里程碑 join 冗余，非数据错，见 A6）。
- **缺陷分布（chart-bugs）**：宽度 30px/单位。rtl 1(30)/tb 1(30)/infra 10(300)/spec 6(180)，和=18=bugs.total。独立核 bugs 归属列：rtl=BUG-009(1)、infra=005/006/007/011/012/013/014/015/017/018(10)、spec=001/002/003/004/008/010(6)、tb=016(1) → **1/10/6/1 与图一致**。
- **验证金字塔（chart-pyramid）**：w=440×(0.35+0.65·n/49)。反算 49→440 ✓、32→340.8 ✓、31→334.9 ✓、27→311.6 ✓。层值 49/32/31/27 均已在 A1 核实。
- **架构标签（chart-arch-labels）**：ppa_top 209/SVA10/端口11、apb_slave_if 313/8/31、packet_sram 85/5/8、packet_proc_core 332/9/19；行数和=939、SVA 和=32，与 A1 一致。

结论：**五张图坐标全部与数据反算吻合；M1 空心+虚线+域注记、M2→M3 下降均如实。**

### A3. 措辞红线逐条走查

| 红线 | 结论 | 证据 |
| --- | --- | --- |
| ASSERT 100% 每处带分母 88 + 域 tb_top | 通过 | report.html L761–767「88 条实例…88/88…差额 3 条 uvm_pkg 立即断言，位于测量域之外」+ 红线句「单写『91 条 100%』或『49 条 100%』都是错的」；defense §9 L124–125 与 Q13 逐字引 rev 裁决原文。L658 的「assert 100.00」是六类覆盖**分项**（非「N 条断言」口径），不触发该红线 |
| 断言拦截力两段式（可拦红 + 历史清白系事后复算非流程保障） | 通过 | report.html 诚实项 7（L580–582）、defense 页15-7、Q17 均含「现在会让回归变红（负向实验背书）」+「历史清白是事后复算…不是当时流程保障的」 |
| 无「lint 干净/清零/全部修复」 | 通过 | 全部命中均为**否定/守卫语境**（「不写『lint 干净/清零/全部修复』」）；README L124、defense L196/270/273、report.html L598 |
| 无「261 份」 | 通过 | 三件材料 grep `261` 零命中；defense Q18 明确「具体份数不写进对外材料（回扫清单未落盘、不可审计）」 |
| 无「32 份 log 遍布信号名」 | 通过 | grep `遍布` 零命中 |
| 无「8 个 BUG」类 | 通过 | 仅否定语境（「不笼统称『8 个 BUG』」，defense L62 / report.html L289） |
| spec 修订写作 11 次 / 8 闭环=6+2 | 通过 | defense L62、report.html「闭环 8 = 6 缺陷裁决 + 2 门禁仲裁」；现算一致 |
| 覆盖率摘录交叉校验写 3 份（非 4） | 通过 | defense Q18「参与…交叉校验的是 3 份——v0.1.7 因首测/复测并存降级」；report.py [2/8] 现算「4 份，1 处降级 warn」，即有效比对 3 份 |

### A4. 诚实专栏完整性 + 事实核对（自 grep/wc 核）

report.html 9 条与 defense.md 页15 九条**同一套事实、无互相矛盾**。逐条核代码事实：

- 记分板：`ppa_scoreboard.sv` 实测 **47 行**，只做读写计数；`predict()` 定义于 `ppa_core_seq_item.sv:65`、**唯一调用者** `ppa_core_driver.sv:39`，`ppa_ref_model.sv`/`golden_calc` 全域零残留 → **predict() 系唯一参考模型属实**。
- 无 RAL：`grep uvm_reg tb/` = **0** ✓；无 p_sequencer = **0** ✓；无 set_type/inst_override = **0** ✓。
- 功能覆盖率：`ppa_cov.sv` 仅 `apb_cg`，3 coverpoint（cp_region/cp_dir/cp_slverr）+ 1 cross（x_region_dir）✓。
- 诚实项 8「report-check 通过≠仓库无过期承诺」、诚实项 9「不写 lint 干净/清零/全部修复」——**均正确保留了红线的自我限定**。

### A5. lint 实跑对账（诚实专栏第 9 条 / F7 历史缺口是否已闭合）

本实例真跑 `make -C sim lint`（exit 2，见告警即非零属预期），按 (类别,文件,行号) 去重统计本仓库范围 = **81 处**（NS 32 + SVA-DIU 45 + WMIA-L 4），与登记表 + 归档件求和的 81 处**双向差集为空**。即 review-report-tool §B.1/F7 记的「74 登记 vs 84 实测、10 处未登记」缺口已由 BUG-012 补齐（现 12 条豁免覆盖 81 处）。故 README L124 / report.html 诚实项 9 / defense L273「现 81 处告警 / 全部经 rev 复核」**属实且已避「lint 干净」**——诚实边界成立。

### A6. defense §11.5 对齐 + 演示脚本可执行性 + README 链接

- **§11.5 五项逐页对齐**（核 spec.md L676–689）：页8=必1（一键回归100%）、页9=必2（覆盖率等级，spec 原文五类；defense 如实标注本仓库 +assert=六类、适配 5 改证据链+现场 urg）、页10=必3（testplan 五字段）、页11=选4（过滤登记，Excel→markdown）、页12=选5（选做纳回归）——**全部命中，适配注记如实**。
- **演示 9 步抽 3 步实跑**：步 0 `command -v vcs` → `/home/synopsys/…/vcs`（真）；步 1 `make handover` → 现算版本 0.5.7/状态/日志块（真）；步 8 `python3 scripts/docs.py --check` → `docs-check 通过`（真）。可执行。
- **引用路径有效性**：报告/讲稿引用的 15 个文件路径（coverage-exclude-registration.md、review-bug-009-arbitration.md、bugs/BUG-009.md、review-bug-013-014.md、evidence/README.md、reg_defs.sv、ppa_core_seq_item.sv 等）**全部存在**；commit `5a58c64`（BUG-011）`git cat-file` 存在。README 一屏内叙事—链接自洽。

### A7. 材料侧发现（返工/闭环动作）

**M-1（中 · 需 arch 返工）· defense.md Q16 与演示步 8 的「svacheck 被绕过四次/四轮」计数内部不一致。**
- Q16（L275–276）称「断言检查器 `svacheck` 自己被绕过了四次」「四轮绕过——BUG-014、BUG-017、BUG-018」，但括号与正文**只枚举 3 条**（014/017/018）。且该问被明确限定在 **svacheck 断言检查器**范畴——而演示步 8（L221）里凑齐「四轮」的第 4 条是 **BUG-011**（docs.py 里程碑签核门禁恒真），**与 svacheck 无关**。
- 技术事实：svacheck 脚本被构造绕过的是 BUG-017（三向量）与 BUG-018（两向量）两轮；连同 BUG-014「原始盲区」至多 3 轮；无论按「轮」还是「向量」计都不等于 4。步 8 的「门禁体系 BUG-011/014/017/018 四轮」（面向**门禁体系**、含 BUG-011）自洽，问题**只在 Q16 把门禁体系的 4 收窄到 svacheck 后仍写 4**。
- 要求：Q16 改为「三次/三轮」（BUG-014/017/018），或改述为「门禁体系四轮（含 BUG-011 docs.py 门禁，非 svacheck）」，使数字与枚举、与作用域一致。此项仅见于 defense.md，report.html 未作此计数、无需动。

**M-2（低 · 需 orch 在收尾 report-sync）· report.html 生成区（footer-stamp + data-json）在 HEAD 处已过期，report.py --check 因此 RED。**
- 机制：`truth_digest()` 覆盖 `doc/bugs.md` 等全部真值源。R4（`59c07f1`）交付时 report-check 8/8 全绿；随后 `a12ae7b`（本卡起点，docs 回填把 BUG-018 FIXING→FIX_READY）**改了 bugs.md 却未 `make report-sync`**，令 footer-stamp 的真值源快照（现算 `180e37d2…` vs 应为 `10a37f7f…`）与 data-json 内嵌的 BUG-018 状态（内嵌仍 `FIXING`/rounds 0）滞后。
- 影响面**仅限这两个生成区**：把 report.html 副本重注入实测只改这 2 区（footer-stamp、data-json），**98 个可见 data-metric span 一个不动**（[6/8] 静态比对全绿即证）。即报告**人读内容全部正确**，红的只是自更新的落款戳 + 内嵌 provenance JSON。
- 处置：orch 在 BUG-018 关单 + 本记录落盘后跑一次 `make report-sync` 即恢复 report-check 全绿（这本是 /closeout 标准步）。**注：`a12ae7b` 改真值源未同步 report.html，属回填遗漏，建议 orch 收尾一并补。** 我按写入域不动 report.html。

**非阻断 cosmetic**：① chart-regress M4 柱标签「M4/M4」（里程碑 join 冗余）；② M1 覆盖率 marker 的 y=150 系无 SCORE 行下的占位纵坐标（已由空心+虚线+「不同轴」注记消歧，可接受）。

---

## B. BUG-018 复验关单

修复 commit `59c07f1`（DV）。处置三项逐条独立复验（改 `sva_baseline.json` 一律字节备份+还原+sha256）：

### B1. 处置① 基线机械守卫（report.py --check 第 8 项 floor⇄changelog 留痕）——堵住

隔离调用 `report.check_sva_baseline()`：
- 基线原状（91/88，changelog 末行 91/88）→ **GREEN**。
- **A 语料重放**：静默把 floor 改 0/0、changelog 不动 → **FAIL**：`floor（0/0）与 changelog 末行声明值（91/88）不符…静默改动，BUG-018 判据①命中`。还原后 sha256 `15efabf1…41cb98` **一致**。
- 正当程序：改值 90/87 + changelog 末行追声明 90/87 → **GREEN**。再还原，sha256 一致，`git status` 无残留。

### B2. 处置② 层 1 尾锚放宽 + docstring 第三次收窄——命中且不误伤

- **B 语料重放**：`"…packet_proc_core_sva.sv", 45: …a_done_hold: started at 155000ps failed at 165000ps  Offending 'done_o'` 喂 svacheck CLI → **SVA_FAIL（层 1 命中，a_done_hold @165000ps）退出码 1**。`FAIL_LINE_RE` 尾锚已由 `\s*\r?$` 放宽为 `failed at \S+(?:\s.*)?$`（`.` 不跨行）。
- **七类对抗语料**（length/type/chk_error 引用、ERROR_STATE、succeeded、引用形态历史记录、# 文档引用 Summary=3 failures、not finished）→ **CLEAN 退出码 0**（零误报）。
- **零误伤实跑**：`svacheck -q` 扫 33 份归档摘录 + 34 份 sim/out log（含 covreset）= **67 份全 CLEAN、0 份违例**——放宽尾锚未对真实 log 引入任何假阳。
- **docstring 自述**：`svacheck.py` L61–86 已改为「逐层盲区覆盖矩阵表」，明写「不再作『全覆盖/fail-closed，对任何 log 都有效』这类总括声明」，逐条标注单层兜底（唯一层2/唯一层3）。**正是 BUG-017 R2 / BUG-018 B 要求的『逐层如实写明盲区、不再全覆盖声明』**，自述过宽问题已消除。

### B3. 处置③ 负向复验 A/B 均转 FAIL/命中——已达成（见 B1/B2）。

### B4. 换角度新绕过尝试 + 边界声明裁定

按卡要求另构造新绕过：**伪造 changelog 一致的假声明**——把 floor 改 0/0 且 changelog 末行也声明「total_min=0 attempted_min=0」。实测 `check_sva_baseline()` 判 **GREEN**（骗过机械校验），层 3 随即被 0/0 floor 停用，`$assertoff` 向量（91/0/0）复判 CLEAN。

**裁定：修复人对此「非密码学级防篡改」的边界声明成立，接受，不阻断关单。** 依据：
1. BUG-018-A 的处置要求原文是「sha 登记**或**『floor 值变更须同 commit 追 changelog 行』的机械核对」——二者择一即满足。修复取后者，**完整实现了 A 的既定目标**（「使『只准人工改+changelog』从纪律升为门禁」）：静默一行改动**已被拦死**（B1 实测）。
2. 残留（同时伪造数值+一致 changelog）需**多工件一致伪造**，且 changelog 会留下「total_min=0」这种自我指认的明文条目，`/closeout` 的 git diff 人工复核可见——属机械门禁的合理边界（门禁挡疏忽/随手绕过，带审计痕迹的蓄意伪造交人工兜底）。
3. 该边界已如实写进 `sva_baseline.json` 说明字段与修复人交付声明，**未过宽自述**。sha-pin 属可选增强（把信任锚移到另一文件，收益递减），**非关单前置**；如需可另开低优先级加固项。

### B5. 关单判定 → **CLOSED**

处置三项全部达成并独立复验（B1/B2/B3），零误伤经 67 份真实 log 坐实，新绕过属已如实声明的能力边界。关单人=rev ≠ 修复人=DV。复验证据 = 本文件。

---

## C. 门禁复核（本记录 + bugs.md 改动后）

- `make docs-check` → 通过（BUG-018 置 CLOSED + 填复验证据路径合法）。
- `python3 scripts/report.py --check`（本记录 + BUG-018 CLOSED 落盘后实跑，exit 1）：[1/8] spec sha256、[2/8] 覆盖率⇄回归、[3/8] regress.list、[4/8] 漏点守卫、[7/8] 源码注释、[8/8] 基线留痕**六项全绿**；RED 为 [5/8] 生成区新鲜度（report.html 的 kpi-row/footer-stamp/data-json + README/defense 的 readme-kpi 过期）与 [6/8] 一处静态比对（`results.reviews.count` 页面 `13` ≠ 现算 `14`）。
- **成因是本记录自身**：本文件是一份新的 `review*.md`，令 `results.reviews.count` 由 13→**14**（这是唯一被改动的可见 KPI，属「新增一份审查记录」的必然自增）；叠加写 `doc/bugs.md` + 本记录使 `truth_digest` 变化（二者皆在 `TRUTH_SOURCE_GLOBS` 内），触发 footer-stamp/data-json 过期。**除 reviews.count 13→14 外，98 个 span 其余全部仍与现算 JSON 一致**（[6/8] 只报这一处）。**任何写 evidence 的 rev 记录都会触发同一链条**——须由 orch 在收尾 `make report-sync` 一次性清除（把 13 全量刷为 14 并重注入落款/内嵌 JSON），恢复 report.py --check 全绿。这是 /closeout 的标准步，不在 rev 写入域内（我不动 report.html/README/defense）。
- 本轮未 bump、未 commit；除本记录与 bugs.md BUG-018 三格外未改任何文件。

---

## D. 总体结论：**有条件通过**

三件材料的**数据正确性、图表保真、措辞红线、诚实专栏、§11.5 对齐、路径有效性**均达标（A1 18/18、A2 五图反算全吻合、A3 八条红线全过、A5 lint 81=81 实跑闭合、A6 演示步实跑通过）；BUG-018 **CLOSED**。放行须满足：

- **条件 1（必须，arch 返工）**：修 defense.md **Q16「svacheck 被绕过四次/四轮」计数不一致**（枚举仅 3 条 014/017/018；BUG-011 非 svacheck）——改「三次/三轮」或改述为「门禁体系四轮（含 docs.py 门禁 BUG-011）」。见 A7-M-1。
- **条件 2（必须，orch 收尾机械动作）**：`make report-sync`（在 BUG-018 CLOSED + 本记录落盘之后）——把三件材料的 `results.reviews.count` 由 13 刷为 14（本记录令其自增），并重注入 report.html/README/defense 的生成区（kpi-row/readme-kpi/footer-stamp/data-json），恢复 report.py --check 全绿。注：起点 HEAD `a12ae7b` 回填 bugs.md 时已漏做此步（当时仅 footer-stamp/data-json 过期），一并补。见 A7-M-2、§C。
- **建议（非阻断）**：chart-regress「M4/M4」标签、可选 sva_baseline 的 sha-pin 增强，下次触及时顺手处理。

被审 HEAD `a12ae7b`。本轮零 git 写、未 bump、未 commit。
