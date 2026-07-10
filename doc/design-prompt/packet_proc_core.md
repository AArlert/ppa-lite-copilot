# packet_proc_core 设计输入

- **里程碑**：M2

> 说明：spec §2.2/§2.3 中本模块标注的「M3」是**模块实例编号**，不是项目 Milestone。本仓库 Milestone 定义见 CLAUDE.md §4.1：M2=Lab2，范围即本模块 packet_proc_core。后续实例引用时以模块名为准，勿混用 M2/M3 编号。

## spec 依据章节（逐条）

- **§0 适配 #2**：选做项按必做对待——§11.3 选做验收项 4（type 合法性 + type_mask）、5（hdr_chk 校验/旁路 + sum/XOR）计入 M2 完成判据。
- **§0 适配 #7**：RTL 内部不变量断言由 DE 撰写（覆盖率含 assert 口径）。
- **§0 适配 #8**：`make lint` 干净是交付条件；告警登记 `doc/lint-waivers.md` 经 rev 复核。
- **§2.2 模块职责一览**：M3 = 3 态 FSM（IDLE→PROCESS→DONE）；读取 SRAM、解析包头、格式检查、payload 摘要、输出结果与错误标志。
- **§2.3 M3 packet_proc_core 端口表**：本模块端口的唯一定义源（19 个信号）。
- **§3.1 包结构**：Byte0=pkt_len / Byte1=pkt_type / Byte2=flags（保留 0x00）/ Byte3=hdr_chk（=B0^B1^B2）/ payload=Byte4..(pkt_len-1)，最大 28 byte。
- **§3.2 包长约束**：合法 [4,32]；越界判 length_error。
- **§3.4 算法核输出**：res_pkt_len / res_pkt_type / res_payload_sum（8-bit 截断）/ res_payload_xor 语义。
- **§5.2 寄存器表**：CFG.algo_mode / CFG.type_mask / PKT_LEN_EXP.exp_pkt_len 的语义（本模块输入的含义源）；STATUS/RES_*/ERR_FLAG 复位值 0 且由 M1 只读直透（本模块输出即读回值，复位/保持/清除责任在本模块）。
- **§6.1 地址映射**：8 word 窗口，Word N ↔ Byte 4N..4N+3。
- **§6.2 写入规则**：最后一个 word 可部分有效，有效字节范围由本模块按 pkt_len 控制。
- **§7.1/§7.2 FSM 与状态转移表**：三态转移条件与各转移动作（含 IDLE/DONE→PROCESS 清除上一帧结果、PROCESS→DONE 写入结果与错误标志）。
- **§7.3 PROCESS 内部数据流**：第 0 拍提取头部并执行三类检查；第 1..(N-1) 拍累加 sum/XOR；最后拍 = 第 ceil(pkt_len/4)-1 拍；含 r5「非法包长行为」与 r6「读延迟说明」两条注记。
- **§7.4 各状态输出约定**：busy_o / done_o / mem_rd_en_o 与状态的对应表。
- **§8.1 done 信号**：done_o 为电平信号，DONE 态保持高，IDLE/PROCESS 为低。
- **§9.1 错误标志位**：length_error / type_error / chk_error 触发条件（含 r4 的 exp_pkt_len=0 未配置哨兵）。
- **§9.2 判定优先级**：三类错误并行判定、互不中止，检查完成后统一写入并进 DONE；algo_mode=0 时 chk_error 固定 0；format_ok 相关的 STATUS.error 汇总定义。
- **§9.3 清除时机**：所有错误标志与 format_ok 在下一次合法 start 被接受时同步清零。
- **§10.1–10.3 场景矩阵**：N-1..N-4 / E-1..E-6 / B-1、B-4 的期望结果（验收锚点）。
- **§11.3 Lab2**：第 3 周设计要点（3 态 FSM、字计数器驱动 mem_rd_addr_o、第 0 拍头部提取、pkt_len 范围检查、DONE 态结果保持、busy/done 与状态严格对应）+ 必做验收项 1–3 + 选做验收项 4–5。

> 与 §0 冲突时以 §0 为准（§0 抬头）。

## 端口定义

端口以 **spec §2.3「M3 packet_proc_core」表为唯一权威**，DE 按该表逐信号实现，方向/位宽/命名不得偏离；发现需要增删改端口，必须先走 spec 修改提案（CLAUDE.md §8），不得在本文件或 RTL 私改。摘要（详表见 spec）：

