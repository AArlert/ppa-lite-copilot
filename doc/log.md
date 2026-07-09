# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.1.7] 2026-07-09 M1 首轮场景全 PASS（DV 交付）+ 里程碑抽查 + BUG-005 关单 + BUG-006/007 处置 + 修复回归假失败

**做了什么**
- **M1 全部 6 个场景首次真实 PASS**：DV 交付 UVM 场景（`ppa_m1_01~06_test`）+ 接口/协议 SVA（`tb/sva/apb_protocol_sva.sv`、`apb_slave_if_sva.sv`，逐条标 spec 章节号）+ DUT 接入（`tb_top.sv` 例化 apb_slave_if/packet_sram，M3 结果输入用受控 `m3_stub_if`/`m3_stub_driver` 驱动，非写死 initial block）。`make regress` 7/7 PASS，orch 独立复验可复现；证据 `doc/evidence/v0.1.6/M1-0{1..6}.log` 均 `make evidence` 机械生成。testplan M1 六行全 ✅
- **rev 里程碑抽查**（`doc/evidence/v0.1.6/rev-review-M1.md`）：M1 完成三条硬条件中①②③均核实（RTL 就绪+场景全✅、regress 可复现 PASS、rev 审查记录），代码审查确认 r6/r7 裁决在 RTL 中正确落地；但**指出覆盖率未采集**（spec §0 适配 7 要求六类 ≥90%，本轮无证据）与**回归假失败风险**（脏 `sim/out` 复用致 `constraint.sdb` 损坏），**建议覆盖率证据补齐前不打 `v0.1.6` 里程碑 tag**——本轮未打 tag，M1 功能完成但里程碑包装（覆盖率+result_summary 归档）留待下一轮
- **BUG-005 关单**：DV 复验 `make compile`/`make regress` 后 `make evidence BUG=BUG-005` 机械生成证据置 CLOSED（`doc/evidence/v0.1.6/BUG-005.log`），关单人≠修复人（orch 是修复人）
- **BUG-006 处置**：DV 任务中途因 API session 限额中断，orch 核实并补完——`Lint-[NS]`（6处）/`Lint-[WMIA-L]`（4处）登记豁免 `doc/lint-waivers.md` #5/#6（0.1.0 遗留，待 rev 复核）；`Lint-[ULCO]`（`ppa_ref_model.sv` 3 处比较，共 6 子表达式）直接加 `int'(...)` 显式转换修复（非豁免），orch 复验 regress 无回归。另发现本轮新交付的 `tb/uvm/env/m3_stub_driver.sv` 有 8 处同类 `Lint-[NS]` 未登记（非 BUG-006 范围内的 0.1.0 遗留），补登记豁免 #7。状态置 FIX_READY（commit 见下一提交，本次先降 OPEN，避免自引用）
- **新登记 BUG-007（infra，orch 直接修复）**：rev 里程碑抽查发现 `make regress` 在残留 `sim/out`（如刚跑过 `make lint`）上运行会因构建数据库损坏产生假失败（4/7），`make clean` 后才 7/7。`scripts/regress.py` 加了清理步骤（回归前自动 `make -C sim clean`），orch 复验：故意先跑 `make lint` 弄脏 `out/` 后不手动 clean 直接 `make regress`，7/7 PASS，修复有效
- 全程用 `` `ifndef SYNTHESIS`` 包裹的断言写法核实：`rtl/apb_slave_if.sv`（261-311 行）、`rtl/packet_sram.sv`（54-85 行）全部断言都在综合排除块内，综合工具定义 `SYNTHESIS` 宏时会被预处理器跳过，不会进综合网表

**没做什么**
- M1 覆盖率（line+cond+fsm+tgl+branch+assert 六类 ≥90%）未采集/未归档，`v0.1.6`/`v0.1.7` 均未打里程碑 tag，等覆盖率证据后再补
- `doc/lint-waivers.md` #5/#6/#7（共 18 条）尚未经 rev 复核批准（#1~#4 已批准）
- `sim/result_summary.txt` 尚未复制入 `doc/evidence/` 目录（里程碑人工三件之一，随覆盖率一起补）
- `doc/design-prompt/apb_slave_if.md` 与 RTL 顶部注释里 BUG-004 OPEN 的陈旧措辞仍未同步成 r7 引用（低优先级，非本轮阻塞项）

**下一步**
- 派 rev 复核 lint-waivers.md #5/#6/#7
- 采集覆盖率（`make regress COV=1` + `make cov`），六类是否达标；不达标需再派 DV 补场景
- 覆盖率达标后：`sim/result_summary.txt` 复制入 `doc/evidence/v0.1.7/`，补齐里程碑人工三件，可考虑 `git tag v0.1.7`（或对应版本）标记 M1 完成
- BUG-005/006/007 复验关单后续跟进

**如何验证**
- 本地 VM：`cd sim && make regress`（7/7 PASS，独立可复现）；`make lint`（收窄范围内仅 #1~#7 已登记告警，无新增未处置发现）
- `python3 scripts/docs.py --check` 通过；`grep -n "BUG-00[5-7]" doc/bugs.md` 核对状态；`cat doc/evidence/v0.1.6/rev-review-M1.md` 看里程碑抽查记录

## [0.1.6] 2026-07-09 M1 apb_slave_if/packet_sram RTL 首次交付 + 修复 sim 构建顺序（BUG-005）+ BUG-004 裁决落地 spec（r7）

**做了什么**
- **M1 两模块 RTL 首次交付**：DE 分别交付 `rtl/apb_slave_if.sv`、`rtl/packet_sram.sv`（各含内部不变量断言），`sim/flist/rtl.f` 对应两行已启用；本地 VM 真实 `make -C sim compile` 通过（0 error/0 warning，两模块均入编译）
- **BUG-005（infra，orch 直接修复）**：`sim/Makefile` `FLISTS` 原顺序 `rtl.f` 先于 `tb.f`，导致 RTL `import ppa_reg_defs_pkg` 报"包未定义"；改为 `tb.f` 先于 `rtl.f` 后本地实测编译通过。因修复 commit 存在自引用问题（提交前不知自身 hash），bugs.md 暂留 OPEN，回填 commit 后随附属小提交置 FIX_READY（复验关单人待 DV 指派）
- **lint 门禁范围收窄（orch 直接修复）**：`make lint` 原判定对供应商 UVM-1.2 库头文件告警也计入失败，事实上永不可能通过；改为仅统计 `../rtl/` `../tb/` 范围。收窄后确认两个新 RTL 文件仅剩 13 条 `Lint-[SVA-DIU]`（DE 已登记 `doc/lint-waivers.md`，**rev 已复核批准**）；另发现 tb/ 范围 17 条 0.1.0 遗留告警（非本轮引入），登记 **BUG-006**（OPEN，待派 DV/rev 处置）
- **BUG-004 rev 裁决（2026-07-09）由 orch 落地**：DE 实现 apb_slave_if 时发现 spec §6.3"APB 读 PKT_MEM 返回真实内容"与 §2.3 端口表结构性冲突（M1 无读回端口）；rev 通读 §11.2 验收范围等章节后裁决收窄 §6.3——APB 读 PKT_MEM 窗口一律 PSLVERR=0、PRDATA=32'h0 占位值，否决新增读回端口方案（零验收收益、增复杂度）。spec r7 已落地并 `--pin-spec`；两模块 RTL **均无需返工**（DE 临时实现恰好与裁决一致）；testplan 新增 M1-06 锁定该行为
- BUG-003 承接自上一版本（0.1.5 已 SPEC_CHANGED，本版无新动作）

**没做什么**
- `doc/design-prompt/apb_slave_if.md` 中 BUG-004 OPEN 的临时处理措辞、`apb_slave_if.sv` 顶部同类注释，均未同步改引用 r7（rev 评估为纯注释性、非行为返工，留待下次触及该文件时顺带处理）
- BUG-006（tb/ 17 条遗留 lint 告警）未处置，未派单
- BUG-005 修复 commit 未回填（本提交后紧跟一个小提交回填）
- 两模块尚未派 DV：testplan M1 全部 6 行仍 🔲，无 UVM 场景/接口 SVA，未跑过 `make smoke`

**下一步**
- 按 `make next`：可派全新 DV 实例为 M1-01~06 建场景 + 接口 SVA，跑 `make smoke`/`make run` 出首个真实证据
- BUG-006（tb/ lint 遗留）需 orch 决定派 DV 修复还是批量登记豁免经 rev 复核
- design-prompt/apb_slave_if.md 与 RTL 注释的 r7 引用同步（低优先级，可并入下次 DE 触及该模块时处理）

**如何验证**
- 本地 VM：`cd sim && make compile`（0 error/0 warning）、`make lint`（仅报本仓库范围告警，当前为 rtl/ 13 条已豁免 SVA-DIU + tb/ 17 条 BUG-006 遗留，无新增未处置项）
- `python3 scripts/docs.py --check` 通过；`grep -n "r7" doc/spec.md` 可见 BUG-004 裁决条文；`grep -n "BUG-00[3-6]" doc/bugs.md` 核对状态

## [0.1.5] 2026-07-09 M1 两个 design-prompt 交付 + BUG-003 裁决落地 spec（r6）+ CLAUDE.md 固化 push 纪律

**做了什么**
- **M1 design-prompt 交付**：arch 撰写 `doc/design-prompt/apb_slave_if.md`、`packet_sram.md`，端口逐字对齐 spec §2.3、边界约束逐条标 spec 章节号；rev 门禁审查（spec 锚点核对+行为泄漏检查）——apb_slave_if.md 有条件通过（字节拆分职责措辞与 packet_sram.md 自相矛盾）、packet_sram.md 通过（读时序待裁决项已标注不得私定）；已派第二个 arch 实例落地修正，两文件 `docs-check` 通过
- **BUG-003 rev 裁决（2026-07-09）由 orch 落地**：arch 撰写 packet_sram.md 时发现 spec §2.2/§2.3"同步 SRAM"与 §7.3"第 0 拍同拍读并提取头字段"对读延迟拍数的暗示相互矛盾；rev 独立通读 spec 裁决为**同拍组合读**（rd_en=1 当拍 rd_data 有效，写端口同步写），spec r6（§2.3 M2 表补注、§7.3 第 0 拍补说明）已 `--pin-spec`；packet_sram.md 读时序约束与写后读断言同步；bugs.md BUG-003 回填裁决并置 SPEC_CHANGED
- **CLAUDE.md §6 / closeout skill 固化收尾推送纪律**：按用户要求，`/closeout` 收尾流程新增第 8 步 `git push`（标注为用户长期授权、无需每次再问，失败如实汇报不静默跳过不 force push）

**没做什么**
- 两份 design-prompt 尚未派 DE：M1 RTL 仍为零，全部场景 🔲
- packet_sram.md 遗留一处未决项（SRAM 复位初值语义未在 spec 明文），影响面小，暂未走提案，留待 M1-02 验收需要时再处理
- packet_proc_core.md / ppa_top.md（M2/M3/顶层 design-prompt）仍未撰写，等对应 M 启动时补

**下一步**
- 按 `make next`：两份 M1 design-prompt 均已过 rev 门禁，orch 可派全新 DE 实例分别实现 apb_slave_if / packet_sram RTL
- DE 交付后派全新 DV 实例建 testplan M1-01~05 场景 + 接口 SVA，跑 `make smoke`/`make run` 验证

**如何验证**
- `python3 scripts/docs.py --check` 通过；`grep -n "r6" doc/spec.md` 可见 BUG-003 裁决条文；`cat doc/design-prompt/apb_slave_if.md doc/design-prompt/packet_sram.md` 核对格式与 spec 锚点
- `grep -n "BUG-003" doc/bugs.md` 确认状态 SPEC_CHANGED

