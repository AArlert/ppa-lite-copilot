# rev 审查记录：scripts/report.py 抽数正确性 R2 交付门禁（gold-standard 独立复算）

> 标题里的"门禁"二字是**被迫**加的，不是修辞：见 E.4 的 F10——本记录原标题为
> 「rev 审查记录：scripts/report.py 抽数正确性（R2 gold-standard 独立复算）」，落盘后
> `python3 scripts/report.py --check` 当场 exit 1（`标题 … 无法归类（里程碑/门禁/仲裁/豁免）`），
> 即"新增一份合法 rev 记录"会直接打挂已挂进 CI 硬门禁的 report-check。

- 审查人：rev 实例（本轮独立实例，**非 report.py 实现者**；本轮全程只读分析 + 本文件写入，未改动 `scripts/report.py`、`rtl/`、`tb/`）
- 审查日期：2026-07-26
- 被审 HEAD：`8377422773b65649fc32a503c44cbcab8572d6f1`（`8377422` feat: M4 收官…0.5.0）
- 被审工件：`scripts/report.py`（未提交）、`Makefile`（新增 report/report-json/report-sync/report-check）、`.github/workflows/ci.yml`（新增 report --check 步 + fetch-depth: 0）
- 判据出处：CLAUDE.md §4.2（防验证造假）、§7（质量门禁）、§8（单一事实源）；spec.md §0 适配 3/7（六类口径、≥90 门槛）、§11.5-必2
- 工作方式：**A 部分十组数据一律先手工从原文复算、记录结果，再运行脚本比对**（先手算后跑脚本的顺序有对话时序为证：本轮先读了四份 coverage-summary / 五份 result_summary / bugs / lint-waivers / testplan / regress.list / rtl / tb 原文并逐组算完，之后才第一次读 `scripts/report.py` 与运行它）
- 工具环境：本地 VM 探测到 `vcs` / `urg` / `verdi` / `xloc`（`xcov`/`xdebug` 不可用）。本轮为验证争议点 B.1 **真跑了一次 `make -C sim lint`**（见 D.4），仿真回归未复跑（其复算已由 `doc/evidence/v0.4.1/review-m4-milestone.md` 的 M4 签核完成，本轮范围是抽取层而非测量层）

**总体结论：有条件通过。** 抽数正确性本身无一处出错（A 十组 10/10 一致，C 抽查 12/12 一致，D 十次负向验证全部硬失败退出）；条件全部落在"R3 交付展示材料时会引爆"的门禁设计问题与措辞边界上，见文末条件清单。另发现一项与本脚本无关但由本轮实测暴露的项目缺陷（lint 豁免登记表缺 10 处），建议 orch 单独登记。

---

## A. 十组独立复算对照

复算基准一律为真值源原文；"我的结果"栏是读脚本源码之前手工算出的值。

### A.1 四个覆盖率历史点的六类数值 + SCORE

我的算法：分别打开 `doc/evidence/v0.1.7/coverage-summary-M1.md`、`v0.2.3/`、`v0.3.0/`、`v0.4.0/coverage-summary.md`，人工定位"设计+验证环境域（tb_top）"那张表（v0.1.7 无此域，取其"六类结果（复测）"表），逐格抄录百分比。

| 版本 | 我读到的表 | line | cond | toggle | fsm | branch | assert | SCORE | 脚本结果 | 一致 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v0.1.7 | 六类结果（复测），`百分比（首测→复测）`列 | 94.92 | 91.30 | 73.32 | N/A | 95.12 | 100.00 | 无 SCORE 行 | 逐格相同，score=null | 是 |
| v0.2.3 | §2 设计+验证环境域，`数值(%)`列 | 97.84 | 90.43 | 71.44 | 60.00 | 97.22 | 100.00 | 86.16 | 逐格相同 | 是 |
| v0.3.0 | §2 设计+验证环境域，`数值(%)`列 | 95.88 | 82.61 | 65.73 | 60.00 | 93.75 | 94.32 | 82.05 | 逐格相同 | 是 |
| v0.4.0 | §1 设计+验证环境域，`闭环(v0.4.0)`列 | 100.00 | 94.35 | 90.42 | 100.00 | 100.00 | 100.00 | 97.46 | 逐格相同 | 是 |

补充核对：脚本记录的取列依据（`col_rule`）与我人工取列一致——v0.4.0 走"列头含版本号 0.4.0"命中唯一的 `闭环(v0.4.0)`（**没有误取同表的 `基线(v0.3.0)` 列**，这是本文件最容易出的错，脚本躲过了）；v0.2.3/v0.3.0 走"列头匹配 `数值`"；v0.1.7 走"列头匹配 `百分比`" 且单元格 `93.22% → **94.92%**` 取右段。另外交叉核对：v0.4.0 表的"基线(v0.3.0)"整列与我从 v0.3.0 文件读到的 6 个值逐格相同，说明两份 evidence 自身自洽。

### A.2 五条回归历史的通过数与日期

我的算法：`find doc/evidence -name result_summary.txt`，逐份读首行的 `日期=` 与 `通过=N/N`，并 `grep -c '^PASS'` 与首行声明对账。

| 版本 | 我读首行 | 我数的 PASS 行 | 脚本结果 | 一致 |
| --- | --- | --- | --- | --- |
| v0.1.7 | 2026-07-09 通过=10/10 | 10 | 10/10 @2026-07-09 | 是 |
| v0.2.3 | 2026-07-14 通过=17/17 | 17 | 17/17 @2026-07-14 | 是 |
| v0.3.0 | 2026-07-14 通过=22/22 | 22 | 22/22 @2026-07-14 | 是 |
| v0.4.0 | 2026-07-16 通过=32/32 | 32 | 32/32 @2026-07-16 | 是 |
| v0.4.1 | 2026-07-16 通过=32/32 | 32 | 32/32 @2026-07-16 | 是 |

（我第一遍用 `ls -R | head` 漏看了 v0.4.1 的 `result_summary.txt`，一度把 `sim/result_summary.txt` 当第五条；重查目录后修正，与脚本一致。`diff doc/evidence/v0.4.0/result_summary.txt doc/evidence/v0.4.1/result_summary.txt` 为空，与 M4 签核记录第 35 行的三处 diff 结论一致。）

脚本的加分项：把 v0.4.0/v0.4.1（同日期同结果）合并为**一批**再画柱（`series` 4 点、`history` 5 点），避免把同一次回归画成两次增长；并在 `note` 里说明 v0.1.6 那轮 7/7 未归档摘要故曲线不含该点。我核对 `doc/evidence/v0.1.6/` 确无 result_summary.txt，v0.1.7 覆盖率文第 60 行确写"7/7 PASS 摘要已被下方复测的 10/10 摘要覆盖"——处理正确。

### A.3 SVA 条数分侧

我的算法：`grep -cE 'assert\s+property'` 逐文件。

