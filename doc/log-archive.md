# 交接日志归档

> 默认不读。仅在追溯历史时用 grep 定位（如 `grep -n "\[0.1" doc/log-archive.md`）。
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

## [0.2.1] 2026-07-10 M2 packet_proc_core design-prompt 交付 + rev 门禁通过 + spec r8/r9 落地

**做了什么**
- 派 arch 新实例（Fable 5）撰写 `doc/design-prompt/packet_proc_core.md`：spec §2.3/§7/§9/§10/§11.3 等章节逐条锚点、功能要求对应 testplan M2-01~M2-06、边界约束、内部断言建议、明确不做。撰写中发现两处 spec 空白，未擅自拍板，转成修改提案 P1/P2 交 rev 仲裁。
- 派 rev 新实例（Fable 5）做 design-prompt 门禁（spec 锚点核对+行为泄漏检查）+ 仲裁 P1/P2，书面记录 `doc/evidence/v0.2.0/rev-gate-packet_proc_core.md`：
  - **门禁：通过（有条件）**——无行为泄漏、无锚点失配、feature 分解无遗漏。
  - **P1 裁决**：§7.3 r5 读拍数公式 `min(ceil(pkt_len/4),8)` 在 pkt_len=0 时算出 0 拍，与"第 0 拍必然发生"矛盾；裁决补下界，钳位区间改为 [1,8]（`min(max(ceil(pkt_len/4),1),8)`），pkt_len=0 帧 PROCESS 仅第 0 拍即进 DONE。
  - **P2 裁决**：`res_pkt_len_o` 6-bit vs pkt_len 8-bit，非法大包长（>63）取值未定义；裁决恒 = Byte0[5:0]（低 6 位截断），不并入 r5 UNSPECIFIED 集合，pkt_len>63 时必伴 length_error=1，可验可比对。
- orch 落地两条裁决入 spec.md：新增修改记录 `r8`（P1，§7.3 读拍数下界）、`r9`（P2，§3.4/§2.3/§5.2 res_pkt_len 截断定义），`--pin-spec` 重新钉住；同步 `packet_proc_core.md` 两处受影响文字（P1 临时底线句、P2 待决句）改为引用 r8/r9，"已裁决歧义"补齐 BUG-P1/P2 两条，"未决"清空（仅剩非阻塞的配置取样点，待后续登记）；`doc/testplan.md` M2-02 期望列补充 [1,8] 区间与建议追加激励（pkt_len=0、pkt_len>63）。

**没做什么**
- 未派 DE：门禁虽通过但本轮未启动 RTL 实现，design-prompt 交付即停，等待下一轮派单。
- 遗留风险（非阻塞，rev 记录第五节指出）：配置取样点（algo_mode/type_mask/exp_pkt_len 帧中改写时的取样行为）无正式提案、bugs.md 未登记；当前 M2-01~06 场景不涉及，不阻塞派单，但需在 DV 编 checker 前补登记，避免 DE/DV 默认假设（寄存采样 vs 组合直通）不一致产生假 mismatch。
- testplan M2-02 只更新了期望描述文字，未新增激励用例条目（pkt_len=0/>63 是否单独开场景留给后续 DV 实例决定）。

**下一步**
- 派全新 DE 实例：输入 = `doc/design-prompt/packet_proc_core.md`（已过 rev 门禁）+ spec §7/§9/§2.3 相关章节，实现 packet_proc_core RTL。
- DE 交付后派全新 DV 实例建 M2-01~M2-06 场景 + 接口 SVA（不接收 DE 推理过程）。
- 责成后续 arch/orch 实例为"配置取样点"行为登记 bugs.md 或出正式提案，在 DV 编写相关 checker 前裁决。

**如何验证**
- `cat doc/design-prompt/packet_proc_core.md` 核对已裁决歧义节含 BUG-P1/r8、BUG-P2/r9，未决项清空。
- `cat doc/evidence/v0.2.0/rev-gate-packet_proc_core.md` 看门禁与仲裁全文。
- `grep -n "^| r[89]" doc/spec.md`；`grep -n "r8\|r9" doc/spec.md`（§7.3/§3.4/§2.3/§5.2 均已引注）；`python3 scripts/docs.py --check` 通过（含 spec pin 校验）。

## [0.2.0] 2026-07-10 rev 裁决 M1 toggle 覆盖率口径 + 豁免#7 追加复核 → M1 收官，进入 M2

