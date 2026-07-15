# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.5.0] 2026-07-16 M4 收官：M4-01..05 全 ✅ + BUG-011 闭环 + rev 里程碑签核通过——M1–M4 四里程碑全部完成，项目验证收官

**做了什么**
- DV 收口 M4-01/03/05：真跑回归 32/32 PASS，M1–M3 九个必做场景 ↔ testcase 映射逐条核对；testplan 头部补字段口径注记（§11.5-必3 映射）与 regress.list 双向对应说明（smoke 例外声明）；三行 make evidence 机械登记 ✅。至此 testplan 全表 M1 9/9、M2 7/7、M3 5/5、M4 10/10（含 M4-02a..e）全 ✅。
- **BUG-011 全闭环**（DV 发现 → orch 修复 5a58c64 → rev 复验关单 CLOSED）：scripts/docs.py cmd_next() 里程碑"rev 签核记录存在"检查恒真——`any(Path.glob() 生成器)` 误用（生成器对象恒真）+ 模式大写 review-M 与既有小写命名不匹配，会放行未签核里程碑。修复后两态验证：签核记录落盘前报"还差 rev 签核"、落盘后报"已齐"。
- rev 里程碑签核**通过**（`doc/evidence/v0.4.1/review-m4-milestone.md`）：① 三条硬条件独立现算全满足；② 覆盖率 gold-standard 复算——rev 本人重跑 `make regress COV=1 && make covreset && make cov`，六类逐格与归档 coverage-summary.md 完全一致（SCORE 97.46/LINE 100/COND 94.35/TOGGLE 90.42/FSM 100/BRANCH 100/ASSERT 100），无编造；③ M4-04 过滤登记逐条 spec 依据成立、登记表×exclude 配置抽查 4 条一致、apb_slave_if 未覆盖 50 位逐位确认恰为 PRDATA[31:8]+PREADY 纯 spec 强制常量，无"可达却排除"；④ lint 豁免 #10/#11 复核批准（全部豁免至此均已 rev 复核）。
- 版本 0.4.1 → 0.5.0（bump-minor），tag v0.5.0。**M1=Lab1 … M4=Lab4 四个里程碑全部完成、选做项全按必做交付，项目验证收官。**

**没做什么**
- rev 记录的三条低风险遗留未处置（均不阻塞）：① TOGGLE 90.42 仅高于线 0.42pt，PRDATA 位映射若变需重估；② `make lint` 因 flist 顺序报错（BUG-005 WONTFIX 范畴，lint 依赖手动诊断运行）；③ 过滤项 B-5（PSEL=0&PENABLE=1）登记但未配 .el 位级项（数值取保守口径、非虚高）。
- 两处可选清理未做：M2/M3 部分 testplan 行"spec 依据"列缺 §11.x-必/选 编号标签（可追溯性精度，非字段空缺）；lint-waivers #11 对象列行号微差（29 实为 L30，rev 已注记）。
- 未新增任何 RTL/激励（M4 冻结纪律，rtl/tb 本周期零功能改动）。

**下一步**
- 项目主线（M1–M4）已收官，无机械待办（`make next` 对 M5 无定义会提示范围由 arch 定）。若继续：候选方向有 SpyGlass lint 后端接入（换掉 VCS +lint 及 BUG-005 尾巴）、答辩材料整理（spec §11.5 第 8 周）、或按 CLAUDE.md 由 arch 提出新项目计划。
- 上面"没做什么"三条低风险遗留与两条可选清理，接手者可按需处置。

**如何验证**
- `git tag` 含 v0.5.0；`make handover` 看 testplan 四个 M 全 ✅、无未关闭缺陷。
- `doc/evidence/v0.4.1/`：review-m4-milestone.md（签核）、M4-01/03/05.log、result_summary.txt（32/32）；`doc/evidence/v0.4.0/`：coverage-summary.md（六类）、coverage-gap-analysis.md、coverage-exclude-registration.md、M4-02a..e.log。
- 覆盖率复现：`make regress COV=1 && make covreset && make cov`（tb_top 域 SCORE 97.46、六类全 ≥90）。
- `grep -n "BUG-011" doc/bugs.md` 状态 CLOSED、修复 commit 5a58c64、复验证据=review-m4-milestone.md。

## [0.4.1] 2026-07-16 M4-02/04 交付：六类覆盖率闭环 82.05→97.46（六类全 ≥90）+ 过滤登记合规

**做了什么**
- DV 实例完成 M4-02（六类覆盖率达标）+ M4-04（过滤登记合规）闭环：基线测量 → itemized 缺口分析（`doc/evidence/v0.4.0/coverage-gap-analysis.md`）→ 补强激励 → 合法过滤登记 → 复测达标。设计+验证域（tb_top）六类：LINE 100 / COND 94.35 / TOGGLE 90.42 / FSM 100 / BRANCH 100 / ASSERT 100，SCORE 97.46（≥95 优良档）。
- 新增 5 类补强测试（testplan M4-02a..e，各带机械证据）：ppa_m1_10_rand（CSR/stub 随机）、ppa_m2_08_rand（随机帧多 seed）、ppa_m2_09_reset（M2 运行中复位）、ppa_m3_06_rand（集成随机帧）、ppa_m3_07_reset（集成运行中复位）；序列库 `tb/uvm/test/m4_seq_lib.sv`。回归列表 22→32 条，`make regress COV=1` 32/32 PASS、UVM_ERROR/FATAL=0，M1/M2/M3 零回归。
- 覆盖率过滤仅三类合法项（spec 强制常量 PREADY≡1/§5.2 无 ≥bit8 CSR 字段、APB 非法态、UVM-1.2 库域外），逐条登记 `coverage-exclude-registration.md`；配置在 `sim/cov_exclude/`（域级 cov_domain.cfg 已生效 + 位级 coverage_exclude.el 佐证用）。无"可达却过滤"项，无新缺陷（随机+复位注入零 mismatch）。
- FSM 复位弧覆盖流程固化：`make covreset` 独立 vdb + urg 多路合并（规避 VCS O-2018 共享 cm_dir 对异步复位弧的不稳定丢弃）。

