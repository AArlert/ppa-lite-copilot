# rev 审查记录：M2 packet_proc_core design-prompt 门禁 + spec 修改提案 P1/P2 仲裁

- 日期：2026-07-10
- 审查员：rev（与 design-prompt 撰写人 arch 不同实例）
- 版本：0.2.0
- 审查对象：
  1. `doc/design-prompt/packet_proc_core.md`（arch 新交付）——门禁：spec 锚点逐条核对 + 行为泄漏检查（判据：`doc/design-prompt/README.md`、CLAUDE.md §0 arch 边界）
  2. spec 修改提案 P1（§7.3 r5 读拍数公式 pkt_len=0 矛盾）、P2（res_pkt_len_o 6-bit 位宽 vs pkt_len 8-bit 截断未定义）——仲裁：CLAUDE.md §8 流程
- 裁决基准：`doc/spec.md` r7（第 0 章适配表优先）；已核对原文章节：§0、§2.2、§2.3（M1/M2/M3 表含 r6/r7 注）、§3.1–3.4、§5.1–5.2、§6.1–6.3、§7.1–7.4（含 r5/r6 注）、§8.1–8.3、§9.1–9.3、§10.1–10.3、§11.2–11.3、修改记录 r4–r7
- 交叉核对：`doc/feature-matrix.md` F2-1..F2-4 行、`doc/testplan.md` M2-01..M2-06 行（锚点、场景关联均与 design-prompt 一致，无幽灵引用）
- 环境说明：本卡为纯文档审查与仲裁，无需仿真/覆盖率工具；全部结论基于 spec 原文逐条比对，未采信 design-prompt 转述。

---

## 一、门禁审查：design-prompt 逐条锚点核对

### 1.1 核对方法

对文件"spec 依据章节""端口定义""功能要求""边界与约束""明确不做"各节的每条主张，回到 spec 对应章节原文核实；对无直接原文的条目，判定其是否为"可直接推得"（合规）还是"新定义对外可见行为"（泄漏，打回项）。

### 1.2 核对结果（抽样明细，全部通过）

| 条目 | design-prompt 主张 | spec 原文核实 | 判定 |
| --- | --- | --- | --- |
| 端口摘要 | 19 信号方向/位宽 | §2.3 M3 表逐一比对（含 exp_pkt_len_i[6]、res_pkt_len_o[6]、mem_rd_addr_o[3]） | 一致 |
| M2/M3 编号澄清 | 「M3」为模块实例编号、项目里程碑为 M2 | §2.2 实例名列 + CLAUDE.md §4.1 M2=Lab2 | 一致（有效防混淆） |
| 复位初值 | FSM=IDLE、busy/done/rd_en=0、res_*/err/format_ok=0 | §7.1 `[*]→IDLE`、§7.4 IDLE 行、§5.2 RO 复位值 0 + §11.2 只读直透 | 可直接推得 |
| start 语义 | 单拍脉冲、门控在 M1、本模块视 start_i=1 即触发 | §2.3 M1 start_o（W1P 单拍）、§5.2 CTRL.start 接受条件、§7.2 IDLE/DONE 行 | 一致 |
| busy 时序 | start 后 1 拍 busy=1、busy/done 互斥 | §11.3 必做 3；§7.4 三行无 busy=done=1 | 一致 |
| 读时序 | 同拍组合读、无对齐拍、地址自 0 递增 | §7.3 r6 注、§2.3 M2 表 r6 注、§7.2/§11.3 第 3 周 | 一致 |
| 读拍钳位 | min(ceil(pkt_len/4),8)、pkt_len=0 矛盾列为 P1 未决 | §7.3 r5 注原文即此公式；矛盾属实（见 P1 仲裁） | 一致 + 正确前置登记 |
| 三类错误 | 触发条件、并行判定、algo_mode=0 旁路、r4 哨兵 | §9.1（r4）、§9.2、§5.2 CFG/PKT_LEN_EXP | 一致 |
| 错误输出时机 | PROCESS 期间保持清零、PROCESS→DONE 一次性写入 | §7.2 动作列（进 PROCESS 清除、进 DONE 写入）+ §9.3 | 可直接推得 |
| 零扩展比较 | exp_pkt_len 比对须全宽、并自证不改变对外结果 | §9.1 语义为值比较；pkt_len>63 ⇒ >32 范围检查必已触发——推理经复核成立 | 实现约束（非行为泄漏） |
| payload 摘要 | sum 8-bit 截断、末 word 按 pkt_len 取有效字节、空 payload sum=0/xor=0 | §3.4、§6.2、§10.1 N-1（sum=0）；xor=0 为空集异或恒等元，数学必然 | 一致/可直接推得 |
| done 电平 | DONE 保持、错误帧同样 done=1 | §8.1、§10.2 E-1..E-6 | 一致 |
| flags 不校验 | 提取但不校验、不得私设错误位 | §3.1 保留=0x00、§9.1 无对应错误位、§2.3 format_ok 定义不含 flags | 一致（正向防泄漏约束） |
| 明确不做 | CSR/APB、中断、SRAM 存储、顶层连线归属 | §2.2、§5.2、§8.2、§8.3、§6.3 | 一致 |

