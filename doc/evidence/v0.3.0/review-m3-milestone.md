# M3 里程碑签核审查记录

- 版本：0.3.0（version.json 现值：version=0.3.0 / milestone=M3）
- 审查人：rev（全新实例，未参与本次 M3 的 DE(ppa_top RTL)/DV(M3-01..05) 工作，未做过 BUG-010 仲裁，未复核 lint 豁免 #9）
- 日期：2026-07-14
- 判据出处：CLAUDE.md §4.1「M 完成判据（三条硬条件）」
- 结论：**通过（签核）**。三条硬条件均独立核验为真；BUG-010 已 SPEC_CHANGED 闭环、r11 已 pin；无本轮阻塞缺陷；覆盖率缺口经裁定属 M4-02、不卡 M3；未见证据造假迹象。遗留风险见文末，须携入 M4，不阻塞本次签核。

---

## 判据①：该 M 的 RTL 全部就绪且 feature-matrix 关联场景全 ✅

**结论：满足。**

- `make handover` / `make next`（本人实跑，未采信转述）：`make next` 输出「M3 三条硬条件已齐 → make bump-minor + git tag v0.4.0 进入下一 M」；feature-matrix 现算 M3 RTL 交付 1/1、验证 ✅1/1；testplan 现算 M3 ✅5/5、无 ❌/⚠️/🔲。
- feature-matrix F3-1（doc/feature-matrix.md:20）：`ppa_top` 三模块纯连线集成 + 时钟复位分发（无状态逻辑），§2.3，关联 M3-01/02/03；无幽灵引用。
- testplan M3-01~M3-05（doc/testplan.md:38-42）逐行核对：状态均 ✅，证据链接 `doc/evidence/v0.3.0/M3-0N.log` 均存在，复现命令 `make run TEST=ppa_m3_0N_test SEED=1` 完整；对应 test 源文件 `tb/uvm/test/ppa_m3_0{1..5}_test.sv` 五份均在工作树。
- **RTL 独立核对 `rtl/ppa_top.sv`（不采信 DE 汇报，直接读源码，对照 design-prompt/ppa_top.md 与 spec §2.1/§2.2/§2.3/§6.3/§8.1/§8.2）**：
  - **对外端口严格对齐 §2.3 Top 表 11 信号**（spec 第 241–253 行）：PCLK/PRESETn/PSEL/PENABLE/PWRITE/PADDR[11:0]/PWDATA[31:0]（7 输入）+ PRDATA[31:0]/PREADY/PSLVERR/irq_o（4 输出），方向/位宽逐一吻合（rtl L17-27）。**未引出 done_o 顶层引脚**——与 r11/BUG-010 裁决一致：M3.done_o 仅内部接 M1.done_i（rtl L51、L92、L140），软件经 APB 轮询 STATUS.done 观察（§8.1）。design-prompt L41/L124 已更新引用 r11，与本裁决自洽。
  - **时钟/复位直连映射，无同步器/门控/分频/极性变换**：Top.PCLK 直连 u_sram.clk、u_core.clk（rtl L110/L127）；Top.PRESETn 直连 u_sram.rst_n、u_core.rst_n（rtl L111/L128），均低有效直连；M1 用 PCLK/PRESETn（L68-69）。与 §2.1（第 118 行分发约定）、§2.3 M2/M3 表 clk/rst_n 说明一致。内含 4 条时钟/复位同源连通性断言（a_sram/core_clk/rst_conn，L192-206）捕获意外门控/极性变换。
  - **互连与端口表「说明」列一致**：M1↔M2 写端口 pkt_mem_we/addr[2:0]/wdata[31:0]（L34-36、L87-89→L113-115）；M3↔M2 读端口 mem_rd_en/addr[2:0]/data[31:0]（L39-41、L135-137→L117-119，同拍组合读、不插寄存 BUG-003/r6，另有 a_rd_data_direct 断言 L187）；M1→M3 控制 start/algo_mode/type_mask[3:0]/exp_pkt_len[5:0]（L44-47、L80-83→L130-133）；M3→M1 结果/状态 10 信号 busy/done/format_ok/length_error/type_error/chk_error/res_pkt_len[5:0]/res_pkt_type[7:0]/res_payload_sum[7:0]/res_payload_xor[7:0]（L50-59、L139-150→L91-100），位宽逐条对齐 §2.3 M1/M3 表（含 res_pkt_len 6-bit 直连无截断 BUG-P2/r9）。
  - **纯连线无状态**：模块体仅子模块例化 + wire 互连，无 always_ff/always_comb 业务逻辑、无寄存器/FSM/运算/译码；唯一 `always`/`assign` 为 `assign rst = !PRESETn`（L163，仅供断言 disable iff 使用，`ifndef SYNTHESIS` 内）。符合 §2.2 第 158 行「无额外状态逻辑」、§2.1「薄层连线」、§11.4「纯连线」。未发现行为泄漏（PSLVERR/IRQ/STATUS/SRAM/包处理均在子模块产生）。
  - **允许悬空的输出**：M1.enable_o/done_irq_en_o/err_irq_en_o 为字段观测抽头、§2.3 Top 表无对应引脚，rtl L79/L84/L85 显式留空并注明，与 design-prompt「允许悬空的输出」一致。

