# Lint 豁免登记表

> `make lint`（VCS +lint；SpyGlass 部署后换后端、入口与本表不变）告警的处置：修复，或在此逐条登记豁免。
> 登记人 = DE；**复核人 = rev**（未复核的豁免不算数）。格式仿覆盖率过滤登记：对象/位置/原因/结论。

| # | 告警类别 | 对象（文件:行） | 原因 | 结论（豁免/待修） | 复核（rev/日期） |
| --- | --- | --- | --- | --- | --- |
| 1 | Lint-[SVA-DIU] Disable iff used | rtl/packet_sram.sv:61,65,70,74,80（a_wr_addr_no_x/a_rd_addr_no_x/a_wr_en_no_x/a_rd_en_no_x/a_read_after_write 五条内部不变量断言） | `+lint=all` 对任何使用 `disable iff` 的并发断言均提示告警；`disable iff (rst)` 是复位期间屏蔽断言评估的标准/推荐写法（避免复位期间 X 态误报断言失败），去掉会导致复位阶段断言误触发。已用单一信号 `rst`（`assign rst = !rst_n;`）而非复合表达式 `!rst_n`，规避了更实质的 `Lint-[SVA-CE] Complex expression found` 告警；本条属"使用了 disable iff 结构"的提示性告警，五处均为等价必要用法，无法进一步消除又不破坏断言语义 | 豁免 | rev 2026-07-09 批准 |
| 2 | Lint-[SVA-DIU] Disable iff used | rtl/apb_slave_if.sv:268,273,278,283,290,295,300,306（a_pready_always1/a_we_valid_cond/a_no_we_when_busy/a_start_implies_enable_idle/a_start_single_pulse/a_addr_decode_mutex/a_pslverr_no_we_sideeffect/a_pslverr_on_ro_write 八条内部不变量断言） | 与 #1 同一豁免理由：`disable iff` 为复位期间屏蔽断言评估的标准写法，已采用单一信号 `rst`（`assign rst = !PRESETn;`，模块内定义于 `` `ifndef SYNTHESIS`` 块）规避 `Lint-[SVA-CE]` 复合表达式告警，仅余提示性的 `Lint-[SVA-DIU]`，八处均为等价必要用法 | 豁免 | rev 2026-07-09 批准 |

（注：本次自检除上表 2 条外未见其余 `Lint-` 告警指向 rtl/packet_sram.sv 或 rtl/apb_slave_if.sv；tb/ 下既有 `Lint-[NS]` `Lint-[ULCO]` `Lint-[WMIA-L]` 等告警属既有 TB/UVM 库代码，非本次交付范围，未登记于此表。`make -C sim lint` 因 sim/flist 顺序问题实测报错（rtl.f 早于 tb.f 编译，package 未就绪），详见 BUG-005；本表结论基于诊断性验证——手动执行 `vcs +lint=all,noVCDE -f flist/tb.f -f flist/rtl.f`（仅调换清单顺序，未改 Makefile/flist 任何文件）——两次分别针对 packet_sram.sv、apb_slave_if.sv 均未见 `Error-` 级别发现，退出码 0）
