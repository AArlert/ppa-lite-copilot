# M1 覆盖率 summary（六类）

- 生成日期：2026-07-09
- 采集命令：
  ```
  make regress COV=1     # 根 Makefile 转发 sim/；7/7 PASS，见 result_summary.txt
  make cov                # urg -full64 -dir out/cov.vdb -report out/urgReport
  ```
- 判据：spec §0 适配表 #7（六类 `line+cond+fsm+tgl+branch+assert`，≥90% 合格）。
- 数据来源：`sim/out/urgReport/`（HTML）逐模块解析（`mod5.html`=apb_slave_if、`mod7.html`=packet_sram、
  `mod13.html`=apb_protocol_sva、`mod14.html`=apb_slave_if_sva，均为 M1 交付的 RTL/SVA 范围）。
  说明：本地 `xcov`（xverif 工具箱）当前仅有 Python 源码，未打包出可执行的 `xcov` CLI（`command -v xcov`
  探测不到；`tools/xcov` 需配合特定 VDB/Python 环境，本次尝试后判定不如直接解析 urg 报告可靠），故本次
  采用直接解析 `urg` 生成的 HTML 报告（逐 metric 锚点定位表格，非手写数字）。urg 命令行本身对 `Fsm` shape
  报 `Warning-[UCAPI-SNF]`（vdb 中无 FSM shape）。

## 范围口径

- line/cond/toggle/branch：M1 交付的两个 RTL 模块 `rtl/apb_slave_if.sv`（mod5）+ `rtl/packet_sram.sv`（mod7）聚合。
- assert：按 spec §0 适配 #7，覆盖 DE 内部不变量断言 + DV 接口/协议 SVA，聚合 mod5 + mod7 + `tb/sva/apb_protocol_sva.sv`（mod13，bind 到 apb 接口）+ `tb/sva/apb_slave_if_sva.sv`（mod14，bind 到 apb_slave_if）——这 4 个模块是 urg 报告中仅有的含断言的模块（`hierarchy.html` 中 tb_top 汇总 ASSERT=78.26% 与本表聚合结果一致，交叉验证口径正确）。
- fsm：M1 两个 RTL 模块（`apb_slave_if.sv`/`packet_sram.sv`）均无 `typedef enum` 状态机构造（`grep -n "case\|state" rtl/*.sv` 仅命中 `apb_slave_if.sv:241` 的组合读数据 `unique case(1'b1)` 多路选择器，非状态机），urg vdb 中也确认无 FSM shape。**M1 无 FSM 设计对象，该类判据结构性不适用（N/A），非"未覆盖"**。

## 六类结果

| 类别 | 判据范围 | Covered/Total | 百分比 | ≥90% |
| --- | --- | --- | --- | --- |
| line | mod5(51/54) + mod7(4/5) | 55/59 | **93.22%** | ✅ |
| cond | mod5(37/46)；mod7 无条件表达式（0 分母，不计入） | 37/46 | **80.43%** | ❌ |
| toggle | mod5 Total Bits(287/446) + mod7 Total Bits(76/150) | 363/596 | **60.91%** | ❌ |
| branch | mod5(35/37) + mod7(3/4) | 38/41 | **92.68%** | ✅ |
| assert | mod5(6/8) + mod7(3/5) + mod13(4/4) + mod14(5/6)（Succeeded/Matched 口径） | 18/23 | **78.26%** | ❌ |
| fsm | M1 RTL 无状态机构造 | — | **N/A** | N/A（结构性不适用，见上）|

**结论：未达标**。line/branch 达标；cond/toggle/assert 三类实测低于 90% 门槛；fsm 结构性不适用不参与判定。按任务要求如实报告，不放宽口径、不造假。

## 缺口清单（按根因分组，供后续 M1 收尾或 M2 联调参考）