- 输入：`clk` `rst_n`（低有效）`start_i` `algo_mode_i` `type_mask_i[4]` `exp_pkt_len_i[6]` `mem_rd_data_i[32]`
- 输出（SRAM 读口）：`mem_rd_en_o` `mem_rd_addr_o[3]`
- 输出（状态/结果）：`busy_o` `done_o` `res_pkt_len_o[6]` `res_pkt_type_o[8]` `res_payload_sum_o[8]` `res_payload_xor_o[8]` `format_ok_o` `length_error_o` `type_error_o` `chk_error_o`

## 功能要求（对应 feature-matrix）

- **F2-1（§7 §7.4 §8.1）**：3 态 FSM（IDLE/PROCESS/DONE）+ busy/done 输出与状态严格对应；done 电平在 DONE 态保持，再次 start 清零。→ M2-01 M2-03
- **F2-2（§7.3 §11.3）**：第 0 拍读 Word0 并同拍提取 pkt_len/pkt_type/flags/hdr_chk（依赖 M2 同拍组合读，r6）；字计数器驱动 `mem_rd_addr_o` 自 0 递增。→ M2-01
- **F2-3（§9.1–9.3）**：三类错误并行判定（length/type/chk）+ format_ok 输出 + 下一次 start 接受时同步清零。→ M2-02 M2-04 M2-05 M2-06
- **F2-4（§3.4 §7.3 §6.2）**：payload 逐字节 sum（8-bit 截断）与逐字节 XOR，最后 word 按 pkt_len 只取有效字节。→ M2-01 M2-05

## 边界与约束（每条标 spec 章节号）

**复位与初值**

- 复位（`rst_n` 低有效，§2.3）后 FSM 处于 IDLE（§7.1 `[*]→IDLE`）；`busy_o=0`、`done_o=0`、`mem_rd_en_o=0`（§7.4 IDLE 行）。
- `res_*_o`、`length_error_o/type_error_o/chk_error_o`、`format_ok_o` 复位值 0（§5.2：对应 RO 寄存器复位值均为 0，且 M1 只读直透不锁存，读回值即本模块输出）。

**FSM 与 start**

- 转移条件/动作严格按 §7.2 状态转移表；PROCESS 态不响应 `start_i`（§7.2 PROCESS 行仅按计数器转移，"其他"保持）。
- `start_i` 是 M1 已完成 enable/busy 门控后发出的单拍脉冲（§2.3 M1 表 start_o、§5.2 CTRL.start 接受条件）；本模块视每个 `start_i=1` 为合法触发，IDLE/DONE 态收到即进 PROCESS（§7.2）。
- `start_i` 有效后第 1 拍 `busy_o=1`（§11.3 必做 3），即 PROCESS 为寄存后的状态，busy/done/rd_en 按 §7.4 表与状态严格对应；`busy_o` 与 `done_o` 互斥（§7.4 各行无同时为 1）。
- IDLE/DONE→PROCESS 时清除上一帧结果与错误标志、字计数器初始化、自 addr=0 开始读（§7.2 动作列；§9.3 清除时机——ERR_FLAG/format_ok 同步清零；done 清零见 §11.3 必做 3 与 §10.3 B-1）。

**SRAM 读时序**

- PROCESS 每拍 `mem_rd_en_o=1`，IDLE/DONE 恒 0（§7.4）；`mem_rd_addr_o` 由字计数器驱动、自 0 逐拍 +1（§7.2、§11.3 第 3 周）。
- 读数据当拍有效（M2 同拍组合读，§7.3 r6 注、§2.3 M2 表 r6 注）：各拍均为"当拍发 rd_addr、当拍消费 rd_data"，无读延迟对齐拍。
- 合法包读拍数 = ceil(pkt_len/4)，最后拍为第 ceil(pkt_len/4)-1 拍，完成计算后进 DONE（§7.3）。
- 非法 pkt_len 时读拍数钳位 min(max(ceil(pkt_len/4), 1), 8)，区间 [1,8]，禁止越出 8-word 窗口、禁止卡死（§7.3 r8 注、§6.1）。pkt_len=0 时 PROCESS 仅第 0 拍（下界 1）即进 DONE，length_error=1（见"已裁决歧义"BUG-P1/r8）。

**头部解析与错误判定**

