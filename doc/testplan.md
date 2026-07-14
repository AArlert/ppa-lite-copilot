# Testplan（场景真值表）

> 状态位：✅ 通过（必须填证据+复现） / ❌ 失败 / ⚠️ 部分通过或有保留 / 🔲 未开始。
> 置 ✅ 的硬条件（docs-check 机械校验）：证据列指向 `doc/evidence/` 下真实文件；复现列含 TEST 与 SEED 的完整命令。
> 场景来源：spec 第 10 章验收矩阵 + 第 11 章各 Lab 验收项（选做按必做，见 spec 第 0 章）。新场景随开发登记，编码之前先加行。
> 接口/协议/时序契约类检查点由 tb/sva/ 下 SVA 承担（随所有场景被动生效，断言失败即场景 FAIL）；断言覆盖率并入 M4-02 口径（spec §0 适配 7）。

## M1（Lab1：apb_slave_if + packet_sram）

| ID | 里程碑 | 场景 | 检查点摘要 | spec 依据 | 状态 | 证据 | 复现 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M1-01 | M1 | APB 两段式读写时序 + CSR 默认值 | SETUP→ACCESS 时序；PREADY=1；CTRL/CFG/STATUS 等复位值与寄存器表一致 | §4.1 §5.2 §11.2-必1 | ✅ | doc/evidence/v0.1.6/M1-01.log | `make run TEST=ppa_m1_01_test SEED=1` |
| M1-02 | M1 | PKT_MEM 写入地址映射 | 写 0x040–0x05C 8 word；wr_en/wr_addr 递增/wr_data 匹配 | §6.1 §11.2-必2 | ✅ | doc/evidence/v0.1.6/M1-02.log | `make run TEST=ppa_m1_02_test SEED=1` |
| M1-03 | M1 | RES_* 只读通路 | stub 驱动 res_* 输入；APB 读 0x018/0x01C/0x020/0x024 与输入一致 | §5.2 §11.2-必3 | ✅ | doc/evidence/v0.1.6/M1-03.log | `make run TEST=ppa_m1_03_test SEED=1` |
| M1-04 | M1 | PSLVERR 统一响应 | 写 RO/W1P 寄存器、访问保留/未定义地址均 PSLVERR=1 且无副作用 | §8.3 §11.2-选4 | ✅ | doc/evidence/v0.1.6/M1-04.log | `make run TEST=ppa_m1_04_test SEED=1` |
| M1-05 | M1 | IRQ 寄存器组 | IRQ_EN 读写；IRQ_STA RW1C；irq_o=done_irq\|err_irq 组合输出 | §5.2 §8.2 §11.2-选5 | ✅ | doc/evidence/v0.1.6/M1-05.log | `make run TEST=ppa_m1_05_test SEED=1` |
| M1-06 | M1 | PKT_MEM APB 读回占位行为 | APB 读 0x040~0x05C（PKT_MEM 窗口）任意时刻：PSLVERR=0，PRDATA=32'h0（M1 无 SRAM 读回通路，占位值，不反映真实内容） | §6.3(r7) §2.3 M2 表注(r7) | ✅ | doc/evidence/v0.1.6/M1-06.log | `make run TEST=ppa_m1_06_test SEED=1` |
| M1-07 | M1 | CTRL 先 enable 后 START 两步序列，START 单拍脉冲 | 附录A"先写enable再写start"两步序列：enable=1&&busy=0 时写 start 产生单拍 start_o=1；enable=0 或 busy=1 时写 start 不产生 start_o；CTRL.start 读回恒 0 | §5.1 §5.2 附录A | ✅ | doc/evidence/v0.1.7/M1-07.log | `make run TEST=ppa_m1_07_test SEED=1` |
| M1-08 | M1 | busy=1 期间写 PKT_MEM 被保护 | busy=0 基线写入生效；busy=1 期间写同一 word：PSLVERR=1 且经 packet_sram 组合读口核实内容未变；busy 恢复 0 后写入正常生效 | §6.3 | ✅ | doc/evidence/v0.1.7/M1-08.log | `make run TEST=ppa_m1_08_test SEED=1` |
| M1-09 | M1 | packet_sram 读口行为 | APB 写入 8 word 已知数据后，经 m3_stub 驱动 rd_en/rd_addr，rd_data 同拍组合读回与写入一致（遍历地址 + 多样数据图案） | §2.3 M2 表注(r6) §7.3 | ✅ | doc/evidence/v0.1.7/M1-09.log | `make run TEST=ppa_m1_09_test SEED=1` |

## M2（Lab2：packet_proc_core，独立 TB + 行为 SRAM 模型）