**做了什么**
- 派新 rev 实例裁决两项悬而未决的 M1 收尾事项（`doc/evidence/v0.1.9/rev-review-toggle-lint7.md`）：
  1. **toggle 覆盖率口径**：裁定 spec §11.5（M4）才是「五类覆盖率 ≥90% 验收」+「过滤登记表」的判据挂载点，spec §0 #7 只是项目级口径定义；spec §11.2（M1）验收项仅三条功能项，无覆盖率门槛；CLAUDE.md §4.1 三条硬条件也不含覆盖率。据此 toggle 73.32% **不阻塞 M1 tag**。结构性零翻转 26 bit（PRDATA[31:8]/PREADY/rst 单次复位）判定**豁免**，真实缺口 45+ bit（CFG/PKT_LEN_EXP 写通路、CTRL/IRQ_EN 回落沿、M3 stub 结果多样性）判定**顺延 M2/M3**（M4 强制回访，届时无结构性理由不得再豁免）。
  2. **lint 豁免 #7 追加 4 处**（`m3_stub_driver.sv:71,74,77,87`，`read_sram`/`watch_start_pulse` 内 `Lint-[NS]`）：逐行核对根因与首批 8 处一致，批准豁免，#7 扩为全 12 处。
- orch 落地：新建 `doc/coverage-waivers.md`（6 条登记：3 条豁免共 26 bit + 3 组顺延 M2M3 共 45+ bit，附 M4 强制回访清单）；`doc/lint-waivers.md` #7 行结论栏改「豁免（全 12 处）」、复核栏补 rev 2026-07-10 批准记录。
- `python3 scripts/docs.py --check` 通过 → **M1 三条硬条件确认齐全**（RTL 交付 6/6+feature-matrix 场景 9/9 ✅、`make regress` 10/10 PASS 证据归档、rev 审查记录×3 存 doc/evidence/）→ `make bump-minor` 进入 M2，随后打 tag `v0.2.0`。

**没做什么**
- 未新增/修改任何 RTL/TB 代码，未重跑仿真（沿用 v0.1.7 证据与复测数据，未过期）。
- `doc/coverage-waivers.md` 中「顺延M2M3」的 45+ bit 缺口未实际闭合，只是登记跟踪，留待 M2/M3 联调或后续场景。
- M2（packet_proc_core）的 design-prompt 尚未起草，本轮只完成 M1 收官，未派发 M2 设计任务。

**下一步**
- 派 arch 出 M2 design-prompt（packet_proc_core，spec 对应 Lab2 章节），过 rev 门禁（行为泄漏检查）后派 DE。
- M2 场景落地前 DV 先在 testplan.md 登记 M2-01~M2-06 场景行细节（目前是占位 🔲）。
- doc/outlook.html 按文件头 SYNC 标记同步本次里程碑/版本变化（version 0.1.9→0.2.0，milestone M1→M2）。

**如何验证**
- `cat doc/evidence/v0.1.9/rev-review-toggle-lint7.md` 看裁决全文；`cat doc/coverage-waivers.md` 核对 6 条登记；`grep -n "^| 7" doc/lint-waivers.md` 确认 #7 已更新为全 12 处。
- `cat version.json`（应为 0.2.0/M2）；`git tag -l v0.2.0`；`python3 scripts/docs.py --check` 通过。

## [0.1.9] 2026-07-09 新增 doc/outlook.html 项目一览（Agent 可低 token 维护的可视化快照）

**做了什么**
- 新建 `doc/outlook.html`（用户指定需求，orch 汇总现有事实直接绘制）：三章可视化快照——Ⅰ harness 工作流（make 闭环、四角色派单与实例隔离、缺陷闭环、滚动归档表）、Ⅱ RTL 设计（系统框图带真实信号名、包格式、CSR 表、模块M3 FSM、交付现状；显式澄清模块编号与里程碑编号是两套体系）、Ⅲ UVM 验证（组件树、config_db/virtual interface 双世界桥、base test 模板方法与回归清单）。纯 HTML/CSS 盒子图（无 SVG 坐标），自适应亮暗主题，自包含无外部依赖
- 文件开头放置渲染后不可见的 Agent 维护说明：grep `id="` 取骨架、grep `SYNC:` 列出五个易变数据点（version/milestone/coverage/bugs/tests）后局部 Edit，禁止通读全文件

**没做什么**
- 本轮无 RTL/TB/脚本改动；toggle 覆盖率口径裁决、豁免 #7 追加 4 处复核、M1 tag 仍悬（见 0.1.8 块）
- outlook.html 未纳入 docs-check 守卫（快照文档允许滞后，SYNC 标记靠约定维护）

**下一步**
- 同 0.1.8 块：派 rev 裁决 toggle 口径 + 复核 #7 追加项 → 打 M1 tag → arch 出 M2（packet_proc_core）design-prompt
- 里程碑推进/结构变化时按文件头维护说明同步 outlook.html 的 SYNC 数据点

