# 覆盖率 summary 摘录（v0.4.0，M4-02/M4-04 覆盖率闭环）

- 生成命令：`make -C sim regress COV=1`（32/32 PASS，UVM_ERROR/FATAL=0）→ `make -C sim covreset` → `make -C sim cov`（urg 合并主回归库 + 复位测试独立库）
- urg 报告目录：`sim/out/urgReport/`（dashboard/hierarchy/modlist/modinfo/asserts）
- 覆盖率口径：六类 line+cond+fsm+tgl+branch+assert（spec §0 适配 7）；门槛 ≥90% 合格 / ≥95% 优良 / 100% 优秀
- 日期：2026-07-16　工具：VCS-MX + URG O-2018.09-SP2（本地 VM）
- 数据来源：urg text 报告逐类如实抄录（真实机测，非手写编造）
- 测量域：设计+验证环境域 = urg hierarchy 顶层实例 `tb_top` 子树；UVM-1.2 库骨架（uvm_pkg/uvm_custom_install_*）域外（M4-04，`cov_domain.cfg`）

## 1. 设计+验证环境域（hierarchy 顶层 `tb_top`）—— M4-02 验收口径

| 类别 | 基线(v0.3.0) | 闭环(v0.4.0) | ≥90 | 等级 |
| --- | --- | --- | --- | --- |
| LINE   | 95.88 | 100.00 | ✅ | 优秀 |
| COND   | 82.61 | 94.35 | ✅ | 优良 |
| TOGGLE | 65.73 | 90.42 | ✅ | 合格 |
| FSM    | 60.00 | 100.00 | ✅ | 优秀 |
| BRANCH | 93.75 | 100.00 | ✅ | 优秀 |
| ASSERT | 94.32 | 100.00 | ✅ | 优秀 |
| **SCORE（六类综合）** | **82.05** | **97.46** | ✅ | **优良** |

**结论**：六类综合 SCORE 97.46% ≥ 90（合格）且 ≥ 95（优良），六类全部 ≥90 —— 满足 spec §11.5-必2 / §0 适配 7 的 M4-02 判据。

## 2. Total Coverage Summary（urg 全域，含 UVM 库，仅作对照）

| 类别 | 数值(%) |
| --- | --- |
| LINE | 42.63 | COND 94.35 | TOGGLE 90.16 | FSM 100.00 | BRANCH 78.00 | ASSERT 100.00 | SCORE 86.45 |

> 全域 LINE/BRANCH 被 UVM-1.2 库与 VCS 自动录制骨架（uvm_custom_install_*）大量未激励代码拉低，非设计域真实水位；设计+验证域以 §1 tb_top 行为准（M4-04 域级过滤）。

## 3. 关键实例（hierarchy.html / urgReport）

| 实例 | SCORE | LINE | COND | TOGGLE | FSM | BRANCH | ASSERT |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tb_top（设计+验证域） | 97.46 | 100.00 | 94.35 | 90.42 | 100.00 | 100.00 | 100.00 |
| u_ppa_top（集成实例） | 96.88 | 100.00 | 90.43 | 90.87 | 100.00 | 100.00 | 100.00 |
| ├ u_apb（集成 M1） | 95.63 | 100.00 | 91.38 | 86.76 | — | 100.00 | 100.00 |
| ├ u_core（集成 M3） | 97.59 | 100.00 | 89.47 | 96.09 | 100.00 | 100.00 | 100.00 |
| └ u_sram（集成 M2） | 100.00 | 100.00 | — | 100.00 | — | 100.00 | 100.00 |
| u_apb_slave_if（M1 单元） | 96.55 | 100.00 | 96.55 | 86.22 | — | 100.00 | 100.00 |
| u_packet_proc_core（M2 单元） | 99.35 | 100.00 | 100.00 | 96.09 | 100.00 | 100.00 | 100.00 |

## 4. 模块定义域（modlist，设计+SVA 模块，跨实例合并）

| 模块 | LINE | COND | TOGGLE | FSM | BRANCH | ASSERT |
| --- | --- | --- | --- | --- | --- | --- |
| packet_proc_core | 100.00 | 100.00 | 95.93 | 100.00 | 100.00 | 100.00 |
| apb_slave_if | 100.00 | 97.83 | 88.79 | — | 100.00 | 100.00 |
| packet_sram | 100.00 | — | 100.00 | — | 100.00 | 100.00 |
| ppa_top | — | — | 87.80 | — | — | 100.00 |
| apb_protocol_sva | — | — | 96.08 | — | — | 100.00 |
| apb_slave_if_sva | — | 91.67 | 83.67 | — | — | 100.00 |
| packet_proc_core_sva | — | — | 100.00 | — | — | 100.00 |

> apb_slave_if 模块 TOGGLE 88.79%（covered 396/446）：唯一未翻转的 50 位翻转恰为 PRDATA[31:8]+PREADY 两组 spec 强制常量（§5.2/§4.1），扣除后 = 100%，见 M4-04 登记表 B 组。ppa_top TOGGLE 87.80% 残差同为高位 PRDATA 连线。

## 5. FSM 复位弧覆盖说明（M4-02d/e）

- packet_proc_core 两实例 FSM 均 5/5 转移（含复位弧 PROCESS→IDLE / DONE→IDLE），tb_top 域 FSM=100.00。
- 复位弧由 `ppa_m2_09_reset_test`（单元）/`ppa_m3_07_reset_test`（集成）运行中注入异步复位覆盖；因 VCS 共享 -cm_dir 累积对 async-reset FSM 弧存在丢弃，复位测试另出独立 vdb（`make covreset`），报告期 urg 多路 `-dir` 合并取并集（见 gap-analysis §2.1）。
- ASSERT：域内 89/89 全 Success；91 总计中 2 条未覆盖为 uvm_pkg 库内建断言（域外）。
