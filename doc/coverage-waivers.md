# 覆盖率过滤登记表

> 判据出处：spec.md §11.5（Lab4=M4）必做验收 #2 五类覆盖率等级验收 ≥90%，选做 #4「覆盖率过滤登记表，逐条列过滤对象/行数/原因/结论，未登记不得过滤」；spec §0 适配表 #7（六类 line+cond+fsm+tgl+branch+assert ≥90% 合格）为项目级口径定义，实际验收/过滤动作挂在 M4。
> 登记人 = DV；**复核人 = rev**（未复核的豁免/顺延不算数）。结论分三类：**豁免**（结构性/契约性零翻转，不计入达标分母，效力于 M4 覆盖率闭环终审）、**顺延M2M3**（真实缺口，非本 M 必闭，随后续里程碑联调自然收窄，M4 强制回访——若届时仍未覆盖且无结构性理由，不得再豁免，须补场景闭合）、**待修**（应在本 M 内补场景闭合）。
> 首批登记来源：`doc/evidence/v0.1.7/coverage-summary-M1.md`（复测节第 103-136 行 toggle 缺口逐项根因）+ `doc/evidence/v0.1.9/rev-review-toggle-lint7.md`（rev 裁决记录）。

| # | 过滤对象（模块/信号[位]） | 位数 | 原因 | 结论 | 复核（rev/日期） |
| --- | --- | --- | --- | --- | --- |
| 1 | `apb_slave_if.sv` `PRDATA[31:8]` | 24 bit | spec §5.2 全部寄存器字段位宽 ≤8 bit（RES_PKT_TYPE/SUM/XOR 的 `[7:0]` 为最宽字段），且 §5.2 明文「未列出的位域读回为 0」，PRDATA 高 24 位在 M1 寄存器表下永远输出 0，非激励可改 | 豁免 | rev 2026-07-10 批准 |
| 2 | `apb_slave_if.sv` `PREADY` | 1 bit | spec §4.1「PREADY 固定为 1」，恒定值，按 spec 契约本就不允许翻转 | 豁免 | rev 2026-07-10 批准 |
| 3 | `apb_slave_if.sv`/`packet_sram.sv` `rst`/`rst_n` | 2 bit | 复位仅在仿真起始释放一次，本轮各测试均为独立 `simv` 单次运行，无"运行中二次复位"场景，`1→0` 方向天然不出现 | 豁免 | rev 2026-07-10 批准 |
| 4 | `apb_slave_if.sv` CSR 写通路：`cfg_algo_mode`/`cfg_type_mask[3:0]`/`algo_mode_o`/`type_mask_o[3:0]`/`pkt_len_exp[5:0]`/`exp_pkt_len_o[5:0]` | 约 25 bit | M1-01~M1-09 全部场景均未对 `CFG`（0x004）、`PKT_LEN_EXP`（0x014）寄存器做过 APB 写入（M1-01 仅复位后读一次默认值），非 spec §11.2 M1 必做验收范围（M1 #1 仅要求读默认值），随 M2/M3 配置流程联调自然覆盖 | 顺延M2M3 | rev 2026-07-10 批准（M4 回访） |
| 5 | `apb_slave_if.sv` `ctrl_enable`/`irq_en_done`/`irq_en_err` 1→0 回落沿 | 约 3 bit | M1-07 两个负例均为"enable 本就是 0"，未构造"先 1 后 0"回落沿；IRQ_EN 同理未曾写回 0；非 M1 必做验收范围 | 顺延M2M3 | rev 2026-07-10 批准（M4 回访） |
| 6 | M3 stub 结果字段：`res_pkt_len_i`/`res_pkt_type_i`/`res_payload_sum_i`/`res_payload_xor_i`/`type_error_i`/`chk_error_i` 多数位 | 约 20+ bit | M1-03/M1-05 各自仅 `set_result` 一次固定值，未在同一测试内把已置 1 的结果位写回 0；`type_error_i`/`chk_error_i` 全程未被 stub 置过 1（M1-05 仅用 `length_error` 触发 err 分支）。理论上不依赖真实 M3 到位、可通过扩展 `m3_stub_driver.set_result` 调用组合补齐，留待后续场景或 M2/M3 联调后用真实结果值多样性自然收窄 | 顺延M2M3 | rev 2026-07-10 批准（M4 回访） |

## M4 回访清单（强制）

M4 覆盖率闭环时逐条核对本表「顺延M2M3」结论（#4/#5/#6，约 45+ bit）是否已随 M2/M3 联调自然覆盖：
- 已覆盖 → 结论改「已闭合」，注明闭合场景 ID。
- 仍未覆盖且无新的结构性理由 → 不得再豁免，须补场景闭合，方可判定 spec §11.5 五类覆盖率 ≥90% 达标。

「豁免」结论（#1~#3，共 26 bit）不计入 M4 达标分母，除非设计变更（如新增更宽寄存器字段、引入运行中复位场景）改变其结构性前提。