**如何验证**
- 浏览器打开 `doc/outlook.html`（亮/暗主题各看一遍）；`grep -c 'SYNC:' doc/outlook.html`（应 ≥6 处标记）
- `python3 scripts/docs.py --check` 通过

## [0.1.8] 2026-07-09 bugs/lint-waivers 滚动归档机制 + 豁免 #5-7 复核批准 + BUG-006/007 关单 + M1 覆盖率收窄（仅剩 toggle 未达标）

**做了什么**
- **bugs.md / lint-waivers.md 滚动归档机制**（orch 直改 scripts/，同 BUG-007 先例）：`make docs-archive` 现在会把 bugs.md 终态行（CLOSED/TB_BUG/SPEC_CHANGED/WONTFIX，保留最新 2 条）搬入 `doc/bugs-archive.md`、把 lint-waivers.md 已批准豁免行（保留最新 2 条）搬入 `doc/lint-waivers-archive.md`；活跃缺陷/待复核豁免永不归档。docs-check 新增守卫：终态缺陷行 >4、已批准豁免行 >6 报错提示归档，缺陷 ID/豁免编号跨归档查重，孤儿详情页校验覆盖归档，归档件混入活跃行即拦截。已实跑一轮：BUG-001/002/003 与豁免 #1/#2 入归档。CLAUDE.md §3 同步
- **rev 复核 lint 豁免 #5/#6/#7**（opus 实例）：18 处告警全部批准；实跑 lint 对账判定范围内 41 条告警与 #1~#7 一一对应、无未登记新增。审查记录 `doc/evidence/v0.1.7/rev-review-waivers-5-7.md`；#6 原因栏"6 处"笔误 orch 已更正为 4 处
- **BUG-006/007 复验关单**（DV 实例，关单人≠修复人）：BUG-006 按收窄范围 lint 对账 PASS、BUG-007 按登记步骤脏 out 直接 regress 无 VFS_SDB_ERROR 假失败，均 `make evidence BUG=<ID>` 机械关单置 CLOSED（`doc/evidence/v0.1.7/BUG-00{6,7}.log`）
- **M1 覆盖率采集 + 收窄**（两个 DV 实例）：首测 cond 80.43%/toggle 60.91%/assert 78.26% 三类不达标；补场景 M1-07（enable→START 两步序列+单拍脉冲）/M1-08（busy=1 写 PKT_MEM 保护）/M1-09（packet_sram 读口同拍组合读，锁定 r6/BUG-003 裁决行为），`make regress COV=1` **10/10 PASS**，复测 line 94.92%✅ cond 91.30%✅ branch 95.12%✅ assert 100%✅、fsm 结构性 N/A、**toggle 73.32% 仍 ❌**。testplan M1 9/9 ✅，证据 `doc/evidence/v0.1.7/M1-0{7,8,9}.log` + `coverage-summary-M1.md`（含首测/复测与缺口分层）+ `result_summary.txt`
- TB 侧配套：`m3_stub_if` 增 rd_en/rd_addr/rd_data 与 start_pulse 观测、`tb_top` 把 sram 读口从常量 0 改接 stub、`m3_stub_driver` 增 read_sram/watch_start_pulse task（新增 4 处 Lint-[NS] 追加登记豁免 #7，待 rev 复核）

**没做什么**
- **未打 M1 tag**：`make next` 机械三条件已齐，但 spec §0 适配 7 要求六类 ≥90%，toggle 73.32% 未达标，orch 判定不收官。toggle 剩余缺口已分层（见 coverage-summary-M1.md 复测章节）：①结构性零翻转约 26 bit（PRDATA[31:8] 字段≤8bit 硬上限、PREADY 恒 1、rst 单次复位）——待 rev 裁决豁免口径；②真实缺口约 45+ bit（CFG/PKT_LEN_EXP 从未写入、enable/IRQ_EN 无 1→0 回落沿、stub res_* 单向置位）——补场景可闭合或顺延 M2/M3 联调
- 豁免 #7 追加的 4 处（read_sram/watch_start_pulse）未经 rev 复核
- design-prompt/apb_slave_if.md 与 RTL 顶部注释的 BUG-004 陈旧措辞仍未同步 r7（低优先级遗留）

**下一步**
- 派 rev：裁决 toggle 覆盖率口径（结构性 26 bit 是否豁免/如何登记过滤；真实缺口 45+ bit 是 M1 必闭还是顺延 M2/M3）+ 顺带复核豁免 #7 追加 4 处
- 按裁决执行：需补场景则派 DV，需登记过滤则建覆盖率豁免登记（仿 lint-waivers 格式）；toggle 口径闭合后打 M1 tag（bump-minor 进 M2）
- M2 前置：arch 出 packet_proc_core 等 M2 design-prompt（过 rev 门禁）

