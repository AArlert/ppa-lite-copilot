# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.5.2] 2026-07-26 用户质疑触发的诚实性排查：BUG-012 关单 + BUG-013 注释腐烂订正 + 新增源码守卫，并挖出 BUG-014 断言不拦回归

**做了什么**
- **BUG-012 关单（CLOSED）**：rev 独立复算 lint 对账——自实现 `(类别,文件,行号)` 去重得实测 **81 处**，登记表 #1–#12 覆盖 81 处，**双向差集为空**；并用受控负向复现（`git show 615f31a^:` 取修复前文件 + 独立 `OUT=out_neg`）证实"修复前 84 处"，集合差恰为那 3 处 WMIA-L。豁免 #12 **批准**且不是"图省事"——rev 做了负向实验：剥除 7 处 `disable iff (rst)` 后复跑 `ppa_m2_09_reset_test`，`a_done_hold` 在 DONE 态异步复位下**虚假失败**，证明 `disable iff` 语义承重，与零语义代价的 `8'()` 显式转换不同类。3 处 WMIA-L 直接改源码的等价性由 rev **不依赖回归 PASS** 独立确认（`payload` 为 `bit[7:0]`、`new[28]` ⇒ `i∈[0,27]`、RHS 值域全 ⊆[0,255]，`8'()` 不截任何有效位）。
- **BUG-013 订正注释腐烂**（用户人工审阅代码提出"这个仓库的项目真的已经做完了吗"触发）：`tb/tb_top.sv`、`tb/m3_stub_if.sv`、`tb/uvm/env/ppa_env.sv` 的 4 处「M3 尚未交付」是 0.1.x 期措辞冻结——`rtl/packet_proc_core.sv` 已于 0.2.2（`b4fb27e`）交付、tb_top 现同时例化三条通路（M1 单元 / M2 单元 / ppa_top 集成），m3_stub 保留是通路隔离的正确设计、只是措辞过期；DV 顺带查出并订正第 5、6 处（`m3_stub_if.sv:12` 的"由后续 Lab2 独立交付"、`sim/flist/rtl.f:1-2` 只认 M1 的清单自述）。`ppa_scoreboard.sv` 两条 `TODO(M1,DV)`/`TODO(M3,DV)` 撤销并如实改写为"已选架构 + 代价"（检查落在自检序列与 driver 内建参考模型；代价是分散、非集中式记分板，补齐列为后续演进项）。**纯注释改动零语义变更**，`make regress` **32/32 PASS** 背书。
- **新增第 7 项守卫（`report.py --check`）堵住守卫体系的源码盲区**：`docs.py --check` 只守 doc/ 文档，完全不覆盖源码注释与交付状态失步——正是这个盲区让腐烂一路带到 0.5.0 收官。新守卫扫描 rtl/tb/sim 注释里"未完成标记 ⇄ 里程碑编号"绑定出现的过期承诺，与 `version.json` 当前 M 对照，指向已收官 M 即报错。设计上避开三类误伤：场景 ID（`M1-06` 后随 `-数字`）排除、同句且间隔 ≤24 字符的绑定窗口、字符串字面量屏蔽；开放式留白（如 apb_sequencer 的"占位以便将来加仲裁"）与在途承诺只计数不 warn；另设 `report-check:allow-stale-milestone` 逃生口（降级 warn 并登进 JSON 的 suppressed 列表交 rev 复核）。**历史回放验证**：在修复前的树上报出 9 处过期承诺、0 误报，精确覆盖 BUG-013 点名的全部位置。
- **登记 BUG-014/015/016 三条新缺陷**（均由本轮排查衍生，见下）。

**没做什么**
- **BUG-014 未修（OPEN，最高优先）**：SVA 断言失败**不会让回归变红**。49 条断言动作块一律 `else $error(...)`，而 `regress.py:19-26` / `evidence.py:40-42` 判 PASS 的唯一依据是 UVM_ERROR/FATAL——`$error` 不经 UVM report server、不计入 UVM_ERROR，VCS 默认也不改 simv 退出码。rev 做负向实验时同一份 log 里 `a_done_hold` 真实失败而 `UVM_ERROR : 0`、退出码 0、`regress.py` 判 PASS。**后果：断言失败可被登记成 ✅**。历史结论是否受影响需回扫全部归档 log 才能定论。
- **BUG-015 未修（OPEN）**：`rtl/apb_slave_if.sv:9` 仍称 BUG-004 为 OPEN、称 PKT_MEM 读回行为是"临时处理、不作为对外行为承诺"，而 BUG-004 已 SPEC_CHANGED、spec r7 已把该行为定为正式契约。属 rtl/ 侧，归 DE。新守卫抓不到这一类（绑定的是里程碑号不是缺陷号）。
- **BUG-016 未修（OPEN）**：`ppa_ref_model.sv::golden_calc()` **零调用者**，期望值实际由 `ppa_core_seq_item::predict()` 内联另实现一份——双份参考模型静默漂移风险，且没有调用者的那份永远不会被仿真证伪。
- 三件展示材料仍一件未做（`doc/report.html` / README 改写 / 答辩讲稿）；`doc/outlook.html` 未删。
- BUG-013 未关单（关单人须 ≠ 修复人）。

