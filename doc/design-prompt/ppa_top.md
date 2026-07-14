# ppa_top 设计输入

- **里程碑**：M3

> 说明：spec §2.2/§2.3 中 M1/M2/M3 是**模块实例编号**，不是项目 Milestone。本仓库 Milestone 定义见 CLAUDE.md §4.1：M3=Lab3，范围即本模块 ppa_top（三模块集成冒烟）。前置 M1（apb_slave_if + packet_sram）、M2（packet_proc_core）RTL 已就绪，本模块不重复其行为，仅做连线与引脚透传。

## spec 依据章节（逐条）

- **§0 适配 #2**：选做项按必做对待——§11.4 选做验收项 4（busy 期间写 PKT_MEM 返回 PSLVERR）、5（中断路径闭环）计入 M3 完成判据；对本模块而言仅意味着须提供对应**连线通路**（行为在 M1，见"明确不做"）。
- **§0 适配 #7**：RTL 内部不变量断言由 DE 撰写（覆盖率含 assert 口径）；纯连线模块无状态，断言以连通性/无 X 为主，见"内部断言建议"。
- **§0 适配 #8**：`make lint` 干净是交付条件；告警登记 `doc/lint-waivers.md` 经 rev 复核。
- **§2.1 系统结构**：顶层框图与时钟/复位分发约定——`ppa_top` 对外接 `PCLK`/低有效 `PRESETn`，统一分发到 M1/M2/M3；M1↔M2 写端口、M3↔M2 读端口、M1→M3 控制、M3→M1 结果/状态互连；irq_o 为对外引脚（第 118 行分发约定、第 104–114 行连线约定）。
- **§2.2 模块职责一览**（ppa_top 行，第 158 行）：三模块连线与引脚透传；统一分发时钟/复位到 M1/M2/M3；**无额外状态逻辑**。
- **§2.3 Top ppa_top 端口表**（第 241–253 行）：本模块对外端口的唯一定义源（11 个信号）。
- **§2.3 M1/M2/M3 端口表**（第 164–237 行）：三子模块端口的唯一权威，互连信号名/位宽/方向以各表「说明」列为准。
- **§6.3 访问限制**：busy 期间写 PKT_MEM → PSLVERR=1 的**通路**（M3.busy_o → M1.busy_i，供 M1 判定）；行为实现在 M1，本模块只连线。
- **§8.2 中断生成时序**：irq_o 闭环**通路**（M3.done_o → M1.done_i 供 IRQ 生成；M1.irq_o → 顶层 irq_o 引脚）；置位/清除行为在 M1，本模块只连线。
- **§10.1 正常场景 / §10.3 边界场景**：N-1..N-4、B-1..B-4 经端到端链路的期望结果（集成验收锚点，行为由 M1/M2/M3 产生）。
- **§11.4 Lab3**：第 5 周集成设计要点（纯连线 + 时钟/复位分发）+ 必做验收项 1（端到端链路）/2（连续两帧）/3（STATUS 总线通路）+ 选做 4（busy 写保护）/5（中断闭环）。

> 与 §0 冲突时以 §0 为准（§0 抬头）。

## 端口定义

对外端口以 **spec §2.3「Top ppa_top」表（第 241–253 行）为唯一权威**，DE 按该表逐信号实现，方向/位宽/命名不得偏离；发现需增删改端口必须先走 spec 修改提案（CLAUDE.md §8），不得在本文件或 RTL 私改。11 个对外信号：

| 方向 | 信号 | 位宽 | 说明（§2.3 Top 表） |
| --- | --- | --- | --- |
| 输入 | PCLK | 1 | APB 时钟 |
| 输入 | PRESETn | 1 | APB 复位（低有效） |
| 输入 | PSEL | 1 | APB 从设备选择 |
| 输入 | PENABLE | 1 | APB 使能信号 |
| 输入 | PWRITE | 1 | APB 写使能 |
| 输入 | PADDR | 12 | APB 地址 |
| 输入 | PWDATA | 32 | APB 写数据 |
| 输出 | PRDATA | 32 | APB 读数据 |
| 输出 | PREADY | 1 | APB 就绪（固定 1） |
| 输出 | PSLVERR | 1 | APB 错误响应 |
| 输出 | irq_o | 1 | 中断输出（来自 M1，覆盖 done/err 事件通知） |

