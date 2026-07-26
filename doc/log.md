# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.5.8] 2026-07-27 R5 终审通过（条件已清）+ BUG-018 关单——展示材料线收官

**做了什么**
- **R5 终审（全新 rev）有条件通过，两项条件本 commit 全部清零**：① defense.md Q16 把 svacheck 被绕过计数误写"四次/四轮"（正文只枚举 BUG-014/017/018 三条；凑四的 BUG-011 属 docs.py 门禁非 svacheck）——orch 按 rev 裁定机械订正为"三次/三轮"（演示脚本第 8 步的"门禁体系四轮（含 BUG-011）"表述 rev 认可保留）；② `make report-sync` 清生成区过期（rev 落盘审查记录使 reviews.count 13→14 的必然自增）。
- **终审实录**（`doc/evidence/v0.5.7/review-materials-final.md`）：data-metric 三方核对 **18/18 一致**（回证据原文/源码独立复算，专防"JSON 抽错但比对自洽"共谋态）；五张 SVG 图坐标全部反算吻合（覆盖率三个可比点 y 值、M1 空心+虚线+域注记、M2→M3 下降如实、回归柱 10/17/22/32、缺陷分布 18 条、金字塔宽度公式）；八条措辞红线全过（ASSERT 100% 处处带 88+tb_top、两段式拦截完整、被禁表述零命中或仅否定语境）；诚实专栏与代码事实逐一核对（scoreboard 47 行、predict() 唯一参考模型）；§11.5 五项逐页对齐、演示抽 3 步实跑通过、15 个引用路径全存在；**lint 实跑 81=81 双向差集为空**。
- **BUG-018 关单（CLOSED）**：A/B 两条语料真跑复验（静默改 floor→[8/8] FAIL、正当留痕→绿；同行 Offending→层 1 命中；67 份真实 log 零误伤）；rev 换角度构造"伪造 changelog 一致假声明"实测能骗过 [8/8]，**裁定该非密码学级边界声明成立、接受**——残留需多工件一致伪造且留自指认明文，git 历史是恶意场景的人工兜底，sha-pin 非关单前置。
- 至此**展示材料线收官**：`doc/report.html`（单页全景）+ `README.md`（成果门面）+ `doc/presentation/defense.md`（答辩讲稿）三件齐备且经独立终审；**无未关闭缺陷**（BUG-001..018 全终态）。

**没做什么**
- rev 接受但记录在案的已知边界未再加固：基线守卫非密码学级（见上）；BUG-013 源码注释守卫召回窄（精度优先）；`data-baseline` 生成区接线（arch 发现的 infra 改进项）未做——三者均为登记在案的接受态，非欠账。
- 未打 tag（材料线不是里程碑 M；M1–M4 的 tag 体系到 v0.5.0 为止）。

**下一步**
- 无机械待办。候选（需用户确认）：SpyGlass lint 后端接入（BUG-005 尾巴）、data-baseline 生成区接线、scoreboard 集中式比对演进项、或按 CLAUDE.md 由 arch 提新项目计划。

**如何验证**
- `make report-check`（8/8）+ `make docs-check` 双绿；`make handover` 无未关闭缺陷。
- 三件材料：浏览器开 `doc/report.html`（浅/深各一次）、`README.md` 首屏、`doc/presentation/defense.md` 15 页。
- `doc/evidence/v0.5.7/review-materials-final.md` 看 18/18 核对清单与 BUG-018 关单实录。

## [0.5.7] 2026-07-27 R4 答辩讲稿交付 + BUG-018 svacheck 二轮加固——三件展示材料齐备，待 rev 终审

**做了什么**
- **R4 交付（arch 新实例）**：`doc/presentation/defense.md`——15 页提纲（页 8–12 右上角逐页标注 §11.5-必1/2/3+选4/5）、演示脚本 0–9 步各带兜底列、Q&A **19 条**（含直面"svacheck 被绕过四次怎么还敢说证据链可信"的 Q16——答法：四轮绕过全是项目自己的 rev 红队构造、发现即登记闭环+负向复验，这个循环本身是可信度来源）。头条数字全部落在受 report-check 守护的两个生成区，正文零重抄；手写数字仅 spec 结构常量与 rev 裁决引用句。arch 实测发现 `data-baseline` 未接入可注入生成区（report.py 的 `--md` 暴露了但没进 GEN_KEYS），改用已接线的两个 MD 生成区承载，结果等价，已在基线块注明——此 infra 小缺口留作改进项。
- **BUG-018 修复（DV）**：A（中危）基线守卫——`report.py --check` 新增第 8 项 `floor⇄changelog 留痕校验`：静默改 floor 值（changelog 不追行）即 FAIL（rev 语料重放命中），正当程序改值（changelog 同步声明）即绿，changelog 空/格式非法/缺字段/文件缺失四类 fail-closed；B（低危）`FAIL_LINE_RE` 尾锚放宽吃掉同行 `Offending` 尾巴（BUG-014 真实失败行形态命中），§A2-a 七类对抗语料零误报；svacheck 文件头自述第三次收窄为**逐层盲区覆盖矩阵表**，不再作任何总括声明。回归 32/32 零误伤。
- orch 修版本漂移：`020c7d0` 落盘后 bump 至 0.5.6 造成 report.html/README 的 `project.version` data-metric 停在 0.5.5（data-metric 只被校验不被注入），sed 订正 + `make report-sync` 后 report-check **8/8 全绿**（rc=0）。
- DV 如实声明的守卫边界：A 项非密码学级防篡改——同时伪造数值与 changelog 末行可骗过机械校验，git 历史是恶意场景的最终人工兜底（已写进基线文件注释）。

**没做什么**
- **BUG-018 未关单**（本 commit 回填 FIX_READY，关单人须 ≠ 修复人）。
- **R5 材料终审未做**：三件材料（report.html / README / defense.md）的数字 ⇄ `report.py --json` ⇄ evidence 原文三方核对，是材料线最后一道门。
- `data-baseline` 生成区接线（arch 发现的 infra 改进项）未做，不阻断。

**下一步**
- 派 rev（全新实例）R5 终审：三方核对三件材料全部数字与措辞红线（ASSERT 88/88 口径、断言两段式、无 lint 干净类表述、spec 修订 6+2、M1 覆盖率点域注记、M2→M3 回落如实呈现），并复验关单 BUG-018。
- R5 通过后 /closeout 收官（材料线完成）；有意见则按意见返工再审。

**如何验证**
- `doc/presentation/defense.md` 看 15 页/§11.5 标注/Q&A 19 条；`make report-check` 8/8 rc=0；`make docs-check` 绿。
- BUG-018 负向复验：字节改 `sva_baseline.json` floor 为 0/0 不追 changelog → report-check 第 8 项 FAIL；还原即绿。
- `python3 scripts/svacheck.py` 文件头看逐层盲区覆盖矩阵表。

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

