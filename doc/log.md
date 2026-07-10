# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.2.0] 2026-07-10 rev 裁决 M1 toggle 覆盖率口径 + 豁免#7 追加复核 → M1 收官，进入 M2

**做了什么**
- 派新 rev 实例裁决两项悬而未决的 M1 收尾事项（`doc/evidence/v0.1.9/rev-review-toggle-lint7.md`）：
  1. **toggle 覆盖率口径**：裁定 spec §11.5（M4）才是「五类覆盖率 ≥90% 验收」+「过滤登记表」的判据挂载点，spec §0 #7 只是项目级口径定义；spec §11.2（M1）验收项仅三条功能项，无覆盖率门槛；CLAUDE.md §4.1 三条硬条件也不含覆盖率。据此 toggle 73.32% **不阻塞 M1 tag**。结构性零翻转 26 bit（PRDATA[31:8]/PREADY/rst 单次复位）判定**豁免**，真实缺口 45+ bit（CFG/PKT_LEN_EXP 写通路、CTRL/IRQ_EN 回落沿、M3 stub 结果多样性）判定**顺延 M2/M3**（M4 强制回访，届时无结构性理由不得再豁免）。
  2. **lint 豁免 #7 追加 4 处**（`m3_stub_driver.sv:71,74,77,87`，`read_sram`/`watch_start_pulse` 内 `Lint-[NS]`）：逐行核对根因与首批 8 处一致，批准豁免，#7 扩为全 12 处。
- orch 落地：新建 `doc/coverage-waivers.md`（6 条登记：3 条豁免共 26 bit + 3 组顺延 M2M3 共 45+ bit，附 M4 强制回访清单）；`doc/lint-waivers.md` #7 行结论栏改「豁免（全 12 处）」、复核栏补 rev 2026-07-10 批准记录。
- `python3 scripts/docs.py --check` 通过 → **M1 三条硬条件确认齐全**（RTL 交付 6/6+feature-matrix 场景 9/9 ✅、`make regress` 10/10 PASS 证据归档、rev 审查记录×3 存 doc/evidence/）→ `make bump-minor` 进入 M2，随后打 tag `v0.2.0`。

**没做什么**
- 未新增/修改任何 RTL/TB 代码，未重跑仿真（沿用 v0.1.7 证据与复测数据，未过期）。
- `doc/coverage-waivers.md` 中「顺延M2M3」的 45+ bit 缺口未实际闭合，只是登记跟踪，留待 M2/M3 联调或后续场景。
- M2（packet_proc_core）的 design-prompt 尚未起草，本轮只完成 M1 收官，未派发 M2 设计任务。

**下一步**
- 派 arch 出 M2 design-prompt（packet_proc_core，spec 对应 Lab2 章节），过 rev 门禁（行为泄漏检查）后派 DE。
- M2 场景落地前 DV 先在 testplan.md 登记 M2-01~M2-06 场景行细节（目前是占位 🔲）。
- doc/outlook.html 按文件头 SYNC 标记同步本次里程碑/版本变化（version 0.1.9→0.2.0，milestone M1→M2）。

**如何验证**
- `cat doc/evidence/v0.1.9/rev-review-toggle-lint7.md` 看裁决全文；`cat doc/coverage-waivers.md` 核对 6 条登记；`grep -n "^| 7" doc/lint-waivers.md` 确认 #7 已更新为全 12 处。
- `cat version.json`（应为 0.2.0/M2）；`git tag -l v0.2.0`；`python3 scripts/docs.py --check` 通过。

## [0.1.9] 2026-07-09 新增 doc/outlook.html 项目一览（Agent 可低 token 维护的可视化快照）

**做了什么**
- 新建 `doc/outlook.html`（用户指定需求，orch 汇总现有事实直接绘制）：三章可视化快照——Ⅰ harness 工作流（make 闭环、四角色派单与实例隔离、缺陷闭环、滚动归档表）、Ⅱ RTL 设计（系统框图带真实信号名、包格式、CSR 表、模块M3 FSM、交付现状；显式澄清模块编号与里程碑编号是两套体系）、Ⅲ UVM 验证（组件树、config_db/virtual interface 双世界桥、base test 模板方法与回归清单）。纯 HTML/CSS 盒子图（无 SVG 坐标），自适应亮暗主题，自包含无外部依赖
- 文件开头放置渲染后不可见的 Agent 维护说明：grep `id="` 取骨架、grep `SYNC:` 列出五个易变数据点（version/milestone/coverage/bugs/tests）后局部 Edit，禁止通读全文件

**没做什么**
- 本轮无 RTL/TB/脚本改动；toggle 覆盖率口径裁决、豁免 #7 追加 4 处复核、M1 tag 仍悬（见 0.1.8 块）
- outlook.html 未纳入 docs-check 守卫（快照文档允许滞后，SYNC 标记靠约定维护）

**下一步**
- 同 0.1.8 块：派 rev 裁决 toggle 口径 + 复核 #7 追加项 → 打 M1 tag → arch 出 M2（packet_proc_core）design-prompt
- 里程碑推进/结构变化时按文件头维护说明同步 outlook.html 的 SYNC 数据点