| ID | 里程碑 | 场景 | 检查点摘要 | spec 依据 | 状态 | 证据 | 复现 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M2-01 | M2 | 合法包完整处理 | N-1/N-2/N-3：done 拉高、res_pkt_len/type/sum/xor 正确、FSM IDLE→PROCESS→DONE | §7 §10.1 | ✅ | doc/evidence/v0.2.3/M2-01.log | `make run TEST=ppa_m2_01_test SEED=1` |
| M2-02 | M2 | 长度越界检测 | E-1(len=3)/E-2(len=33)：length_error=1（第 0 拍判定）、format_ok=0、不卡死；sum/xor 不比对（UNSPECIFIED）；读拍钳位区间 [1,8]（r8，pkt_len=0 恰 1 拍），不越 SRAM 窗口；建议补 pkt_len=0（读拍下界）与 pkt_len>63（res_pkt_len=Byte0[5:0]，r9）激励 | §7.3 §9.1 §10.2 | ✅ | doc/evidence/v0.2.3/M2-02.log | `make run TEST=ppa_m2_02_test SEED=1` |
| M2-03 | M2 | busy/done 时序 | start 后 1 拍 busy=1；DONE 态 done 保持；再次 start 清零（B-1） | §7.4 §8.1 §10.3 | ✅ | doc/evidence/v0.2.3/M2-03.log | `make run TEST=ppa_m2_03_test SEED=1` |
| M2-04 | M2 | 类型合法性 + type_mask | E-3(0x03 非 one-hot)/E-4(mask 屏蔽)：type_error=1 | §9.1 §10.2 | ✅ | doc/evidence/v0.2.3/M2-04.log | `make run TEST=ppa_m2_04_test SEED=1` |
| M2-05 | M2 | hdr_chk 校验与旁路 | E-5(algo_mode=1 错校验 chk_error=1)/E-6(algo_mode=0 旁路 chk_error=0) | §9.1 §10.2 | ✅ | doc/evidence/v0.2.3/M2-05.log | `make run TEST=ppa_m2_05_test SEED=1` |
| M2-06 | M2 | PKT_LEN_EXP 一致性 | B-4：exp≠0 且与 pkt_len 不符 → length_error=1；exp=0（未配置/复位默认）→ 跳过比对不报错（r4） | §5.2 §9.1 §10.3 | ✅ | doc/evidence/v0.2.3/M2-06.log | `make run TEST=ppa_m2_06_test SEED=1` |
| M2-07 | M2 | 配置帧内稳定契约 | 配置（algo_mode/type_mask/exp_pkt_len）在 start 前置好、整个 busy 期间不改写 → 判定结果符合帧起始时的配置预期（单元级正向验证：type_mask/exp/algo 活值确参与第 0 拍判定，r10 组合取活值）；负向观测"busy 期间写 CFG/PKT_LEN_EXP 不报 PSLVERR"（与 §6.3 PKT_MEM 写保护对照，二者不同等约束，BUG-008/r10）需 APB 通路，属集成层，M3 集成 test 覆盖（core 单元级无 PSLVERR 端口） | §5.2 §6.3 §7.2 §7.3(r10) | ✅ | doc/evidence/v0.2.3/M2-07.log | `make run TEST=ppa_m2_07_test SEED=1` |

## M3（Lab3：ppa_top 集成）

| ID | 里程碑 | 场景 | 检查点摘要 | spec 依据 | 状态 | 证据 | 复现 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M3-01 | M3 | 端到端链路 | 写包→CTRL 配置→start→轮询 done→读 RES_* 与写入一致 | §11.4-必1 | 🔲 | - | - |
| M3-02 | M3 | 连续两帧 | N-4：两帧结果独立正确；帧间 done 有清零过程 | §10.1 §11.4-必2 | 🔲 | - | - |
| M3-03 | M3 | STATUS 总线通路 | busy 期间 STATUS[1:0]=01；done 期间 =10 | §11.4-必3 | 🔲 | - | - |
| M3-04 | M3 | busy 写保护 | B-2：busy=1 写 PKT_MEM → PSLVERR=1 且 SRAM 不变 | §6.3 §10.3 | 🔲 | - | - |
| M3-05 | M3 | 中断路径闭环 | B-3：done_irq_en=1→irq_o=1→写 1 清→irq_o=0 | §8.2 §10.3 | 🔲 | - | - |

## M4（Lab4：回归与覆盖率闭环）

| ID | 里程碑 | 场景 | 检查点摘要 | spec 依据 | 状态 | 证据 | 复现 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M4-01 | M4 | 一键回归 100% | make regress 全 PASS；M1–M3 每个必做场景 ≥1 条 testcase | §11.5-必1 | 🔲 | - | - |
| M4-02 | M4 | 六类覆盖率达标 | line+cond+fsm+tgl+branch+assert 综合 ≥90%（≥95% 优良，100% 优秀），urg 报告 | §11.5-必2 §0-适配7 | 🔲 | - | - |
| M4-03 | M4 | testplan 文档完整 | 本表字段完整、与回归列表一一对应 | §11.5-必3 | 🔲 | - | - |
| M4-04 | M4 | 覆盖率过滤登记合规 | 过滤项逐条登记对象/行数/原因/结论（markdown 表） | §11.5-选4 | 🔲 | - | - |
| M4-05 | M4 | 选做功能回归 | M1-04/05、M2-04/05/06、M3-04/05 全部纳入回归并 PASS | §11.5-选5 | 🔲 | - | - |
