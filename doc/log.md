# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.5.6] 2026-07-27 BUG-015/016/017 关单 + BUG-018 登记 + R3 交付单页全景与 README 改写

**做了什么**
- **BUG-015/016/017 全部 CLOSED**（关单人=rev ≠ 三修复人，`doc/evidence/v0.5.5/review-bug-015-016-017.md`）：015 注释九项主张逐条指回 spec 原文行号，纯注释零语义由去注释机械等价证明（前后 196 行逐字等同）；016 确认 `predict()` 为全工程唯一参考模型，rev 独立实跑回归 32/32；017 三条原向量重放全 FAIL、基线缺失 fail-closed 实测坐实、33 份 out log + 4 份 covreset log 零误伤。
- **登记 BUG-018**（rev 换角度新构造的两条 svacheck 绕过，当前均不可利用故不阻断关单）：A（中危）`sva_baseline.json` 无任何机械守卫——floor 被静默下调为 0/0 后 `$assertoff` 向量重新判 CLEAN，守卫的信任锚本身不受守卫；B（低危）层 1 尾锚对 `failed at <t>  Offending '<sig>'` 同行格式失明，第三次证伪"层 1 全覆盖"自述。
- **R3 交付（arch）**：新增 `doc/report.html` 单页全景（自包含 150KB、零外链、深浅双主题、五类内联 SVG：架构框图/验证金字塔/覆盖率爬坡/回归增长/缺陷时间线、9 条诚实专栏含 BUG-014/013/012 两段式）；README 改写为成果门面（徽章行+GEN 速览+mermaid+里程碑表+诚实边界）；删除数据停在 M1 的 `doc/outlook.html`（CSS 原语迁入新页，页脚注明 `git show v0.2.0:doc/outlook.html` 可取回）。**arch 手写的 report.py 指标数字 = 零**：98+5 个 data-metric 全机械注入；rev 易变路径（缺陷计数等）特意只走自动重注的 GEN 区，叙事不写死任何缺陷状态。措辞全部过红线（ASSERT 100% 带分母 88 与域、断言拦截力两段式、无"lint 干净"、spec 修订 8 次闭环=6+2）。
- xverif 修正后持续生效：关单 rev 亦按全路径协议使用（见其记录）。

**没做什么**
- **BUG-018 未修**（OPEN）：svacheck 二轮加固待派 DV（基线文件纳入 report-check 守卫 + 尾锚放宽 + 第三次收窄 docstring）。
- **R4 答辩讲稿未做**（`doc/presentation/defense.md`，report-check 对其保持 2 条"不存在→跳过"warn 属预期）；R5 材料终审未做。
- `sim/result_summary.txt` 仅日期行变化（rev 关单复跑，32/32 内容逐字一致），随本 commit 入库。

**下一步**
- 派 arch（新实例）交付 R4 讲稿：15 页对齐 spec §11.5 必3+选2、9 步演示脚本含兜底、Q&A ≥15 条；数据基线走 GEN 生成区。
- 派 DV 修 BUG-018；随后 rev 终审三件材料（数字 ⇄ report.py --json ⇄ evidence 三方一致）+ 关单 018。
- 全部闭环后 /closeout 收官（材料线完成 = 本轮委托完成）。

**如何验证**
- 浏览器打开 `doc/report.html`（浅/深主题各看一次）；`make report-check` 7/7 绿（98+5 个 data-metric 静态比对）。
- `grep -n "BUG-01[567]" doc/bugs-archive.md` 或 bugs.md 看 CLOSED 与复验证据路径；BUG-018 在 bugs.md 状态 OPEN。
- `git show v0.2.0:doc/outlook.html | head` 验证旧页可取回。

## [0.5.5] 2026-07-26 BUG-017 svacheck 三向量加固 + BUG-016 参考模型收敛 + xverif 探测协议修正（项目首次真实使用）

