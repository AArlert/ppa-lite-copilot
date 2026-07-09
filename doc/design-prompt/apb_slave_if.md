# apb_slave_if 设计输入

- **里程碑**：M1

## spec 依据章节（逐条）

- **§0 适配 #7**：内部不变量断言由 DE 撰写（覆盖率含 assert 口径）。
- **§0 适配 #8**：`make lint` 干净是交付条件；告警登记 `doc/lint-waivers.md` 经 rev 复核。
- **§2.3 M1 apb_slave_if 端口表**（第 157–191 行）：本模块端口的唯一定义源。
- **§4.1 APB 3.0 访问规则**：两段式 SETUP→ACCESS；PREADY 固定 1；读写在 ACCESS 阶段生效/返回。
- **§4.2 地址空间划分**：CSR 区 `0x000~0x02B`、保留区、PKT_MEM 区 `0x040~0x05C`、越界区。
- **§5.1 字段属性说明**：RW / RO / W1P / RW1C 四类属性语义。
- **§5.2 完整寄存器表**：CTRL/CFG/STATUS/IRQ_EN/IRQ_STA/PKT_LEN_EXP/RES_*/ERR_FLAG 的偏移、位域、属性、复位值。
- **§6.1 PKT_MEM 地址映射**：`0x040 + 4×N → Word N`（N=0–7），本模块负责写地址译码与向 M2 转发 `pkt_mem_we_o/pkt_mem_addr_o/pkt_mem_wdata_o`。
- **§8.2 中断生成时序**：IRQ_STA 置位条件与时机、irq_o 组合输出。
- **§8.3 PSLVERR 统一响应策略**：合法/写只读/busy 写 PKT_MEM/越界四类响应。
- **§9.1 错误标志位**：ERR_FLAG 三位的语义（本模块只读透传 M3 结果，不做判定）。
- **§11.2 Lab1 必做项 1–3 + 选做项 4–5**：M1 验收范围。

> 与 §0 冲突时以 §0 为准（§0 抬头）。

## 端口定义

端口以 **spec §2.3「M1 apb_slave_if」表（第 157–191 行）为唯一权威**，DE 按该表逐信号实现，方向/位宽/命名不得偏离。此处不誊抄整表，仅摘录三类关键信号以便对齐职责边界：

- 写通路转发（送 M2）：`pkt_mem_we_o[1] / pkt_mem_addr_o[3] / pkt_mem_wdata_o[32]`。
- M3 结果只读输入（透传到 RES_*/STATUS/ERR_FLAG）：`busy_i / done_i / format_ok_i / length_error_i / type_error_i / chk_error_i / res_pkt_len_i[6] / res_pkt_type_i[8] / res_payload_sum_i[8] / res_payload_xor_i[8]`。
- 字段广播输出（送 M3）：`enable_o / start_o / algo_mode_o / type_mask_o[4] / exp_pkt_len_o[6] / done_irq_en_o / err_irq_en_o`。
- 中断输出：`irq_o[1]`。

> 地址/常量的 TB 侧唯一定义点为 `tb/uvm/env/ppa_reg_defs.sv`（CLAUDE.md §2/§8），RTL 侧不得另立硬编码来源与之冲突。

## 功能要求（对应 feature-matrix）

- **F1-1**（§4.1）：APB 3.0 两段式从机时序，PREADY 固定 1、无等待态。
- **F1-2**（§5.2）：全部 CSR 寄存器组的读写/只读/脉冲/写一清零行为，复位值与 §5.2 一致。
- **F1-3**（§4.2 §6.1）：地址译码 + PKT_MEM 窗口 `0x040~0x05C` 转写端口。
- **F1-4**（§8.3）：PSLVERR 统一错误响应（选做，按必做对待，§0 适配 #2）。
- **F1-5**（§8.2）：IRQ 生成、RW1C 清除、irq_o 组合输出（选做，按必做对待）。

## 边界与约束（每条标 spec 章节号）

- **复位（PRESETn 低有效，§2.3）**：所有 CSR 可写字段回到 §5.2 复位值——CTRL=0、CFG.algo_mode=1、CFG.type_mask=4'b1111、IRQ_EN=0、IRQ_STA=0、PKT_LEN_EXP=0；RO 字段复位读回 0（§5.2）。
- **APB 时序（§4.1）**：仅 SETUP（PSEL=1,PENABLE=0）→ACCESS（PSEL=1,PENABLE=1）两段式；写在 ACCESS 阶段生效，读在 ACCESS 阶段返回 PRDATA；PREADY 恒 1。PRDATA 与测试向量对齐即可（组合或寄存器输出均可，§4.1）。
- **字段属性（§5.1 §5.2）**：
  - RW（CTRL.enable / CFG.algo_mode / CFG.type_mask / IRQ_EN.* / PKT_LEN_EXP）：写入保持新值，可读回。
  - W1P（CTRL.start）：写 1 产生单拍脉冲即 `start_o`，不存储，读回为 0；仅在 `enable=1 && busy=0` 时被接受（§5.2 CTRL.start 行）。
  - RO（STATUS.* / RES_* / ERR_FLAG.*）：写入返回 PSLVERR=1 且寄存器值不变（§5.1 §8.3）。
  - RW1C（IRQ_STA.done_irq / err_irq）：读出当前状态，写 1 清零、写 0 无效（§5.1）。
