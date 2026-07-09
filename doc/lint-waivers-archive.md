# Lint 豁免登记表归档件

> **默认不读**，只在核对历史豁免时 grep。由 `make docs-archive` 机械搬运 lint-waivers.md 中
> 已经 rev 批准的豁免行，新的在上；待复核行永不入此文件。归档行的豁免效力不变——核对 lint
> 告警是否已登记时 grep 本文件与 lint-waivers.md 两处。新豁免编号取两文件最大 # 递增。

| # | 告警类别 | 对象（文件:行） | 原因 | 结论（豁免/待修） | 复核（rev/日期） |
| --- | --- | --- | --- | --- | --- |
| 3 | Lint-[SVA-DIU] Disable iff used | tb/sva/apb_protocol_sva.sv:21,27,32,38（a_pready_always1/a_access_preceded_by_setup/a_setup_then_access/a_addr_stable_setup_to_access 四条接口/协议 SVA，bind 到 tb_top） | 与 #1/#2 同一豁免理由：DV 撰写的接口/协议契约断言同样采用单一信号 `rst`（`assign rst = !presetn;`）规避 `Lint-[SVA-CE]`，仅余提示性的 `Lint-[SVA-DIU]`，四处均为等价必要用法（复位期间屏蔽断言评估） | 豁免 | rev 2026-07-09 批准 |
| 4 | Lint-[SVA-DIU] Disable iff used | tb/sva/apb_slave_if_sva.sv:51,57,63,68,73,78（a_pktmem_write_map/a_pktmem_busy_protect/a_pktmem_read_placeholder/a_reserved_addr_slverr/a_irq_done_same_cycle/a_irq_err_same_cycle 六条接口 SVA，bind 到 apb_slave_if，仅引用模块端口信号） | 与 #1/#2 同一豁免理由：采用单一信号 `rst`（`assign rst = !PRESETn;`）规避 `Lint-[SVA-CE]`，仅余提示性的 `Lint-[SVA-DIU]`，六处均为等价必要用法 | 豁免 | rev 2026-07-09 批准 |
| 5 | Lint-[NS] Null statement | tb/tb_top.sv:20（`repeat (5) @(posedge pclk);`）；tb/uvm/apb_agent/apb_driver.sv:20/21/46/49（`wait(vif.presetn===1'b1);` / `@(vif.drv_cb);`（x2）/ `do @(vif.drv_cb); while(...);`）；tb/uvm/apb_agent/apb_monitor.sv:23（`@(vif.mon_cb);`） | `+lint=all` 对"仅含时序控制、无其他动作"的语句（纯 `@(...)`/`wait(...)`/`repeat(...)@(...)`/`do...while(...)` 同步等待）提示 Null statement，这是 UVM/SV driver-monitor 两段式握手的标准写法（等待时钟沿/复位释放/PREADY），无实质"空语句"可优化——去掉该语句即破坏时序同步语义。6 处均为 BUG-006 登记范围内 0.1.0 里程碑遗留代码，非本轮引入 | 豁免（0.1.0 遗留，非本轮引入；见 doc/bugs.md BUG-006） | rev 2026-07-09 批准 |
| 1 | Lint-[SVA-DIU] Disable iff used | rtl/packet_sram.sv:61,65,70,74,80（a_wr_addr_no_x/a_rd_addr_no_x/a_wr_en_no_x/a_rd_en_no_x/a_read_after_write 五条内部不变量断言） | `+lint=all` 对任何使用 `disable iff` 的并发断言均提示告警；`disable iff (rst)` 是复位期间屏蔽断言评估的标准/推荐写法（避免复位期间 X 态误报断言失败），去掉会导致复位阶段断言误触发。已用单一信号 `rst`（`assign rst = !rst_n;`）而非复合表达式 `!rst_n`，规避了更实质的 `Lint-[SVA-CE] Complex expression found` 告警；本条属"使用了 disable iff 结构"的提示性告警，五处均为等价必要用法，无法进一步消除又不破坏断言语义 | 豁免 | rev 2026-07-09 批准 |
| 2 | Lint-[SVA-DIU] Disable iff used | rtl/apb_slave_if.sv:268,273,278,283,290,295,300,306（a_pready_always1/a_we_valid_cond/a_no_we_when_busy/a_start_implies_enable_idle/a_start_single_pulse/a_addr_decode_mutex/a_pslverr_no_we_sideeffect/a_pslverr_on_ro_write 八条内部不变量断言） | 与 #1 同一豁免理由：`disable iff` 为复位期间屏蔽断言评估的标准写法，已采用单一信号 `rst`（`assign rst = !PRESETn;`，模块内定义于 `` `ifndef SYNTHESIS`` 块）规避 `Lint-[SVA-CE]` 复合表达式告警，仅余提示性的 `Lint-[SVA-DIU]`，八处均为等价必要用法 | 豁免 | rev 2026-07-09 批准 |