> **注意（已裁决，r11/BUG-010）**：§2.1 框图此前将 `done_o` 画为顶层对外引脚，与 §2.3 Top 端口表（不含 `done_o`）不一致；rev 裁决取方向 (a)——§2.1 已删除 done_o 对外引脚画法并补澄清注，与本 design-prompt 一致：**ppa_top 不引出 done_o 顶层引脚**，M3.done_o 仅内部接入 M1.done_i；软件经 APB 轮询 STATUS.done（§8.1）观察完成。M3-01/M3-03 场景均经 APB 读 STATUS 观察，不受影响。

## 功能要求（对应 feature-matrix）

- **F3-1（§2.1 §2.3 §11.4 第 5 周）**：三模块纯连线集成 + 时钟/复位分发，**无状态逻辑**。→ M3-01 M3-02 M3-03（另经通路支撑选做 M3-04 M3-05）

模块互连清单（信号名/位宽以 §2.3 各表「说明」列为唯一依据，DE 按名对接）：

**顶层引脚 ↔ M1（APB + 中断，§2.3 M1/Top 表）**
- Top.PCLK/PSEL/PENABLE/PWRITE/PADDR/PWDATA → M1.PCLK/PSEL/PENABLE/PWRITE/PADDR/PWDATA
- Top.PRESETn → M1.PRESETn
- M1.PRDATA/PREADY/PSLVERR → Top.PRDATA/PREADY/PSLVERR
- M1.irq_o → Top.irq_o

**时钟/复位分发（§2.1 第 118 行；§2.3 M2/M3 表 clk/rst_n 说明）**
- Top.PCLK → M2.clk、M3.clk
- Top.PRESETn → M2.rst_n、M3.rst_n（低有效直连映射，无极性变换）

**M1 → M2 写端口（§2.3 M1 表 pkt_mem_*_o / M2 表 wr_*；§11.4「M1↔M2 写端口」）**
- M1.pkt_mem_we_o → M2.wr_en
- M1.pkt_mem_addr_o → M2.wr_addr
- M1.pkt_mem_wdata_o → M2.wr_data

**M3 → M2 读端口（§2.3 M3 表 mem_rd_*_o / M2 表 rd_*；§11.4「M3↔M2 读端口」）**
- M3.mem_rd_en_o → M2.rd_en
- M3.mem_rd_addr_o → M2.rd_addr
- M2.rd_data → M3.mem_rd_data_i

**M1 → M3 控制（§2.3 M3 表输入「来自 M1」说明；§11.4「M1→M3 控制信号」）**
- M1.start_o → M3.start_i
- M1.algo_mode_o → M3.algo_mode_i
- M1.type_mask_o → M3.type_mask_i
- M1.exp_pkt_len_o → M3.exp_pkt_len_i

**M3 → M1 结果/状态（§2.3 M1 表输入「M3 …」说明；§11.4「M3→M1 结果/状态」）**
- M3.busy_o → M1.busy_i
- M3.done_o → M1.done_i
- M3.format_ok_o → M1.format_ok_i
- M3.length_error_o → M1.length_error_i
- M3.type_error_o → M1.type_error_i
- M3.chk_error_o → M1.chk_error_i
- M3.res_pkt_len_o → M1.res_pkt_len_i
- M3.res_pkt_type_o → M1.res_pkt_type_i
- M3.res_payload_sum_o → M1.res_payload_sum_i
- M3.res_payload_xor_o → M1.res_payload_xor_i