### 1. packet_sram 读口（rd_en/rd_addr/rd_data）几乎零覆盖 —— 主因
- `rtl/packet_sram.sv:44-45`（`if (rd_en) rd_data = mem[rd_addr];`）分支 **0% 覆盖**（`Not Covered`，`45 0/1`）。
- 断言 `a_rd_addr_no_x`（0/274 Real Successes）、`a_read_after_write`（0/274 Real Successes）从未真正触发。
- 根因：按 spec r7 / BUG-004 裁决，M2 的 `rd_en/rd_addr/rd_data` 读端口**专供 M3**，APB 无读回通路；M1 里程碑尚无真实 M3，`tb/uvm/env/m3_stub_driver.sv` 只桩驱动 `res_*/busy/done` 等结果输入，未驱动 `packet_sram` 的 `rd_en/rd_addr`。这是 M1 阶段的**结构性覆盖空洞**，需等 M2/M3 落地后由真实读通路联调覆盖，或由 DV 在 stub 里补一段"模拟 M3 读 SRAM"的桩激励（如果该行为在 M1 验收范围内需要单独锁定，需先过 arch/rev 是否要求，本卡不做场景开发）。
- 该项直接拖累 packet_sram 的 line(80%)/branch(75%)/toggle(50.67%)/assert(60%) 四项，是 cond/toggle/assert 三类不达标的主要贡献源之一。

### 2. apb_slave_if CTRL.START 脉冲路径未被激励
- `rtl/apb_slave_if.sv:151`（`start_o` 组合式 5 项与逻辑）condition 覆盖出现 3 处 `Not Covered`（MC/DC 意义下 term1/term2/term3 单独翻转未验证）。
- 断言 `a_start_implies_enable_idle`、`a_start_single_pulse` **Real Successes=0**（274 次 attempt，0 次真正在"start 有效脉冲"场景下被验证，且 0 failure——即该前提从未成立）。
- 根因：现有 testplan M1-01~M1-06 六个场景均未构造"先写 CTRL.enable=1，再写 CTRL.start=1 且 busy=0"的两步序列（§5.2 附录 A 示例场景），CTRL.START 位的 W1P 单拍脉冲行为未被端到端验证。这是**testplan 场景空白**，非 RTL/TB 缺陷；本卡不做场景开发，登记于此供后续排期。

### 3. apb_slave_if_sva 的 busy 写保护场景未覆盖
- `a_pktmem_busy_protect`（tb/sva/apb_slave_if_sva.sv）**Real Successes=0**：M1 现有场景未在 `busy_i=1`（M3 stub 拉高 busy）期间尝试写 PKT_MEM 窗口来验证"写不生效/PSLVERR=1"的保护路径（§6.3/§8.3）。同样是 testplan 场景空白。

### 4. toggle 类整体偏低的补充成因
- 除上述读口/start 路径外，PWDATA/PRDATA/mem 阵列等宽位宽信号在现有 8-word 顺序写测试模式下，0→1、1→0 双向翻转组合不够充分（如 mod5 Total Bits 0->1=154/223=69.06%），随机化/边界值激励不足也是 toggle 偏低的一般性原因。

## 达标类明细（供交叉核对）
- line 93.22%：mod5 剩余未覆盖为 `cfg_algo_mode`/`cfg_type_mask`（CFG 寄存器部分字段写入组合，line 128/129）与 `pkt_len_exp` 某写入分支（line 135）未被 100% 命中，量级小，不影响整体达标。
- branch 92.68%：mod7 的 `if(rd_en)` 分支（见缺口 1）是唯一未覆盖分支，mod5 剩余 2 处 MC/DC 项未覆盖（对应缺口 2 的 start 表达式子项）。

## 附
- 回归证据（首测）：`doc/evidence/v0.1.7/result_summary.txt` 对应版本（本次 `make regress COV=1` 7/7 PASS 摘要，已被下方复测的 10/10 摘要覆盖，见"复测"一节）。
- 详细 urg HTML 报告位于本地 `sim/out/urgReport/`（未纳入版本控制，属仿真产物，可按需重新生成复核）。

---

## 复测（M1-07/08/09 收窄场景补齐后，2026-07-09）

