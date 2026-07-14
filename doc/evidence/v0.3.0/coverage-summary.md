# 覆盖率 summary 摘录（v0.3.0，M3 收官）

- 生成命令：`make -C sim regress COV=1`（22/22 PASS，UVM_ERROR/FATAL=0）→ `make -C sim cov`（urg）
- urg 报告目录：`sim/out/urgReport/`（dashboard.html / hierarchy.html / modlist.html）
- 覆盖率口径：六类 line+cond+fsm+tgl+branch+assert（spec §0 适配 7）；门槛 ≥90% 合格
- 日期：2026-07-14　工具：URG O-2018.09-SP2（本地 VM）
- 数据来源：urg dashboard.html「Total Coverage Summary」表 + hierarchy.html + modlist.html，逐类如实列出（含不达标项，交 orch/rev 判断是否影响 M3 签核）

> 说明：本次为 **M1+M2+M3 全量回归**（22 条，均 SEED=1，含新增 M3-01..05 集成场景）。覆盖率
> 闭环（六类综合 ≥90%）是 **M4-02**（spec §11.5-必2）的验收目标，非 M3 完成判据（M3 判据=
> ppa_top RTL 就绪 + feature-matrix F3-1 关联场景全 ✅ + regress 100% PASS + rev 审查，见
> CLAUDE.md §4.1）。此处如实记录当前水位供参考。

## 1. Total Coverage Summary（urg 全局，含 TB/UVM 库/未激励代码）

| 类别 | 数值(%) | ≥90% |
| --- | --- | --- |
| LINE   | 41.04 | ❌ |
| COND   | 82.61 | ❌ |
| TOGGLE | 65.54 | ❌ |
| FSM    | 60.00 | ❌ |
| BRANCH | 73.50 | ❌ |
| ASSERT | 94.32 | ✅ |
| （SCORE 综合） | 73.86 | — |

注：Total 口径把整个编译域计入——UVM-1.2 库模块、`uvm_custom_install_recording` 等未激励代码、
tb_top 下并存的 M1/M2/M3 独立单测通路与新增 ppa_top 集成通路合计。较 v0.2.3（M2 收官）LINE
41.04% vs 29.08% 有所提升（新增 ppa_top 与集成路径带来更多被激励代码），非设计域真实水位，
仅作全局基线。

## 2. 设计+验证环境域（hierarchy 顶层 `tb_top`）

| 类别 | 数值(%) | ≥90% |
| --- | --- | --- |
| LINE   | 95.88 | ✅ |
| COND   | 82.61 | ❌ |
| TOGGLE | 65.73 | ❌ |
| FSM    | 60.00 | ❌ |
| BRANCH | 93.75 | ✅ |
| ASSERT | 94.32 | ✅ |
| （SCORE 综合） | 82.05 | — |

## 3. ppa_top 集成实例域（hierarchy.html，`tb_top.u_ppa_top` 子树——本次 M3 新增的真实集成路径）

| 实例 | 说明 | SCORE | LINE | COND | TOGGLE | FSM | BRANCH | ASSERT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| u_ppa_top | 顶层集成实例（内含真实 M1+M2+M3） | 77.73 | 93.65 | 74.78 | 58.75 | 60.00 | 90.28 | 88.89 |
| ├─ u_apb（M1，集成路径实例） | apb_slave_if | 76.41 | 87.04 | 74.14 | 65.68 | — | 83.78 | 71.43 |
| ├─ u_apb_slave_if_sva（集成路径 bind） | 接口/协议 SVA | 68.82 | — | 83.33 | 73.13 | — | — | 50.00 |
| ├─ u_core（M3，集成路径实例） | packet_proc_core | 77.86 | 98.51 | 75.44 | 42.70 | 60.00 | 96.77 | 93.75 |
| ├─ u_packet_proc_core_sva（集成路径 bind） | 内部不变量断言 | 81.82 | — | — | 63.64 | — | — | 100.00 |
| ├─ u_sram（M2，集成路径实例） | packet_sram | 95.17 | 100.00 | — | 80.67 | — | 100.00 | 100.00 |
| └─ u_top_if | 顶层 irq 观测接口 | 83.33 | — | — | 83.33 | — | — | — |