**如何验证**
- 浏览器打开 `doc/outlook.html`（亮/暗主题各看一遍）；`grep -c 'SYNC:' doc/outlook.html`（应 ≥6 处标记）
- `python3 scripts/docs.py --check` 通过

## [0.1.8] 2026-07-09 bugs/lint-waivers 滚动归档机制 + 豁免 #5-7 复核批准 + BUG-006/007 关单 + M1 覆盖率收窄（仅剩 toggle 未达标）

**做了什么**
- **bugs.md / lint-waivers.md 滚动归档机制**（orch 直改 scripts/，同 BUG-007 先例）：`make docs-archive` 现在会把 bugs.md 终态行（CLOSED/TB_BUG/SPEC_CHANGED/WONTFIX，保留最新 2 条）搬入 `doc/bugs-archive.md`、把 lint-waivers.md 已批准豁免行（保留最新 2 条）搬入 `doc/lint-waivers-archive.md`；活跃缺陷/待复核豁免永不归档。docs-check 新增守卫：终态缺陷行 >4、已批准豁免行 >6 报错提示归档，缺陷 ID/豁免编号跨归档查重，孤儿详情页校验覆盖归档，归档件混入活跃行即拦截。已实跑一轮：BUG-001/002/003 与豁免 #1/#2 入归档。CLAUDE.md §3 同步
- **rev 复核 lint 豁免 #5/#6/#7**（opus 实例）：18 处告警全部批准；实跑 lint 对账判定范围内 41 条告警与 #1~#7 一一对应、无未登记新增。审查记录 `doc/evidence/v0.1.7/rev-review-waivers-5-7.md`；#6 原因栏"6 处"笔误 orch 已更正为 4 处
- **BUG-006/007 复验关单**（DV 实例，关单人≠修复人）：BUG-006 按收窄范围 lint 对账 PASS、BUG-007 按登记步骤脏 out 直接 regress 无 VFS_SDB_ERROR 假失败，均 `make evidence BUG=<ID>` 机械关单置 CLOSED（`doc/evidence/v0.1.7/BUG-00{6,7}.log`）
- **M1 覆盖率采集 + 收窄**（两个 DV 实例）：首测 cond 80.43%/toggle 60.91%/assert 78.26% 三类不达标；补场景 M1-07（enable→START 两步序列+单拍脉冲）/M1-08（busy=1 写 PKT_MEM 保护）/M1-09（packet_sram 读口同拍组合读，锁定 r6/BUG-003 裁决行为），`make regress COV=1` **10/10 PASS**，复测 line 94.92%✅ cond 91.30%✅ branch 95.12%✅ assert 100%✅、fsm 结构性 N/A、**toggle 73.32% 仍 ❌**。testplan M1 9/9 ✅，证据 `doc/evidence/v0.1.7/M1-0{7,8,9}.log` + `coverage-summary-M1.md`（含首测/复测与缺口分层）+ `result_summary.txt`
- TB 侧配套：`m3_stub_if` 增 rd_en/rd_addr/rd_data 与 start_pulse 观测、`tb_top` 把 sram 读口从常量 0 改接 stub、`m3_stub_driver` 增 read_sram/watch_start_pulse task（新增 4 处 Lint-[NS] 追加登记豁免 #7，待 rev 复核）

**没做什么**
- **未打 M1 tag**：`make next` 机械三条件已齐，但 spec §0 适配 7 要求六类 ≥90%，toggle 73.32% 未达标，orch 判定不收官。toggle 剩余缺口已分层（见 coverage-summary-M1.md 复测章节）：①结构性零翻转约 26 bit（PRDATA[31:8] 字段≤8bit 硬上限、PREADY 恒 1、rst 单次复位）——待 rev 裁决豁免口径；②真实缺口约 45+ bit（CFG/PKT_LEN_EXP 从未写入、enable/IRQ_EN 无 1→0 回落沿、stub res_* 单向置位）——补场景可闭合或顺延 M2/M3 联调
- 豁免 #7 追加的 4 处（read_sram/watch_start_pulse）未经 rev 复核
- design-prompt/apb_slave_if.md 与 RTL 顶部注释的 BUG-004 陈旧措辞仍未同步 r7（低优先级遗留）

**下一步**
- 派 rev：裁决 toggle 覆盖率口径（结构性 26 bit 是否豁免/如何登记过滤；真实缺口 45+ bit 是 M1 必闭还是顺延 M2/M3）+ 顺带复核豁免 #7 追加 4 处
- 按裁决执行：需补场景则派 DV，需登记过滤则建覆盖率豁免登记（仿 lint-waivers 格式）；toggle 口径闭合后打 M1 tag（bump-minor 进 M2）
- M2 前置：arch 出 packet_proc_core 等 M2 design-prompt（过 rev 门禁）

**如何验证**
- 本地 VM：`make regress COV=1`（10/10 PASS）+ `make cov`；`make lint`（收窄范围内全部已登记，含归档件，grep 两文件核对）
- `python3 scripts/docs.py --check` 通过；`make docs-archive` 幂等（再跑显示无需归档）
- `grep -n "BUG-00[67]" doc/bugs.md`（均 CLOSED 带证据）；覆盖率数据 `doc/evidence/v0.1.7/coverage-summary-M1.md` 对照 `sim/out/urgReport/`