| 侧 | 文件 | 我的结果 | 脚本 | 一致 |
| --- | --- | --- | --- | --- |
| DE（rtl/） | apb_slave_if 8 / packet_proc_core 9 / packet_sram 5 / ppa_top 10 | **32** | 32（逐文件同） | 是 |
| DV（tb/sva/） | apb_protocol_sva 4 / apb_slave_if_sva 6 / packet_proc_core_sva 7 | **17** | 17（逐文件同） | 是 |
| 合计 | — | **49** | 49 | 是 |

另核：`grep -rl 'assert property' tb/` 只命中 tb/sva/ 三个文件，不存在"tb 其他目录还有 SVA 被漏计"。

### A.4 缺陷 11 条：编号 / 终态 / 归属分类 / 多轮修复

我的算法：手读 `doc/bugs.md`（BUG-008、BUG-011）+ `doc/bugs-archive.md`（另 9 条），逐行抄"疑似归属"与"状态"，"多轮"按修复 commit 列里 sha 个数判。

| 项 | 我的结果 | 脚本 | 一致 |
| --- | --- | --- | --- |
| 总数/编号 | 11 条，BUG-001…011 连续无缺号 | 11 | 是 |
| 终态 | SPEC_CHANGED 6（001/002/003/004/008/010）、CLOSED 5（005/006/007/009/011） | `{SPEC_CHANGED:6, CLOSED:5}` | 是 |
| 归属 | spec 6、infra 4（005/006/007/011）、rtl 1（009） | `{spec:6, infra:4, rtl:1}` | 是 |
| 多轮修复 | 仅 BUG-009（`9c28fea, b8a1890` 两个 sha，历经 DV 复验驳回 FIX_READY→OPEN 后二次修复） | `BUG-009 (2 轮)` | 是 |

归属分类规则我单独验过顺序陷阱：infra 行原文写作"infra（…，**非 spec 歧义**）"，若先匹配 "spec" 会把 4 条 infra 全部误归 spec。脚本的 `BUG_KIND_RULES` 明确按 rtl→infra→spec 有序匹配并在注释里写明原因，处理正确；我用 N9（见 D.3）验证过归类不到时会硬失败而非静默归"其他"。

### A.5 lint 豁免条数 / 类别分布 / 复核状态

我的算法：手读两个登记表，逐条数"对象（文件:行）"列的行号个数（注意 `,` 与 `/` 两种分隔符、`10-13` 区间写法）。

| # | 类别 | 我数的处数（依据） | 脚本 | 一致 |
| --- | --- | --- | --- | --- |
| 1 | SVA-DIU | 5（packet_sram 61,65,70,74,80） | 5 | 是 |
| 2 | SVA-DIU | 8（apb_slave_if 268…306） | 8 | 是 |
| 3 | SVA-DIU | 4（apb_protocol_sva 21,27,32,38） | 4 | 是 |
| 4 | SVA-DIU | 6（apb_slave_if_sva 51…78） | 6 | 是 |
| 5 | NS | 6 = tb_top 1 + apb_driver 4（`20/21/46/49` **斜杠分隔**）+ apb_monitor 1 | 6 | 是 |
| 6 | WMIA-L | 4（apb_seq_item `10-13` **区间**=10,11,12,13） | 4 | 是 |
| 7 | NS | 12（m3_stub_driver 26…87） | 12 | 是 |
| 8 | SVA-DIU | 9（packet_proc_core 278…322） | 9 | 是 |
| 9 | SVA-DIU | 6（ppa_top 166…187） | 6 | 是 |
| 10 | NS | 2（m3_seq_lib 329,344） | 2 | 是 |
| 11 | NS | 12 = m4_seq_lib 2 + ppa_core_driver 10 | 12 | 是 |
| **合计** | — | **74** | **74** | **是** |

类别分布我数：SVA-DIU 6 条（#1/2/3/4/8/9）、NS 4 条（#5/7/10/11）、WMIA-L 1 条（#6）；脚本 `{SVA-DIU:6, NS:4, WMIA-L:1}`，一致。复核状态我逐行看"复核（rev/日期）"列 11 条全部非空且均为"批准"；脚本 `reviewed=11, all_reviewed=true`，一致。

### A.6 testplan 行数与分 M 计数

我的算法：手数 `doc/testplan.md` 四张表的数据行。

| 里程碑 | 我数 | 脚本 by_milestone | 一致 |
| --- | --- | --- | --- |
| M1 | 9（M1-01…09） | total 9 / pass 9 | 是 |
| M2 | 7（M2-01…07） | total 7 / pass 7 | 是 |
| M3 | 5（M3-01…05） | total 5 / pass 5 | 是 |
| M4 | 10（M4-01…05 + M4-02a…e） | total 10 / pass 10 | 是 |
| 合计 | **31**，全部为通过状态 | rows 31 / passed 31 / pass_rate 100.0 | 是 |

### A.7 regress.list 条目数与唯一测试名数

我的算法：`awk '!/^\s*#/ && NF'` 数行 = 32；`awk '{print $1}' | sort -u | wc -l` = 27。脚本 `entries 32 / unique_tests 27`，一致。多 seed 项我数得 `ppa_m2_08_rand_test`(3)、`ppa_m1_10_rand_test`(2)、`ppa_m3_06_rand_test`(3) 共 3 个测试，脚本 `multi_seed_tests` 同。

### A.8 RTL 四模块行数 / 端口数 / 内部断言数

我的算法：`wc -l`；端口用 `awk '/^\s*module/,/\);/'` 截出端口清单再数 `input|output|inout` 行；断言同 A.3。

| 模块 | 我的行数 | 我的端口 | 我的断言 | 脚本 | 一致 |
| --- | --- | --- | --- | --- | --- |
| apb_slave_if | 311 | 31 | 8 | 311/31/8 | 是 |
| packet_proc_core | 332 | 19 | 9 | 332/19/9 | 是 |
| packet_sram | 85 | 8 | 5 | 85/8/5 | 是 |
| ppa_top | 209 | 11 | 10 | 209/11/10 | 是 |
| 合计 | **937** | **69** | **32** | 937/—/32 | 是 |

（脚本端口数用全文件正则 `^\s*(input|output|inout)`，我用模块头截段后再数，两法同值——因为四份 RTL 均无端口清单之外的 input/output 行。**这是巧合而非保证**，见 E 的低风险清单。）

### A.9 tb 文件数与行数、UVM 测试类三分类

我的算法：`find tb -name '*.sv'` = 63 个文件（`.svh` 0 个），`wc -l` 合计 3562 行；测试类按 `class X extends …` 的父类归并。

