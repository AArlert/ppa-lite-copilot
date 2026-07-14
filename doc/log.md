# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.4.0] 2026-07-14 M3 收官：ppa_top 顶层集成交付 + BUG-010/r11 落地，里程碑签核通过，进入 M4

**做了什么**
- arch 撰写 `doc/design-prompt/ppa_top.md`（M3 顶层集成设计输入，feature-matrix F3-1），过 rev 门禁（spec 锚点逐条核对 + 行为泄漏检查，通过）。
- rev 门禁审查期间由 arch 发现 §2.1 顶层框图与 §2.3 Top 端口表对 `done_o` 是否为顶层对外引脚存在矛盾，登记 **BUG-010**；rev 仲裁取方向 (a)——`done_o` 为 M3→M1 内部信号（§8.1 已定名），不引出顶层，与 §2.3（唯一权威）对齐；orch 应用 spec 修改记录 **r11**（§2.1 ASCII/mermaid 框图删去 done_o 对外引脚画法，补澄清注）并重新 pin，BUG-010 → SPEC_CHANGED。
- DE 交付 `rtl/ppa_top.sv`（三模块纯连线 + PCLK/PRESETn 统一分发 + 10 条内部连通性/无 X 断言），编译 0 error；lint 仅 6 处 `Lint-[SVA-DIU]`（与已批准的 #1/#2/#8 同类写法），登记豁免 #9，rev 复核批准。
- DV 建 M3-01~M3-05 五条集成场景（端到端链路、连续两帧、STATUS 总线、busy 写保护、中断闭环），改造 `tb_top.sv` 接入真实 `ppa_top`（M1/M2/M3 单元级通路与集成路径物理隔离），全部 PASS；全量回归 22/22 PASS（smoke+M1×9+M2×7+M3×5），M1/M2 零回归。新增 2 处 `Lint-[NS]` 豁免登记 #10（同 #7 根因），待 rev 复核。
- orch 归档里程碑三件人工证据：`result_summary.txt`、`coverage-summary.md`（六类覆盖率含未达标项如实记录）；rev 独立复核签核 `review-m3-milestone.md`——三条硬条件（RTL 就绪+场景全✅、regress 100% PASS、rev 审查记录）均独立验算通过。

**没做什么**
- lint 豁免 #10（DV 登记的 2 处 `Lint-[NS]`）尚未经 rev 复核，遗留给下一周期顺带处理（不阻塞 M3 签核，性质与已批准的 #7 完全相同）。
- 覆盖率六类综合未达 90%（TOGGLE/FSM/COND 主要缺口，另发现 M1 侧 SVA 在集成场景下部分未触发，ASSERT 从模块定义域 100% 降到 ppa_top 集成实例域 88.89%）——按 M2 先例裁定为 M4-02 判据，非 M3 阻塞项，已如实记入 coverage-summary.md 供 M4 参考。
- 未新增 M4（Lab4 回归与覆盖率闭环）相关任何工件，M4 尚未启动。

**下一步**
- `make next` 进入 M4：需 arch 补 M4 相关 design-prompt（若有）或由 orch 直接规划 M4-01~M4-03（一键回归/六类覆盖率闭环/testplan 文档完整性）任务卡；覆盖率缺口（TOGGLE/FSM/COND 及 M1 侧 SVA 集成覆盖）是 M4 的直接工作对象。
- 顺带处理：lint 豁免 #10 送 rev 复核；design-prompt/ppa_top.md 与 apb_slave_if.md 等历史 BUG 遗留的"引用更新"类小尾巴（如有）一并检查。

**如何验证**
- `make handover` / `make next` 查看 M4 起点状态；`git tag v0.4.0` 标记本次里程碑。
- `doc/evidence/v0.3.0/`：`M3-0{1..5}.log`（复现命令 `make run TEST=ppa_m3_0N_test SEED=1`）、`result_summary.txt`（22/22）、`coverage-summary.md`、`review-m3-milestone.md`。
- `doc/bugs.md` BUG-010（SPEC_CHANGED，r11 已 pin）；`doc/lint-waivers.md` #9（已批准）/#10（待复核）。

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