## 边界与约束（每条标 spec 章节号）

**纯连线 / 无状态（核心约束）**
- ppa_top 为**结构化网表**：只做子模块例化与信号互连，**不含任何寄存器、FSM、组合运算或译码逻辑**（§2.2 第 158 行「无额外状态逻辑」、§2.1 第 102 行「薄层连线，无状态逻辑」、§11.4 第 5 周「纯连线」）。
- 不得在顶层新增任何对外可见行为：所有寄存器语义、协议时序、错误响应、中断、SRAM 读写、包处理均由 M1/M2/M3 产生（§2.2 各模块职责行）。顶层引入的任何"加工"都属行为泄漏，禁止。

**时钟/复位分发**
- 三子模块同源时钟 = Top.PCLK；同源复位 = Top.PRESETn（低有效），M2/M3 的 clk/rst_n 由 PCLK/PRESETn 直连映射（§2.1 第 118 行、§2.3 M2 表 clk/rst_n 说明第 202–203 行、M3 表第 219–220 行）。
- 不得插入复位同步器、时钟门控、分频或复位极性变换——spec 未定义此类行为，属新增对外行为（§2.1 分发约定、行为泄漏禁区 CLAUDE.md §8）。PRESETn 与 rst_n 均低有效，直连即可。

**互连完整性**
- 每条互连按上「功能要求」清单一一对接，位宽/方向以 §2.3 各表为准；不得截断、错接或悬空**已定义的功能连线**（§2.3 M1/M2/M3/Top 表）。
- **允许悬空的输出**：M1 的 `enable_o`（CTRL.enable 可见性抽头）、`done_irq_en_o`、`err_irq_en_o`（IRQ_EN 字段可见性抽头）为 M1 对外暴露的字段观测信号，无子模块消费、§2.3 Top 表亦无对应引脚——ppa_top 不引出、可保持未连接（§2.3 M1 表第 176/181–182 行；这些字段的功能作用发生在 M1 内部，§5.2/§8.2）。DE 应在此处按 lint 要求妥善处理未使用端口并（如触发告警）登记 `doc/lint-waivers.md`（§0 适配 #8）。

**busy 写保护通路（§6.3）**
- ppa_top 须保证 M3.busy_o → M1.busy_i 连线成立，使 M1 能据 busy 判定 PKT_MEM 写保护并返回 PSLVERR（§6.3 表、§8.3）。判定与 PSLVERR 生成行为在 M1，本模块只提供通路。

**中断闭环通路（§8.2）**
- ppa_top 须保证 M3.done_o → M1.done_i、M1.irq_o → Top.irq_o 连线成立，使中断"同拍置位/组合输出"链路闭合（§8.2 表）。置位/RW1C 清除/irq_o 组合汇聚行为在 M1，本模块只提供通路。

> 以上均为 spec 已定义/可直接推得的约束；DE 不得在顶层新增 spec 之外的对外可见行为。任何需要顶层"加工"的需求（如复位同步、done_o 引脚化）须先走 spec 修改提案（CLAUDE.md §8）。

## 内部断言建议（非强制，DE 撰写）

> 纯连线无状态模块，无 FSM/计数器可断言；建议聚焦连通性与信号确定性（§0 适配 #7）：
- 复位释放后（PRESETn=1 稳定若干拍），关键互连线无 X（如 M1.pkt_mem_we_o、M3.mem_rd_en_o、M3.busy_o/done_o 等），用于早期发现悬空/错接。
- `M2.clk === PCLK`、`M3.clk === PCLK` 恒成立（同源时钟连通性，可用简单 assert 或形式化等价，视 DE 判断，非强制）。
- 若 DE 以 SystemVerilog 具名连接例化，可辅以断言校验读通路 `M2.rd_data === M3.mem_rd_data_i` 恒等（组合直连，无中间逻辑）。

## 已裁决歧义与未决项