### 1.3 行为泄漏专项检查

- **未发现越权新定义对外可见行为。** 两处 spec 未覆盖点（P1、P2）均被正确隔离到"未决项"并显式声明"裁决前不构成对外契约"，符合 CLAUDE.md §8 修改路径。
- 唯一临时表述：约束节"裁决前 DE 以'不越窗、不卡死、第 0 拍后尽快进 DONE'为底线"——其中"第 0 拍后尽快进 DONE"无直接 spec 原文（E-1 仅约束 pkt_len=3 的 done/不卡死）。因其显式标注为待裁决临时底线、且本记录 P1 裁决（下文 r8 草案）给出了精确定义（PROCESS 恰 1 拍），**不按泄漏打回**；要求 orch 应用 r8 后同步该句为引用 r8（CLAUDE.md §8：spec 修改后受影响 design-prompt 必须同步）。

### 1.4 feature 分解查漏

F2-1..F2-4 覆盖 §7（FSM/输出约定/done）、§7.3（数据流）、§9（错误判定）、§3.4/§6.2（摘要计算），对照 §11.3 必做 1–3 + 选做 4–5（§0 #2 按必做）无遗漏；M2-01..M2-06 场景关联与 testplan 现行行一致。

### 1.5 门禁结论

**通过（有条件）**：P1/P2 裁决（本记录第二/三节）由 orch 落地 spec（加修改记录条目 + `--pin-spec`）并同步 design-prompt 两处受影响文字（§1.3 所列临时底线句、"结果输出"节 P2 待决句）后，方可派 DE。无打回项。

---

## 二、P1 仲裁：§7.3 r5 读拍数公式 pkt_len=0 矛盾

### 2.1 矛盾确认（依据 spec 原文）

- §7.3 表第 0 拍行**无条件**规定"读 Word0；提取 pkt_len/..."；r5 注自身规定"length_error 在第 0 拍解析 Byte0 后即判定"——即 pkt_len 的取值只有读完 Word0 才可知，第 0 拍读必然发生。
- r5 公式 min(ceil(pkt_len/4), 8) 在 pkt_len=0 时值为 0 拍，与上述矛盾。矛盾属实，且仅 pkt_len=0 触发（pkt_len∈{1,2,3} 时 ceil=1，不受影响）。

### 2.2 裁决

