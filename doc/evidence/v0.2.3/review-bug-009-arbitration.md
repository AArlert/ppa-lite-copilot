# BUG-009 仲裁记录：packet_proc_core 包头字节内端序

- 版本：0.2.3（version.json 现值）
- 仲裁人：rev（全新实例，未参与 BUG-009 相关 DE/DV/arch 工作）
- 日期：2026-07-14
- 争议：RTL 按小端抽取 32-bit word 内的四字节头（pkt_len=bit[7:0]…hdr_chk=bit[31:24]）；
  DV 参考模型按 spec 附录 A/B 数值示例按大端搭建（pkt_len=bit[31:24]…hdr_chk=bit[7:0]），
  M2-01~M2-07 全 FAIL。
- **裁决：(A) 附录 A/B 为准（大端）→ 判 RTL bug，归 DE。** 依据见下。

---

## 1. 独立验算：附录 A/B 三个数值示例只能按大端自洽解读吗？

我未采信 BUG-009.md 的算式，独立重新核对。**先纠正 BUG-009.md 一处不严谨之处**，再给出真正的判据。

### 1.1 校验和自洽性本身不能区分端序（纠正 BUG-009.md）

BUG-009.md（L27-29）称 `0x08^0x01^0x00=0x09` 的自洽"仅在大端时成立、自洽要求大端"。
这一推理不成立：hdr_chk 关系 `hdr_chk = Byte0 ^ Byte1 ^ Byte2`，等价于四个头字节整体
XOR = 0。四字节整体 XOR 对字节置换对称，故无论大端还是小端，该关系都成立。逐例验算：

附录 A `32'h08_01_00_09`：
- 大端假设：Byte0..3 = 0x08/0x01/0x00/0x09，关系 0x09 == 0x08^0x01^0x00 = 0x09 ✔
- 小端假设：Byte0..3 = 0x09/0x00/0x01/0x08，关系 0x08 == 0x09^0x00^0x01 = 0x08 ✔

两种假设下校验和**都自洽**（因为 0x08^0x01^0x00^0x09 = 0）。所以"XOR 算式自洽"不是判据。

### 1.2 真正的判据：显式字段值标注 + 隔离性结果

大端由以下两类证据钉死，与校验和无关：

**(a) 附录注释里显式写死的字段"数值"只在大端下成立：**

| 示例 | 字面量 | 注释断言 | 大端读数 | 小端读数 | 结论 |
| --- | --- | --- | --- | --- | --- |
| 附录A(826) | `32'h08_01_00_09` | pkt_len=**8**, pkt_type=**0x01**, flags=**0** | len=8,type=1,flags=0 ✔ | len=9,type=0,flags=1 ✘ | 只大端符 |
| B.1(866) | `32'h0C_01_00_0D` | pkt_len=**12(0x0C)** | len=0x0C=12 ✔ | len=0x0D=13 ✘ | 只大端符 |
| B.2(874) | `32'h04_03_00_07` | pkt_type=**0x03** | type=bit[23:16]=0x03 ✔ | type=bit[15:8]=0x00 ✘ | 只大端符 |
| B.3(882) | `32'h04_01_00_FF` | hdr_chk=**0xFF** | chk=bit[7:0]=0xFF ✔ | chk=bit[31:24]=0x04 ✘ | 只大端符 |

**(b) 示例的"隔离性结果"（比字面标注更硬，因为它由 outcome 而非注释固定）：**

- 附录 A 步骤6：`APB_WRITE(0x014, 8)` 设 exp_pkt_len=8，结果注 `err_flag = 0（无错误）`、
  `res_pkt_len = 8`、`res_pkt_type = 0x01`。
  - 大端：pkt_len=8=exp → 无 length_error；pkt_type=0x01 合法；flags=0；chk=0x09=8^1^0 → err_flag=0，res_pkt_len=8，res_pkt_type=0x01。**全部吻合 ✔**
  - 小端：pkt_len=9≠exp=8 → length_error=1 → err_flag≠0，且 res_pkt_len=9。**与注释矛盾 ✘**
- B.3 意在演示"**仅** chk_error"（标题=hdr_chk 校验失败）：
  - 大端：pkt_len=0x04(合法)、pkt_type=0x01(合法)、flags=0、hdr_chk=0xFF≠(0x04^0x01^0x00=0x05) →
    **只** chk_error=1 ✔，正是示例意图。
  - 小端：pkt_len=bit[7:0]=0xFF=255>32 → length_error；pkt_type=0x00 → type_error；chk 也错。
    三错齐发，破坏"隔离演示 chk_error"的意图 ✘。

结论：四个示例的字段标注一致指向大端，且附录 A(err_flag=0/res_pkt_len=8) 与 B.3(隔离 chk_error)
两处由 **结果** 而非注释锁定，无法用"注释笔误"搪塞。**附录 A/B 唯一自洽解读 = 大端**
（Byte0/pkt_len→bit[31:24]，Byte3/hdr_chk→bit[7:0]）。

## 2. §3.1/§6.1 正文是否真对 bit 位留白？（重读原文，不采信详情页转述）

- §3.1（spec.md:259-277）：字段表列 pkt_len=Byte0 … hdr_chk=Byte3，只规定**字节偏移顺序**，
  未提任一字节落在 32-bit word 的哪几 bit。示意图同样只画字节偏移 0..N-1。
- §6.1（spec.md:377）：Word0 = "Byte 0–3（头部：pkt_len/pkt_type/flags/hdr_chk）"，只给
  word↔byte 归属，未给 word 内 bit 映射。
- §3.3(289)/§6.2(390)："硬件负责将 word 拆分为字节存入 SRAM"——只说"拆"，未定端序。