**下一步**
- **先修 BUG-014 再出材料**：派 DV 让 `regress.py`/`evidence.py` 在 UVM_ERROR/FATAL 之外同时扫描 SVA 失败特征，任一命中即判 FAIL / 拒登证据；**对全部既有归档 log 与重跑的 32 条回归 log 做历史回扫**，确认历史上是否真有被漏判的断言失败。在本条闭环前，对外材料不得就"断言"做任何强度声明（可写覆盖事实，不得写或暗示"断言全部通过"）。
- BUG-015 派 DE（rtl/ 归 DE）；BUG-016 由 orch 定 scope（删死代码 vs 收敛到单一参考模型）。
- BUG-013 派 rev 复验关单（关单人 ≠ 修复人）。
- 上述闭环后再派 arch 出三件材料；材料须遵守 rev 的措辞裁决（见 `review-report-tool.md` §B/§C3、`review-lint-waiver-12.md`）：lint 只能写「81 处告警、12 条豁免全部经 rev 复核批准」，**不可写"lint 干净/清零"**（`make lint` 至今 exit 1）、**不可写"全部修复"**（本轮只修 3 处）。

**如何验证**
- `make docs-check` + `make report-check`（现为七项）双绿；`git grep -n "尚未交付\|骨架阶段\|TODO(M" rtl/ tb/ sim/` 应 0 命中。
- `doc/evidence/v0.5.1/review-lint-waiver-12.md` 看 rev 的对账实录、`disable iff` 剥除负向实验、等价性独立确认。
- `python3 scripts/report.py --json` 看 `results.waivers`（12 条 / 81 处 / reviewed 12/12 / `sites_line_drift` 空）与新增的 `source_markers` 子树。
- 断言盲区复现：`grep -n -A3 "assert property" tb/sva/*.sv rtl/*.sv` 确认 49 条全为 `else $error(...)`；`sed -n '19,26p' scripts/regress.py` 确认判定只看 UVM_ERROR/FATAL。

## [0.5.1] 2026-07-26 成果展示层基座：scripts/report.py 机械抽数（rev 复算通过）+ BUG-012 lint 登记补齐

**做了什么**
- 新增 `scripts/report.py`（成果数据机械抽取层）：从真值源现算设计/验证/结果三类数据，`--json / --summary / --md / --inject / --check` 五接口 + 42 条 provenance（每个会印进材料的数字都带出处与定位规则）。定位是**后续三件展示材料（单页全景 HTML、README 改写、答辩讲稿）唯一的取数口**——材料里禁止手写数字，全部由 `--inject` 写入 `<!-- GEN:key -->` 生成区，`--check` 保证不漂移。接进 `make report / report-json / report-sync / report-check` 与 CI（checkout 加 `fetch-depth: 0`）。`scripts/docs.py` 零改动（BUG-011 教训：不动既有硬门禁）。
- rev gold-standard 独立复算**有条件通过**（`doc/evidence/v0.5.0/review-report-tool.md`）：先手算再跑脚本，A 部分十组复算 10/10 一致、C 部分 provenance 抽查 12/12 一致、D 部分 10 次自设负向验证全部硬失败退出、`--check` 六项无一恒真（未重演 BUG-011）。裁决三条：① 豁免处数是可追溯机械事实但不进 KPI 带、须带"登记时刻计数"限定；② v0.1.7 覆盖率点测量域是 M1 模块聚合域非 tb_top，`comparable=false`、取复测值、FSM/SCORE 为 null 不得用 0 补位；③ 内置常量 `COV_THRESHOLD=90.0` ← spec §0 适配 7、`MILESTONE_LABS` ← CLAUDE.md §4.1，合法。
- 按 rev 放行条件返工 report.py：F1（footer-stamp/data-json 内嵌 git HEAD、提交数、今日日期 → HTML 一入库 CI 必然长红）改为"版本 + spec 钉住 sha + 真值源内容派生摘要"，新鲜度比对改 `same/volatile-only/different` 三态；F2（`--check` 三目标 vs `report-sync` 两目标）改 `--inject` 无参即取脚本内 TARGETS，消灭两份清单；F10（`REVIEW_KIND_RULES` 封闭四类命中不到即 fail——rev 写审查记录时当场把新门禁打挂）扩类目 + 兜底 `other` + warn，不再阻断出数链；另修 F3/F4/F5/F9。
- **返工中自查出两处会直接印错对外材料的缺陷**：① 缺陷归属分类被 BUG-012 的"infra（…非 RTL/spec 缺陷）"括号否定式打穿，infra 被误判成 rtl → 改为只匹配括号前抬头；② `reviewed` 沿用 docs.py 的"非空即已复核"宽口径，把"待 rev 复核"算成已复核 → 材料会印出"12/12 全部经 rev 复核批准"这句假话，已改为"含'批准'且不以'待'开头"并新增 `pending_review` + warn，现如实输出 11/12。
- **BUG-012 登记 + 处置**：rev 为验证豁免处数而实跑 `make -C sim lint`，发现 HEAD 处本仓库范围 84 处告警、登记表只覆盖 74 处，**10 处从未登记**（违反 CLAUDE.md §7）。DV 独立复现并自算差集一致后处置——7 处 `Lint-[SVA-DIU]`（tb/sva/packet_proc_core_sva.sv）与已批准的 #3/#4 同写法同根因，登记豁免 **#12**（复核栏留"待 rev 复核"，未自批）；3 处 `Lint-[WMIA-L]`（ppa_m2_01/02_test.sv）判定根因与 #6 不同（`foreach` 的 int 下标隐式赋给 `bit[7:0]`），**直接改源码 `8'(...)` 修掉不走豁免**，沿用 BUG-006 时 `Lint-[ULCO]` 的先例；顺带订正 #8 行号漂移（BUG-009 修复后整体后移）、撤销 #11 复核栏"29 实为 L30"的错误注记（L29/L30 是两处独立告警）。修后实测 84 → 81 处，逐一核对全被 #1–#12 覆盖，`make regress` **32/32 PASS** 零回归。
- `doc/evidence/README.md` 补"rev 审查记录的命名沿革"节：M1 签核用旧命名 `rev-review-M1.md`、BUG-011 修复后的 glob 对它不匹配——**这是命名不一致不是签核缺失**（该文件 129 行，含审查人、被审 HEAD ff6b50e、三条硬条件逐条验算）；处置为**不改历史证据文件名**（证据不可变性优先于表面整洁，改名会让归档件引用变死链），以说明代替改名，并规定非里程碑类记录不得以 `review-m<数字>` 开头。