**采纳补下界方案：读拍数钳位区间修正为 [1, 8]。** 下界 1 是 spec 既有条文（§7.3 第 0 拍行 + r5 第 0 拍判定 + r6 同拍组合读）的必然推论，非新增行为；pkt_len=0 帧的行为由此完全确定：PROCESS 恰 1 拍（仅第 0 拍），随后按 §7.2 进 DONE，length_error=1（0 < 4，§9.1），res_payload_sum/xor 仍按 r5 为 UNSPECIFIED。

### 2.3 spec 修改草案（供 orch 作为 rN 落地，措辞可直接采用）

修改点：§7.3「非法包长行为」注第三条，原文

> payload 读拍数必须**钳位在 8-word 窗口内**：读拍数 = min(ceil(pkt_len/4), 8)（§6.1 窗口 0x040–0x05C 共 8 word，rd_addr 为 3-bit），禁止读越窗口或卡死（如 pkt_len=33 按公式需 9 拍/读 Word8，属越界，须钳到 8 拍以内）。

改为：

> payload 读拍数必须**钳位在 [1, 8] 拍**：读拍数 = min(max(ceil(pkt_len/4), 1), 8)。下界 1：第 0 拍读 Word0 以获取 pkt_len 本身必然发生（本节第 0 拍行、r6 同拍组合读），故 pkt_len=0 时 PROCESS 仅第 0 拍即进 DONE；上界 8：§6.1 窗口 0x040–0x05C 共 8 word、rd_addr 为 3-bit，禁止读越窗口或卡死（如 pkt_len=33 按公式需 9 拍/读 Word8，属越界，须钳到 8 拍以内）。

修改记录条目草案：`rN | 日期 | orch | P1 rev 裁决落地：§7.3 r5 读拍数公式补下界——钳位区间 [1,8]（min(max(ceil(pkt_len/4),1),8)），明确 pkt_len=0 时 PROCESS 仅第 0 拍即进 DONE`

同步项：design-prompt「SRAM 读时序」节 P1 临时底线句改为引用本条；testplan M2-02 期望列"读拍钳位 ≤8"建议补"（区间 [1,8]，pkt_len=0 恰 1 拍）"；建议 DV 在 M2-02 或新增用例中覆盖 pkt_len=0 激励。

---

## 三、P2 仲裁：res_pkt_len_o 6-bit 位宽 vs pkt_len 8-bit

### 3.1 问题确认（依据 spec 原文）

§2.3 M3 表 res_pkt_len_o 位宽 6、§5.2 RES_PKT_LEN [5:0]；§3.1 pkt_len=Byte0 为 8-bit。pkt_len>63 时 6-bit 无法表示，spec 未定义输出值。问题属实。

### 3.2 裁决

**定义为 Byte0 低 6 位截断（res_pkt_len_o = Byte0[5:0]），不并入 r5 UNSPECIFIED 集合。** 依据：

1. §3.4 对 res_pkt_len 的定义（"从 Byte0 解析得到的总包长"）**无"仅合法包"限定**；r5 的 UNSPECIFIED 为穷举列举（仅 res_payload_sum/xor），有意未包含 res_pkt_len/res_pkt_type——二者第 0 拍解析即得、无逐拍计算依赖，与 sum/xor 的 don't-care 理由不同源。
2. pkt_len∈(32, 63] 时 6-bit 可精确表示且按 §3.4 应输出解析值（E-2 的 pkt_len=33 即此域）；若仅将 >63 划为 UNSPECIFIED，会在 32<len≤63 与 >63 间造成无谓口径分裂；若整个非法域划 UNSPECIFIED 则直接抵触 §3.4 的无条件定义。
3. 截断定义确定、可验（§0 #7 要求 SVA property 逐条指回 spec，UNSPECIFIED 面越大验证越弱），实现零成本（6-bit 端口取 Byte0 即天然行为，无额外逻辑）。
4. 软件侧无误导风险：pkt_len>63 ⇒ 必 >32 ⇒ length_error=1、format_ok=0（§9.1），软件以 ERR_FLAG 为准，res_pkt_len 仅作诊断参考。