- **STATUS/RES_*/ERR_FLAG 只读直透（§5.2 §8.1 §11.2）**：本模块不锁存、不判定，仅把 M3 结果输入映射到只读寄存器读口——STATUS.busy=`busy_i`、STATUS.done=`done_i`（§8.1 直连不额外锁存）、STATUS.error=`length_error_i|type_error_i|chk_error_i`（§5.2 STATUS[2] 定义为 ERR_FLAG 各位的或）、STATUS.format_ok=`format_ok_i`；RES_* 直透对应 `res_*_i`；ERR_FLAG.* 直透对应 `*_error_i`。
- **字段广播（§5.2 §2.3）**：`enable_o/algo_mode_o/type_mask_o/exp_pkt_len_o/done_irq_en_o/err_irq_en_o` 反映对应 RW 字段当前值；`start_o` 为接受的 start 脉冲。
- **PKT_MEM 写通路（§6.1 §6.2 §3.3 §8.3）**：ACCESS 阶段对 `0x040~0x05C` 的合法写，产生 `pkt_mem_we_o=1`、`pkt_mem_addr_o=(PADDR-0x040)>>2`（=Word N，§6.1 地址公式）、`pkt_mem_wdata_o=PWDATA`；M1 将 PWDATA 以 32-bit 整字驱动 pkt_mem_wdata_o，M2 按 word 整字存储；§3.3 所述字节视图仅为 word 内 4 字节到包字节的映射，两模块均不做字节级拆分/部分字节写。**busy=1（`busy_i`）期间写 PKT_MEM：写入无效且 PSLVERR=1**（§6.3 §8.3），即此时不得产生 `pkt_mem_we_o` 有效脉冲。
- **PSLVERR 统一响应（§8.3 §4.2 §5.1）**：① 合法 CSR/PKT_MEM 读写→PSLVERR=0；② 写 RO/W1P 寄存器→PSLVERR=1，寄存器值不变；③ busy=1 写 PKT_MEM→PSLVERR=1，写入无效；④ 访问保留区（`0x02C~0x03F`、`0x05D~0x05F`）或未定义地址（`0x060` 及以上）→PSLVERR=1 且无副作用（§4.2）。PSLVERR 仅在 ACCESS 阶段随访问给出（§4.1）。
- **中断（§8.2）**：IRQ_STA.done_irq 在 `done_i` 上升沿且 `done_irq_en=1` 时同拍置位；IRQ_STA.err_irq 在 `done_i` 上升沿且任意错误有效且 `err_irq_en=1` 时同拍置位；`irq_o = done_irq | err_irq` 组合输出无额外延迟；软件写 IRQ_STA 对应位 1 则下一拍清零、irq_o 随即拉低（§8.2）。
- **未列位域（§5.2 尾注）**：未列出的位域读回 0、写入无效。

> 以上均为 spec 已定义的对外可见行为；DE 不得新增任何 spec 之外的寄存器语义/时序/错误响应。发现 spec 缺陷走 §8 修改提案流程，不得在本文件或 RTL 私自定义。

## 内部断言建议（非强制，DE 撰写）

- PREADY 恒为 1（§4.1）。
- `pkt_mem_we_o` 有效当且仅当处于 ACCESS 写、地址落在 `0x040~0x05C` 且 `busy_i=0`（§6.3 §8.3）；`busy_i=1` 时 PKT_MEM 写不产生 we 脉冲。
- `start_o` 至多单拍脉冲、且蕴含 `enable=1 && busy_i=0`（§5.2）。
- 地址译码互斥：同一 ACCESS 拍 CSR 命中与 PKT_MEM 命中不同时有效。
- PSLVERR=1 与"寄存器/SRAM 状态改变"互斥（写只读/越界/busy 写不得留副作用，§8.3）。

## 已裁决歧义

- **BUG-001 / spec 修改记录 r4（SPEC_CHANGED）**：§5.2 PKT_LEN_EXP 与 §9.1 明确 `exp_pkt_len=0` 为未配置、跳过一致性检查。**对本模块的影响仅限于**：`exp_pkt_len_o` 必须透传 PKT_LEN_EXP 字段当前值（含复位默认 0），"未配置=跳过比对"及 length_error 一致性判定属 M3 职责，M1 不判定。
- **BUG-002 / spec 修改记录 r5**：涉及 M3 非法包长时 sum/xor 与读拍钳位，**不属于本模块行为**，此处仅备注、不引用为 M1 约束。

## 验收关联（testplan 场景 ID，DE 自检不替代 DV 验证）

- **M1-01**（§4.1 §5.2 §11.2-必1）：APB 两段式读写时序 + CTRL/CFG/STATUS 复位值。
- **M1-02**（§6.1 §11.2-必2）：PKT_MEM 写入地址映射（本模块负责的写通路：wr_en/wr_addr 递增/wr_data 匹配）。
- **M1-03**（§5.2 §11.2-必3）：RES_* 只读通路（外部 stub 驱动 res_*_i，APB 读回比对）。
- **M1-04**（§8.3 §11.2-选4）：PSLVERR 统一响应（选做，按必做对待）。
- **M1-05**（§5.2 §8.2 §11.2-选5）：IRQ 寄存器组（选做，按必做对待）。

## 明确不做

- **SRAM 本体存储**：8×32-bit 双端口 SRAM 的存储/读写时序是 M2（packet_sram）职责，本模块只产生写端口信号，不实例化存储阵列（§2.2 §6.3 教学提示）。
- **包语义判断 / 处理 FSM**：包头解析、格式检查、错误判定、payload 摘要计算均为 M3（packet_proc_core）职责；本模块对 STATUS/ERR_FLAG/RES_* 只读透传，不做任何判定（§2.2 §9）。
- **busy 期间写保护的仲裁本体**：写保护由 M1 的 PSLVERR 机制实现（§8.3），但 SRAM 侧不做仲裁——M2 不判 busy（§6.3 教学提示）。