- 采集命令：
  ```
  make regress COV=1     # 10/10 PASS，见 sim/result_summary.txt（已同步覆盖 doc/evidence/v0.1.7/result_summary.txt）
  make cov                # urg -full64 -dir out/cov.vdb -report out/urgReport
  ```
- 新增/回归场景：M1-07（CTRL 两步 START 单拍脉冲）、M1-08（busy 写保护，经 packet_sram 组合读口核实内容不变）、
  M1-09（packet_sram 读口遍历地址+多样数据，含升序/降序两趟遍历收 `rd_addr` toggle）；M1-01~M1-06 原场景一并回归，
  全部 PASS（10/10，见 `sim/result_summary.txt`）。
- 关键基础设施变更（供追溯）：`tb/m3_stub_if.sv` 新增 `rd_en`/`rd_addr`/`rd_data`（驱动/观测 `packet_sram` 读口，
  spec §2.3 M2 表"来自 M3"）与 `start_pulse`（旁路观测 `apb_slave_if.start_o`，spec §2.3 M1 端口表）；
  `tb/tb_top.sv` 将 `packet_sram` 的 `rd_en/rd_addr/rd_data` 由常量 0 改接至 `m3_stub`；
  `tb/uvm/env/m3_stub_driver.sv` 新增 `read_sram()`/`watch_start_pulse()` 任务。均为 tb/ 侧 TB 基础设施变更，未改
  rtl/，不影响既有场景行为（M1-01~M1-06 复跑结果不变）。

### 六类结果（复测）

| 类别 | 判据范围 | Covered/Total | 百分比（首测→复测） | ≥90% |
| --- | --- | --- | --- | --- |
| line | mod5(51/54) + mod7(5/5) | 56/59 | 93.22% → **94.92%** | ✅ |
| cond | mod5(42/46)；mod7 无条件表达式（0 分母，不计入） | 42/46 | 80.43% → **91.30%** | ✅ |
| toggle | mod5 Total Bits(289/446) + mod7 Total Bits(148/150) | 437/596 | 60.91% → **73.32%** | ❌ |
| branch | mod5(35/37) + mod7(4/4) | 39/41 | 92.68% → **95.12%** | ✅ |
| assert | mod5(8/8) + mod7(5/5) + mod13(4/4) + mod14(6/6)（Succeeded/Matched 口径，8个此前 0 Real Successes 的断言全部转正） | 23/23 | 78.26% → **100.00%** | ✅ |
| fsm | M1 RTL 无状态机构造（同首测结论） | — | N/A | N/A |

**结论：五类达标（line/cond/branch/assert 新转正，line/branch 保持），仅 toggle 仍 <90%**。三个已知缺口（SRAM 读口、
START 脉冲、busy 写保护）已通过 M1-07/08/09 完全闭合：

- `a_start_implies_enable_idle`/`a_start_single_pulse`（mod5）Real Successes 由 0 → 各 1 次。
- `a_rd_addr_no_x`/`a_read_after_write`（mod7）Real Successes 由 0 → 各 19 次；`packet_sram.sv:44-45` 的 `if(rd_en)`
  分支由 0% → 双分支 100%（mod7 branch 3/4→4/4）。
- `a_pktmem_busy_protect`（mod14）Real Successes 由 0 → 1 次。
- 副作用：mod7 line 80%→100%、toggle 50.67%→98.67%（`rd_addr[2:0]` 三位经升序+降序两趟遍历后双向翻转全覆盖，
  仅 `rst_n`/`rst` 因单次复位结构性不翻转，2/150 bit 不可覆盖，见下）；mod5 cond 80.43%→91.30%（新增 CTRL/busy
  相关条件表达式真实分支）；assert 全类别转正（100.00%）。

### toggle 剩余缺口逐项根因（模块/信号级，不放宽口径）

复测后 toggle 仍为 73.32%（437/596），主因集中在 **mod5（apb_slave_if）**：Total Bits 289/446=64.80%（mod7 已达
148/150=98.67%，接近上限）。逐项根因（`sim/out/urgReport/mod5.html` Toggle Coverage 明细）：

