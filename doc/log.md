# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.3.0] 2026-07-14 M2 收官：BUG-009 端序缺陷两轮闭环 + 里程碑签核，进入 M3

**做了什么**
- 派全新 DV 建 M2-01~07 场景（新建 core agent、M2 test 套件、`packet_proc_core_sva.sv`），首轮 7 test 全 FAIL，同一根因登记 **BUG-009**：packet_proc_core 包头/payload 字节内端序与 spec 附录 A/B 相反（RTL 小端，附录钉大端），正文未显式规定 bit 位、只由附录示例隐含。
- 派 rev 仲裁 BUG-009：独立验算纠正 DV 详情页一处不严谨推理（hdr_chk XOR 自洽对端序对称、不能作判据），改用附录显式字段值+结果级隔离约束定案，裁决 **方向(A)：附录大端为准，判 RTL bug**，M1 零回归风险确认。
- 派 DE 首次修复（commit `9c28fea`）：仅改组合抽取路径（L76-79 头字段、L143-146 payload），遗漏头字段锁存 `always_ff`（L222-225 仍小端）。DV 复验（同一 DV 实例，≠修复人）**驳回**，精确定位多字帧走锁存路径致 M2-01/02/03/06/07 仍 FAIL，退回 OPEN。
- 派全新 DE 二次修复（commit `b8a1890`）：锁存路径改大端，并独立核实 payload 累加器（存算术中间值而非字节镜像）无同类遗漏。DV 复验全部 PASS（17/17 回归），`make evidence BUG=BUG-009` 关单 CLOSED，M2-01~07 全部回填 ✅。
- 补齐 M2 里程碑三件套：`sim/result_summary.txt` 复制入 `doc/evidence/v0.2.3/`；DV 跑 `make -C sim regress COV=1` 产出六类覆盖率（`coverage-summary.md`，如实记录 TOGGLE/FSM 偏低）；派全新 rev 做里程碑签核（`review-m2-milestone.md`），独立验证 spec §11.5 覆盖率门槛只适用 M4-02、不卡 M2，**签核通过**。
- 清理会话开始时遗留的旧仿真产物 `sim/result_summary.txt`（stale，非本轮生成）。

**没做什么**
- 覆盖率 TOGGLE(59.63~71.44%)/FSM(60%)/packet_proc_core COND(89.47%，差 0.53pt) 未达 90%，按 rev 裁决属 M4-02 范畴，未在本轮补随机化/多 seed 激励。
- M2-07 负向观测（busy 期间写 CFG/PKT_LEN_EXP 不报 PSLVERR）单元级无 APB 端口，下沉到 M3 集成 test，本轮未覆盖。
- spec 附录端序未在正文 §3.1/§6.1 显式化、附录 B.3(spec.md:881) 注释算式笔误（应 0x04^0x01^0x00=0x05）——rev 建议 arch 走 §8 澄清，本轮未派 arch。
- lint-waivers.md 豁免 #8 行号因两次 RTL 修复新增注释而漂移（278→282 起，语义未变）——rev 复核时提示，未处理。

**下一步**
- 进入 M3（Lab3）：按 `make next` 派 arch 出 M3 design-prompt（spec 相关章节待定），过 rev 门禁后派 DE/DV。
- 顺带处理：① 派 arch 走 §8 提案 spec 附录端序正文显式化 + B.3 笔误订正；② lint-waivers.md #8 行号对齐；③ M2-07 负向观测、覆盖率缺口计入 M3/M4 待办。

**如何验证**
- `cat version.json` = 0.3.0/M3；`git tag` 含 `v0.3.0`。
- `grep -n "^| BUG-009" doc/bugs.md` 状态 CLOSED，两个修复 commit 均在列；`grep -n "^| M2-0" doc/testplan.md` 七行全 ✅。
- `ls doc/evidence/v0.2.3/` 含 BUG-009.log、M2-01~07.log、result_summary.txt、coverage-summary.md、review-bug-009-arbitration.md、review-m2-milestone.md。
- `python3 scripts/docs.py --check` 通过；`make next` 显示 M2 三条硬条件已齐、下一步指向 M3。

## [0.2.3] 2026-07-13 rev 复核 lint 豁免 #8 + 仲裁 BUG-008 并应用 spec r10

**做了什么**
- 登记 `doc/bugs.md` BUG-008：packet_proc_core 的 `algo_mode`/`type_mask`/`exp_pkt_len` 三个配置 CSR 无"取样点"spec 条文（design-prompt 已列为唯一未决项）。
- 派 rev（隔离新实例）复核 `doc/lint-waivers.md` 豁免 #8（packet_proc_core 9 处 SVA-DIU）：通过，逐条核实与 #1/#2 同类主张、实测 `make -C sim lint` 判定范围内无未处置新增；至此豁免 #1–#8 全部完成 rev 复核。审查记录 `doc/evidence/v0.2.2/review-lint-waiver-8.md`。
- 派另一 rev 实例仲裁 BUG-008：裁决方向 (B)——三个 CSR 不做 start 时刻快照锁存、M3 组合取当拍活值判定（结果于 PROCESS→DONE 拍寄存），配套软件契约（start 前配置好、busy 期间保持不变，busy 期间改写不受写保护但生效 UNSPECIFIED）；否决强制锁存与硬件写保护两个方向。**RTL 无需返工**（DE 现有实现已与裁决一致）。
- orch 应用裁决：spec.md 新增修改记录 r10，§5.2/§6.3/§7.2/§7.3 补帧级配置契约注，`pin-spec` 重新钉住；BUG-008 状态置 SPEC_CHANGED；`doc/testplan.md` 新增 M2-07 锁定该行为（含 busy 期间写 CFG 不报 PSLVERR 的负向观测）；`doc/design-prompt/packet_proc_core.md` 已裁决歧义段落补 BUG-008/r10、未决项清空、验收关联补 M2-07 引用。