## 4. RTL 各模块定义 / bind SVA（modlist.html，设计域细分，跨所有实例合并）

| 模块 | SCORE | LINE | COND | TOGGLE | FSM | BRANCH | ASSERT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ppa_top（M3 新交付） | 80.12 | — | — | 60.24 | — | — | 100.00 |
| packet_proc_core | 85.00 | 100.00 | 89.47 | 60.56 | 60.00 | 100.00 | 100.00 |
| apb_slave_if_sva | 90.76 | — | 91.67 | 80.61 | — | — | 100.00 |
| apb_slave_if | 91.09 | 96.30 | 93.48 | 68.39 | — | 97.30 | 100.00 |
| packet_proc_core_sva | 95.45 | — | — | 90.91 | — | — | 100.00 |
| apb_protocol_sva | 98.04 | — | — | 96.08 | — | — | 100.00 |
| tb_top | 99.39 | 100.00 | — | 98.78 | — | — | — |
| packet_sram | 99.67 | 100.00 | — | 98.67 | — | 100.00 | 100.00 |

（"—" = 该模块无此覆盖类目（如无 FSM 的组合/连线模块）或 urg 未产出该类目数据。ppa_top 为纯
连线模块，LINE/COND/BRANCH 无可数条目，urg 只报出 TOGGLE 与 ASSERT。）

## 5. 不达标项与判读（如实，供 orch/rev）

- **ppa_top 集成路径 ASSERT 从模块定义域 100.00% 降到实例域 88.89%（u_ppa_top）**，细看是
  `u_apb_slave_if_sva`（集成路径 bind）仅 50.00%、`u_apb`（集成路径 M1 实例）仅 71.43%——
  M1 的部分接口/协议 SVA（apb_slave_if_sva.sv）在 M3-01..05 五条集成场景的激励模式下未被
  触发，例如 M1 单测覆盖的某些边界地址/非法访问模式未出现在集成冒烟流程（写包→配置→start→
  轮询→读结果）中。**功能上不影响 M3 判据**（M3-01..05 全部 PASS，行为正确性由端到端结果比对
  确认），但提示：M1 侧断言在集成场景下的覆盖缺口需 M4 随机化/多 seed 或专项负向激励补齐。
- **TOGGLE（58-66% 区间）/ FSM（60%）/ COND（74-83%）跨口径持续偏低**，与 v0.2.3 M2 收官时
  同类缺口一致（定向激励 SEED=1 未翻转大量数据位、FSM 部分转移未覆盖）；M3 新增的连续两帧
  （M3-02）、busy 写保护（M3-04）、中断闭环（M3-05）场景对 FSM/TOGGLE 有边际提升但未根本
  改变水位，仍需 M4 随机化闭环。
- **u_core（M3 集成路径实例）TOGGLE 42.70%，明显低于 u_packet_proc_core（M3 独立单测路径
  60.85%）**：集成冒烟场景激励模式比 M2 定向单测更收敛（聚焦端到端流程正确性，非穷举数据翻转），
  预期之内，不构成 M3 阻塞项。

设计域 LINE/ASSERT 多数模块已达标或接近（packet_sram/tb_top LINE≈100，多数模块 ASSERT=100）。
**结论**：功能验收（22/22 PASS + F3-1/M3-01..05 场景全 ✅）已满足 M3；覆盖率六类综合达标遗留
至 M4-02 闭环，当前 TOGGLE/FSM/COND 为主要缺口、且发现 M1 侧断言在集成场景下的覆盖缺口，
均非 M3 阻塞项，交 rev 里程碑签核判定。
