# 覆盖率 summary 摘录（v0.2.3，M2 收官）

- 生成命令：`make -C sim regress COV=1`（17/17 PASS，UVM_ERROR/FATAL=0）→ `make -C sim cov`（urg）
- urg 报告目录：`sim/out/urgReport/`（dashboard.html / hierarchy.html / modlist.html）
- 覆盖率口径：六类 line+cond+fsm+tgl+branch+assert（spec §0 适配 7）；门槛 ≥90% 合格
- 日期：2026-07-14　工具：URG O-2018.09-SP2（本地 VM）
- 数据来源：urg dashboard.html「Total Coverage Summary」表 + hierarchy.html + modlist.html，逐类如实列出（含不达标项，交 orch/rev 判断是否影响 M2 签核）

> 说明：本次为 **M2 单元级定向回归**（17 条，均 SEED=1）。覆盖率闭环（六类综合 ≥90%）是
> **M4-02**（spec §11.5-必2）的验收目标，非 M2 完成判据（M2 判据=RTL 就绪 + feature-matrix
> 场景全 ✅ + regress 100% PASS + rev 审查，见 CLAUDE.md §4.1）。此处如实记录当前水位供参考。

## 1. Total Coverage Summary（urg 全局，含 TB/UVM 库/未激励代码）

| 类别 | 数值(%) | ≥90% |
| --- | --- | --- |
| LINE   | 29.08  | ❌ |
| COND   | 90.43  | ✅ |
| TOGGLE | 71.04  | ❌ |
| FSM    | 60.00  | ❌ |
| BRANCH | 64.06  | ❌ |
| ASSERT | 100.00 | ✅ |
| （SCORE 综合） | 73.52 | — |

注：Total 口径把整个编译域计入——UVM-1.2 库模块、M2 未激励的通路（`tb_top` 无-DUT `else`
占位分支、M3 集成路径 stub、APB 全 agent 在 M2 独立 TB 下未走等），大幅拉低 LINE/TOGGLE/BRANCH。
非设计域真实水位，仅作全局基线。

## 2. 设计+验证环境域（hierarchy 顶层 `tb_top`）

| 类别 | 数值(%) | ≥90% |
| --- | --- | --- |
| LINE   | 97.84  | ✅ |
| COND   | 90.43  | ✅ |
| TOGGLE | 71.44  | ❌ |
| FSM    | 60.00  | ❌ |
| BRANCH | 97.22  | ✅ |
| ASSERT | 100.00 | ✅ |
| （SCORE 综合） | 86.16 | — |

## 3. RTL 各模块 / bind SVA（modlist.html，设计域细分）

| 模块 | SCORE | LINE | COND | TOGGLE | FSM | BRANCH | ASSERT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| packet_proc_core（M2 DUT） | 84.85 | 100.00 | 89.47 | 59.63 | 60.00 | 100.00 | 100.00 |
| packet_sram      | 99.67 | 100.00 | —    | 98.67  | —    | 100.00 | 100.00 |
| apb_slave_if     | 89.03 | 94.44  | 91.30 | 64.80  | —    | 94.59  | 100.00 |
| tb_top           | 99.38 | 100.00 | —    | 98.75  | —    | —      | —      |
| packet_proc_core_sva（bind） | 95.45 | — | 90.91 | — | — | — | 100.00 |
| apb_slave_if_sva（bind）     | 90.76 | 91.67 | — | 80.61 | — | — | 100.00 |
| ppa_core_if（M2 行为 SRAM 接口） | 65.12 | 65.12 | — | — | — | — | — |

（"—" = 该模块无此覆盖类目，如无 FSM 的组合模块/接口。数值列对齐 NAME/SCORE/LINE/COND/TOGGLE/FSM/BRANCH/ASSERT 表头，缺项按 urg 输出跳过。）

## 4. 不达标项与判读（如实，供 orch/rev）

跨口径一致低于 90% 的类别：
- **TOGGLE（~59-71%）**：M2 定向激励（SEED=1，固定图案）未翻转大量数据位（如 payload 全字节、
  type_mask/exp_pkt_len 各取值组合）；需 M4 随机化/多 seed 补翻转。
- **FSM（60%）**：packet_proc_core 3 态 FSM 的部分转移未覆盖（如 DONE→PROCESS 连续重启、
  非法态 default 回退分支等）；部分需 M3 集成场景（连续帧 N-4、B-1 再 start）与错误注入触发。
- **packet_proc_core COND 89.47%**：临界差 0.53pt，个别条件子项未全覆盖；M4 补边界激励可达标。

设计域 LINE/BRANCH/ASSERT 已达标或接近（packet_proc_core LINE=100/BRANCH=100/ASSERT=100，
packet_sram/tb_top LINE≈100）。**结论**：功能验收（17/17 PASS + 场景全 ✅）已满足 M2；覆盖率
六类综合达标遗留至 M4-02 闭环，当前 TOGGLE/FSM 为主要缺口，非 M2 阻塞项，交 rev 里程碑签核判定。