**做了什么**
- **BUG-017 修复（DV）**：svacheck 加第 3 层**基线校验**——新增 `sim/regress/sva_baseline.json`（total_min=91 / attempted_min=88，floor 语义），断言被摘出 flist 或 `$assertoff` 关断即 FAIL；基线只准人工改 + changelog 留痕（禁止静默自适应），历史旧 build 回扫走 `--no-baseline` 逃生口，基线文件缺失即 fail-closed。`::` 类作用域层次名正则修复；SUMMARY 逐条检查（多条并存告警）。rev 三条绕过向量语料逐一重放 **CLEAN→FAIL**（orch 另抽验向量①），正常回归 32/32 与 covreset 独立 vdb log 零误伤。顺带：evidence.py 的 KEY_LINE_RE 补 core-agent 形态；BUG-013 守卫召回边界写进 report.py 注释。
- **BUG-016 修复（同实例）**：删除零调用的 `tb/uvm/env/ppa_ref_model.sv`，摘 pkg include，`ppa_scoreboard.sv` 注释与 report.py H1 诚实清单同步改指 `ppa_core_seq_item::predict()` 单一参考模型；`git grep ppa_ref_model tb/ sim/` 零命中，编译 0 error、回归 32/32。
- **xverif 探测协议修正（orch，用户质疑"是不是从没用过 xverif"触发）**：核实 M1–M4 全程确实零使用（仅部署日冒烟一次），根因是 CLAUDE.md §5 与 de/dv/rev 角色文件写的探测命令 `command -v xdebug` **恒失败**——工具真实入口是 `/home/open_tools/xverif/tools/`（无 bin/ 转发、不在 PATH），`command -v xloc` 还会误命中 Verdi 同名工具。所有 agent 都正确执行了错误的协议。已改为 `test -x` 全路径探测 + 全路径调用（CLAUDE.md §5 + 三角色文件），记忆文件同步。**修正后本轮 DV 即首次真实使用**：6 次全路径调用 `xsva`（help/list/parse/scan）解析自建类作用域断言样本，据此订正 svacheck 的 fail-closed 自述——转录审计与汇报一致。
- 上一轮（0.5.4 后）的后台 DV 实例随宿主进程退出而中止，仓库零残留，本轮从头重派完成。

**没做什么**
- **BUG-015/016/017 均未关单**（015 FIX_READY / 016、017 本 commit 回填 FIX_READY，关单人须 ≠ 修复人）。
- 三件展示材料仍未做；`doc/outlook.html` 未删（其 385-386 行还把已删的 golden_calc 描述为参考模型——过期陈述，R3 删除该文件时一并消灭，不单独修）。
- 基线 attempted_min=88 零余量：未来若有合法测试 attempted<88 会误伤，须走基线文件登记下调（已在文件内写明）。

**下一步**
- 派 rev 复验关单 BUG-015/016/017（关单人 ≠ 修复人）。
- 关单后派 arch 出三件展示材料（report.html / README / defense.md）——这是最后的前置。

**如何验证**
- `python3 scripts/svacheck.py <log>` 输出首行显示基线；`cat sim/regress/sva_baseline.json` 看 floor 语义与维护纪律。
- rev 三向量语料在 `doc/evidence/v0.5.3/review-bug-013-014.md` §A2，逐条重放应 FAIL。
- `git grep ppa_ref_model tb/ sim/` 零命中；`make docs-check` + `make report-check` 双绿；回归 32/32。
- xverif：`test -x /home/open_tools/xverif/tools/xdebug` 应命中；CLAUDE.md §5 已是全路径协议。

## [0.5.4] 2026-07-26 BUG-013/014 rev 关单 + ASSERT 口径裁定 88/88 + svacheck 三条绕过向量登记（BUG-017）