## 判据②：`make regress` 100% PASS 且证据归档

**结论：满足。**

- 本人独立复跑 `make -C sim regress`（本地 VM，VCS O-2018.09-SP2，自设 VCS_HOME/VERDI_HOME/LM_LICENSE_FILE/PATH）：**22/22 PASS**（smoke + M1×9 + M2×7 + M3×5），逐条 PASS，与归档 `doc/evidence/v0.3.0/result_summary.txt`（22/22，日期 2026-07-14）完全一致；smoke $finish 正常收尾。
- 单场景证据抽查 `doc/evidence/v0.3.0/M3-0{1..5}.log`：五份 log 首行均为含 TEST+SEED 的复现命令（`make run TEST=ppa_m3_0N_test SEED=1`），与 testplan 复现命令自洽；**UVM_ERROR=0 / UVM_FATAL=0** 五份全部满足。
- 防造假机械保证：证据由 `make evidence` 生成，evidence.py 强制 UVM_ERROR/FATAL=0 才登证据、源 log 不存在即拒登；本人独立复跑 22/22 复现，与归档 result_summary 一致——证据只可能由真实通过的 log 生成。

## 判据③：rev 审查记录存 doc/evidence/

**结论：满足。**

- 本审查记录 `doc/evidence/v0.3.0/review-m3-milestone.md`；配套 `coverage-summary.md`（六类覆盖率、如实记录未达标项）、`result_summary.txt`、M3-01~05.log。
- `python3 scripts/docs.py --check` 本人实跑：**通过**（docs-check 通过，EXIT=0）。

---

## 覆盖率缺口裁决

**裁定：TOGGLE/FSM/COND 等类别低于 90% 不卡 M3 签核。**

- 依据：CLAUDE.md §4.1 M3 三条硬条件不含覆盖率门槛；覆盖率 ≥90% 六类综合的验收归属 spec §11.5「Lab4：集成回归与覆盖率闭环」，即 **M4-02**（沿用 v0.2.3 M2 签核裁定，见 doc/evidence/v0.2.3/review-m2-milestone.md「覆盖率缺口裁决」）。`coverage-summary.md` 抬头亦已如实声明此归属。
- `coverage-summary.md` 数据可信性核查：口径分层清晰（Total 全域 / tb_top 域 / u_ppa_top 集成实例域 / modlist 模块域），如实列出不达标项（TOGGLE 58-66%、FSM 60%、COND 74-83%），未粉饰；设计域达标项（packet_sram/tb_top LINE≈100、多数模块 ASSERT=100、tb_top 域 LINE 95.88%/BRANCH 93.75%/ASSERT 94.32%）与「新增 ppa_top 集成路径」相符（较 v0.2.3 LINE 由 29.08%→41.04% 提升，成因归因合理）。
- **可信性核查的一处限制（如实记录）**：本人复跑为不含 COV 的 `make regress`，`sim/out/urgReport/` 当前不在磁盘、本地 xcov 工具亦未部署（`command -v xcov` 无输出），故未能对 urg 报告做逐数字实时比对。但：(1) 覆盖率非 M3 硬条件，此项不影响签核；(2) coverage-summary 内部四层口径数据自洽（如 u_core 集成路径 TOGGLE 42.70% 低于独立单测 60.85% 的解释与激励收敛特性一致）、诚实记录缺口、结论保守（未据此声称达标）。如需精确复核 urg 数字，建议 M4-02 闭环时以 `make regress COV=1 && make cov` 现场核对。
- 故不因覆盖率缺口卡关；缺口须携入 M4-02 闭环（见遗留风险）。

