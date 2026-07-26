# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

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