- 第 0 拍提取 Byte0–3 四字段并执行：长度范围检查 [4,32]、类型合法性检查、hdr_chk 校验（仅 algo_mode=1 时）（§7.3 第 0 拍行；字节序按 §6.1 Word0 ↔ Byte0–3）。
- `length_error`：pkt_len<4 或 >32；或 `exp_pkt_len_i≠0` 且 pkt_len≠exp_pkt_len；`exp_pkt_len_i=0` 为未配置哨兵、跳过一致性比对（§9.1 r4）。注意 pkt_len 为 8-bit、exp_pkt_len_i 为 6-bit，比对须零扩展后全宽比较，不得截断 pkt_len 后比对（截断别名不会改变 length_error 结果——高位非 0 必已触发范围越界，但实现须避免写出截断比较）。
- `type_error`：pkt_type 非 {0x01,0x02,0x04,0x08} one-hot，或对应 `type_mask_i` bit 为 0（§9.1、§5.2 CFG.type_mask：bit[n]=1 允许 pkt_type=(1<<n)）。
- `chk_error`：仅 algo_mode=1 时判 hdr_chk≠B0^B1^B2；algo_mode=0 时固定 0（§9.1、§9.2、§5.2 CFG.algo_mode）。
- 三类错误并行判定、互不中止，全部检查完成后统一随 PROCESS→DONE 写入输出（§9.2、§7.2 动作"写入结果和错误标志"）；r5 的"length_error 第 0 拍判定"约束的是内部判定时机（用于读拍钳位），输出置位时机仍按 §7.2 于 DONE 生效、PROCESS 期间输出保持清零态（§7.2 IDLE/DONE→PROCESS 已清除 + §9.3）。
- `format_ok_o` = 长度/类型/校验均通过（§2.3 端口说明、§5.2 STATUS.format_ok），即三类错误均为 0；随错误标志同时机写入/清除（§9.3 明列 format_ok）。

**结果输出**

- `res_pkt_len_o`/`res_pkt_type_o` 取自第 0 拍解析的 Byte0/Byte1（§3.4、§7.3）；DONE 态保持有效直至下一次 start（§7.2 DONE 行、§11.3 第 3 周）。
- `res_payload_sum_o`/`res_payload_xor_o`：对 payload（Byte4..pkt_len-1，共 pkt_len-4 字节）逐字节累加/异或，sum 8-bit 截断（§3.4、§7.3）；最后 word 只取 pkt_len 界定的有效字节（§6.2）；纯头部包（pkt_len=4）payload 为空，sum=0（§10.1 N-1），XOR 同理为初值 0。
- 非法 pkt_len 时 `res_payload_sum_o/res_payload_xor_o` 为 UNSPECIFIED（don't-care），RTL 不要求特定值（§7.3 r5 注）；`res_pkt_len_o` 恒 = Byte0[5:0]（6-bit 截断），pkt_len>63 时为截断值且必伴 length_error=1，不属于 UNSPECIFIED 集合，可验可比对（§3.4、见"已裁决歧义"BUG-P2/r9）。

**done**

- `done_o` 电平信号：DONE 态保持 1，IDLE/PROCESS 为 0（§8.1、§7.4）；无论有无错误，处理完成即 done=1（§10.2 E-1..E-6 均期望 done=1）。

> 以上均为 spec 已定义/可直接推得的约束（含 rev 已裁决的 P1/r8、P2/r9）；DE 不得新增 spec 之外的对外可见行为，唯一未决项（配置取样点）走 §8 提案，不在本文件或 RTL 私定。

## 内部断言建议（非强制，DE 撰写）

- FSM 状态恒在 {IDLE, PROCESS, DONE} 合法编码内，无 X/非法态。
- `busy_o` 与 `done_o` 永不同时为 1；`mem_rd_en_o=1` 仅出现在 PROCESS（busy_o=1）拍。
- PROCESS 连续拍数 ≤ 8（读拍钳位，§7.3 r5）；`mem_rd_addr_o` 自 0 起每拍 +1、不回绕越过 7。
- PROCESS 态 `start_i=1` 不改变状态（§7.2）。
- PROCESS 期间错误标志/format_ok/res_* 输出保持清零态；仅 PROCESS→DONE 一次性更新。
- `algo_mode_i=0` 的帧，`chk_error_o` 恒 0（§9.2）。
- `format_ok_o` 与三类错误输出互斥一致：format_ok_o == ~(length_error_o|type_error_o|chk_error_o)（DONE 态）。

