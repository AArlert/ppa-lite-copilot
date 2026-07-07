# Feature Matrix（功能分解，arch 维护）

> 本表是**纯设计分解工件**：由 arch 维护行（功能拆分、spec 锚点、场景映射），**不含任何状态位**。
> 交付状态由脚本从 rtl/ 文件现算、验证状态从 testplan 现算——`make handover` / `make next` 查看，不落盘。
> docs-check 守卫：编号唯一；关联场景必填且必须真实存在于 testplan（防幽灵引用）。
> M 完成判据见 CLAUDE.md §4.1：该 M 模块 RTL 齐 + 关联场景全 ✅ + regress 证据 + rev 签核（`make next` 机械核对）。

| 编号 | 里程碑 | 模块 | 功能 | spec 依据 | 关联场景 |
| --- | --- | --- | --- | --- | --- |
| F1-1 | M1 | apb_slave_if | APB 3.0 两段式从机时序（PREADY 固定 1） | §4.1 | M1-01 |
| F1-2 | M1 | apb_slave_if | CSR 寄存器组（CTRL/CFG/STATUS/IRQ_EN/IRQ_STA/PKT_LEN_EXP/RES_*/ERR_FLAG） | §5.2 | M1-01 M1-03 |
| F1-3 | M1 | apb_slave_if | 地址译码 + PKT_MEM 窗口 0x040–0x05C 转写端口 | §4.2 §6.1 | M1-02 |
| F1-4 | M1 | apb_slave_if | PSLVERR 统一错误响应 | §8.3 | M1-04 |
| F1-5 | M1 | apb_slave_if | IRQ 生成与 RW1C 清除、irq_o 组合输出 | §8.2 | M1-05 |
| F1-6 | M1 | packet_sram | 8×32bit 双端口同步 SRAM | §2.3 | M1-02 |
| F2-1 | M2 | packet_proc_core | 3 态 FSM（IDLE/PROCESS/DONE）+ busy/done 输出约定 | §7 | M2-01 M2-03 |
| F2-2 | M2 | packet_proc_core | 第 0 拍头部解析（len/type/flags/hdr_chk）+ 读地址递增 | §7.3 | M2-01 |
| F2-3 | M2 | packet_proc_core | 三类错误并行判定 + format_ok + 清除时机 | §9 | M2-02 M2-04 M2-05 M2-06 |
| F2-4 | M2 | packet_proc_core | payload sum/XOR 累加（8bit 截断） | §3.4 §7.3 | M2-01 M2-05 |
| F3-1 | M3 | ppa_top | 三模块纯连线集成 + 时钟复位分发（无状态逻辑） | §2.3 | M3-01 M3-02 M3-03 |
| F4-1 | M4 | (全系统) | 回归清单整理 + result_summary.txt 生成链路 | §11.5 §12.4 | M4-01 |
| F4-2 | M4 | (全系统) | 覆盖率收集/合并/报告与缺口修复（含 assert，§0 适配 7） | §11.5 | M4-02 M4-04 |