| 项 | 我的结果 | 脚本 | 一致 |
| --- | --- | --- | --- |
| tb 文件数 | 63 | 63 | 是 |
| tb 行数 | 3562 | 3562（TB:RTL=3.80） | 是 |
| 基类 | 3（ppa_base_test / ppa_m2_base_test / ppa_m3_base_test，均 extends uvm_test） | base 3 | 是 |
| 场景测试类 | 27 = ppa_base_test 系 11 + m2 系 9 + m3 系 7 | scenario 27 | 是 |
| 序列库 | 3（m1_seq_lib / m3_seq_lib / m4_seq_lib） | seq_lib 3 | 是 |
| package | 1（ppa_test_pkg） | package 1 | 是 |

强交叉校验：场景测试类 27 == regress.list 唯一测试名 27（A.7），且脚本内建的"regress.list 里有测试在 tb/uvm/test/ 找不到同名文件就 warn"未触发——两侧完全对齐。脚本另有"四类之和必须等于目录 .sv 文件数（34）"的穷尽性断言，27+3+3+1=34 成立。

### A.10 spec 修订条数与"闭环"判定

我的算法：手读 spec.md "修改记录"表 r1…r11 = 11 条；逐条看能否反查到 BUG-ID。

| 版次 | 我的判定 | 依据 |
| --- | --- | --- |
| r11 | 闭环，BUG-010 | 内容首句"BUG-010 rev 裁决落地" |
| r10 | 闭环，BUG-008 | 同上 |
| r9 | **无 BUG-ID**，但确为 rev 门禁附带仲裁（P2） | "rev 裁决落地（packet_proc_core design-prompt 门禁附带仲裁 P2）" |
| r8 | **无 BUG-ID**，rev 门禁附带仲裁（P1） | 同上 |
| r7 | 闭环，BUG-004 | — |
| r6 | 闭环，BUG-003 | — |
| r5 | 闭环，BUG-002 | — |
| r4 | 闭环，BUG-001 | — |
| r3 / r2 / r1 | 非闭环（适配表扩项 / 建章 / 原件入库） | 无"rev 裁决"措辞 |

我的手算：**能反查到 BUG-ID 的 6 条**（r4/r5/r6/r7/r10/r11），不能的 5 条。
脚本输出：`spec_revision_count=11`、`spec_closed_loop_count=8`、`spec_closed_loop_via_bugs=6`、`spec_closed_loop_via_gate=2`。

**判定：一致，且脚本口径优于我的二分法。** 我把 r8/r9 归为"非闭环"是粗糙的——它们确实是 rev 仲裁驱动的修订，只是仲裁走的是 design-prompt 门禁而非 bugs.md（记录在 `doc/evidence/v0.2.0/rev-gate-packet_proc_core.md`，我核对该文件标题确为"…design-prompt 门禁 + spec 修改提案 P1/P2 仲裁"）。脚本拆成 6+2 两个字段并在 `spec_closed_loop_note` 里明写"**材料不得笼统称 N 个 BUG**"，正是我要提的措辞约束，脚本已自行封堵。另有独立佐证：`via_bugs=6` 恰等于 A.4 里 SPEC_CHANGED 的 6 条缺陷，两条路径互证。

**A 部分小结：十组全部一致（10/10）。唯一出现数字差异的一处（闭环 6 vs 8）经核实为口径分解而非抽数错误，且脚本给出的分解更精确。**

---

## B. 三条裁决

### B.1 `results.waivers.sites_total = 74` 该不该印进对外材料

**独立复算结果**：见 A.5，我逐条手数 11 条豁免共 **74 处**，与脚本逐条、逐文件完全相同（含 `/` 分隔的 #5、`10-13` 区间的 #6、跨两文件的 #5/#11）。另外我手工核对了 4 条以中文数字自述处数的行（#1"五处"、#2"八处"、#3"四处"、#4"六处"），与解析值 5/8/4/6 同样一致——即 11 条中实际有 10 条能被自述交叉印证（脚本只认阿拉伯数字，故报 6/11，属保守如实）。

**三个附带字段的审查**：

- `sites_crosscheck`："6/11 条豁免在结论/原因列自述了 N 处，全部与行号解析一致（0 处矛盾）"——我复核为**准确**（自述行为 #5/#6/#7/#8/#9/#10）。且 D.3-N8 实测：把 #10 的"全 2 处"篡改为"全 5 处"，脚本立即 `[FAIL] … 登记表内部矛盾，拒绝出数` 并 exit 1，不是摆设。
- `sites_line_drift`：脚本报出唯一一条漂移 `#8 rtl/packet_proc_core.sv: 登记 9 行，现文件仍命中 0 行`。我独立验证：登记的 278,283,288,293,298,304,309,317,322 与今日实际断言行 282,287,292,297,302,308,313,321,326 相差 4~5 行（BUG-009 两轮修复后文件位移）。**脚本的漂移检测是对的，且这条漂移是我手工比对时独立发现的同一条**。
- `sites_caveat`："处数=登记时刻的 lint 告警条数……绝对行号是登记时刻快照，文件后续改动会漂移"——措辞准确，是这个数字唯一正确的自我限定。

**关键的新证据（本轮实测）**：我在本地 VM 真跑了 `make -C sim lint`（见 D.4），**HEAD 处本仓库范围内实际有 84 处告警（去重后），登记表只覆盖 74 处，有 10 处从未登记**。

**裁决**：

1. **74 是可追溯的机械事实——但它的被测对象是"登记表"，不是"项目的 lint 告警数"。** 作为"11 条豁免登记共覆盖 74 处告警"，它可机械复算、可交叉校验、有 rev 复核背书，允许进对外材料。
2. **不允许进 KPI 带。** 理由：KPI 带是不带上下文的裸数字位，而 74 必须与"登记时刻""登记表覆盖范围"两个限定同时出现才不失真；且今日实测 84≠74，裸放会诱导"项目只有 74 处 lint 告警"的错误推论。当前 `KPI_SPEC` 用的是 `results.waivers.total`（11 条）而非 sites_total，**现状合规，维持即可**。
3. **允许的措辞**（正文/附录）：
   - 可以写：「lint 豁免登记 11 条，逐条经 rev 复核批准，累计覆盖 74 处告警（处数为登记时刻计数，登记表内 6 条自述处数与逐行号解析 0 矛盾）」。
   - **禁止**写：「全项目 lint 告警 74 处」「lint 告警已全部登记/清零」「make lint 干净」——前两句在 HEAD 处为**假**（实测 84 处、10 处未登记），第三句本就与 `make lint` 语义相反（该目标见到本仓库范围内告警即 exit 1）。
   - 若材料确实要谈 lint 覆盖面，必须先把未登记的 10 处补登记并经 rev 复核，否则只谈"豁免登记表"本身，不谈"告警总数"。

### B.2 `COV_ANCHORS` 的 `domain` / `comparable` / `note` 语义标注是否成立；v0.1.7 取首测还是复测

**(a) `comparable=false` 成立，裁决维持。** 依据：

