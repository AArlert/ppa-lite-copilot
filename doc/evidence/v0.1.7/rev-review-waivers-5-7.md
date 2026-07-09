# rev 审查记录：lint 豁免登记 #5/#6/#7 复核

- 日期：2026-07-09
- 审查员：rev（与登记人 DV/orch 不同实例）
- 审查对象：doc/lint-waivers.md 表中 # = 5、6、7（共 18 处告警）
- 判据：CLAUDE.md §7（lint 门禁——`make lint` 干净或告警登记豁免经 rev 复核）；豁免成立标准参照 #1~#4 已批准先例（误报/不可控/修复即破坏语义，且无隐藏真实缺陷）

## 结论汇总

批准 3 条（#5、#6、#7），打回 0 条。18 处告警全部批准豁免。
另发现 #6 原因栏一处笔误（"6 处"应为"4 处"），不影响豁免成立（豁免范围由位置栏 10-13 四条宏界定且准确），已在复核栏注记，建议 orch 下次触及时更正。

## lint 实跑证据（2026-07-09 本地 VM）

- 环境：`command -v vcs` = /home/synopsys/vcs-mx/O-2018.09-SP2/bin/vcs（探测到，真跑）
- 执行：`make -C sim clean`（先清 out，规避 BUG-007 脏 out 假象）→ `make -C sim lint`
- 完整 log：sim/out/lint.log（退出码 2 = 判定范围内有已登记告警，符合预期）
- 判定范围（../rtl/ ../tb/）内 Lint- 告警按类别计数：

| 类别 | 数量 | 分布 |
| --- | --- | --- |
| Lint-[SVA-DIU] | 23 | rtl/apb_slave_if.sv(8) + rtl/packet_sram.sv(5) + tb/sva/apb_protocol_sva.sv(4) + tb/sva/apb_slave_if_sva.sv(6) |
| Lint-[NS] | 14 | tb_top.sv(1) + apb_driver.sv(4) + apb_monitor.sv(1) + m3_stub_driver.sv(8) |
| Lint-[WMIA-L] | 4 | apb_seq_item.sv(4) |
| 合计 | 41 | — |

- 登记对账（41 处一一对应，无未登记新增）：
  - #1（归档）SVA-DIU packet_sram.sv:61,65,70,74,80 = 5
  - #2（归档）SVA-DIU apb_slave_if.sv:268,273,278,283,290,295,300,306 = 8
  - #3 SVA-DIU apb_protocol_sva.sv:21,27,32,38 = 4
  - #4 SVA-DIU apb_slave_if_sva.sv:51,57,63,68,73,78 = 6
  - #5 NS = 6
  - #6 WMIA-L = 4
  - #7 NS = 8
  - 合计 5+8+4+6+6+4+8 = 41 ✅，与实跑一致，无判定范围内未登记告警。

## 逐条结论

### #5 Lint-[NS] Null statement（6 处，批准）

- 位置逐条核对（源码行号与登记一致）：
  - tb/tb_top.sv:20 `repeat (5) @(posedge pclk);` — 复位保持，纯时序
  - tb/uvm/apb_agent/apb_driver.sv:20 `wait (vif.presetn === 1'b1);` — 等复位释放
  - apb_driver.sv:21 `@(vif.drv_cb);` — 时钟对齐
  - apb_driver.sv:46 `@(vif.drv_cb);` — SETUP→ACCESS 对齐
  - apb_driver.sv:49 `do @(vif.drv_cb); while (vif.drv_cb.pready !== 1'b1);` — 等 PREADY
  - apb_monitor.sv:23 `@(vif.mon_cb);` — 采样点时钟对齐
- 依据：6 处均为"仅含时序控制、无其他动作"的同步语句，`+lint=all` 的 Lint-[NS] 对此类 `@(...)`/`wait(...)`/`repeat(...)@(...)`/`do...while(...)` 语句为已知误报；去掉即破坏 driver/monitor 两段式握手时序语义，无实质空语句可优化。属 0.1.0 脚手架遗留（BUG-006 登记范围一致核对：BUG-006 现象列列举的 6 处 NS 与本条完全吻合），非本轮引入。无隐藏真实缺陷。
- 结论：批准。

### #6 Lint-[WMIA-L] Width mismatch in assignment（4 处，批准）

- 位置：tb/uvm/apb_agent/apb_seq_item.sv:10-13，`uvm_field_int(write/addr/data/slverr, UVM_ALL_ON)` 四条宏调用。
- 实跑 log 展开核对（sim/out/lint.log）：告警 Source info 为 `uvm_pkg::uvm_object::__m_uvm_status_container.status = 1;`（32-bit 字面量赋 1-bit 库内部字段），系 UVM-1.2 `uvm_macros.svh` 内 `uvm_field_int` 宏内部实现，非本仓库可控写法；仓库侧仅按标准用法调用宏，无法通过修改调用点消除。
- 结论：批准。
- 注记（笔误，不影响豁免）：原因栏叙述"6 处均为 BUG-006 登记范围内"中的"6 处"为笔误——位置栏（10-13 四条宏）、实跑计数（4）、BUG-006 现象列（"共 4 处"）三者一致均为 4 处。豁免范围由位置栏界定且准确，故不构成打回；已在 lint-waivers.md #6 复核栏注记，建议 orch 更正原因栏措辞。

### #7 Lint-[NS] Null statement（8 处，批准）

- 位置逐条核对：tb/uvm/env/m3_stub_driver.sv:26,35,41,43,50,52,57,59，8 处均为 `@(vif.drv_cb);` clocking-block 同步等待，分布于 set_result/set_busy/pulse_done/clear_done 各 task。
- 依据：与 #5 同一类别、同一根因（VCS 对纯 `@(clocking_block);` 同步语句的 Lint-[NS] 误报）；去掉即破坏 M3 stub 对 apb_slave_if 结果输入的同拍驱动时序。本文件为本轮（0.1.6）DV 新交付、非 0.1.0 遗留，单独登记不并入 BUG-006 的做法正确。无隐藏真实缺陷。
- 结论：批准。

## 遗留风险

- 低。18 处均为供应商工具（VCS `+lint=all`）对标准 SV/UVM 同步惯用法与库宏内部实现的提示性告警，无一指向本仓库设计/验证语义缺陷。
- 建议（非阻塞）：SpyGlass 后端到位后（Makefile lint 目标预留切换）应复核这些 Lint-[NS]/WMIA-L 在新后端下是否仍触发，届时可精简豁免表。
- 文档清洁项（非阻塞）：#6 原因栏"6 处"笔误待 orch 更正。

## 复现命令

```
cd sim && make clean && make lint    # 退出码 2；out/lint.log 为完整证据
```
