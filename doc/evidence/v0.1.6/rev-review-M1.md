# M1 里程碑审查记录（rev-review-M1）

- 里程碑：M1（Lab1：apb_slave_if + packet_sram）
- 版本：0.1.6
- 审查人：rev（本实例，与本轮 DE/DV 隔离）
- 审查日期：2026-07-09
- 裁决基准：doc/spec.md（第 0 章适配表优先）+ CLAUDE.md §4.1 三条硬条件
- 被审 HEAD：ff6b50e

---

## 1. 审查范围清单

RTL：
- rtl/apb_slave_if.sv（M1，全文）
- rtl/packet_sram.sv（M2，全文）

DV 交付：
- tb/tb_top.sv（DUT 接入部分）
- tb/m3_stub_if.sv、tb/uvm/env/m3_stub_driver.sv（M3 桩）
- tb/sva/apb_protocol_sva.sv（APB 协议 SVA，bind tb_top）
- tb/sva/apb_slave_if_sva.sv（apb_slave_if 接口 SVA，bind apb_slave_if）

证据/工程：
- doc/evidence/v0.1.6/M1-01..06.log（evidence.py 机械生成）
- sim/result_summary.txt、sim/flist/tb.f、sim/Makefile
- doc/lint-waivers.md 第 3、4 行

环境：VCS-MX O-2018.09-SP2 已探测到（`command -v vcs` 命中）；xverif（xcov/xdebug）未安装，故覆盖率用原生 urg 口径评估。

---

## 2. 逐项发现

### 2.1 RTL 与 spec 一致性

**packet_sram.sv（r6 落地核对）**：读端口为组合读——`always_comb` 中 `rd_en=1` 当拍 `rd_data = mem[rd_addr]`（rtl/packet_sram.sv:43-49），`rd_en=0` 输出 32'd0；写端口为同步写（时钟沿 `wr_en` 写入）。与 §2.3 M2 表注（r6）"同步写/组合读、无 1 拍寄存延迟"逐字一致。BUG-003 r6 裁决正确落地。**通过**。

**apb_slave_if.sv（r7 落地核对）**：APB 读 PKT_MEM 窗口一律 PSLVERR=0（rtl/apb_slave_if.sv:226-228，pkt_mem_range 分支 `PSLVERR = write_access && busy_i`，读访问 busy 不参与 → 恒 0）且 PRDATA=32'd0（rtl/apb_slave_if.sv:253）。与 §6.3(r7)"APB 读 PKT_MEM 任意时刻 PSLVERR=0、PRDATA=占位值 32'h0"一致。BUG-004 r7 裁决正确落地。**通过**。

其余关键行为均可指回 spec：
- PREADY 恒 1（§4.1）— apb_slave_if.sv:63。
- 两段式 ACCESS 判定 access=PSEL&&PENABLE（§4.1）— :69。
- 保留/未定义地址 PSLVERR=1（§4.2 §8.3）— :223-225。
- 写只读寄存器 PSLVERR=1（§5.1 §8.3）— :232。
- busy=1 写 PKT_MEM PSLVERR=1 且不产生 we（§6.3 §8.3）— :213/:228。
- start_o W1P：仅 enable=1 && busy=0 接受，用写前 ctrl_enable 判定，符合附录 A 两步序列（§5.2）— :151。
- IRQ 同拍置位 + RW1C 清除（§8.2）— :162-196。
- STATUS/RES_*/ERR_FLAG M3 结果只读直透、不锁存（§8.1 §9.1）— :240-256。
- PKT_MEM 写地址映射 (PADDR-0x040)>>2=Word N（§6.1）— :211-214。

未发现 RTL 对 spec 的误读或私自定义对外行为。

### 2.2 DUT 接入（tb_top.sv）