**没做什么**
- 未派 DV：M2-01~07 场景仍全部 🔲，本轮只到 spec/testplan/文档层面，未产生仿真证据。
- lint-waivers.md #8 审查记录提到的非阻塞观察（"尚未接入 tb_top"措辞已过时）未修正，留给下次触及该文件时顺带处理。

**下一步**
- 派全新 DV 实例：输入 = spec §5.2/§6.3/§7/§9/§10 相关章节 + `tb/uvm/env/ppa_reg_defs.sv` + testplan M2-01~07（现七行全 🔲），需先建立 M2 独立 TB 或替换 `m3_stub_if` 桩驱动才能跑通。
- DV 编写 M2-07 checker 时直接依据 spec r10 注（组合取值、不锁存、软件契约稳定窗口=start 至 done），不得构造 busy 期间改配置的激励卡 DUT（UNSPECIFIED 区，spec 已注明）。

**如何验证**
- `grep -n "r10" doc/spec.md`；`cat doc/spec.sha256` 与 `python3 -c "import hashlib;print(hashlib.sha256(open('doc/spec.md','rb').read()).hexdigest())"` 比对一致。
- `grep -n "^| BUG-008" doc/bugs.md` 确认状态 SPEC_CHANGED；`grep -n "^| 8 " doc/lint-waivers.md` 确认复核状态列。
- `grep -n "^| M2-07" doc/testplan.md`。
- `python3 scripts/docs.py --check` 通过。

## [0.2.2] 2026-07-10 DE 交付 packet_proc_core RTL（本地真跑通过）

**做了什么**
- 派全新 DE 实例（Sonnet 5）实现 `rtl/packet_proc_core.sv`：3 态 FSM（IDLE/PROCESS/DONE）、字计数器驱动 `mem_rd_addr_o`、第 0 拍同拍组合读提取头部（r6）、三类错误并行判定（length/type/chk）、payload sum/xor 逐拍累加（末拍含本拍贡献）、`res_pkt_len_o` 恒 = Byte0[5:0]（BUG-P2/r9）、读拍钳位 [1,8]（BUG-P1/r8）。逐条对照 design-prompt 无新增对外可见行为。
- 新增 9 条内部不变量断言（FSM 合法编码、busy/done 互斥、mem_rd_en_o 仅 PROCESS 拍、读拍计数边界、PROCESS 忽略 start、PROCESS 期间输出保持清零、algo_mode=0 时 chk_error 恒 0、DONE 态 format_ok 一致性）。
- `sim/flist/rtl.f` 按文件自身约定取消注释纳入编译（模块尚未接入 tb_top，仍是独立 top 编译自检，不影响现有仿真）。
- 本地 VM 真跑：`make -C sim compile` 0 error/0 warning；`make -C sim lint` 判定范围内新增 9 条 `Lint-[SVA-DIU]`（与已批准的 #1/#2 同类同因，`disable iff` 屏蔽复位期断言的标准写法），登记 `doc/lint-waivers.md` 豁免 #8（登记人=DE，待 rev 复核）；`make smoke` 复跑两次均 PASS，无回归。orch 抽查 RTL 逻辑（读拍钳位边界、pkt_len=0/>63 两个裁决角点、清零/累加时序）与 design-prompt/spec 对照未见矛盾。

**没做什么**
- 未派 DV：本轮只到 RTL 交付，M2-01~06 场景尚未落地，testplan 仍是 🔲。
- lint 豁免 #8 未经 rev 复核，不构成正式豁免。
- 模块未接入 `tb_top.sv`（仍连 `m3_stub_if`），接入属 DV/集成职责，design-prompt"明确不做"已排除。
- "配置取样点"（algo_mode/type_mask/exp_pkt_len 帧中改写时取样行为）仍未登记/未提案，DE 自认输入取当拍活值，未做特殊处理；不阻塞当前 M2-01~06 场景。

**下一步**
- 派 rev 复核 lint 豁免 #8（可与后续 DV 阶段的门禁合并，或单独一轮）。
- 派全新 DV 实例：输入 = spec §7/§9/§10 相关章节 + `doc/spec.md` §2.3 端口表 + testplan M2-01~06，不接收 DE 推理过程；建场景 + 接口 SVA，需先建立 M2 独立 TB 或替换 `m3_stub_if` 桩驱动才能跑通。
- DV 编 checker 前先处理"配置取样点"未决项（登记 bugs.md 或 arch 出提案）。

**如何验证**
- `cat rtl/packet_proc_core.sv`；`grep -n "^| 8" doc/lint-waivers.md` 确认豁免 #8 待复核。
- 本地 VM：`make -C sim compile`（0 error/0 warning）、`make -C sim lint`（判定范围内仅 #1~#8 已登记告警）、`make smoke`（PASS）。
- `python3 scripts/docs.py --check` 通过。