1. `doc/evidence/v0.1.7/coverage-summary-M1.md` 第 17–21 行"范围口径"自述：line/cond/toggle/branch 为 `rtl/apb_slave_if.sv`(mod5) + `rtl/packet_sram.sv`(mod7) **两模块聚合**；assert 另聚合 mod13/mod14。这是作者手工把逐模块 Covered/Total 相加，**不是 urg 的 hierarchy 顶层汇总**。后三点则一律自述为"设计+验证环境域 = hierarchy 顶层实例 `tb_top` 子树"（v0.4.0 第 8 行写得最明确）。二者是结构上不同的测量域。
2. 域选择对数值的影响是数量级的，同一份 v0.2.3 报告里 Total 域 LINE=29.08 vs tb_top 域 LINE=97.84，相差 68.76 pt。跨域连线等于把两把不同的尺画在同一根轴上。
3. v0.1.7 该表**没有 SCORE 行**（我逐行确认），而覆盖率曲线的 y 值就是 SCORE。脚本的处理比"标注不可比"更严：`score=null` → 图表只给 x 不给 y、`polyline` 只串三个 comparable 点、并在注里写"绝不用 0 补位"。这是本轮我最认可的一处设计——**用 0 补位是覆盖率曲线最常见的造假形态，脚本从数据结构层面就堵死了**。
4. 唯一可能反驳的材料是该文件第 20 行"hierarchy.html 中 tb_top 汇总 ASSERT=78.26% 与本表聚合结果一致"。但这句仅对 **assert 一类**、且仅对**首测**成立，不能反推 line/cond/toggle/branch 也是 tb_top 域。反驳不成立。

**(b) 取复测，不取首测，裁决维持。** 依据：

1. 归档的 `doc/evidence/v0.1.7/result_summary.txt` 是 **10/10**，对应的是复测那一轮（首测是 7/7，该文件第 60 行明写"已被下方复测的 10/10 摘要覆盖"）。若取首测数值，材料上就会出现"回归 10/10 配一组 7/7 时的覆盖率"的错配。CLAUDE.md §4.2 的证据口径是归档的终态，复测才是终态。
2. **独立第三方佐证**：早于本轮的另一份 rev 记录 `doc/evidence/v0.1.9/rev-review-toggle-lint7.md` 第 26 行逐类引用的正是复测值——"toggle 73.32%…其余五类（line 94.92% / cond 91.30% / branch 95.12% / assert 100%）均已 ≥90%，fsm 结构性 N/A"。与脚本抽出的 5 个数字逐一相同。历史裁决与本次抽取口径一致。
3. 脚本的落实手段有双保险：章节锚点 `^#{2,3}\s*六类结果（复测）` 直接切到复测表（我验证过切片区间是第 82–102 行，只含复测这一张表，且脚本另有"同一类别出现两行即 FAIL"的跨表守卫）；单元格 `93.22% → **94.92%**` 再取 `→` 右段。两层都指向复测。

**(c) `note` 文本**：三条注（"复测值/无 SCORE/域非 tb_top 不可同轴"、v0.3.0 的"较 v0.2.3 下降属集成引入未激励代码、非回归劣化"、v0.4.0 的"取闭环列"）我逐条对照原文，均为如实描述，无夸大。v0.3.0 那条尤其重要——**曲线上 M2→M3 是真的掉了 4.11 pt，脚本要求"必须画出来并注解"而不是抹平**，这与 §4.2 的诚实原则一致，我明确背书。

**结论：B.2 三个字段的语义标注全部成立，覆盖率爬坡曲线按"M1 点单独 marker + 不入折线 + 注明域不同，M2→M3 的下降如实画出并注解"绘制。**

### B.3 `COV_THRESHOLD = 90.0` 与 `MILESTONE_LABS` 等内置常量的合法性

逐条溯源，全部合法，非脚本作者拍脑袋：

| 常量 | 值 | 出处（我核对的原文） | 判定 |
| --- | --- | --- | --- |
| `COV_THRESHOLD` | 90.0 | spec.md 第 34 行（§0 适配表 #7）"覆盖率口径扩为 `line+cond+fsm+tgl+branch+assert`，**合格线沿用 ≥90%**"；另 §0 适配 #3 第 30 行、§11.5-必2 第 681 行"≥90% 合格 / ≥95% 优良 / 100% 优秀" | 合法。脚本另在 `COV_THRESHOLD_src` 里自标"判据来自 spec，非实测值"，审计友好 |
| `SIX_METRICS` | line/cond/toggle/fsm/branch/assert | spec.md 第 34 行（§0 适配 #7）。注意 §11.5-必2 原文是**五类**（无 assert），脚本取六类=正确，因 §0 第 24 行明定"与本章冲突时以本章为准" | 合法，且优先级处理正确 |
| `MILESTONE_LABS` | M1=Lab1…M4=Lab4 | CLAUDE.md §4.1"Milestone = spec 的 Lab：M1=Lab1 … M4=Lab4" | 合法 |
| `ver_milestone`（minor 号=M 号） | — | CLAUDE.md §4.1"版本 `0.M.P`"、"`make bump-minor` 进下一 Milestone" | 合法。脚本另有守卫：与 `version.json` 的 milestone 字段不符即 warn（本轮 0.5.0/M5 相符，未触发） |
| tag 约定 v0.{M+1}.0 | — | CLAUDE.md §4.1 + BUG-011 条目实录"M4 三条硬条件已齐 → make bump-minor + git tag v0.5.0" | 合法；`process.note` 里已写明该约定 |
| `METRIC_ALIAS` / `BUG_KIND_RULES` / `REVIEW_KIND_RULES` / `SITE_ANCHOR_PATTERNS` / `CHART_GEOM` / `ARCH_LABEL_POS` / `PYRAMID_LAYERS` | — | 均为"去哪读/怎么读/怎么排版"的解析与版式规则，不含成果数字（D.1 已用两种方法证实） | 合法 |

---

## C. provenance 抽查（12 条，按其 source + rule 回原文复核）

`--json` 的 `provenance[]` 实为 **42 条**（33 条静态登记 + 4 条覆盖率历史点 + 5 条回归历史点），任务卡写的 39 条略有出入，属任务卡口径，不是缺陷。抽查 12 条：

