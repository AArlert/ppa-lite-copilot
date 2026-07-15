# 覆盖率过滤登记表（M4-04，v0.4.0）

- 判据出处：spec §11.5-选4「覆盖率过滤合规：逐条列明过滤对象/行数/原因/结论；未登记不得过滤」（本仓库以 markdown 表替代 Excel，§0 适配 5）。
- 反造假红线：过滤只允许「真正不可达」或「设计域外」两类；凡"可用激励覆盖却图省事排除"一律禁止。本表每条均给 spec 依据；缺口分析见 `coverage-gap-analysis.md`（可用激励闭合项一律补测，不入本表）。
- 过滤配置产物：
  - 域级（设计域外）：`sim/cov_exclude/cov_domain.cfg`（VCS `-cm_hier`，`make regress COV=1 CMHIER=cov_exclude/cov_domain.cfg`）；报告亦可直接读 urg hierarchy 的 `tb_top` 顶层实例行（等价）。
  - 位级（结构不可达）：`sim/cov_exclude/coverage_exclude.el`（URG `-elfile`）。

## A. 设计域外过滤（排除出测量域）

| # | 过滤对象 | 类目 | 行数/范围 | 原因（依据） | 结论 |
| --- | --- | --- | --- | --- | --- |
| A-1 | `uvm_pkg`（UVM-1.2 类库） | line/assert 等 | 整模块（含 `uvm_reg_map::do_read`/`do_write` 内建断言 2 条） | UVM-1.2 供应商库，非本仓库设计/验证代码；spec §0 适配 7 六类口径针对"设计+验证环境域"，第三方库不在域内；DV/DE 无法也不应修改其覆盖 | 排除出测量域（设计域外，c） |
| A-2 | `uvm_custom_install_recording` | line/branch | 整模块 | VCS `-kdb`/`-debug_access` 自动生成的录制骨架模块，非人写设计/验证代码 | 排除出测量域（设计域外，c） |
| A-3 | `uvm_custom_install_verdi_recording` | line/branch/tgl | 整模块 | 同 A-2（Verdi 录制骨架） | 排除出测量域（设计域外，c） |

> A 组即"测量域 = tb_top 子树"的边界定义。上述三者为 tb_top 的兄弟顶层实例/包，`cov_domain.cfg` 以 `+tree tb_top` + `-module` 双重排除；本仓库汇报的域覆盖率取 urg hierarchy 顶层实例 `tb_top` 行，天然已排除 A 组。

## B. 结构性合法不可达过滤（design 域内、spec 强制常量/协议非法态）

| # | 过滤对象 | 类目 | 行数/范围 | 原因（spec 依据） | 结论 |
| --- | --- | --- | --- | --- | --- |
| B-1 | `apb_slave_if.PRDATA[31:8]` | toggle | rtl/apb_slave_if.sv L26 端口；PRDATA 高 24 位 | §5.2 完整寄存器表中**无任何 CSR 字段落在 bit≥8**，所有可读字段位于低字节（STATUS/CFG/IRQ_*/RES_*/ERR_FLAG 均 ≤8 位宽落在 [7:0] 或更窄）；PRDATA[31:8] 恒 0，结构性 tie-low，任何合规激励都不可能翻转 | 合法不可达，过滤（b） |
| B-2 | `apb_slave_if.PREADY` | toggle | rtl/apb_slave_if.sv L27,L63（`assign PREADY = 1'b1;`） | §4.1 APB 两段式、PREADY 恒 1、无等待态；PREADY 永不为 0，不可翻转 | 合法不可达，过滤（b） |
| B-3 | `apb_if.prdata[31:8]` | toggle | tb/apb_if.sv PRDATA 高 24 位（两实例 `apb`/`apb_top`） | 同 B-1：接口 prdata 直连 DUT PRDATA，高 24 位随之恒 0 | 合法不可达，过滤（b） |
| B-4 | `apb_if.pready` | toggle | tb/apb_if.sv pready（两实例） | 同 B-2：直连 DUT PREADY，恒 1 | 合法不可达，过滤（b） |
| B-5 | `apb_slave_if` 条件 `PSEL && PENABLE`（L69）组合 `0 1` | condition | rtl/apb_slave_if.sv L69 | PSEL=0 且 PENABLE=1 是 **APB 协议非法态**（PENABLE 只能在 PSEL 有效后的 ACCESS 拍拉高，§4.1）；协议合规激励下不可达，且 `apb_protocol_sva.a_access_preceded_by_setup` 主动禁止该态出现——若强行制造将触发协议断言失败，不允许 | 合法不可达，过滤（b） |

### B 组说明与"扣除后调整值"

- B 组均为 spec §4.1/§5.2 强制的恒定值或 APB 协议非法态，**非"可用激励覆盖却图省事排除"**：PRDATA 高位无字段源、PREADY 恒 1、PSEL=0&PENABLE=1 违反协议。
- 位级过滤配置为 URG `-elfile coverage_exclude.el`（已生成）。O-2018.09 URG 对手写 elfile 有 per-module checksum 复核门（需 DVE 载入复核后回写 checksum 方"静默应用"），故**本仓库汇报的域 TOGGLE 数值为不扣除 B 组的保守实测值 90.42%（B 组仍计为 hole 的下界，已 ≥90 合格）**。B 组仅用于登记与算术佐证，非达标所需。
- 调整算术（apb_slave_if 模块定义域，`sim/out/urgReport` 实测）：Total Bits=446、covered=**396**、未覆盖=50；该 50 项**恰好等于** B-1（PRDATA[31:8]=24 位×2 方向=48）+ B-2（PREADY=1 位×2=2）。扣除 B-1/B-2 后 apb_slave_if 翻转 = 396/(446-50) = **100.00%**（即设计侧数据翻转已完全饱和，残差纯为 spec 强制常量）。
- ASSERT：域内 89 条断言全 Success（tb_top 域 ASSERT=100.00%）；91 条总计中未覆盖 2 条即 A-1 的 uvm_pkg 内建断言，属 A 组域外过滤，不计入设计+验证域。

## C. 未过滤的已识别项（存档，保守不排除）

- 无。所有"本应可达"项（FSM 复位弧、集成域断言、数据高位、CSR 双向、PADDR 位）均已用真实激励闭合（见 gap-analysis §4），未作任何"图省事"过滤。
- 若后续回归出现"看似可达却打不到"的翻转/分支（疑似 RTL 死码），按 CLAUDE.md §4.3 登记 doc/bugs.md，**不得过滤**。本轮无此类项。