**没做什么**
- 三件展示材料一件未做：`doc/report.html`（单页全景）、`README.md` 改写、`doc/presentation/defense.md`（答辩讲稿）均待 arch 交付。README 仍是 0.1.x 时期的 47 行操作说明、零成果数据；过时的 `doc/outlook.html`（数据停在 M1）尚未删除。
- **BUG-012 未关单**（状态 OPEN）：豁免 #12 待 rev 复核批准（登记人=DV，不得自批），关单人须 ≠ 登记人。在它闭环之前，对外材料不得出现任何"lint 告警全部登记/清零/干净"类表述。
- `--check` 的 [5/6] 生成区新鲜度与 [6/6] 静态数字比对目前是空跑（三个目标文件都不存在），只在 scratch fixture 上验证过逻辑；R3 交付 HTML 后才转为实校验。
- RTL 零改动；tb/ 仅 3 行 `8'(...)` 显式截断（BUG-012 处置），无功能变更。

**下一步**
- 派 rev（全新实例）复核豁免 #12 + 复算 lint 对账 + **BUG-012 关单**（关单人 ≠ 登记人），审查记录入 `doc/evidence/v0.5.x/`（文件名不得以 `review-m<数字>` 开头）。
- 派 arch（全新实例，与 rev 分实例）交付 `doc/report.html` + `README.md` 改写 + 删 `doc/outlook.html`；再派另一 arch 实例交付 `doc/presentation/defense.md`。两件材料的数字全部走 `make report-sync` 注入，禁止手写。
- 材料定稿前须遵守 rev 的措辞裁决（见 review-report-tool.md §B/§C3）：覆盖率 M1 点单独 marker 不入折线、M2→M3 的 −4.11pt 下降如实画出并注解、豁免处数不进 KPI 带、spec 修订写作"11 次修订其中 8 次闭环（6 次源自 bugs.md + 2 次源自 rev 门禁附带仲裁）"不得笼统称"8 个 BUG"。
- 材料齐备后派 rev 终审（材料数字 ⇄ `report.py --json` ⇄ evidence 原文三方一致），**下一次 bump 之前必须先 `make docs-archive`**（log.md 已达 4 块上限）。

**如何验证**
- `make report` 看成果速览；`make report-json` 看全量 JSON 与 provenance；`make report-check` 与 `make docs-check` 双绿。
- 关键抽数现状：缺陷 12 条（spec 6 / infra 5 / rtl 1）、豁免 12 条 81 处（SVA-DIU 7 / NS 4 / WMIA-L 1）、rev 复核 11/12（#12 待复核）、`sites_line_drift` 已归零、SVA 49 条（DE 32 / DV 17）、testplan 31/31 ✅、回归 32/32。
- `doc/evidence/v0.5.0/review-report-tool.md` 看 rev 的十组复算对照表、12 条 provenance 抽查、10 次负向验证实录与 §E.4 待修清单。
- `grep -n "BUG-012" doc/bugs.md` 状态 OPEN；`grep -n "^| 12 |" doc/lint-waivers.md` 复核栏应为"待 rev 复核"。

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