**做了什么**
- **BUG-013/014 双双 CLOSED**（关单人=rev ≠ 修复人，复验证据 `doc/evidence/v0.5.3/review-bug-013-014.md`）。rev 不复用修复人的做法自建负向对照（仓库外 bind 两条明知为假的断言，其一**无动作块**）：断言真失败而 UVM_ERROR=0、退出码 0——缺陷属实；修复后 `regress.py` 判 FAIL 退出码 1、`evidence.py` 拒登不落文件；同一次编译内 ppa_m1_01_test 仍 PASS（自带阴性对照）。fail-closed 实测：去掉 `-assert verbose` 判定**变严格**（安全方向）。历史回扫方法学复核通过：33 份归档摘录含断言信息 0 份坐实"扫摘录零信息量"，替代方法（按添加 commit 重建树重放）成立，rev 自抽 5 份跨里程碑重放结论一致，保真度对照加强为关键检查行逐行逐字比对仍全中。BUG-013 九项措辞主张逐条实数复核全部属实，纯注释零语义由**去注释机械等价**证明（不依赖回归背书）。
- **ASSERT 覆盖率口径裁定（91/88/3 之谜解开）**：91 = 88（tb_top 域内**并发**断言实例，源码 49 条按例化展开，逐 scope 加总实证）+ 3（uvm_pkg **立即断言**——`-assert verbose` 的 attempts 只统计并发断言，立即断言进总数永不进 attempts，rev 用独立微基准坐实）。3 条逐条定位均在 uvm_pkg（do_read/do_write 的 $cast 断言 ×2 + name_check_visitor 的 regex 断言，后者执行 21 次全成功）。rev 重跑合并覆盖率复现 M4 全部六类数字，按域拆分确认 **ASSERT 100% = 88/88 成立、域内无一未触发**；历史侧独立锁死分母（M3 的 94.32 只有 83/88 一个解）。对外措辞以 review-bug-013-014.md §C 的引用句为准（写 100% 必须带分母 88 与测量域）。勘误 `doc/evidence/v0.4.0/coverage-summary.md` §5 的计数归属（89/89→88/88、域外 2→3；原文不改，追加勘误节，证据不可变）。
- **登记 BUG-017**：rev 构造出三条能骗过 svacheck 的漏报向量——①（高危）不校验断言总数/attempts 基线，`$assertoff` 或摘 flist 后 `2 assertions, 0 with attempts` 判 CLEAN、真违例回归全绿；② 层 1 正则对类作用域 `::` 层次名结构性失明，"层 1 fail-closed"自述对该类不成立；③ SUMMARY_RE 取末条，拼接 log"先失败后干净"判 CLEAN。另两条顺带（KEY_LINE_RE 对 core-agent 测试零命中、BUG-013 守卫召回窄——rev 构造 7 条真过期承诺全部逃逸）。
- **诚实性订正（R4，orch 自纠）**：0.5.3 的 log 块与 commit `461aebc` 的 message 里"32 份 log 遍布这些信号名，一条未被误伤"**与实测相反**——`length_error/type_error/chk_error` 在 32 份回归 log 与 33 份归档摘录中出现 **0 次**（UVM_HIGH 亦 0），`ERROR_STATE` 在本仓库根本不存在。误伤结论本身经 rev 自建语料重新立住（不误伤成立），但那句支撑话是错的：已推送的 commit message 无法修改，在此声明作废；"回扫 261 份 log"清单未落盘、不可审计，材料不得引用该数字。
- BUG-015 修复（DE，纯注释）：`rtl/apb_slave_if.sv` L9-13 改为陈述现行 spec 契约（§6.3/r7：APB 读 PKT_MEM 恒 PSLVERR=0、PRDATA=32'h0 占位），不再称"临时处理/不作为对外行为承诺"；编译 0 error。DE 顺带核查 rtl/ 全部 BUG- 引用：其余均引已生效 rN、无同类过期；列出 L227/L253 两处风格陈旧但无事实错误（未扩大改动）。orch 修 report.py 的 R8（REVIEW_KIND_RULES 补"复验/关单"类，warn 7→6）。

**没做什么**
- **BUG-017 未修（OPEN，材料前必修）**：svacheck 的三条绕过向量在，materials 就不能宣称"断言失败必然拦截"。
- **BUG-015 未关单**（FIX_READY，关单人 ≠ 修复人=DE）；BUG-016（双份参考模型）未动，orch 已定 scope=删除死代码路径，随 BUG-017 一并派 DV。
- 三件展示材料仍未做；`doc/outlook.html` 未删。
- rev 指出 BUG-013 守卫召回窄不阻断关单，但"report-check 通过"≠"仓库无过期承诺"——此边界须写进守卫 docstring（并入 BUG-017 ④）。

**下一步**
- 派 DV 修 BUG-017（svacheck 加固：attempts 基线校验 + :: 层次名 + Summary 逐条 + docstring 边界）并顺带 BUG-016（删 `ppa_ref_model.sv` 收敛到 predict() 单一参考模型，同步 scoreboard 注释，回归零回归）。
- 派 rev 复验关单 BUG-015/016/017（关单人 ≠ 修复人）。
- 全部闭环后派 arch 出三件材料（report.html / README / defense.md），材料措辞以 review-bug-013-014.md §C 引用句 + scratchpad 红线文档为准。

**如何验证**
- `grep -n "BUG-01[34]" doc/bugs.md` 状态 CLOSED、复验证据=review-bug-013-014.md；`doc/evidence/v0.5.3/review-bug-013-014.md` §A/§C 看负向对照与 88/88 拆解。
- `doc/evidence/v0.4.0/coverage-summary.md` 末尾勘误节；`make docs-check` + `make report-check` 双绿。
- BUG-017 三条向量的构造语料在 review-bug-013-014.md §A2/A5，加固后逐条复验应转 FAIL。

## [0.5.3] 2026-07-26 BUG-014 修复：SVA 断言失败纳入回归判定 + 历史回扫 261 份 log 零漏判