## 已裁决歧义与未决项

**已裁决（引用 bugs.md SPEC_CHANGED 条目与 spec 修改记录版次）**

- **BUG-001 / r4**：`exp_pkt_len=0` = 未配置哨兵，跳过一致性检查；非 0 且不符才计 length_error。锚点：§5.2 PKT_LEN_EXP、§9.1 length_error。
- **BUG-002 / r5**：非法 pkt_len 时 res_payload_sum/xor 为 UNSPECIFIED（验证不比对）；读拍数钳位 min(ceil(pkt_len/4),8)；length_error 第 0 拍判定。锚点：§7.3「非法包长行为」注。
- **BUG-003 / r6**：M2 读端口为同拍组合读，本模块"第 0 拍读 Word0 并同拍提取/检查"即依赖此契约，无读延迟对齐拍。锚点：§7.3「读延迟说明」注、§2.3 M2 表注。
- **BUG-004 / r7**：APB 无 SRAM 读回通路，M2 读端口专供本模块（§6.3、§2.3 M2 表注）——对本模块无行为影响，仅说明读口独占。
- **BUG-P1 / r8**：§7.3 r5 读拍数公式在 pkt_len=0 时值为 0，与"第 0 拍必然发生"矛盾；rev 裁决补下界，钳位区间改为 [1,8]（min(max(ceil(pkt_len/4),1),8)），pkt_len=0 帧 PROCESS 仅第 0 拍即进 DONE。锚点：§7.3「非法包长行为」r8 注。
- **BUG-P2 / r9**：`res_pkt_len_o` 6-bit 位宽 vs pkt_len 8-bit，非法大包长下取值未定义；rev 裁决恒 = Byte0[5:0]（低 6 位截断），不并入 r5 UNSPECIFIED 集合，pkt_len>63 时必伴 length_error=1。锚点：§3.4 res_pkt_len 注（r9）、§2.3/§5.2 同步引注。

**未决**：无（配置取样点 [algo_mode/type_mask/exp_pkt_len 帧中改写时的取样行为] 尚无正式提案，当前 M2-01~06 场景不涉及，不阻塞派单；DV 编写相关 checker 前需另行登记 bugs.md 或提案）。

## 验收关联（testplan 场景 ID，DE 自检不替代 DV 验证）

- **M2-01**（§7 §10.1）：合法包完整处理——N-1/N-2/N-3，done 拉高、res_* 正确、FSM IDLE→PROCESS→DONE。
- **M2-02**（§7.3 §9.1 §10.2）：长度越界——E-1(len=3)/E-2(len=33)，length_error=1、format_ok=0、不卡死、读拍钳位 ≤8、sum/xor 不比对（r5）。
- **M2-03**（§7.4 §8.1 §10.3）：busy/done 时序——start 后 1 拍 busy=1、DONE 态 done 保持、再次 start 清零（B-1、N-4 连续两帧）。
- **M2-04**（§9.1 §10.2）：类型合法性 + type_mask——E-3/E-4，type_error=1。
- **M2-05**（§9.1 §10.2）：hdr_chk 校验与旁路——E-5(algo_mode=1 chk_error=1)/E-6(algo_mode=0 旁路 chk_error=0)。
- **M2-06**（§5.2 §9.1 §10.3）：PKT_LEN_EXP 一致性——B-4 exp≠0 不符报 length_error；exp=0 跳过（r4）。

## 明确不做

- **CSR 存储与 APB 协议**：寄存器组、PSLVERR、W1P/RW1C 语义、start 的 enable/busy 门控判定均为 M1（apb_slave_if）职责（§2.2、§5.2、§8.3）；本模块只消费已接受的 `start_i` 脉冲与字段广播输入。
- **中断生成**：IRQ_STA 置位/清除与 irq_o 输出为 M1 职责（§8.2）；本模块仅提供 done_o/错误输出电平。
- **SRAM 存储与写端口**：存储阵列、写通路、busy 期间写保护均为 M2/M1 职责（§2.2、§6.3 教学提示）；本模块只用读端口。
- **flags 字段检查**：§3.1 仅声明 flags 保留恒 0x00，§9.1 无对应错误位、§2.3 format_ok 定义（长度/类型/校验）不含 flags——本模块提取但不校验 flags，不得私自增设错误行为。
- **顶层连线**：时钟/复位分发与模块互连为 ppa_top 职责（§2.2）。