**如何验证**
- 本地 VM：`make regress COV=1`（10/10 PASS）+ `make cov`；`make lint`（收窄范围内全部已登记，含归档件，grep 两文件核对）
- `python3 scripts/docs.py --check` 通过；`make docs-archive` 幂等（再跑显示无需归档）
- `grep -n "BUG-00[67]" doc/bugs.md`（均 CLOSED 带证据）；覆盖率数据 `doc/evidence/v0.1.7/coverage-summary-M1.md` 对照 `sim/out/urgReport/`

## [0.1.7] 2026-07-09 M1 首轮场景全 PASS（DV 交付）+ 里程碑抽查 + BUG-005 关单 + BUG-006/007 处置 + 修复回归假失败

**做了什么**
- **M1 全部 6 个场景首次真实 PASS**：DV 交付 UVM 场景（`ppa_m1_01~06_test`）+ 接口/协议 SVA（`tb/sva/apb_protocol_sva.sv`、`apb_slave_if_sva.sv`，逐条标 spec 章节号）+ DUT 接入（`tb_top.sv` 例化 apb_slave_if/packet_sram，M3 结果输入用受控 `m3_stub_if`/`m3_stub_driver` 驱动，非写死 initial block）。`make regress` 7/7 PASS，orch 独立复验可复现；证据 `doc/evidence/v0.1.6/M1-0{1..6}.log` 均 `make evidence` 机械生成。testplan M1 六行全 ✅
- **rev 里程碑抽查**（`doc/evidence/v0.1.6/rev-review-M1.md`）：M1 完成三条硬条件中①②③均核实（RTL 就绪+场景全✅、regress 可复现 PASS、rev 审查记录），代码审查确认 r6/r7 裁决在 RTL 中正确落地；但**指出覆盖率未采集**（spec §0 适配 7 要求六类 ≥90%，本轮无证据）与**回归假失败风险**（脏 `sim/out` 复用致 `constraint.sdb` 损坏），**建议覆盖率证据补齐前不打 `v0.1.6` 里程碑 tag**——本轮未打 tag，M1 功能完成但里程碑包装（覆盖率+result_summary 归档）留待下一轮
- **BUG-005 关单**：DV 复验 `make compile`/`make regress` 后 `make evidence BUG=BUG-005` 机械生成证据置 CLOSED（`doc/evidence/v0.1.6/BUG-005.log`），关单人≠修复人（orch 是修复人）
- **BUG-006 处置**：DV 任务中途因 API session 限额中断，orch 核实并补完——`Lint-[NS]`（6处）/`Lint-[WMIA-L]`（4处）登记豁免 `doc/lint-waivers.md` #5/#6（0.1.0 遗留，待 rev 复核）；`Lint-[ULCO]`（`ppa_ref_model.sv` 3 处比较，共 6 子表达式）直接加 `int'(...)` 显式转换修复（非豁免），orch 复验 regress 无回归。另发现本轮新交付的 `tb/uvm/env/m3_stub_driver.sv` 有 8 处同类 `Lint-[NS]` 未登记（非 BUG-006 范围内的 0.1.0 遗留），补登记豁免 #7。状态置 FIX_READY（commit 见下一提交，本次先降 OPEN，避免自引用）
- **新登记 BUG-007（infra，orch 直接修复）**：rev 里程碑抽查发现 `make regress` 在残留 `sim/out`（如刚跑过 `make lint`）上运行会因构建数据库损坏产生假失败（4/7），`make clean` 后才 7/7。`scripts/regress.py` 加了清理步骤（回归前自动 `make -C sim clean`），orch 复验：故意先跑 `make lint` 弄脏 `out/` 后不手动 clean 直接 `make regress`，7/7 PASS，修复有效
- 全程用 `` `ifndef SYNTHESIS`` 包裹的断言写法核实：`rtl/apb_slave_if.sv`（261-311 行）、`rtl/packet_sram.sv`（54-85 行）全部断言都在综合排除块内，综合工具定义 `SYNTHESIS` 宏时会被预处理器跳过，不会进综合网表

**没做什么**
- M1 覆盖率（line+cond+fsm+tgl+branch+assert 六类 ≥90%）未采集/未归档，`v0.1.6`/`v0.1.7` 均未打里程碑 tag，等覆盖率证据后再补
- `doc/lint-waivers.md` #5/#6/#7（共 18 条）尚未经 rev 复核批准（#1~#4 已批准）
- `sim/result_summary.txt` 尚未复制入 `doc/evidence/` 目录（里程碑人工三件之一，随覆盖率一起补）
- `doc/design-prompt/apb_slave_if.md` 与 RTL 顶部注释里 BUG-004 OPEN 的陈旧措辞仍未同步成 r7 引用（低优先级，非本轮阻塞项）

**下一步**
- 派 rev 复核 lint-waivers.md #5/#6/#7
- 采集覆盖率（`make regress COV=1` + `make cov`），六类是否达标；不达标需再派 DV 补场景
- 覆盖率达标后：`sim/result_summary.txt` 复制入 `doc/evidence/v0.1.7/`，补齐里程碑人工三件，可考虑 `git tag v0.1.7`（或对应版本）标记 M1 完成
- BUG-005/006/007 复验关单后续跟进

**如何验证**
- 本地 VM：`cd sim && make regress`（7/7 PASS，独立可复现）；`make lint`（收窄范围内仅 #1~#7 已登记告警，无新增未处置发现）
- `python3 scripts/docs.py --check` 通过；`grep -n "BUG-00[5-7]" doc/bugs.md` 核对状态；`cat doc/evidence/v0.1.6/rev-review-M1.md` 看里程碑抽查记录

## [0.1.6] 2026-07-09 M1 apb_slave_if/packet_sram RTL 首次交付 + 修复 sim 构建顺序（BUG-005）+ BUG-004 裁决落地 spec（r7）

**做了什么**
- **M1 两模块 RTL 首次交付**：DE 分别交付 `rtl/apb_slave_if.sv`、`rtl/packet_sram.sv`（各含内部不变量断言），`sim/flist/rtl.f` 对应两行已启用；本地 VM 真实 `make -C sim compile` 通过（0 error/0 warning，两模块均入编译）
- **BUG-005（infra，orch 直接修复）**：`sim/Makefile` `FLISTS` 原顺序 `rtl.f` 先于 `tb.f`，导致 RTL `import ppa_reg_defs_pkg` 报"包未定义"；改为 `tb.f` 先于 `rtl.f` 后本地实测编译通过。因修复 commit 存在自引用问题（提交前不知自身 hash），bugs.md 暂留 OPEN，回填 commit 后随附属小提交置 FIX_READY（复验关单人待 DV 指派）
- **lint 门禁范围收窄（orch 直接修复）**：`make lint` 原判定对供应商 UVM-1.2 库头文件告警也计入失败，事实上永不可能通过；改为仅统计 `../rtl/` `../tb/` 范围。收窄后确认两个新 RTL 文件仅剩 13 条 `Lint-[SVA-DIU]`（DE 已登记 `doc/lint-waivers.md`，**rev 已复核批准**）；另发现 tb/ 范围 17 条 0.1.0 遗留告警（非本轮引入），登记 **BUG-006**（OPEN，待派 DV/rev 处置）
- **BUG-004 rev 裁决（2026-07-09）由 orch 落地**：DE 实现 apb_slave_if 时发现 spec §6.3"APB 读 PKT_MEM 返回真实内容"与 §2.3 端口表结构性冲突（M1 无读回端口）；rev 通读 §11.2 验收范围等章节后裁决收窄 §6.3——APB 读 PKT_MEM 窗口一律 PSLVERR=0、PRDATA=32'h0 占位值，否决新增读回端口方案（零验收收益、增复杂度）。spec r7 已落地并 `--pin-spec`；两模块 RTL **均无需返工**（DE 临时实现恰好与裁决一致）；testplan 新增 M1-06 锁定该行为
- BUG-003 承接自上一版本（0.1.5 已 SPEC_CHANGED，本版无新动作）

**没做什么**
- `doc/design-prompt/apb_slave_if.md` 中 BUG-004 OPEN 的临时处理措辞、`apb_slave_if.sv` 顶部同类注释，均未同步改引用 r7（rev 评估为纯注释性、非行为返工，留待下次触及该文件时顺带处理）
- BUG-006（tb/ 17 条遗留 lint 告警）未处置，未派单
- BUG-005 修复 commit 未回填（本提交后紧跟一个小提交回填）
- 两模块尚未派 DV：testplan M1 全部 6 行仍 🔲，无 UVM 场景/接口 SVA，未跑过 `make smoke`

**下一步**
- 按 `make next`：可派全新 DV 实例为 M1-01~06 建场景 + 接口 SVA，跑 `make smoke`/`make run` 出首个真实证据
- BUG-006（tb/ lint 遗留）需 orch 决定派 DV 修复还是批量登记豁免经 rev 复核
- design-prompt/apb_slave_if.md 与 RTL 注释的 r7 引用同步（低优先级，可并入下次 DE 触及该模块时处理）

**如何验证**
- 本地 VM：`cd sim && make compile`（0 error/0 warning）、`make lint`（仅报本仓库范围告警，当前为 rtl/ 13 条已豁免 SVA-DIU + tb/ 17 条 BUG-006 遗留，无新增未处置项）
- `python3 scripts/docs.py --check` 通过；`grep -n "r7" doc/spec.md` 可见 BUG-004 裁决条文；`grep -n "BUG-00[3-6]" doc/bugs.md` 核对状态

## [0.1.5] 2026-07-09 M1 两个 design-prompt 交付 + BUG-003 裁决落地 spec（r6）+ CLAUDE.md 固化 push 纪律

**做了什么**
- **M1 design-prompt 交付**：arch 撰写 `doc/design-prompt/apb_slave_if.md`、`packet_sram.md`，端口逐字对齐 spec §2.3、边界约束逐条标 spec 章节号；rev 门禁审查（spec 锚点核对+行为泄漏检查）——apb_slave_if.md 有条件通过（字节拆分职责措辞与 packet_sram.md 自相矛盾）、packet_sram.md 通过（读时序待裁决项已标注不得私定）；已派第二个 arch 实例落地修正，两文件 `docs-check` 通过
- **BUG-003 rev 裁决（2026-07-09）由 orch 落地**：arch 撰写 packet_sram.md 时发现 spec §2.2/§2.3"同步 SRAM"与 §7.3"第 0 拍同拍读并提取头字段"对读延迟拍数的暗示相互矛盾；rev 独立通读 spec 裁决为**同拍组合读**（rd_en=1 当拍 rd_data 有效，写端口同步写），spec r6（§2.3 M2 表补注、§7.3 第 0 拍补说明）已 `--pin-spec`；packet_sram.md 读时序约束与写后读断言同步；bugs.md BUG-003 回填裁决并置 SPEC_CHANGED
- **CLAUDE.md §6 / closeout skill 固化收尾推送纪律**：按用户要求，`/closeout` 收尾流程新增第 8 步 `git push`（标注为用户长期授权、无需每次再问，失败如实汇报不静默跳过不 force push）

**没做什么**
- 两份 design-prompt 尚未派 DE：M1 RTL 仍为零，全部场景 🔲
- packet_sram.md 遗留一处未决项（SRAM 复位初值语义未在 spec 明文），影响面小，暂未走提案，留待 M1-02 验收需要时再处理
- packet_proc_core.md / ppa_top.md（M2/M3/顶层 design-prompt）仍未撰写，等对应 M 启动时补

**下一步**
- 按 `make next`：两份 M1 design-prompt 均已过 rev 门禁，orch 可派全新 DE 实例分别实现 apb_slave_if / packet_sram RTL
- DE 交付后派全新 DV 实例建 testplan M1-01~05 场景 + 接口 SVA，跑 `make smoke`/`make run` 验证

**如何验证**
- `python3 scripts/docs.py --check` 通过；`grep -n "r6" doc/spec.md` 可见 BUG-003 裁决条文；`cat doc/design-prompt/apb_slave_if.md doc/design-prompt/packet_sram.md` 核对格式与 spec 锚点
- `grep -n "BUG-003" doc/bugs.md` 确认状态 SPEC_CHANGED

## [0.1.4] 2026-07-09 本地 VCS 环境打通 + BUG-001/002 裁决落地 spec（r4/r5）+ xverif 全局部署

**做了什么**
- **本地 VM 仿真环境首次闭环**：`make smoke` PASS（UVM_ERROR/FATAL=0，TB-only）、`make run FSDB=1` 生成波形、`make lint` 机制验证 OK。修了三个环境坑：① `$VCS_HOME/etc/uvm-1.2/dpi/uvm_hdl_vcs.c:34` 弯引号致 GCC 11 报错（已改，`.orig` 备份同目录）；② Ubuntu 22.04 g++ 默认 `--as-needed` 致 VCS 链接失败 → sim/Makefile 加 `LD_FIX`；③ FSDB 系统任务需 Verdi PLI → sim/Makefile 加 `NOVAS`（-P novas.tab pli.a）
- **BUG-001/002 rev 裁决（2026-07-08）由 orch 落地**：spec r4（§5.2/§9.1：exp_pkt_len=0=未配置跳过比对）、r5（§7.3 新增非法包长行为：sum/xor UNSPECIFIED、读拍钳位 min(ceil(pkt_len/4),8)、length_error 第 0 拍判定），已 `--pin-spec`；testplan M2-02/M2-06 描述同步；bugs.md 两单回填"已应用"
- **xverif 验证工具箱部署**：`/home/open_tools/xverif`（Verdi 2018 适配），skill 装 `~/.claude/skills/xverif`（xwiki 记忆系统按用户决定不装）；已用本项目真实 FSDB 实测 xdebug value.at 闭环。部署/重建细节见 `/home/open_tools/xverif/DEPLOYMENT-LOG.md`

**没做什么**
- M1 design-prompt（apb_slave_if / packet_sram）仍缺，未派 arch；RTL 仍为零，全部场景 🔲
- lint 抓到 TB 一条 `Null statement` 告警未处理（待下轮 DV/DE 修复或登记 lint-waivers.md）
- 未试 `make evidence` 全链路（等首个真实场景 PASS 时走）

**下一步**
- 按 `make next`：派 arch 写 apb_slave_if / packet_sram design-prompt（高档）→ rev 门禁 → 派 DE
- BUG-001/002 已 SPEC_CHANGED 终态，后续 DE/DV 直接引用 spec r4/r5 条文，不再引用 bug 单

**如何验证**
- 本地 VM：`cd sim && make smoke`（UVM_ERROR/FATAL=0）、`make run TEST=ppa_smoke_test SEED=2 FSDB=1`（out/wave.fsdb 生成）
- `python3 scripts/docs.py --check` 通过；`grep -n "r4\|r5" doc/spec.md` 可见裁决条文；xverif：`/home/open_tools/xverif/tools/xbit conv "8'shff"`

## [0.1.3] 2026-07-07 工作流 v2：orch 纯指挥家 + arch 角色 + 脚本指路 + SVA/lint 落地

**做了什么**
- 角色重构：orch 收窄为**纯指挥家**（不产出技术工件）；新增 `arch`（spec 修改提案/design-prompt/feature 分解/接口定义；**行为泄漏禁区**——对外可见行为必须进 spec；交付过 rev 门禁后才可派 DE）；rev 增加 arch 交付门禁职责；de/dv 分工加断言（DE 内部不变量 / DV 接口协议 SVA）
- 脚本指路：`make next`（docs.py --next 读三表机械推导下一步：缺陷推进/待派单/里程碑缺口/三条硬条件核对）；`make bump` 自动在 status/log 插 TODO 骨架（date/version 脚本写死，docs-check 拦未填的 TODO）
- 证据机械化：`make evidence`（scripts/evidence.py 校验 0 error → 抽摘录 → 写证据文件 → 自动回填 testplan ✅/bugs CLOSED），**禁止手写证据文件**
- feature-matrix 去状态位：变纯 arch 工件；交付由 rtl/ 文件现算、验证由 testplan 现算（handover/next 展示，不落盘）；docs-check 改查幽灵引用与关联场景必填
- SVA 纳入验收：tb/sva/ 目录约定（bind 挂接、只引端口、每条 property 注明章节号）；覆盖率口径扩为六类（+assert）；spec 第 0 章新增适配 7/8，修改记录 r3，已重新 pin
- lint 落地：`make lint`（VCS +lint，SpyGlass 部署后换后端入口不变）+ doc/lint-waivers.md 登记表（DE 登记、rev 复核）
- 环境探测硬规则（CLAUDE.md §5）：`command -v vcs` 探测到就必须真跑闭环，探测不到才允许声明未跑

**没做什么**
- tb/sva/ 下暂无实际断言文件（随 M1 DV 派单产出）；lint/仿真/evidence.py 未在真实 VCS 环境跑过（本容器无 VCS，evidence.py 以合成 log 测试）
- BUG-001/002 仍 OPEN 待仲裁；M1 design-prompt 仍缺（make next 已列为待办）

**下一步**
- 本地 VM：`make smoke` 验证 TB 骨架 + `make lint` 试跑 + 任选一景试 `make evidence` 全链路
- 按 `make next` 清单：派 rev 仲裁 BUG-001/002 → 派 arch 写 apb_slave_if/packet_sram design-prompt → rev 门禁 → 派 DE

**如何验证**
- 本容器 `make docs-check` / `make handover` / `make next` 通过；故障注入测试：bump 骨架插入与 TODO 拦截、evidence 场景登记/FAIL 拒绝/复验关单、feature-matrix 幽灵引用拦截、rtl 文件出现后交付状态自动翻转与 next 转派 DV，全部按预期

## [0.1.2] 2026-07-07 Agent 工作流强化：/dispatch 派单技能 + 机械守卫升级

**做了什么**
- 新增 skill `/dispatch`：派单卡模板（档位选择/五类卡型输入清单/隔离自查/回收核对），把 §0 实例隔离从"纪律"变成"操作步骤"；CLAUDE.md §0 档位映射落地（低 haiku/中 sonnet/高 opus，经 Agent model 参数）
- de/dv 增加"交付汇报"固定格式（orch 依此回收核对）；rev 补 Edit 工具（限审查记录、bugs.md 裁决与状态列、详情页仲裁段——原先只有 Write，改单元格要整文件重写）
- docs-check 新增守卫：log 首块版本须同步 version.json；✅ 的 .log 证据首行须含 TEST+SEED 复现命令；feature-matrix ✅ 须至少 1 条关联场景已 ✅；FIX_READY/VERIFYING/CLOSED 须回填修复 commit；doc/bugs/ 详情页双向校验（引用存在+无孤儿）；testplan/feature-matrix/bugs 重复 ID 拦截
- `--pin-spec` 防悄改：spec 正文相对 git HEAD 有改动而"修改记录"表未增行时拒绝钉住
- regress.py 修复 COV=1 被误当列表路径的缺陷；列表格式错误带行号报错。CI 增加 handover 冒烟步骤

**没做什么**
- 未动 rtl/tb/sim 功能代码；0.1.1 遗留项（本地 make smoke、BUG-001/002 仲裁、M1 design-prompt）原样待办
- 新守卫尚无真实 ✅ 条目可检（testplan 全 🔲），正确性以故障注入测试为准

**下一步**
- 同 0.1.1：本地 `make smoke` → 仲裁 BUG-001/002 → 写 M1 design-prompt；首次派 DE 时走 `/dispatch` 流程实测派单卡

**如何验证**
- `make docs-check` / `make handover` 本容器通过；11 组故障注入测试（版本失步/伪证据首行/✅联动/缺修复 commit/孤儿详情页/引用缺失/重复 ID/pin-spec 悄改拒绝与登记放行/回归列表格式/COV 参数）全部按预期拦截或放行

## [0.1.1] 2026-07-06 接入 xverif 工具箱说明与缺陷详情页机制

**做了什么**
- CLAUDE.md §5：登记本地 VM 的 xverif 验证调试工具箱（xdebug/xcov/xloc/xbit/xsva，经 Bash 调用，`command -v` 探测）；明确其 skill/MCP 装用户级 `~/.claude/`，不入仓库
- de/dv/rev 三个 agent 各加一行 xverif 调用指引（各自常用子工具不同）
- CLAUDE.md §4.3（借鉴 xverif 的 xwiki issue 页机制）：复杂缺陷可开 `doc/bugs/<BUG-ID>.md` 详情页承载调试过程（候选根因/已排除项/下一步取证），bugs.md 表保持一行摘要+链接，状态仍以表为准

**没做什么**
- xverif 的本机安装（make 编译、PATH、skill 拷贝、MCP 注册、sync_agent_env.py）是用户 VM 侧操作，仓库不含
- 未采用 xwiki 做项目记忆——与现有三文件记忆系统职责重叠且会制造第二事实源，评估结论见本次对话
- 0.1.0 遗留项（本地 make smoke、BUG-001/002 仲裁、M1 design-prompt）原样待办

**下一步**
- 同 0.1.0：本地 `make smoke` → 仲裁 BUG-001/002 → 写 M1 design-prompt 派 DE
- 用户 VM 装好 xverif 后跑一次 `xdebug -h` 确认 PATH 生效

**如何验证**
- `make docs-check` 本容器通过；本次为纯文档变更，无仿真项

## [0.1.0] 2026-07-06 仓库脚手架初始化

**做了什么**
- 原版 spec 单独存档（commit b542407），随后改造为适配版：新增第 0 章偏离表 + 修改记录，正文未动
- 记忆系统三文件 + 归档件 + feature-matrix + bugs.md 建立；docs.py（handover/check/archive/pin-spec）、bump.py、regress.py 完成并自测
- CLAUDE.md：角色调度、DE/DV 实例隔离、任务流转与缺陷闭环、证据规则、版本判据全部成文
- `.claude/agents/`（de/dv/rev）与 `.claude/skills/`（handover/closeout/evidence）就绪
- UVM 骨架（apb agent + env + ref model + smoke test，一类一文件）与 sim/Makefile（VCS+UVM-1.2+五类覆盖率+fsdb）完成
- 门禁：pre-commit 软门禁 + GitHub Actions 硬门禁（均跑 docs.py --check）

**没做什么**
- 未写任何 RTL（rtl/ 为空）；design-prompt 只有目录结构与模板，内容待 orch/DE 撰写
- UVM 骨架与 sim/Makefile **未经本地 VCS 编译**，正确性未验证（本容器无 VCS）
- ppa_ref_model 中 PKT_LEN_EXP=0 视为"未配置"是暂定假设，对应 BUG-001 待仲裁

**下一步**
1. 本地 VM 执行 `make smoke` 验证 TB 骨架可编译可跑（预期 UVM 报告 0 error 即通过）
2. 仲裁 BUG-001/BUG-002（spec 歧义），必要时修 spec + pin
3. 撰写 doc/design-prompt/apb_slave_if.md 与 packet_sram.md，派 DE 启动 M1

**如何验证**
- `make handover` / `make docs-check` 在本容器已通过
- 仿真侧一切结论以本地 VCS log 为准