**已裁决（引用 bugs.md SPEC_CHANGED 条目与 spec 修改记录版次）**——以下裁决约束的是被本模块连接的子模块行为，对 ppa_top 连线无额外影响，仅供 DE 理解通路语义：
- **BUG-003 / r6**：M2 读端口同拍组合读——M3.mem_rd_addr_o → M2.rd_addr → M2.rd_data → M3.mem_rd_data_i 为同拍组合通路，ppa_top 不得在此路径插入任何寄存/缓冲（§2.3 M2 表注第 211 行）。
- **BUG-004 / r7**：M2 读端口专供 M3，APB 无 PKT_MEM 读回通路——ppa_top 不为 APB 侧引出 SRAM 读连线（§2.3 M2 表注第 213 行、§6.3 第 400 行）。
- **BUG-P2 / r9**：`res_pkt_len_o` = Byte0[5:0]（6-bit）——M3.res_pkt_len_o[6] → M1.res_pkt_len_i[6] 位宽一致直连，无截断（§2.3 M3 表第 230 行）。

**未决**：无。原 [待仲裁-A]（§2.1 框图 vs §2.3 Top 端口表 done_o 不一致）已由 rev 仲裁并经 orch 应用 spec 修改记录 r11 落地（BUG-010 SPEC_CHANGED）：§2.1 已删除 done_o 对外引脚画法、与 §2.3 一致，ppa_top 不引出 done_o 顶层引脚。

## 验收关联（testplan 场景 ID，DE 自检不替代 DV 验证）

- **M3-01**（§11.4-必1 §10.1）：端到端链路——写包→CTRL 配置→start→轮询 done→APB 读 RES_PKT_LEN/TYPE 与写入一致；验证全链路连线正确。
- **M3-02**（§10.1 N-4 §11.4-必2）：连续两帧——两帧结果独立正确、帧间 done 有清零过程；验证 M1↔M3 控制/结果通路可复用。
- **M3-03**（§11.4-必3）：STATUS 总线通路——busy=1 时 STATUS[1:0]=2'b01、done=1 时 =2'b10；验证 M3.busy_o/done_o → M1 状态回读通路。
- **M3-04**（§6.3 §10.3 B-2，选做按必做 §0#2）：busy 写保护——busy=1 写 PKT_MEM 返回 PSLVERR=1 且 SRAM 不变；本模块提供 busy_i 通路，行为在 M1。
- **M3-05**（§8.2 §10.3 B-3，选做按必做 §0#2）：中断路径闭环——done_irq_en=1 → irq_o=1 → 写 IRQ_STA 清除 → irq_o=0；本模块提供 done_i/irq_o 通路，行为在 M1。

## 明确不做

- **APB 协议 / CSR / PSLVERR / IRQ 生成**：两段式时序、寄存器组、W1P/RW1C、地址译码、PSLVERR 判定、IRQ 置位/清除均为 M1（apb_slave_if）职责（§2.2、§4.1、§5.2、§8.2、§8.3）；ppa_top 只透传引脚、只连线。
- **SRAM 存储 / 读写时序**：8×32-bit 阵列、同步写/组合读为 M2（packet_sram）职责（§2.2、§2.3 M2 表注）；ppa_top 不含存储、不插缓冲。
- **包处理 / FSM / 错误判定 / payload 摘要**：三态 FSM、头解析、format 检查、sum/XOR 均为 M3（packet_proc_core）职责（§2.2、§7、§9）；ppa_top 不含状态机与运算。
- **busy 写保护判定、中断置位、STATUS 汇聚**：均为 M1 内部行为（§6.3 教学提示、§8.2、§5.2 STATUS）；ppa_top 仅提供连线通路，不得复制或加工这些行为。
- **任何顶层新增行为**：复位同步器、时钟处理、done_o 引脚化、APB 读 SRAM 回路等在 spec 未定义，均须先走 §8 修改流程，不在本模块私自实现（行为泄漏禁区）。