- M1→M2 写通路：apb_slave_if 的 pkt_mem_we_o/addr_o/wdata_o 经 pkt_mem_*_w 线接到 packet_sram 的 wr_en/wr_addr/wr_data（tb/tb_top.sv:63-90）。连接正确。
- M2 读端口 rd_en=1'b0 / rd_addr=3'b0 / rd_data 悬空（:87-89）：符合 r7（M2 读端口仅供 M3，M1 不消费；M3 未交付）。合理，非错误。
- M3 结果输入：经 m3_stub_if + UVM 组件 m3_stub_driver 受控驱动（:37-76），**不是写死的 initial block**——由 clocking block（tb/m3_stub_if.sv:27-31）与驱动任务 set_result/set_busy/pulse_done/clear_done（m3_stub_driver.sv）产生激励，含 done 上升沿制造，供 M1-03/05/06 使用。驱动方式合理。
- irq_o 经 assign 旁路接 m3_stub.irq 供观测（:41），只读采样，未反灌。

**通过**，无接线错误。

### 2.3 SVA 断言内容（禁止照抄 RTL 行为）

两个 SVA 文件均在 tb.f（第 12-13 行）编译并 bind，本轮回归带断言运行、无一条 fire。

apb_protocol_sva.sv（bind tb_top，仅引用总线级信号 apb.*，不引 RTL 内部信号）：4 条 property 均指回 §4.1，逐条与 spec 自洽——
- a_pready_always1（§4.1 PREADY 恒 1）
- a_access_preceded_by_setup（§4.1 两段式：ACCESS 前必有 SETUP）
- a_setup_then_access（§4.1 无等待态：SETUP 下一拍进 ACCESS）
- a_addr_stable_setup_to_access（§4.1 SETUP→ACCESS 地址/数据稳定）

apb_slave_if_sva.sv（bind apb_slave_if，仅引用模块端口 + 由 spec 公式与 ppa_reg_defs 常量**重新推导**的地址区间，未引用 RTL 内部译码信号）：6 条 property 逐条指回 spec——
- a_pktmem_write_map（§6.1 §6.2 地址映射，用 spec 地址公式而非 RTL is_pkt_mem_range 推导）
- a_pktmem_busy_protect（§6.3 §8.3）
- a_pktmem_read_placeholder（§6.3 r7 占位值）
- a_reserved_addr_slverr（§4.2 §8.3）
- a_irq_done_same_cycle（§8.2 同拍置位）
- a_irq_err_same_cycle（§8.2 §9.1）

抽查确认：期望值均从 spec 条文推导（例如 read_placeholder 断言 PRDATA==32'h0 源自 §6.3(r7) 明文占位值，非"RTL 输出啥就断言啥"；地址区间用 ADDR_PKT_MEM_BASE/END 与 §6.1 公式独立算出）。**未发现照抄 RTL 行为，无明显误读**。**通过**。

### 2.4 lint 豁免复核（任务 1）

第 3 行（apb_protocol_sva.sv:21,27,32,38）、第 4 行（apb_slave_if_sva.sv:51,57,63,68,73,78）：行号与实际 assert 语句逐一核对无误；`disable iff (rst)` 均为单一信号 rst（`assign rst = !presetn` / `!PRESETn`），标准复位屏蔽写法，非复合表达式。Lint-[SVA-DIU] 属"使用了 disable iff 结构"的提示性告警，等价必要用法。豁免理由成立，**批准**（已回填 doc/lint-waivers.md 复核列）。

---

## 3. 里程碑三条硬条件核对（CLAUDE.md §4.1）

**① 该 M 的 RTL 全部就绪且 feature-matrix 关联场景全 ✅ — 满足**
- `make handover`：feature-matrix M1 RTL 交付 6/6、验证 ✅ 6/6；testplan M1 ✅6/6 ❌0 ⚠️0 🔲0。
- `make next`：确认"M1 条目全 ✅"。

**② `make regress` 100% PASS 且证据归档 — 基本满足，1 项归档待补**
- 本人亲自真实执行（非采信汇报）：首跑 `make regress` 在 stale sim/out 上因 `Error-[VFS_SDB_ERROR]`（constraint.sdb 损坏）产出 **4/7**（假失败，详见 §4 遗留风险）。`make clean` 后重跑 `make regress` = **7/7 PASS**，可复现。
- 7 个测试 UVM_ERROR:0 / UVM_FATAL:0（clean 回归日志逐条核对）；SVA 带断言运行无 fire。
- sim/result_summary.txt 存在且与 clean 回归结果一致（7/7）。
- M1-01..06.log 均由 evidence.py 机械生成，首行=含 TEST+SEED 的复现命令，源 log 可溯（抽查 M1-05/M1-06 属实）。
- **待补（orch closeout 机械步骤，§4.2）**：sim/result_summary.txt 尚未复制入 doc/evidence/v0.1.6/（make next 已提示此缺口）。