### 3.3 spec 修改草案（供 orch 作为 rN+1 落地，措辞可直接采用）

修改点 1：§3.4 表 res_pkt_len 行说明改为：

> 从 Byte0 解析得到的总包长；输出/寄存器为 6-bit，恒等于 Byte0[5:0]（pkt_len ≤ 63 时即精确包长；pkt_len > 63 时为低 6 位截断值，此时必有 length_error=1（§9.1，>63 必越界 >32），不属于 §7.3 r5 UNSPECIFIED 集合，验证侧按 Byte0[5:0] 比对）

修改点 2（同义引注）：§2.3 M3 表 res_pkt_len_o 说明列改为"解析包长（=Byte0[5:0]，见 §3.4）"；§5.2 RES_PKT_LEN 说明列改为"M3 解析出的包长（=Byte0[5:0]，见 §3.4）"。

修改记录条目草案：`rN+1 | 日期 | orch | P2 rev 裁决落地：res_pkt_len 恒 = Byte0[5:0]（§3.4 补注，§2.3/§5.2 同步引注）；pkt_len>63 时为截断值且必伴 length_error=1，不并入 r5 UNSPECIFIED，验证侧可比对`

同步项：design-prompt「结果输出」节 P2 待决句改为引用本条；testplan M2-02 可选补充 pkt_len>63 激励（如 0xFF）比对 res_pkt_len=Byte0[5:0]。

---

## 四、结论汇总（供 orch）

1. **门禁：通过（有条件）**——无行为泄漏、无锚点失配、feature 分解无遗漏；条件 = P1/P2 两条裁决按第二/三节草案落地 spec（修改记录 + `--pin-spec`）并同步 design-prompt 受影响两句后，即可派 DE。
2. **P1 裁决**：读拍数钳位区间 [1, 8]（公式补 max(…,1) 下界）；pkt_len=0 帧 PROCESS 恰 1 拍进 DONE。
3. **P2 裁决**：res_pkt_len 恒 = Byte0[5:0] 截断，可验可比对，不并入 UNSPECIFIED。

## 五、遗留风险

- **配置取样点未定义（低，非阻塞）**：design-prompt 末句提及"配置取样点"为未决项但未形成正式提案，bugs.md 亦无登记。algo_mode/type_mask/exp_pkt_len 在帧处理中途被改写时（CSR 写不受 busy 保护，§6.3 仅保护 PKT_MEM）取样行为 spec 未定义。当前 testplan M2-01..06 均无帧中改配置场景，不阻塞派单；建议 orch 责成 arch 在 DV 编写相关 checker 前登记 bugs.md 或出正式提案，避免 DE/DV 各自默认（寄存采样 vs 组合直通）产生假 mismatch。
- P1/P2 落地前若提前派 DE，pkt_len=0 与 >63 两个角点行为无契约可依，DE 自选实现将构成事实私定——故列为门禁放行条件而非风险。

## 六、复现/核实方式

- spec 锚点核实：`doc/spec.md` 修改记录 r4–r7（L6–16）、§2.2（L148）、§2.3 M3（L212）、§3.1–3.4（L256–299）、§5.2（L335）、§6.1–6.3（L366–397）、§7.1–7.4（L403–455）、§8.1（L461）、§9.1–9.3（L493–519）、§10.1–10.3（L525–552）、§11.2–11.3（L567–621）。
- 交叉一致性：`grep -n "F2-" doc/feature-matrix.md`、`grep -n "M2-0" doc/testplan.md` 与 design-prompt 功能/验收节比对。
- P1 矛盾自证：min(ceil(0/4), 8) = 0 与 §7.3 第 0 拍行、r5"第 0 拍判定"并读即得。
- P2 自证：§2.3 M3 表 res_pkt_len_o 位宽 6 vs §3.1 pkt_len 位宽 8；r5 注原文 UNSPECIFIED 仅列 res_payload_sum/xor。