**核实属实：§3.1/§6.1 正文对"字节在 word 内的 bit 位"确实留白**，bit 映射仅由附录 A/B
数值示例隐含。BUG-009.md 的这一转述准确。

但"正文留白"≠"spec 双向歧义"。spec 单一事实源包含附录；附录以自洽示例唯一钉定大端，
且**无任何 spec 文字支持小端**。RTL 选小端没有任何 spec 锚点（CLAUDE.md §8：RTL 对行为的
主张必须引用 spec 章节，小端引不出）。故这是"RTL 与 spec 附录冲突"，不是 spec 自相矛盾。

## 3. M1（已 ✅ 9 场景）是否在字节级触碰端序？→ 无回归风险

- `rtl/packet_sram.sv`：写 `mem[wr_addr] <= wr_data`（整字存）、读 `rd_data = mem[rd_addr]`
  （整字读），**全程按 32-bit 整字搬运，从不拆字节、从不做 bit 映射**。
- `rtl/apb_slave_if.sv`：无字节拆分/端序逻辑（grep 无 byte/[31:24] 相关拆分）。
- 字节→bit 的解释**唯一发生在 M3**（packet_proc_core L75-78 头字段、L141-144 payload）。

结论：M1 写通路/SRAM 从未做字节级端序校验，**修改 M3 的 bit 切片对 M1 零回归风险**。
BUG-009.md 关于"M1 未在字节级校验端序"的判断属实。

## 4. 复现证据自洽性核对

- `sim/out/ppa_m2_01_test_1.log`：13 条 [M2_CHK] UVM_ERROR，例 N-3 `len=32 type=0x04 chk=0x24`
  （大端 Word0=0x20_04_00_24），DUT 实测 res_pkt_len=0x24(=小端 bit[7:0])、res_pkt_type=0x00
  (=小端 bit[15:8]=flags)、length_error 实得1、type_error 实得1。**症状与"RTL 小端"完全一致**。
- DV 参考模型 `tb/uvm/core_agent/ppa_core_seq_item.sv`：`get_word()`(L39-40) 注明"按附录 A
  大端约定组装 [31:24]=Byte(4w)"，`predict()` 引用 §3.4/§9.1/r9/r4 推导期望值，**从 spec 推导、
  未照抄 RTL**，符合 DV 纪律。checker 不需返工。

## 5. 裁决

**方向 (A)：附录 A/B（大端）为准 → BUG-009 定性为 RTL bug。**

- 头字段抽取应改为：`pkt_len=[31:24]`、`pkt_type=[23:16]`、`flags=[15:8]`、`hdr_chk=[7:0]`
  （`rtl/packet_proc_core.sv` L75-78）。
- payload 逐字节应改为：`byte0=[31:24]`、`byte1=[23:16]`、`byte2=[15:8]`、`byte3=[7:0]`
  （L141-144）；使 sum/xor 按有效字节序（Byte(4w+0)..(4w+3)）累加。
- 归属：DE（新实例），输入 = BUG-009 条目 + spec §3.1/§6.1/§3.4 + 附录 A/B + 端口定义；
  不含本仲裁的推理链。修复后回填根因+commit → FIX_READY，DV(≠修复人)用
  `make run TEST=ppa_m2_01_test SEED=1` + M2 回归复验关单。
- 状态：本仲裁不改状态位（保持 OPEN），待 orch 派单后由修复/复验流程推进。

**为何不取方向 (B)（SPEC_CHANGED/小端）**：小端无任何 spec 文字支撑；采用小端需反写全部 4 个
附录示例的字面量**并翻转其隔离性结果**（附录 A err_flag 将非0、B.3 将三错齐发），改动面远大于
改 RTL，且会让 `APB_WRITE(0x040, 32'h08_01_00_09)` 这种"从左到右按 Byte0..3 书写"的直觉写法
失效（pkt_len 要写进 LSB），违背 spec 教学可读性意图。附录既已唯一自洽指向大端，无 spec 修改必要。

## 6. 附带发现（不越权，交 arch/orch 处置，非本裁决前置条件）

1. **[建议 arch 走 §8 补正文澄清注，非行为变更]** §3.1/§6.1 正文对"字节在 32-bit word 内的
   bit 位"留白，端序只靠附录隐含，是文档缺口。建议 arch 在 §3.1 字段表下或 §6.1 补一句显式
   映射："Byte0→bit[31:24] … Byte3→bit[7:0]（大端；见附录 A/B）"。此为把附录已隐含内容
   显式化的**澄清**（不改变已定行为），仍需登记修改记录 + pin。不阻塞 BUG-009 的 RTL 修复。
2. **[spec 笔误，交 arch]** 附录 B.3（spec.md:881）注释 "实际应为 0x01^0x01^0x00 = 0x00"
   算式有误：该包 pkt_len=0x04、pkt_type=0x01、flags=0x00，正确 hdr_chk 应为
   0x04^0x01^0x00 = **0x05**，非注释所写 "0x01^0x01^0x00=0x00"。不影响端序裁决（该例演示
   hdr_chk=0xFF≠正确值即触 chk_error，结论仍成立），但注释算式需 arch 订正。

---
*依据文件：doc/spec.md §3.1(259)/§3.3(287)/§3.4(293)/§6.1(371)/§6.2(388)/附录A(821)/附录B(859)；*
*rtl/packet_proc_core.sv L75-78,L141-144；rtl/packet_sram.sv L38/45；*
*tb/uvm/core_agent/ppa_core_seq_item.sv L39-40,L62-103；sim/out/ppa_m2_01_test_1.log*