**③ rev 审查记录存 doc/evidence/ — 满足**
- 即本文件 doc/evidence/v0.1.6/rev-review-M1.md。

---

## 4. 遗留风险

1. **回归可复现性隐患（建议 orch 登记 bug）**：`make regress` 直接在残留 sim/out 上运行会因 VCS constraint.sdb 损坏产生假失败（本人实测首跑 4/7），必须 `make clean` 后才稳定 7/7。scripts/regress.py 未在回归前清理构建产物，也未把 NOSUMMARY/损坏识别为环境错误而非用例失败——存在"脏目录下误判回归失败"或反向"脏目录下漏跑仍报旧摘要"的双向风险。建议：regress 前强制 clean，或 result_summary 附带构建指纹。非 M1 功能缺陷，但影响证据可信度。
2. **result_summary.txt 未入 evidence**：§4.2 要求随里程碑复制入 doc/evidence/v0.1.6/，尚未完成（orch closeout）。
3. **覆盖率未采集/未归档**：`make regress` 默认 COV=0，本轮无覆盖率数据；§4.2 里程碑"人工三件"含覆盖率 summary 摘录、spec §0 适配 7 要求六类 ≥90%。M1 覆盖率是否达标**尚无证据**，需 orch 补 `make regress COV=1` + `make cov` 并归档摘录后方可完整证明质量门禁。
4. **BUG-005（FIX_READY）/ BUG-006（OPEN）**：BUG-005 为 sim 构建顺序修复，已 FIX_READY 待 DV 复验关单（关单人≠修复人），构建实际已可用；BUG-006 为 0.1.0 脚手架遗留的 tb/ 17 条 lint 告警，非本轮引入、不涉 M1 RTL 功能。两者均不阻塞 M1 三条硬条件，但应在进入 M2 前收口。
5. **RTL 注释陈旧（已登记、非阻塞）**：apb_slave_if.sv:9-13 顶部注释仍称"BUG-004 OPEN、临时处理、不作为对外行为承诺"，与 r7 已认可的对外行为相悖。此为 BUG-004 r7 裁决明示的延后项（"注释同步留待下次触及该文件时处理，不阻塞本轮"），log 0.1.6"没做什么"已记录。仅注释、非行为返工。

---

## 5. 审查结论

- RTL / SVA / DUT 接入 / 证据链的**技术审查：通过**。r6、r7 裁决均正确落地；SVA 逐条指回 spec、未照抄 RTL；DUT 接入正确、M3 桩为受控 UVM 驱动而非写死 initial。
- 里程碑三条硬条件：① 满足、③ 满足；② 的"regress 100% PASS"经本人 clean 复跑**已复现 7/7**，但"证据归档"尚缺 result_summary.txt 入库这一机械步骤。

**里程碑签核结论：有条件通过（技术无阻塞项）。**

允许打 tag `v0.1.6` 的前置动作（均为 orch closeout 机械步骤，非返工）：
1. 复制 sim/result_summary.txt → doc/evidence/v0.1.6/（补齐条件②证据归档）。
2. 采集并归档覆盖率 summary 摘录（`make regress COV=1` + `make cov`），确认六类 ≥90%；若不达标则需 DV 补场景（此项决定"质量门禁"是否成立，属里程碑证据人工三件之一）。
3. 建议将 §4 遗留风险 1（回归脏目录假失败）登记 bugs.md，由 orch 判归属。

完成上述第 1、2 项后，M1 三条硬条件与里程碑证据齐备，可正式签核 v0.1.6。在第 2 项覆盖率证据补齐前，不建议直接打 tag。
