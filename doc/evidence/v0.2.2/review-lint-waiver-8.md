# rev 审查记录：lint 豁免 #8 复核（packet_proc_core.sv 九条 Lint-[SVA-DIU]）

- 日期：2026-07-13
- 审查员：rev（与登记人 DE 不同实例）
- 版本：0.2.2（M2）
- 审查对象：`doc/lint-waivers.md` 豁免 #8 —— `rtl/packet_proc_core.sv` 第 278/283/288/293/298/304/309/317/322 行九条 `Lint-[SVA-DIU] Disable iff used` 告警（M3 内部不变量断言：a_state_legal / a_busy_done_mutex / a_rden_only_process / a_word_cnt_bound / a_word_cnt_incr / a_process_ignores_start / a_process_outputs_clear / a_algo_mode0_no_chkerr / a_format_ok_consistency），登记人=DE，状态「待 rev 复核」。
- 裁决基准：CLAUDE.md §7（lint 门禁——`make lint` 干净，或告警登记 `doc/lint-waivers.md` 经 rev 复核）+ §5（本地 VM 探测到工具须真跑）；豁免成立标准参照已批准先例 #1/#2（同类别 Lint-[SVA-DIU]，rtl/packet_sram.sv、rtl/apb_slave_if.sv）。
- 环境探测：`command -v vcs` = /home/synopsys/vcs-mx/O-2018.09-SP2/bin/vcs（探测到）；`command -v verdi` = /home/synopsys/verdi/Verdi_O-2018.09-SP2/bin/verdi（探测到）；`command -v xdebug` 未探测到。按 §5 探测到即真跑，本记录基于实测 `make -C sim lint` 输出，非声明。

---

## 一、总裁决

**通过（9 处全部准予豁免）。** 依据三点，逐条见下：

1. **告警性质属实为提示性**：`Lint-[SVA-DIU] Disable iff used` 是 VCS `+lint=all` 对"任何使用了 `disable iff` 结构的并发断言"给出的提示性告警，非 `Error-` 级、非语义缺陷提示；本次实测 lint.log 全程 `Error-` 计数为 0。
2. **写法与 #1/#2 同类同因（已核实归档记录，非采信 DE 自述）**：见第三节比对。
3. **无隐藏真实缺陷**：`disable iff (rst)` 仅在复位期间屏蔽断言评估（规避复位期 X 态误报），正常运行期断言语义不被削弱；九条均为检查设计正确性的内部不变量断言，去掉 `disable iff` 会引入复位期误触发，改写为复合表达式 `!rst_n` 又会触发更实质的 `Lint-[SVA-CE] Complex expression found`——现写法是等价必要且已属最优规避。

## 二、抽查明细

### 2.1 RTL 用法核对（Read rtl/packet_proc_core.sv 第 271–326 行）

- 第 271 行 `` `ifndef SYNTHESIS`` 起断言块，第 326 行 `` `endif`` 收束——断言仅在仿真域生效，不入综合，与豁免条目描述一致。
- 第 274–275 行：`logic rst; assign rst = !rst_n;`——确为**单一信号**驱动 `disable iff`，非复合表达式，与 #2（`assign rst = !PRESETn;`，同在 `` `ifndef SYNTHESIS`` 块）写法一致，规避 `Lint-[SVA-CE]`。
- 九条断言逐行核对：均为 `assert property (@(posedge clk) disable iff (rst) ...)`，`disable iff` 引用的正是上述单一信号 `rst`。名称与行号逐一吻合：

  | 行 | 断言名 | 检查内容（内部不变量） |
  | --- | --- | --- |
  | 278 | a_state_legal | FSM 状态恒在 {ST_IDLE,ST_PROCESS,ST_DONE} 内 |
  | 283 | a_busy_done_mutex | busy_o 与 done_o 永不同时为 1 |
  | 288 | a_rden_only_process | mem_rd_en_o=1 仅在 PROCESS 拍 |
  | 293 | a_word_cnt_bound | PROCESS 态 word_cnt_q ≤ last_word_cnt |
  | 298 | a_word_cnt_incr | PROCESS 未到末拍时字计数每拍 +1 |
  | 304 | a_process_ignores_start | PROCESS 态次态不跳回 IDLE |
  | 309 | a_process_outputs_clear | PROCESS 期错误标志/format_ok/res_* 保持清零 |
  | 317 | a_algo_mode0_no_chkerr | algo_mode_i=0 时 chk_error_w 恒 0 |
  | 322 | a_format_ok_consistency | DONE 态 format_ok_o 与三类错误互斥一致 |

  九条均为对 spec §7.2/§7.3/§7.4/§9.2 行为的**内部一致性断言**，`disable iff (rst)` 不改变其正常期语义。

### 2.2 实测 lint 判定范围核对（../rtl/ ../tb/）

以 Makefile lint 目标自带的判定逻辑（`grep -A1 '^Lint-\[' out/lint.log | grep -B1 -E '^\.\./(rtl|tb)/'`）统计实测 `out/lint.log`，判定范围内共 **54** 条告警行，逐类归属全部落入已登记豁免 #1–#8，**无任何新增/未处置告警**：