1. **结构性不可翻转（非缺口，无法通过任何激励改变）**：
   - `PRDATA[31:8]`（24 bit）：spec §5.2 全部已定义寄存器字段宽度均 ≤8 bit（RES_PKT_TYPE/SUM/XOR 恰为 8 bit 已是
     最宽字段），`PRDATA` 高 24 位在当前寄存器表下永远输出 0，无法翻转到 1——设计宽度决定，非激励不足。
   - `PREADY`：`assign PREADY = 1'b1`（§4.1"固定为1"），恒定值，按 spec 契约本就不允许翻转。
   - `rst`/`rst_n`：复位仅在仿真起始释放一次（`tb_top.sv` 单次 `presetn` 拉低再拉高），本轮各测试均为独立
     `simv` 单次运行，无"运行中二次复位"场景，`1->0` 方向天然不出现（mod7 同类 2 bit 也是此因）。
   以上共约 26 bit 数量级的结构性/契约性零翻转位，即便追加任意激励也不会改变。

2. **testplan 未覆盖的 CSR 字段写通路（真实缺口，非本轮任务范围）**：M1-01~M1-09 全部场景均未曾对 `CFG`
   （0x004）、`PKT_LEN_EXP`（0x014）寄存器做过任何 APB 写入（M1-01 仅在复位后读一次默认值），也未曾把
   `CTRL.enable` 从 1 写回 0（M1-07 的两个负例都是"enable 本就是 0"，未构造"先 1 后 0"的回落沿）、未曾把
   `IRQ_EN` 从非 0 写回 0。对应信号：`cfg_algo_mode`(1bit)/`cfg_type_mask[3:0]`(4bit)/`algo_mode_o`(1bit)/
   `type_mask_o[3:0]`(4bit)/`pkt_len_exp[5:0]`(6bit)/`exp_pkt_len_o[5:0]`(6bit)/`ctrl_enable`(1bit 仅缺
   1→0 方向)/`irq_en_done`/`irq_en_err`(各 1bit 仅缺 1→0 方向)，合计约 25 bit。这是**testplan 场景空白**
   （CFG/PKT_LEN_EXP 写通路、CTRL/IRQ_EN 回落沿目前均不在任何已登记场景的检查点范围内），非 RTL/TB 缺陷，
   建议后续单独开 M1 场景（如"CFG/PKT_LEN_EXP 写读回"）或并入 M2/M3 联调时随其配置流程一并覆盖。
   本卡任务范围（三个具名缺口：SRAM 读口/START 脉冲/busy 保护）已全部闭合，此项超出本卡范围，不在本轮展开。

3. **M3 stub 结果字段仅单向变化（真实缺口，部分结构性依赖 M3）**：`res_pkt_len_i`/`res_pkt_type_i`/
   `res_payload_sum_i`/`res_payload_xor_i` 的多数 bit 仅观察到 `0->1`（M1-03/M1-05 各自只 `set_result` 一次固定
   值，从未在同一测试内把某个已置 1 的结果位写回 0），`type_error_i`/`chk_error_i` 全程未被 stub 置过 1（M1-05
   仅用 `length_error` 触发 err 分支）。对应信号合计约 20+ bit。这是 M1 阶段 stub 激励覆盖面不足（可通过扩展
   `m3_stub_driver.set_result` 调用组合补齐，理论上不依赖真实 M3 到位），但同样超出本卡三个具名缺口范围，留待
   后续场景或 M2/M3 联调后用真实结果值的多样性自然收窄。

**结论**：toggle 73.32%（437/596）中，约 26 bit 为结构性零翻转（无法闭合，建议 M4-04 覆盖率过滤登记豁免）、
约 45+ bit 为 testplan 范围外的 CSR 写通路/stub 结果多样性缺口（可闭合但超出本卡三个具名缺口范围，建议顺延至
后续 M1 收尾场景或 M2/M3 联调）。本卡指定的三个缺口（SRAM 读口、START 脉冲、busy 写保护）已用 M1-07/08/09
完全闭合且转正，line/cond/branch/assert 四类均已达标（≥90%），toggle 未达标属如实报告、不放宽口径。