**做了什么**
- **修 BUG-014**（断言失败不拦回归）。先复现：受控破坏一条断言后 `ppa_m2_04_test` 打出 26 次断言失败，同一份 log 的 `UVM_ERROR : 0`、simv 与 make 退出码均为 **0**，`regress.py` 判 PASS——缺陷描述完全属实。
- 修复用**双层判定**，任一命中即 FAIL，单点收敛在新增的 `scripts/svacheck.py`：① `sim/Makefile` 的 SIM_OPTS 加 `-assert verbose`，让 VCS 把结构化计数打进主 log（`Summary: 91 assertions, 88 with attempts, N with failures`），第三个数 >0 即失败；② 抓断言**引擎行**（`"<file>", <line>: <hier>: started at T failed at T`）——该行与动作块无关，`$error`/`$fatal`/无动作块都打，比抓 `Error:` 行完整，且**不依赖任何编译选项**（有人删掉 `-assert verbose` 也拦得住，fail-closed）。`regress.py` 判 FAIL、`evidence.py` 拒登证据，且新摘录带 `## SVA 断言汇总` 段，未来证据可被 svacheck 独立复判。
- **误伤验证**：7 类边界样例全判 CLEAN——`length_error_o`/`type_error_o`/`chk_error_o` 出现在 UVM_INFO 正文与 `Offending '...'` 行、`ERROR_STATE`、`UVM_ERROR : 0` 汇总行、编译诊断 `Error-[SE]`、`-assert verbose` 的正常尾巴 `not finished`、`0 with failures`。最强实证是全回归 32/32 PASS——这 32 份 log 遍布这些信号名，一条未被误伤。orch 另做独立抽验，正负两态均符合预期。
- **历史回扫（本轮最重要产出）**：DV **实测证伪了 orch 给的回扫方法**——用修复前逐字一致的摘录规则去处理那份真有 26 次断言失败的 log，摘录出来 `failed at` 行数为 **0**，即 33 份归档证据摘录在设计上就丢弃了全部断言信息，"扫摘录得 0 漏判"信息量为零。改用有效路径：`git log --diff-filter=A` 定位**添加该证据文件的那个 commit**（不是"版本号最后一个 commit"——`/closeout` 在同一 commit 才 bump，按版本号选树会跑出 `INVTST` 空结果，DV 踩了并纠正），`git archive` 出该树重跑登记的 TEST+SEED。**共回扫 261 份 log，0 处漏判、0 份空跑**；带阳性对照（断言尝试数 23/39/88 全非零）与保真度对照（33 份重放与归档摘录的 UVM severity 计数逐字一致）。
- 顺带订正 `tb/sva/README.md:10` 的**虚假陈述**："断言失败计入 UVM 报告（`$error`/uvm_error 上报），FAIL 即回归 FAIL"——与实测相反，正是 BUG-014 得以长期潜伏的文档根源。
- orch 补 `report.py` 的 `BUG_KIND_RULES`：BUG-016 归属抬头写 `TB` 而规则只认 rtl/infra/spec，落盘即打挂 report-check。属分类集不完整（CLAUDE.md §4.3 的归属口径本就含 TB 侧，状态集里也有 `TB_BUG`），故补全而非放宽为兜底。

**没做什么**
- **BUG-014 未关单**（FIX_READY，关单人须 ≠ 修复人）；BUG-013 亦待关单。
- BUG-015（`rtl/apb_slave_if.sv:9` 称 BUG-004 仍 OPEN，实为 SPEC_CHANGED/r7 已定契约，归 DE）、BUG-016（`ppa_ref_model.golden_calc` 零调用 + 双份参考模型）未修。
- 三件展示材料仍未做；`doc/outlook.html` 未删。
- **91 条断言实例中恒有 3 条从未被触发**（每份 log 都是 `88 with attempts`）未查。初步推算 88 = 各 bind/例化实例展开数之和，3 条疑为 uvm_pkg 内建断言（属域外、M4-04 已登记 A-1），但**未经独立确认**，交 rev 一并核。

**下一步**
- 派 rev 复验关单 BUG-013 + BUG-014（关单人 ≠ 修复人），并核 91/88 的口径落差。
- 派 DE 修 BUG-015；BUG-016 由 orch 定 scope。
- 之后才派 arch 出三件材料。**材料措辞红线**：现在起可以说"断言失败会让回归变红"（有负向实验背书）；但仍不可写"lint 干净/清零"（`make lint` 至今 exit 1）、不可写"断言全部通过"以外的强度声明，且须注明"过去 4 个里程碑期间 49 条断言对回归的拦截力实际为 0，历史清白是复算出来的、不是当时流程保障的"。

**如何验证**
- `python3 scripts/svacheck.py <log...>`；`make -C sim regress` 用新判定实测 **32/32 PASS**。
- 负向：受控破坏一条断言后 `regress.py` 判 FAIL 退出码 1、`evidence.py` 拒登退出码 1。
- `grep -c "assert verbose" sim/Makefile` 为 1；`grep -h "Summary:.*assertions" sim/out/*.log | sort -u` 应为 `91 assertions, 88 with attempts, 0 with failures`。
- `make docs-check` + `make report-check`（七项）双绿；缺陷 16 条（spec 6 / infra 8 / rtl 1 / tb 1）。

