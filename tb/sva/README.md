# SVA 断言目录（接口/协议/时序契约）

> 归属：**DV 撰写**（spec 推导，rev 按审 checker 同规审查）；RTL 内部不变量断言归 DE、放 rtl/ 侧，不入本目录。
> 断言覆盖率已并入 `-cm ...+assert` 口径（见 spec 第 0 章适配表）。

约定：

- 一个被测接口/模块一个文件：`<模块或接口>_sva.sv`（如 `apb_sva.sv`、`proc_core_sva.sv`），用 `bind` 挂接到 RTL 实例，**只准引用端口信号，禁止引用 RTL 内部信号**（引用内部信号 = 照抄实现，rev 打回）。
- 每条 property 上方注释标注 spec 章节号（如 `// §7.4 start 接受后 1 拍 busy=1`）；无法指回 spec 的 property 不许写——先走 spec 修改提案。
- 文件加入 `sim/flist/tb.f` 参与编译；断言失败计入 UVM 报告（`$error` / uvm_error 上报），FAIL 即回归 FAIL。
- 典型必写项（随模块交付逐步补齐）：APB 两段式时序与 PSLVERR 规则（§4.1 §8.3）、start/busy/done 时序契约（§7.4 §8.1）、FSM 合法迁移（§7.2）、IRQ 置位/清除时序（§8.2）。