| # | path | 声明值 | 声明 source / rule | 我的复核动作与结果 | 一致 |
| --- | --- | --- | --- | --- | --- |
| 1 | `project.spec_sha256` | 4880faf…a396 | doc/spec.sha256；现算并比对 | `sha256sum doc/spec.md` = 4880faf8…a396，与 `doc/spec.sha256` 逐字符相同 | 是 |
| 2 | `project.spec_revision_count` | 11 | doc/spec.md 修改记录首表数据行数 | 手数 r1…r11 = 11 | 是 |
| 3 | `project.csr_count` | 11 | doc/spec.md §5.2 切片内"偏移"列非空行数 | 手数 0x000/004/008/00C/010/014/018/01C/020/024/028 = 11 | 是 |
| 4 | `design.fsm.count` | 3 | rtl/packet_proc_core.sv 的 typedef enum 枚举项数 | `packet_proc_core.sv:56-60` = ST_IDLE/ST_PROCESS/ST_DONE = 3 | 是 |
| 5 | `design.feature_count` | 13 | doc/feature-matrix.md parse_table 行数 | 手数 F1-1…F1-6(6)+F2-1…F2-4(4)+F3-1(1)+F4-1/F4-2(2) = 13 | 是 |
| 6 | `verification.sva.dv` | 17 | tb/sva/*.sv 的 assert property 命中数 | 4+6+7 = 17（逐文件 grep -c） | 是 |
| 7 | `verification.functional_coverage.covergroup_count` | 1 | tb/uvm/env/ppa_cov.sv 的 `^\s*covergroup\s+(\w+)` | 该文件仅 `apb_cg`（L9），另 3 coverpoint + 1 cross（L11/18/19/20），与 JSON 的 cp=3/cross=1 同 | 是 |
| 8 | `verification.regress.unique_tests` | 27 | regress.list 去重测试名数 | `awk '{print $1}' \| sort -u \| wc -l` = 27 | 是 |
| 9 | `results.regress.latest.text` | 32/32 | （override）doc/evidence/v0.4.0/ + v0.4.1/result_summary.txt | 两份首行均"通过=32/32"，且 diff 为空；override 把同批两份都列出，未只挑一份 | 是 |
| 10 | `results.coverage.latest.score` | 97.46 | doc/evidence/v0.4.0/coverage-summary.md 的 SCORE 行、闭环列 | 该文件第 20 行 `| **SCORE（六类综合）** | **82.05** | **97.46** | ✅ | **优良** |`，闭环列=97.46；另与 v0.4.1 M4 签核记录第 58 行的独立 urg 复算值 97.46 相同 | 是 |
| 11 | `results.reviews.lines` | 924 | doc/evidence/v*/rev-*.md + review*.md 各文件行数求和 | 我 glob 出同样 9 个文件，`wc -l` 合计 = 924 | 是 |
| 12 | `results.evidence.log_files` | 33 | doc/evidence/v*/*.log 文件数 | `find doc/evidence/v* -maxdepth 1 -name '*.log' \| wc -l` = 33（7+5+0+0+0+8+5+5+3） | 是 |

另附带全量核对（非抽查，顺手做的）：`results.regress.points=5`、`results.coverage.points=4`、`results.bugs.total=11`、`results.waivers.total=11`、`results.waivers.sites_total=74`、`results.reviews.count=9`、`design.rtl_lines=937`、`verification.tb_lines=3562`、`process.commits=29`（`git rev-list --count HEAD`=29）、`process.tags` 4 个（v0.2.0/v0.3.0/v0.4.0/v0.5.0，日期逐个相同）、`date_range` 2026-07-06→2026-07-16——**全部一致，0 条对不上**。

---

## D. 反造假专项

### D.1 JSON 里是否存在硬编码的成果数字

**判定方法（两条互补，不依赖读代码的自我声明）：**

方法一（静态）：用正则枚举 `scripts/report.py` 中所有 ≥2 位或带小数的数字字面量并逐条归类。结果：全部落入四类——(a) 图表几何/版式（`CHART_GEOM`、`ARCH_LABEL_POS`、y 轴 60.0/100.0、金字塔 0.35/0.65）；(b) 判据常量 `COV_THRESHOLD=90.0`（来自 spec，B.3 已裁）；(c) 百分比换算的 `100.0` 与字符串截断长度 40/80/120/160、`timeout=20`；(d) **说明性文本里内嵌的数字**（见下）。**不存在任何"成果数字被写死后当作读数输出"的情形。**

方法二（动态变异跟随，比读代码更强）：故意改动三处真值源，看 JSON 是否跟着动——
- `rtl/ppa_top.sv` 追加 3 空行 → `design.rtl_lines` 937→**940**，KPI「RTL 代码」同步 937→940；
- `tb/sva/apb_protocol_sva.sv` 追加 1 条 `assert property` → `verification.sva.dv` 17→**18**，`sva.total` 49→**50**，KPI 同步；
- `doc/evidence/v0.4.0/coverage-summary.md` 的 SCORE 闭环列 97.46 改为 55.55 → `results.coverage.latest.score` 97.46→**55.55**，KPI「六类综合覆盖率」同步变 55.55。
还原后三个值全部回到 937/17/97.46。**证明这些数字确由文件读取产生，不是内置。**

**结论：无硬编码成果数字。但有一处需要修的边角**——`results.regress.note` 与 `charts.regress.note` 这两个**说明字符串**里手写了成果数字：`"9 个 evidence 目录 ≠ 9 次测量"`、`"v0.1.6 那轮实际 7/7"`、`"已被 10/10 覆盖"`、`"曲线第一点只能是 10/10"`、`"v0.4.0/v0.4.1 为同一批 32/32"`。这些句子今天全部属实（我逐句核对过），但它们不会随数据更新，而 `data-json` 生成区会把它们原样带进 HTML。这与脚本自己第 12–13 行写的第一纪律相悖，列为待修（低）。

### D.2 负向验证实录（10 次，全部自行设计；每次做完 `git checkout` 还原）

> 通用观察：脚本的失败一律走 `fail()` → 打印 `[FAIL] …` 到 stderr 并 `sys.exit(1)`，**没有任何一次给出默认值或猜测值**。

| # | 我破坏了什么 | 命令 | 真实输出（节选） | exit |
| --- | --- | --- | --- | --- |
| N1 | `doc/spec.sha256` 末位 6→0 | `python3 scripts/report.py --summary` / `--check` | `[FAIL] doc/spec.md 现算 sha256 与 doc/spec.sha256 不符——展示材料宣称的"spec 被钉住"当场不成立，拒绝出数` | 1 / 1 |
| N2 | 把 `v0.3.0/coverage-summary.md` 的 `## 2. 设计+验证环境域…` 标题改成 `## 2. 顶层域覆盖率` | `--summary` | `[FAIL] doc/evidence/v0.3.0/coverage-summary.md 中定位不到章节 '^#{2,3}\s*2\..*设计\+验证环境域'——文档结构变了，解析规则须同步更新` | 1 |
| N3 | `v0.2.3/result_summary.txt` 首行 `通过=17/17`→`16/17`（正文 17 条 PASS 不动） | `--summary` | `[FAIL] doc/evidence/v0.2.3/result_summary.txt 首行声明 16/17 与逐行统计 17/17 不符` | 1 |
| N4 | 新建 `doc/evidence/v0.5.0/coverage-summary.md`（含伪造 LINE 99.99）但不登记锚点 | `--summary` | `[FAIL] v0.5.0 有覆盖率摘录但 COV_ANCHORS 未登记解析规则——新增里程碑后必须补锚点，否则趋势曲线会静默漏点` | 1 |
| N5 | `regress.list` 追加一行 | `--check` | `[FAIL] regress.list 条目 33 ≠ 最新回归摘要 v0.4.0/v0.4.1 的结果行数 32——回归列表改过但未重跑归档，或摘要过期` | 1 |
| N6a | `v0.3.0/coverage-summary.md` 只改第 3 行的 `22/22 PASS`→`21/22` | `--check` | **未 FAIL**：`[2/6] …0 处不符，2 处降级 warn`（文件内出现两个互异 N/N PASS → 按设计降级）。见 F6 | 0 |
| N6b | 同文件**全部** `22/22 PASS`→`21/22 PASS`（唯一声明且与 result_summary 冲突） | `--check` | `[FAIL] doc/evidence/v0.3.0/coverage-summary.md 声明 21/22 PASS 与 doc/evidence/v0.3.0/result_summary.txt 的 22/22 不符` | 1 |
| N7 | 造一个 `doc/report.html`：`GEN:kpi-row` 区里塞陈旧内容，区外手写 `data-metric="results.coverage.latest.score">88.88` 与 `…latest.text">30/32` | `--check` | `[FAIL] doc/report.html 生成区已过期（kpi-row）` + `[FAIL] … data-metric=results.coverage.latest.score 页面文本 '88.88' ≠ 现算值 '97.46'` + `[FAIL] … '30/32' ≠ '32/32'` | 1 |
| N8 | 豁免 #10 的"全 2 处"改成"全 5 处" | `--summary` | `[FAIL] lint 豁免处数自述与行号解析不一致: #10 自述 5 处 ≠ 行号解析 2 处（登记表内部矛盾，拒绝出数）` | 1 |
| N9 | `bugs.md` BUG-011 归属列改成"未知归属" | `--summary` | `[FAIL] bugs.md BUG-011 的归属列 '未知归属' 无法归入 rtl/infra/spec——分类规则须更新（拒绝静默归入"其他"）` | 1 |
| N10 | `v0.2.0/rev-gate-packet_proc_core.md` 标题改成无关键字 | `--summary` | `[FAIL] doc/evidence/v0.2.0/rev-gate-packet_proc_core.md 标题 '一份没有关键字的记录' 无法归类（里程碑/门禁/仲裁/豁免）——分类规则须更新` | 1 |

还原核验：全部改动经 `git checkout` / `rm` 还原，`git status --porcelain` 输出恒为
```
 M .github/workflows/ci.yml
 M Makefile
?? scripts/report.py
```
即仅剩本轮被审的三件工件，无残留（`doc/evidence/v0.5.0/` 下的临时伪造文件已删除，本文件为唯一新增）。另复跑 `python3 scripts/docs.py --check` = `docs-check 通过`，既有门禁未被本轮操作污染。

### D.3 `--check` 六项：逐项是否恒真（BUG-011 教训对照）

| 项 | 是否恒真 | 我的验证 |
| --- | --- | --- |
| [1/6] spec sha256 | **否**（真实门禁） | 真正的比对在 `collect_project()`，N1 实测 `--check` 直接 exit 1。**但 cmd_check 里这一行是无条件 `print` 的复述句**，不是判定——见 F4 |
| [2/6] 覆盖率摘录 ⇄ 回归摘要 | **否** | N6b 亲手触发 FAIL。**但有条件降级**：文件内出现 ≥2 个互异 `N/N PASS` 时降 warn（N6a 实测），见 F6 |
| [3/6] regress.list ⇄ 最新摘要 | **否** | N5 亲手触发 FAIL |
| [4/6] COV_ANCHORS 漏点守卫 | **否**（真实门禁） | N4 实测 exit 1。同 [1/6]，cmd_check 里也只是复述句 |
| [5/6] 生成区新鲜度 | **否**（但当前未武装） | N7 亲手触发 FAIL。今天三个目标文件都不存在/无标记，故实际是空跑，我用自造的 doc/report.html 证明其逻辑可用 |
| [6/6] 静态 data-metric 比对 | **否**（但当前未武装） | N7 亲手触发 FAIL（两条），这一项专治"生成区外的手写数字"，是本脚本最有价值的一道闸 |

**结论：六项无一恒真，未重演 BUG-011 的 `any(生成器)` 式假门禁。** 但 [1]/[4] 的措辞与 [5]/[6] 的"未武装"状态各有一处须处理，见 F4、条件 C1/C2。

### D.4 附带实测：`make lint` 与豁免登记表的对账（本轮新增发现）

命令（本地 VM，需先设 `VCS_HOME`/`VERDI_HOME`/`LM_LICENSE_FILE`，见记忆件 vm-eda-environment）：
```
make -C sim lint          # 完整 log: sim/out/lint.log
```
退出码 2（该目标见到本仓库范围告警即 exit 1，属预期）。对 `sim/out/lint.log` 按 `(类别, 文件, 行号)` 去重统计，**HEAD 处本仓库范围内共 84 处**：

| 类别 | 文件 | 处数 | 是否已登记 |
| --- | --- | --- | --- |
| SVA-DIU | rtl/apb_slave_if.sv 268,273,278,283,290,295,300,306 | 8 | #2 |
| SVA-DIU | rtl/packet_proc_core.sv **282,287,292,297,302,308,313,321,326** | 9 | #8（**行号已漂移**，处数吻合） |
| SVA-DIU | rtl/packet_sram.sv 61,65,70,74,80 | 5 | #1 |
| SVA-DIU | rtl/ppa_top.sv 166,170,174,178,182,187 | 6 | #9 |
| SVA-DIU | tb/sva/apb_protocol_sva.sv 21,27,32,38 | 4 | #3 |
| SVA-DIU | tb/sva/apb_slave_if_sva.sv 51,57,63,68,73,78 | 6 | #4 |
| **SVA-DIU** | **tb/sva/packet_proc_core_sva.sv 24,29,34,40,45,51,56** | **7** | **未登记** |
| NS | tb/tb_top.sv 20 / apb_driver 20,21,46,49 / apb_monitor 23 | 6 | #5 |
| NS | tb/uvm/core_agent/ppa_core_driver.sv 29,30,47,52,63,76,81,88,90,110 | 10 | #11 |
| NS | tb/uvm/env/m3_stub_driver.sv 26,35,41,43,50,52,57,59,71,74,77,87 | 12 | #7 |
| NS | tb/uvm/test/m3_seq_lib.sv 329,344 | 2 | #10 |
| NS | tb/uvm/test/m4_seq_lib.sv 309,311 | 2 | #11 |
| WMIA-L | tb/uvm/apb_agent/apb_seq_item.sv 10,11,12,13 | 4 | #6 |
| **WMIA-L** | **tb/uvm/test/ppa_m2_01_test.sv 31** | **1** | **未登记** |
| **WMIA-L** | **tb/uvm/test/ppa_m2_02_test.sv 27,42** | **2** | **未登记** |
| 合计 | — | **84** | 已登记 74 / **未登记 10** |

两个副产品：
1. 除 #8 外，**其余 10 条豁免登记的行号与今日实测逐个精确吻合**——这给 sites_total=74 的可信度提供了最强背书，也确认 `sites_line_drift` 只报 #8 是准确的（不多报、不漏报）。另可顺手订正 #11 复核栏提到的 ppa_core_driver「29」：实测 L29 是 `wait (vif.rst_n === 1'b1);`，本身即 NS 类告警点，L29 与 L30 是**两处独立告警**，原登记 10 处正确，当时复核记的"实为 L30"应予撤销。
2. **发现项目缺陷（非本脚本缺陷）**：10 处 lint 告警从未登记豁免，违反 CLAUDE.md §7"告警须修复或登记 `doc/lint-waivers.md` 经 rev 复核"。其中 `tb/sva/packet_proc_core_sva.sv` 的 7 处 SVA-DIU 与已批准的 #3/#4 同类同根因（DV 交付的 bind SVA 用 `disable iff`），`ppa_m2_01/02_test.sv` 的 3 处 WMIA-L 与已批准的 #6 同类。属登记遗漏而非新风险，但按流程必须补登记 + rev 复核。**我按禁区不新增 bugs.md 行，请 orch 登记并派 DV 补登记、另一 rev 实例复核。**

---

## E. 边界与遗留

### E.1 `scripts/docs.py` 零改动

`git diff scripts/docs.py` 输出为空，`git diff --stat scripts/docs.py` 无条目。**确认零改动**，BUG-011 之后的门禁脚本未被本轮触碰。report.py 只 `from docs import …` 复用解析器与路径常量（`parse_table`/`row_cells`/`read_version`/`status_counts`/`count_mod_records`），且对 `spec_revision_count` 做了与 `docs.py count_mod_records` 的双算交叉校验（不等即 FAIL）——复用方式合规。

### E.2 `Makefile` / `ci.yml` 对既有门禁的影响

- **Makefile**：只在 `.PHONY` 追加 4 个新目标名并新增 4 个独立目标块，未改 handover/next/docs-check/bump/evidence 及仿真转发任何一行。既有门禁无影响。实测 `make report`、`make report-check` 均可用。
  - **缺陷**：`report-sync` 只注入 `doc/report.html README.md`，而 `--check` 的 `TARGETS` 是三个（多一个 `doc/presentation/defense.md`）。见 F2。
- **ci.yml**：`fetch-depth: 0` 只影响 checkout 深度。我核对 `scripts/docs.py` 仅在 `--pin-spec` 路径用 git（第 564 行 `git show HEAD:doc/spec.md`），CI 跑的 `--check` / `--handover` 不碰 git，**既有两步硬门禁不受影响**（fetch-depth 变深只会让 pin-spec 更稳，不会更松）。新增第三步 `report.py --check` 今天在本仓库实测 exit 0。
  - **风险**：把 report-check 挂成 CI 硬门禁，等于把展示材料的新鲜度纳入阻塞路径——一旦 R3 的 HTML 含易变字段就会天天红，见 F1，必须先修再合。

### E.3 当前 6 条 warn 在 R3 后是否会自动转为实校验

**不是全部会转，任务卡的假设需要修正**：

| warn | R3 后 | 说明 |
| --- | --- | --- |
| `doc/report.html 不存在，跳过注入` | **会转实校验** | R3 交付后 [5/6] 生效 |
| `doc/report.html 不存在，跳过静态数字比对` | **会转实校验** | [6/6] 生效 |
| `README.md 中没有生成区标记，跳过` | **会转实校验（仅 [5/6]）** | README 的生成内容是 markdown 表（`gen_readme_kpi`/`gen_readme_milestones`），**不带 `data-metric` 属性**，所以 README 永远只受 [5/6] 保护，[6/6] 对它永久跳过。这是可接受的（[5/6] 已足够），但要知道 |
| `doc/presentation/defense.md 不存在，跳过注入` | **不一定** | 讲稿若不放 GEN 标记，[5/6] 对它永久跳过；且 markdown 讲稿基本不会有 `data-metric`，[6/6] 也永久跳过 → **讲稿里的数字将完全不受任何门禁保护**。见 F2 |
| `doc/presentation/defense.md 不存在，跳过静态数字比对` | 同上 | 同上 |
| `v0.1.7 有 2 个互异 N/N PASS 声明 → 降级 warn` | **永久 warn，与 R3 无关** | 该文件天然含首测 7/7 与复测 10/10 两个声明，交叉校验对这一点永久失效。材料不得称"4 份覆盖率摘录全部与回归摘要交叉校验通过"，实为 3 份 |

### E.4 待修清单（按严重度）

| 编号 | 严重度 | 问题 | 修改要求 |
| --- | --- | --- | --- |
| F1 | **中（阻塞 R3）** | `gen_footer_stamp` 与 `gen_data_json` 把**运行期易变量**写进生成区：git HEAD 短 sha、提交总数、`meta.generated_on`（= `date.today()`）。实测证明：把 head 改成 `deadbee`、commits+1、日期 +1 天，同一函数输出即改变。后果——R3 注入并提交 HTML 之后，HEAD 立刻变成新 commit，`--check` 的 [5/6] 判定生成区已过期，**CI 硬门禁在下一次提交起必然长红**；隔天重跑 CI 也会因 `generated_on` 变化而红 | 三选一：(a) 生成区新鲜度比对时对 `footer-stamp`/`data-json` 两个 key 剔除易变字段（引入 volatile key 白名单，注入照旧、比对跳过）；(b) 把 stamp 改成确定性内容（版本号 + spec sha256 + 最近一次触及真值源的 commit），去掉 HEAD/提交数/今日日期；(c) 这两个区不入库、只在发布时渲染。建议 (b) 为主 + (a) 兜底 |
| F2 | **中（阻塞 R3）** | `--check` 的 `TARGETS` 含 `doc/presentation/defense.md`，但 `make report-sync` 只注入前两个 → 讲稿"检查得到、同步不到"；若讲稿不用生成区，其数字则完全无门禁 | `report-sync` 补上 `doc/presentation/defense.md`；并要求 R3 的讲稿把**所有数字**放进 GEN 生成区（或复用 `--md data-baseline` 片段），否则等于对外材料里最容易被追问的一件没有防线 |
| F3 | 低 | `results.regress.note` / `charts.regress.note` 内嵌手写成果数字（`9 个 evidence 目录`、`7/7`、`10/10`、`32/32`），会随数据演进失真，且经 `data-json` 进入 HTML | 改为 f-string 由现算字段填充，或明确标注为"截至 v0.4.1 的说明性注记" |
| F4 | 低 | `cmd_check` 的 `[1/6]`/`[4/6]` 是无条件 `print` 的复述句，真正的门禁在 `collect()` 里 fail-fast（本轮 N1/N4 已证其有效）。当前不恒真，但若日后有人把 `collect()` 改宽松，这两行会**变成**恒真门禁——正是 BUG-011 的形状 | 改成显式断言（如在 cmd_check 内重算一次 sha256 / 重跑漏点守卫并计入 errors），或把措辞改为"（已在取数阶段硬失败，此处仅复述）" |
| F5 | 低 | `derive_milestones` 里 `cov = {p["milestone"]: p for p in …history}`：同一 M 若有多份 coverage-summary，静默只保留最后一份 | 加"同一 M 多份即 warn/FAIL"守卫；当前每 M 仅 1 份，不触发 |
| F6 | 低 | `cov_pass_crosscheck` 在文件含 ≥2 个互异 `N/N PASS` 时降级为 warn（N6a 实测：只改一处即绕过）。v0.1.7 永久降级 | 可接受（已 warn 外显），但材料措辞须按 E.3 修正为"3 份交叉校验通过、1 份因首测/复测并存降级说明" |
| F7 | **项目缺陷（非本脚本）** | HEAD 处 `make lint` 实测 84 处告警，登记表仅覆盖 74 处，**10 处未登记**（tb/sva/packet_proc_core_sva.sv:24,29,34,40,45,51,56；tb/uvm/test/ppa_m2_01_test.sv:31；ppa_m2_02_test.sv:27,42），违反 CLAUDE.md §7 | 请 orch 登记 bugs.md，派 DV 按 #3/#4/#6 同根因补登记豁免，另一 rev 实例复核。**在补齐之前，对外材料不得出现任何"lint 告警全部登记/清零"类表述**（见 B.1） |
| F8 | 低 | 豁免 #8 登记行号已漂移（278…322 vs 实测 282…326）；#11 复核栏"ppa_core_driver 29 实为 L30"的注记有误（L29/L30 是两处独立告警） | 顺手订正登记表行号与该条复核注记（不改处数，不影响任何结论） |
| F10 | **中（阻塞 R3）** | `REVIEW_KIND_RULES` 只认 里程碑/门禁/仲裁/豁免 四个标题关键字，命中不到即 `fail()` 退出。**本记录落盘时当场触发**：原标题「rev 审查记录：scripts/report.py 抽数正确性（R2 gold-standard 独立复算）」→ `[FAIL] doc/evidence/v0.5.0/review-report-tool.md 标题 … 无法归类（里程碑/门禁/仲裁/豁免）——分类规则须更新`，exit 1。这四个词是从 9 份历史记录归纳出的**封闭**分类，而项目还在持续产生新类型的 rev 记录（本轮就是"工具/数据抽取层审查"这一新类）。由于 report-check 已挂进 CI 硬门禁，**"写一份新的 rev 审查记录"从此成了打挂 CI 的动作**，除非作者恰好知道这四个暗号。R3 还会产出更多审查记录，必踩 | 二选一：(a) 扩类目（补 `tool`/`工具`、`数据`/`报告` 等，并把兜底从 `fail()` 降为 `kind="other"` + warn——分类不到只是画不出饼图分组，不该阻断整条出数链）；(b) 若坚持严格分类，则把该 fail 从 `collect()` 移出 CI 阻塞路径。**建议 (a)**：严格失败该用在"取错数会印错材料"的地方（覆盖率取列、处数解析），而不是"给审查记录贴标签"这种纯装饰性分组上。本记录已临时把标题改成含"门禁"绕开（R2 本就是 R3 的交付门禁，措辞属实），但这是权宜，规则本身必须改 |
| F9 | 提示 | `design.rtl_ports` 用全文件正则 `^\s*(input\|output\|inout)` 统计。我用"截出模块端口段再数"的独立算法得到同值（69），但两法同值是当前四份 RTL 恰无端口清单外 input/output 行的巧合 | 非阻塞。若日后 RTL 里出现 task/function 参数或注释形态的 input/output，该数会虚高；建议限定在 module 头范围内统计 |

---

## 总体结论

**有条件通过。**

抽数正确性维度**无条件通过**：
- A 部分十组独立复算 **10/10 一致**（唯一数字差异经核实是脚本给出了更细的正确分解）；
- C 部分 provenance 抽查 **12/12 一致**，另顺带全量核对的 11 个字段亦全部一致，**0 条对不上**；
- D 部分 10 次自设负向验证**全部硬失败退出（exit 1）**，无一处静默默认值/猜测；变异跟随测试证明所有成果数字均由文件读取产生，脚本内不含硬编码成果数字；
- `--check` 六项**无一恒真**，未重演 BUG-011。

放行条件（全部须在 R3 交付展示材料之前完成）：

- **C1（必须）**：修 F1——`footer-stamp` / `data-json` 的易变字段问题。否则 R3 一旦交付 HTML，CI 的 report-check 从下一次提交起必然长红，会逼出 `--no-verify` 文化，比不加这道门禁更糟。
- **C2（必须）**：修 F2——`report-sync` 补 `doc/presentation/defense.md`；且要求 R3 的讲稿把全部数字放进生成区，否则讲稿数字零防线。
- **C2b（必须）**：修 F10——rev 审查记录的标题分类不得再以 `fail()` 阻断整条出数链（本记录落盘时已实测打挂 report-check）。R3 会继续产出审查记录，不修必再踩。
- **C3（必须，措辞）**：三条材料的数字表述遵守本记录的裁决——
  - `sites_total=74` 不进 KPI 带，正文按 B.1 的准入措辞书写；在 F7 补齐之前禁止任何"lint 告警全部登记/清零/干净"表述；
  - 覆盖率曲线按 B.2：M1 点单独 marker、不入折线、注明域不同；M2→M3 的 −4.11 pt 下降如实画出并注解；
  - spec 修订按脚本口径写作"11 次修订，其中 8 次闭环 = 6 次源自 bugs.md 缺陷裁决 + 2 次源自 rev 门禁附带仲裁"，**不得笼统称"8 个 BUG"**；
  - 覆盖率⇄回归交叉校验按 E.3 写作"3 份通过 + 1 份（v0.1.7）因首测/复测并存降级说明"。
- **C4（并行，不阻塞 R3 但阻塞"lint 相关表述"）**：F7 由 orch 登记 bugs.md 并派单补登记 + rev 复核。
- **C5（建议）**：F3 / F4 / F5 / F6 / F8 / F9 在下次触及时顺手修。

`scripts/report.py` 本身作为"待验收的证据生成器"，在抽数正确性、失败严格性、口径外显（domain/comparable/caveat/drift/provenance）四个维度上均达到本记录的验收要求，**建议按上述条件放行进入 R3**。本轮未修改任何被审工件，未 bump、未 commit。