| 类别 | 文件:行 | 条数 | 归属豁免 |
| --- | --- | --- | --- |
| SVA-DIU | rtl/packet_proc_core.sv:278/283/288/293/298/304/309/317/322 | 9 | **#8（本审查对象）** |
| SVA-DIU | rtl/packet_sram.sv:61/65/70/74/80 | 5 | #1（已批准，archive） |
| SVA-DIU | rtl/apb_slave_if.sv:268/273/278/283/290/295/300/306 | 8 | #2（已批准，archive） |
| SVA-DIU | tb/sva/apb_protocol_sva.sv:21/27/32/38 | 4 | #3（已批准，archive） |
| SVA-DIU | tb/sva/apb_slave_if_sva.sv:51/57/63/68/73/78 | 6 | #4（已批准，archive） |
| NS | tb/tb_top.sv:20; apb_driver.sv:20/21/46/49; apb_monitor.sv:23 | 6 | #5（已批准，archive） |
| WMIA-L | tb/uvm/apb_agent/apb_seq_item.sv:10/11/12/13 | 4 | #6（已批准，archive） |
| NS | tb/uvm/env/m3_stub_driver.sv:26/35/41/43/50/52/57/59/71/74/77/87 | 12 | #7（已批准） |
| 合计 | | **54** | 5+8+4+6+6+4+12+9=54 ✓ |

- packet_proc_core.sv 的 SVA-DIU 命中行**精确为 9 行且与 #8 登记行号完全一致**（278/283/288/293/298/304/309/317/322），无多无少。
- 判定范围内除 SVA-DIU / NS / WMIA-L 三类外**无其他 Lint 类别**；`Error-` 级 0 条。
- 说明：`make -C sim lint` 退出码为 1（因判定范围内存在未清零的已登记豁免告警，Makefile 按设计返回非零），这是"有已登记豁免"的预期行为，非编译/链接失败；lint 编译本身成功（0 Error）。

## 三、"同类同因"主张核实（对照归档 #1/#2，非采信 DE 自我判定）

已 grep `doc/lint-waivers-archive.md` 取 #1/#2 原始登记行比对：

| 维度 | #1 packet_sram.sv | #2 apb_slave_if.sv | #8 packet_proc_core.sv（本次） |
| --- | --- | --- | --- |
| 告警类别 | Lint-[SVA-DIU] Disable iff used | Lint-[SVA-DIU] Disable iff used | Lint-[SVA-DIU] Disable iff used ✓ |
| 断言性质 | DE 内部不变量断言 | DE 内部不变量断言 | DE 内部不变量断言 ✓ |
| disable 信号 | 单一 `rst`（`assign rst=!rst_n;`） | 单一 `rst`（`assign rst=!PRESETn;`，`` `ifndef SYNTHESIS`` 块） | 单一 `rst`（`assign rst=!rst_n;`，`` `ifndef SYNTHESIS`` 块）✓ |
| 规避目标 | 更实质的 Lint-[SVA-CE] | 更实质的 Lint-[SVA-CE] | 更实质的 Lint-[SVA-CE] ✓ |
| 复核结论 | rev 2026-07-09 批准 | rev 2026-07-09 批准 | 本记录批准 |

三维度（类别 / 断言性质 / 单一信号 disable iff 写法与规避目标）完全一致。DE 的"同类同因"自述**属实**，与已批准先例构成同一豁免理由，无区别对待依据。

## 四、观察与遗留风险（非阻塞）

- **豁免正文措辞已略微陈旧（非缺陷，不阻塞）**：#8 原因栏称该模块"尚未接入 tb_top、未实例化"，并以"临时启用 rtl.f 中一行"做自检描述。实测当前 `sim/flist/rtl.f` 已**永久启用** `../rtl/packet_proc_core.sv`（非临时），本次 `make -C sim lint` 是在该行常启状态下真实编译并 lint 出这 9 条告警——即实测证据**强于**豁免自述的临时自检。断言无论是否实例化都会被编译进 lint 范围，豁免效力不受影响。建议 orch 在后续 M3 接线交付时顺手把 #8 原因栏"尚未接入/临时启用"措辞更新为现状，纯文档卫生，非本卡阻塞项。
- **风险评级：低。** 9 条均为 VCS `+lint=all` 对标准 `disable iff` 复位屏蔽惯用法的提示性告警，无一指向 packet_proc_core FSM/数据通路的功能或协议语义缺陷。

## 五、复现/核实方式

- 环境：`command -v vcs / verdi`（均探测到，见首部）。VCS 环境变量取自 `~/.bashrc` Synopsys 段（VCS_HOME / VERDI_HOME / VCS_MX_HOME / SCL_HOME / LD_LIBRARY_PATH / VCS_ARCH_OVERRIDE=linux / LM_LICENSE_FILE=27000@icarray-virtual-machine），非交互 shell 需显式 export 后运行。
- 实测命令：`make -C sim lint`
  - 实际执行：`vcs -full64 -sverilog -timescale=1ns/1ps -ntb_opts uvm-1.2 +vcs+lic+wait -LDFLAGS "-Wl,--no-as-needed" +lint=all,noVCDE -f flist/tb.f -f flist/rtl.f -o out/simv_lint -l out/lint.log`
  - VCS O-2018.09-SP2_Full64；日志 `sim/out/lint.log`。
- 判定范围抽取：`grep -A1 '^Lint-\[' sim/out/lint.log | grep -B1 -E '^\.\./(rtl|tb)/'`（Makefile 内建判定逻辑）。
- 关键实测摘录：
  - `Error-` 级计数：0。
  - packet_proc_core.sv SVA-DIU 命中：`278 283 288 293 298 304 309 317 322`（共 9，与 #8 登记完全一致）。
  - 判定范围内 Lint 告警行合计 54，全部归属已登记豁免 #1–#8，无新增/未处置项。
  - Makefile 末行：`lint 有告警（本仓库文件范围内）：修复，或登记 doc/lint-waivers.md 后由 rev 复核`（退出码 1，系判定范围内存在已登记豁免的预期行为）。
- RTL 核实：`Read rtl/packet_proc_core.sv`（第 271–326 行断言块）。
- 同类核实：`grep '^| 1 \|^| 2 ' doc/lint-waivers-archive.md`（#1/#2 原始登记行）。