## 缺陷与造假防线核查

- **BUG-010 闭环**：状态 = SPEC_CHANGED（终态），rev 裁决取方向 (a)——删除 §2.1 框图 done_o 对外引脚画法，与 §2.3 Top 表对齐、ppa_top 不引出 done_o 顶层引脚。orch 已应用 spec 修改记录 **r11**（doc/spec.md:10）并 pin，spec §2.1 已补澄清注（doc/spec.md:118）；RTL/testplan/feature-matrix 无需返工，本人核 rtl/ppa_top.sv 与裁决一致。docs.py --check 通过（含 spec sha256 pin 校验），修改路径合规。
- **本轮无阻塞缺陷**：`make handover` bugs 段现算「(无未关闭缺陷)」；历史缺陷 BUG-007 CLOSED（带复验证据）、BUG-008/009/010 等均为终态（SPEC_CHANGED/CLOSED）。
- **lint 豁免 #9**（doc/lint-waivers.md:11）复核：ppa_top.sv 六条 disable-iff 内部断言（a_no_x_* / a_rd_data_direct）触发 Lint-[SVA-DIU]，与已批准 #1/#2/#8 同一类别、同一根因、同一写法（单一信号 rst 规避更实质的 Lint-[SVA-CE]），属等价必要用法；另四条时钟/复位连通性断言不用 disable iff、不触发本告警；登记记载本地 VM 实测 compile 0 error、lint 范围内仅此 6 处、未连接输出 enable_o/done_irq_en_o/err_irq_en_o 未触发告警。理由充分、与 rtl/ppa_top.sv L166-189 行号吻合，**复核通过**（此前 rev 2026-07-14 已批准，本次独立复核确认一致）。
- 未见造假迹象：所有证据机械生成，本人独立复跑 22/22 复现，与归档一致。

---

## 最终签核结论：通过

M3 三条硬条件全部独立核验满足；ppa_top RTL 与 spec §2.1/§2.2/§2.3/§6.3/§8.1/§8.2 及 design-prompt 一致、纯连线无状态、无行为泄漏、对外 11 引脚严格对齐 §2.3 Top 表（不引出 done_o，r11/BUG-010）；回归 22/22 独立复现；BUG-010 SPEC_CHANGED/r11 已 pin、lint 豁免 #9 复核通过、无阻塞缺陷；覆盖率缺口按 CLAUDE.md §4.1 与 M2 先例裁定属 M4-02、不卡关。**同意 M3 里程碑签核**，可 `make bump-minor` + 打 tag `v0.4.0` 进入 M4。

### 遗留风险（携入 M4，不阻塞本次签核）

1. **覆盖率缺口（→M4-02）**：TOGGLE 58-66%、FSM 60%、COND 74-83% 跨口径持续偏低；M3 集成实例域 u_core TOGGLE 42.70%、u_apb_slave_if_sva ASSERT 50.00% / u_apb ASSERT 71.43%——**M1 接口/协议 SVA 在 M3-01..05 集成激励下部分未触发**（集成冒烟聚焦端到端流程、非穷举数据翻转/负向）。须 M4 随机化/多 seed + 专项负向激励闭合至六类综合 ≥90%（§11.5-必2）。
2. **urg 报告未在磁盘、无本地 xcov**：本次覆盖率仅据 coverage-summary（自洽、诚实）核，未逐数字比对 urg 原始报告。M4-02 闭环时须 `make regress COV=1 && make cov` 现场复核每类数字。
3. **M4-05 选做回归纳管**：M3-04（busy 写保护）、M3-05（中断闭环）已 ✅ 并入 22 条回归；testplan M4-05（M1-04/05、M2-04/05/06、M3-04/05 全部纳入回归 PASS）仍 🔲，M4 需机械核对纳管完整性。
4. **文档轻微项（承接自 M2，非阻塞）**：spec 附录端序正文显式化 + 附录 B.3 注释算式笔误订正（BUG-009 仲裁建议），M3 未触及；建议 M4 触及 spec 时经 §8 一并处理。