**没做什么**
- M4-01/M4-03/M4-05 未登记 ✅（回归 100%/选做全纳入客观已满足，但证据与 testplan 完整性核对未做，留下一周期）。
- lint 豁免 #10（M3 遗留）与新增 #11（m4_seq_lib 复位对齐 `@(...)` 2 处 Lint-[NS]）均待 rev 复核；M4 里程碑 rev 签核未做。
- RTL 零改动（M4 冻结纪律）；未打 tag（M4 未收官）。

**下一步**
- 派 DV 收 M4-01/03/05：M4-01/05 用现成 32/32 result_summary 走 make evidence，M4-03 核对 testplan 字段与回归列表一一对应。
- 派 rev：复核豁免 #10/#11 + 审计过滤登记表合法性 + M4 里程碑三条硬条件签核（审查记录入 doc/evidence/v0.4.0/）。
- 签核通过后 /closeout 收官：bump-minor 或按需 bump + git tag。

**如何验证**
- `make regress COV=1 && make covreset && make cov` 复现 32/32 与六类数值；`doc/evidence/v0.4.0/` 下 coverage-summary.md（六类摘录）、result_summary.txt、M4-02a..e.log（首行复现命令）。
- `make handover` 看 testplan M4 ✅2/❌0/🔲3（M4-01/03/05 待收）。

## [0.4.0] 2026-07-14 M3 收官：ppa_top 顶层集成交付 + BUG-010/r11 落地，里程碑签核通过，进入 M4

**做了什么**
- arch 撰写 `doc/design-prompt/ppa_top.md`（M3 顶层集成设计输入，feature-matrix F3-1），过 rev 门禁（spec 锚点逐条核对 + 行为泄漏检查，通过）。
- rev 门禁审查期间由 arch 发现 §2.1 顶层框图与 §2.3 Top 端口表对 `done_o` 是否为顶层对外引脚存在矛盾，登记 **BUG-010**；rev 仲裁取方向 (a)——`done_o` 为 M3→M1 内部信号（§8.1 已定名），不引出顶层，与 §2.3（唯一权威）对齐；orch 应用 spec 修改记录 **r11**（§2.1 ASCII/mermaid 框图删去 done_o 对外引脚画法，补澄清注）并重新 pin，BUG-010 → SPEC_CHANGED。
- DE 交付 `rtl/ppa_top.sv`（三模块纯连线 + PCLK/PRESETn 统一分发 + 10 条内部连通性/无 X 断言），编译 0 error；lint 仅 6 处 `Lint-[SVA-DIU]`（与已批准的 #1/#2/#8 同类写法），登记豁免 #9，rev 复核批准。
- DV 建 M3-01~M3-05 五条集成场景（端到端链路、连续两帧、STATUS 总线、busy 写保护、中断闭环），改造 `tb_top.sv` 接入真实 `ppa_top`（M1/M2/M3 单元级通路与集成路径物理隔离），全部 PASS；全量回归 22/22 PASS（smoke+M1×9+M2×7+M3×5），M1/M2 零回归。新增 2 处 `Lint-[NS]` 豁免登记 #10（同 #7 根因），待 rev 复核。
- orch 归档里程碑三件人工证据：`result_summary.txt`、`coverage-summary.md`（六类覆盖率含未达标项如实记录）；rev 独立复核签核 `review-m3-milestone.md`——三条硬条件（RTL 就绪+场景全✅、regress 100% PASS、rev 审查记录）均独立验算通过。

**没做什么**
- lint 豁免 #10（DV 登记的 2 处 `Lint-[NS]`）尚未经 rev 复核，遗留给下一周期顺带处理（不阻塞 M3 签核，性质与已批准的 #7 完全相同）。
- 覆盖率六类综合未达 90%（TOGGLE/FSM/COND 主要缺口，另发现 M1 侧 SVA 在集成场景下部分未触发，ASSERT 从模块定义域 100% 降到 ppa_top 集成实例域 88.89%）——按 M2 先例裁定为 M4-02 判据，非 M3 阻塞项，已如实记入 coverage-summary.md 供 M4 参考。
- 未新增 M4（Lab4 回归与覆盖率闭环）相关任何工件，M4 尚未启动。

**下一步**
- `make next` 进入 M4：需 arch 补 M4 相关 design-prompt（若有）或由 orch 直接规划 M4-01~M4-03（一键回归/六类覆盖率闭环/testplan 文档完整性）任务卡；覆盖率缺口（TOGGLE/FSM/COND 及 M1 侧 SVA 集成覆盖）是 M4 的直接工作对象。
- 顺带处理：lint 豁免 #10 送 rev 复核；design-prompt/ppa_top.md 与 apb_slave_if.md 等历史 BUG 遗留的"引用更新"类小尾巴（如有）一并检查。

**如何验证**
- `make handover` / `make next` 查看 M4 起点状态；`git tag v0.4.0` 标记本次里程碑。
- `doc/evidence/v0.3.0/`：`M3-0{1..5}.log`（复现命令 `make run TEST=ppa_m3_0N_test SEED=1`）、`result_summary.txt`（22/22）、`coverage-summary.md`、`review-m3-milestone.md`。
- `doc/bugs.md` BUG-010（SPEC_CHANGED，r11 已 pin）；`doc/lint-waivers.md` #9（已批准）/#10（待复核）。

