# PPA-Lite 答辩讲稿（defense.md）

> 面向 Lab4（spec §11.5）现场答辩：15 页提纲 + 9 步现场演示脚本 + 预期追问 Q&A。
> **本讲稿所有数字均可当场从 `doc/evidence/` 复现**；数字统一收敛到下方「数据基线」块，
> 由 `make report-sync` 机械注入、`make report-check` 守护，正文不逐处重抄。
> 讲者只讲叙事与判断，数字指着基线块念即可。

---

## 数据基线（本讲稿所有数字的唯一来源）

> 本块两张表由 `make report-sync` 机械注入（`report.py` 的 `readme-kpi` / `readme-milestones`
> 两个生成区），`make report-check` 校验其新鲜度——生成区一旦过期，CI 硬门禁即红。
> 正文一律「指向本块 / 指向 `doc/evidence/`」，**不在段落里重抄数字**（讲稿的手写数字应为零，
> 仅 spec 结构常量与 rev 裁决引用句例外）。
>
> - 字段级 provenance（40+ 字段，每个数字附出处文件 + 解析规则）：`python3 scripts/report.py --md data-baseline`（现算，不落盘）
> - 六类覆盖率分项 / 缺陷分类 / 断言实例展开等细粒度值：`python3 scripts/report.py --json`
> - 说明：`data-baseline` 是 `report.py --md` 的可读快照，当前**未接入可注入生成区**，故本块的机械守护由已接线的 `readme-kpi` + `readme-milestones` 两个生成区承担（覆盖全部头条数字，含 M2→M3 覆盖率回落）。

### 成果 KPI

<!-- GEN:readme-kpi -->
| 指标 | 数值 | 出处 |
| --- | --- | --- |
| 六类综合覆盖率 | 97.46% | `doc/evidence/v0.4.0/coverage-summary.md` |
| 最新回归通过 | 32/32 | `doc/evidence/v0.4.0/result_summary.txt, doc/evidence/v0.4.1/result_summary.txt` |
| testplan 场景 | 31 ✅ | `doc/testplan.md` |
| SVA 断言 | 49 条 | `rtl/ + tb/sva/` |
| RTL 代码 | 939 行 | `rtl/*.sv` |
| TB 代码 | 3514 行 | `tb/**/*.sv` |
| 缺陷闭环 | 18 条 | `doc/bugs.md + doc/bugs-archive.md` |
| lint 豁免 | 12 条 | `doc/lint-waivers.md + 归档` |
| rev 审查记录 | 13 份 | `doc/evidence/v*/rev-*.md + review*.md` |
| spec 修订 | 11 次 | `doc/spec.md` |
<!-- /GEN:readme-kpi -->

### 里程碑总账（含覆盖率爬坡与 M2→M3 回落、每 M 签核记录）

<!-- GEN:readme-milestones -->
| 里程碑 | Lab | 模块 | 场景 | 回归 | 六类综合 | 签核记录 |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Lab1 | apb_slave_if、packet_sram | 9/9 ✅ | 10/10 | N/A（M1 模块聚合域 (mod5+mod7)，该版本无 SCORE 行） | `doc/evidence/v0.1.6/rev-review-M1.md` |
| M2 | Lab2 | packet_proc_core | 7/7 ✅ | 17/17 | 86.16 | `doc/evidence/v0.2.3/review-m2-milestone.md` |
| M3 | Lab3 | ppa_top | 5/5 ✅ | 22/22 | 82.05 | `doc/evidence/v0.3.0/review-m3-milestone.md` |
| M4 | Lab4 | (全系统) | 10/10 ✅ | 32/32 | 97.46 | `doc/evidence/v0.4.1/review-m4-milestone.md` |
<!-- /GEN:readme-milestones -->

---

## 页 1 · 封面

- **项目**：PPA-Lite —— APB 包处理加速器（精简版）。软件经 APB 写入一帧数据包、配置 CSR 触发硬件，硬件完成包头解析与格式合法性检查，经状态位/中断回告，软件再经 APB 读回结果（spec §1.5）。
- **版本 / 里程碑**：版本见 `version.json`（`report.py --json project.version`），里程碑见数据基线里程碑表；M1–M4（= Lab1–Lab4）全部收官，当前处于 M5 收尾（诚实性排查 + 成果展示层）。
- **规模速览**：RTL / TB 行数、TB:RTL 比、回归通过、六类覆盖率 SCORE、SVA 条数、缺陷闭环数、rev 审查记录——**全部见数据基线**，不在此重述。
- **一句话承诺**：本次答辩所讲的每一个数字，都能当场用 `python3 scripts/report.py` 现算、或在 `doc/evidence/<版本>/` 找到含 seed 的复现命令与仿真 log 摘录。**没有 log 就没有 ✅**。

## 页 2 · 需求与约束：spec 是唯一事实源

- **单一事实源**：`doc/spec.md`（行数见基线 `project.spec_lines`），已用 sha256 钉住（`doc/spec.sha256`），`report.py --check`/`docs.py --check` 每次现算比对，被悄改即门禁红。
- **修改路径唯一**：任何角色发现歧义/需要新行为 → 登记 `bugs.md` 或 arch 出提案 → **rev 仲裁** → orch 应用 + `--pin-spec`。禁止任何实例直改 spec 正文。这条纪律把"改规格"从随手动作变成了带审计链的动作。
- **修订账**：spec 共 **11 次修订**，其中 **8 次为闭环修订 = 6 次源自 `bugs.md` 缺陷裁决 + 2 次源自 rev 门禁附带仲裁**（另 3 次是入库/适配基线，非缺陷驱动）。**不要笼统称"8 个 BUG"**——两条门禁仲裁（r8 读拍钳位 [1,8]、r9 res_pkt_len 6-bit 截断）无 BUG-ID，且发生在 RTL 写出来之前。精确拆分见 `report.py --json` 的 `project.spec_closed_loop_via_bugs` / `via_gate`。
- **§0 适配表 8 条偏离**（原 spec 8 周课程 → 本仓库工业迭代）：里程碑代版本、选做按必做、Questa→VCS/Verdi、角色轮换→实例隔离、现场核验→证据链、自建 Makefile、**新增 SVA（适配 7）**、**新增 lint（适配 8）**。这张"原要求 vs 本仓库实现"对照是整场答辩的叙事主线。

## 页 3 · 系统架构

- **顶层 `ppa_top` 是纯连线**（无状态逻辑）：分发时钟/复位，例化三个子模块——`apb_slave_if`（APB 从机 + CSR）、`packet_sram`（8×32bit 双端口）、`packet_proc_core`（3 态 FSM 处理核）。模块数/行数/端口数/内部断言数见基线与 `report.py --json design.modules`。
- **顶层唯一对外中断引脚是 `irq_o`**；`done_o` 是 M3→M1 的**内部**信号（spec r11 裁决：框图不再把 `done_o` 画成顶层引脚，以 §2.3 端口表为唯一权威）。
- **命名澄清（必讲，防评委混淆）**：spec 正文里的 **M1/M2/M3 是"模块实例编号"**（apb_slave_if / packet_sram / packet_proc_core 等在端口表中的分组），而本仓库的 **M1–M4 是"里程碑编号"**（= Lab1–Lab4）。两套 M 编号不是一回事。

## 页 4 · 设计要点 · APB 从机与 CSR

- **两段式 APB 3.0 从机**，`PREADY` 固定为 1（零等待），地址译码分发到 CSR 与 PKT_MEM 窗口（spec §4.1 §4.2）。
- **CSR 寄存器组 11 个**（CTRL/CFG/STATUS/IRQ_EN/IRQ_STA/PKT_LEN_EXP/RES_*/ERR_FLAG，spec §5.2）；地址常量在 `tb/uvm/env/ppa_reg_defs.sv` 单点定义，别处禁止硬编码。
- **PKT_MEM 窗口 0x040–0x05C**：M1 侧只有写通路；读回按 r7 裁决统一返回占位 `32'h0`、`PSLVERR=0`（M1 无 SRAM 读回通路，读端口专供 M3）。
- **PSLVERR 统一错误响应**（保留地址/非法访问，spec §8.3）；**IRQ 为 RW1C**（写 1 清除，spec §8.2）；`irq_o` 组合输出。
- 该模块 8 条 DE 内部不变量断言（`report.py --json design.modules`），全部登记 lint 豁免并经 rev 复核。

## 页 5 · 设计要点 · 处理核 FSM 与错误判定

- **3 态 FSM**：`ST_IDLE → ST_PROCESS → ST_DONE`（spec §7）。`busy`/`done` 输出约定见 §7.4/§8.1。
- **第 0 拍头部解析**：同拍组合读 Word0，提取 len/type/flags/hdr_chk 并起读地址递增（r6 裁决：packet_sram 读端口为同拍组合读，无寄存延迟）。
- **读拍数钳位 [1,8]**（r8 门禁裁决）：`min(max(ceil(pkt_len/4),1),8)`；`pkt_len=0` 时 PROCESS 仅第 0 拍即进 DONE。
- **三类错误并行判定 + 优先级**（spec §9）：length_error / type_error / chk_error 并行算出，`format_ok` 汇总；越界包（`pkt_len>63`）必伴 `length_error=1`（r9）。
- **res 截断口径**：`res_pkt_len = Byte0[5:0]`（6-bit 截断，r9）；payload sum/XOR 为 **8-bit 截断**（spec §3.4 §7.3）。非法包长时 sum/xor 为 UNSPECIFIED、验证不比对（r5）。
- **端序**：包头按 spec 附录 A/B 的**大端**字节序解析——这正是 BUG-009 的战场（见页 13）。

## 页 6 · 验证架构

- **UVM 组件树**：`ppa_base_test` → env（apb_agent + core_agent + scoreboard + cov）。TB 文件数/行数、TB:RTL 比见基线。
- **双 agent**：apb_agent（总线侧）+ core_agent（处理核侧）。
- **三条并存通路 + 实例路径隔离**：M1 单元通路、M2 core 单元通路、M3 集成通路在同一 `tb_top` 内并存、互不相连，靠 `uvm_config_db` 的实例路径作用域隔离（对应 BUG-013 复验里逐条核实的 tb_top 三通路例化）。
- **行为 SRAM 参考模型**：期望值由**唯一参考模型** `predict()`（`tb/uvm/core_agent/ppa_core_seq_item.sv`）从 spec 逐条推导——原双份 `ppa_ref_model.sv` 死代码已按 BUG-016 删除，消除"两份实现静默漂移"风险。

## 页 7 · 验证策略 · 金字塔

- **SVA 分侧**（spec §0 适配 7）：DE 写 **RTL 内部不变量断言**（`rtl/`），DV 写 **接口/协议/时序契约断言**（`tb/sva/`，`bind` 挂接，每条 property 注明 spec 章节号）。两侧条数见基线 `SVA 断言` 与 `report.py --json verification.sva`（DE/DV 分侧）。
- **checker 只从 spec 推导**：DV 的 checker/SVA 禁止照抄 RTL 行为，事实源锚定 spec 章节号（第 0 章适配表优先）。这是切断"DE/DV 共模误读"的关键——但隔离切不断"同模型对同一 spec 的共同误读"，所以还要歧义前置登记 + rev 锚定 spec 审查（见页 14）。
- **层次**：SVA 断言 → 回归条目（TEST×SEED）→ testplan 场景 → UVM 场景测试类，逐层收敛。
- **注意 49 / 88 / 91 三个断言口径的区别**（页 9 详述）：49 = 源码 `assert property` 语句数（DE 32 + DV 17）；88 = 例化展开后的实例数（覆盖率测量域）；91 = 88 + 3 条 uvm_pkg 库立即断言。

## 页 8 · §11.5-必1 一键回归 100%

> 评分对应：**spec §11.5 必做 1**（助教当场执行 `make regress`，全部 PASS）

- **一键回归**：`make regress` 走 `regress.list` 全部条目（固定 SEED），结果见基线里程碑表"回归"列与 `doc/evidence/v0.4.1/result_summary.txt`。
- **Lab1–3 九个必做场景各 ≥1 条对应 testcase**（spec §11.2/§11.3/§11.4 必做）：
  | 必做场景 | 对应 testcase | testplan 行 |
  | --- | --- | --- |
  | Lab1-必1/2/3 | ppa_m1_01/02/03_test | M1-01/02/03 |
  | Lab2-必1/2/3 | ppa_m2_01/02/03_test | M2-01/02/03 |
  | Lab3-必1/2/3 | ppa_m3_01/02/03_test | M3-01/02/03 |
- **regress.list ⇄ testplan 双向对应**：`report.py --check` 第 3 项机械校验"regress.list 条目数 == 最新回归摘要结果行数"。唯一例外是 `ppa_smoke_test`——它在 regress.list 但不是 testplan 场景行，已在 testplan M4-01/M4-03 注里显式声明（不是孤儿）。

## 页 9 · §11.5-必2 覆盖率等级验收

> 评分对应：**spec §11.5 必做 2**（覆盖率等级；原要求 Questa GUI 现场核验、不接受截图 → 本仓库适配 5 改为 `doc/evidence/` 证据链 + 现场 urg）

- **口径六类**（spec §0 适配 7）：line + cond + fsm + tgl + branch + **assert**（原 spec 五类，本仓库 +assert），门槛 90 合格 / 95 优良 / 100 优秀。
- **等级与分项**：最新 SCORE 与六类分项值见 `doc/evidence/v0.4.0/coverage-summary.md`（经 `report.py --check` 第 2/4 项与回归摘要机械交叉校验）与 `report.py --json results.coverage.history`。**六类全部 ≥90**。
- **测量域口径**：`urg` hierarchy 的 `tb_top` 子树（不是模块聚合域）。**M1 那个点口径不同**（M1 模块聚合域 mod5+mod7、无 SCORE 行、FSM 结构性 N/A）→ 基线里程碑表已标"口径不同"，画爬坡曲线时单独 marker、不入折线、不补 0。
- **爬坡曲线必须如实讲 M2→M3 回落**：见基线里程碑表 M2→M3 一列——SCORE **不升反降**（M3 集成路径引入新的未激励代码，非回归劣化），M4 补齐缺口后回到最高水位。这条下降是全场最强的可信度背书，藏起来就毁了整份材料。
- **ASSERT 覆盖率口径（rev 裁决原文，直接引用，见 `doc/evidence/v0.5.3/review-bug-013-014.md` §C）**：
  > 「PPA-Lite 域内共 88 条断言实例（源码 49 条 `assert property` 按模块例化展开），32 条回归全部触发、零失败，ASSERT 覆盖率 100%（88/88，urg 合并 32 次仿真 + 复位独立库）；VCS 汇总行 `91 assertions, 88 with attempts` 中的差额 3 条全部是 UVM-1.2 库的立即断言，位于测量域（tb_top 子树）之外。」
  - 红线：**可以**写"ASSERT 100%"，但**必须**同时给分母 **88** 与测量域 `tb_top`；单写"91 条 100%"或"49 条 100%"都是错的。

## 页 10 · §11.5-必3 testplan 文档

> 评分对应：**spec §11.5 必做 3**（testplan 表格：testcase 名称 / 对应检查点 / 输入摘要 / 期望输出 / 结果）

- **文档**：`doc/testplan.md`，场景行数/通过数见基线 `testplan 场景`。状态位 ✅/❌/⚠️/🔲，✅ 及证据列由 `evidence.py` 机械回填（手写证据会被 `docs.py --check` 拦）。
- **spec 要求字段 → 本表列口径映射**：
  | spec §11.5 要求字段 | 本 testplan 列 |
  | --- | --- |
  | testcase 名称 | 场景 ID + 复现命令（含 TEST） |
  | 对应检查点 | spec 依据列（章节号） |
  | 输入摘要 / 期望输出 | 场景描述 + checker 落点 |
  | 结果（PASS/FAIL） | 状态位 + 证据列（log 路径） |
- 口径注（testplan 表头第 7 行）已说明每列与 spec 字段的对应，避免"字段名不一致"被追问。

## 页 11 · §11.5-选4 覆盖率过滤合规

> 评分对应：**spec §11.5 选做 4**（覆盖率过滤登记；原要求 Excel 登记表 → 本仓库适配 5 改为 markdown 表）

- **登记文件**：`doc/evidence/v0.4.0/coverage-exclude-registration.md`，逐条列过滤对象 / 行数 / 原因 / 结论。
- **两组过滤，逐条给 spec 依据**：A 组 = 域外（测量域 `tb_top` 之外，如 uvm_pkg 库断言）；B 组 = 结构不可达（设计上无法激励的代码/位）。
- **反造假红线**：**可用激励覆盖却排除的，一律禁止**。rev 逐位复核未覆盖位，确认排除项都属"域外"或"结构不可达"，不是"凑数删难点"。
- **诚实点**：TOGGLE 是六类中水位最低、险过 90 门槛的一类，其结构性过滤（PRDATA 高位 + PREADY）若因设计变更失效需重估——精确余量见 `report.html` 诚实专栏脚注（不在此重抄数字）。

## 页 12 · §11.5-选5 选做功能回归

> 评分对应：**spec §11.5 选做 5**（Lab1–3 选做项纳入回归并全部 PASS，提供选做场景 testplan 条目）

- **选做项全部纳入回归且 PASS**，逐条给 testplan 行 ID：
  | Lab | 选做场景 | testplan 行 |
  | --- | --- | --- |
  | Lab1 | PSLVERR 统一响应 / IRQ 寄存器组 | M1-04 / M1-05 |
  | Lab2 | 类型合法性+type_mask / hdr_chk 校验旁路 | M2-04 / M2-05 |
  | Lab3 | busy 写保护 / 中断路径闭环 | M3-04 / M3-05 |
- 汇总登记见 testplan M4-05（选做功能回归）与 `doc/evidence/v0.4.1/M4-05.log`。本仓库按 §0 适配 2"选做按必做对待"，这些场景计入 M 完成判据。

## 页 13 · 缺陷闭环 · BUG-009 深潜

- **全部缺陷中唯一判为"真 RTL 缺陷"的一条**（缺陷分类见 `report.py --json results.bugs.by_kind`，rtl 类仅此 1 条）：`packet_proc_core` 包头字节内端序取**小端**，而 spec 附录 A/B 数值示例钉的是**大端**。
- **闭环链路（关单人 ≠ 修复人）**：
  1. DV 发现 M2 场景全 FAIL（`make run TEST=ppa_m2_01_test SEED=1`）→ 登记 `doc/bugs/BUG-009.md`；
  2. rev 仲裁（`doc/evidence/v0.2.3/review-bug-009-arbitration.md`）：以 spec 附录大端为准，判 **RTL bug**，归 DE 改 bit 切片；
  3. DE 首修（commit `9c28fea`）→ **DV 复验驳回**（漏了头字段的锁存路径端序）；
  4. DE 二修（commit `b8a1890`，补齐锁存端序）→ DV 复跑关单。
- **为什么只有 1 个真 RTL bug ≠ 验证太弱**：18 条缺陷里 6 条是 spec 歧义——在传统流程里它们会变成 RTL bug，被前置到仲裁阶段消灭；且 r8/r9 两条发生在 RTL 写出来之前。BUG-009 是反例：同样是争议，rev 判 RTL 错，DE 改了两轮才过。

## 页 14 · 方法论 · 证据链与角色隔离

- **没有 log 就没有 ✅**：证据一律 `make evidence` 机械生成（校验 UVM_ERROR/FATAL=0、抽摘录、写含 TEST+SEED 复现命令的 `.log`、回填 testplan/bugs）。**禁止手写证据文件**。
- **硬门禁**：`docs.py --check`（doc/ 一致性）+ `report.py --check`（七项，含 spec sha256 现算、覆盖率⇄回归交叉校验、生成区新鲜度、源码注释⇄交付状态）。CI 硬门禁 + 本地 `make regress` 100% PASS 是里程碑必要条件。
- **实例隔离及其边界**：DE/DV/arch/rev 同模块必不同实例、交付即终止；任务卡禁止粘贴其他实例的推理过程。**但隔离切不断"同模型对同一 spec 的共同误读"**——所以还需要：① 歧义前置登记（bugs.md）；② rev 锚定 spec 的审查。这条"边界"要主动讲，比"我们流程很严谨"的自夸有说服力。
- **人工审阅不可替代**：这轮诚实性排查（BUG-012~018）的起点，是**用户人工翻代码问了一句"这个仓库真的做完了吗"**——文档说做完了、四次里程碑签核全过、脚本门禁全绿，而一个人看了两眼源码就问出了正确的问题。机械守卫有价值边界，人工审阅补的正是那个边界。

## 页 15 · 诚实边界与后续

> 本页与 `doc/report.html` 的**诚实专栏（9 条）**共享同一套事实，不另造清单；数字与细节看 `report.html` 详版。

**这个环境没有做什么（现状 → 替代 → 代价，每条给文件路径）：**

1. **记分板非集中式比对**：`ppa_scoreboard.sv` 只做读写计数 → 真正比对分散在 `chk_eq` 自检序列与 core-agent 的 `predict()` 参考模型 → 跨组件追溯成本高。
2. **无 RAL / uvm_reg** → `ppa_reg_defs.sv` 地址常量单点定义 → 无自动 mirror/predictor。
3. **无 virtual sequence / p_sequencer** → `ppa_base_test.main_seq()` 模板方法 → 多 agent 并发编排能力弱。
4. **无 factory override** → 场景差异靠独立 test 类 → test 类数量线性增长。
5. **功能覆盖率只有 1 个 covergroup**（3 coverpoint + 1 cross）→ 验收口径是"代码+断言六类"、功能覆盖率不在判据内 → **SCORE 是代码域水位，不代表功能空间覆盖**（最易被追问）。
6. **约束随机轻量**（无独立 constraint 块，靠 `$urandom` + 多 seed）→ 随机空间靠 seed 数量 → 不是工业级 CRV。

**收官后诚实性排查暴露的三条（正面写——证明审查机制收官后仍在工作）：**

7. **断言曾经不拦回归（BUG-014，两段式）**：过去 4 个里程碑期间，49 条断言对回归的拦截力**实际为 0**（动作块一律 `else $error`，回归只看 UVM_ERROR/FATAL，`$error` 不改退出码）。**已修**（`-assert verbose` 原生计数 + 引擎行双层，fail-closed，单点在 `scripts/svacheck.py`）——**现在断言失败会让回归变红**（有负向实验背书）。**但必须同时讲**：历史清白是**事后复算**出来的（定位证据 commit → `git archive` 重建源码树 → 按 TEST+SEED 重跑，带阳性/保真度对照），**不是当时流程保障的**。
8. **注释腐烂与守卫盲区（BUG-013）**：多处源码注释停在 0.1.x 期，一路带到收官；根因是 `docs.py --check` 只守 `doc/`、不覆盖源码注释。已补 `report.py --check` 第 7 项守卫，但守卫**精度优先、召回窄**——"通过"只等于"无这几种字面形态的过期承诺"，**不等于"仓库无过期承诺"**。
9. **lint 曾漏登（BUG-012）**：`make lint` 实测处数一度超过登记覆盖，是 rev 顺手实跑才发现。**已补齐并全部经 rev 复核**（处数为登记时刻计数，见基线 `lint 豁免`）。**边界**：`make lint` 至今 `exit 1`、本轮只修 3 处其余登记豁免——**不写"lint 干净/清零/全部修复"**。

**两条历史不一致（放注脚）：**
- M1 签核文件名 `rev-review-M1.md` 早于命名规范，BUG-011 修复后的 `docs.py` glob 对它不匹配（内容实质完整，129 行）。**处置：不改历史证据文件名**（证据不可变性优先于表面整洁），在 `doc/evidence/README.md` 补命名沿革说明。"我们为什么不改"本身是一个原则性判断。
- TOGGLE 险过 90 门槛；结构性过滤若因设计变更失效需重估。

**后续方向**：补集中式 scoreboard / RAL、引入 constraint 随机与功能覆盖率、把 `svacheck` 的期望断言实例数落成基线（堵 BUG-018）、把 `data-baseline` 接入可注入生成区。

---

# 现场演示脚本（9 步：命令 · 讲什么 · 兜底）

> 环境探测优先：任何一步前先 `command -v vcs`。探测到即真跑；探测不到（远程容器）只做只读展示，结论以本地 log 为准。
> 全程**不现场改文件污染工作区**、**不做任何 git 写操作**。

| 步 | 命令 | 讲什么 / 对应验收 | 兜底 |
| --- | --- | --- | --- |
| 0 | `command -v vcs` + `git log --oneline -5` | 环境与提交历史的真实性——不是 PPT，是活的仓库 | — |
| 1 | `make handover` | 记忆系统全部**现算**（版本/状态/交接块/testplan 统计/未关闭缺陷），不靠通读 | — |
| 2 | `make regress` | **§11.5-必1**"助教当场执行"，全部 PASS | 超时则只跑 `make smoke`，展示归档 `result_summary.txt`，**如实说明这是提前跑的** |
| 3 | `make cov` → 打开 urg，展开 hierarchy 定位 `tb_top` 行 | **§11.5-必2**（原要求 GUI 现场核验、不接受截图；本仓库以现场 urg + 证据链对齐） | 无 GUI 则开 `urgReport/hierarchy.html` |
| 4 | `make covreset` + 一句话 | FSM 复位弧需独立 vdb 合并的工具坑（VCS O-2018 共享 `cm_dir` 会丢弃异步复位弧）——不是覆盖不到，是工具限制 | — |
| 5 | 打开 `doc/testplan.md` | **§11.5-必3** 字段口径注 + 状态位 + 证据列 | — |
| 6 | 打开 `doc/evidence/v0.4.0/coverage-exclude-registration.md` | **§11.5-选4** 两组过滤逐条 spec 依据 + 反造假红线 | — |
| 7 | 打开 `doc/evidence/v0.2.3/review-bug-009-arbitration.md` + `doc/bugs/BUG-009.md` | 两轮闭环、**关单人 ≠ 修复人**（首修被 DV 驳回、二修才过） | — |
| 8 | `python3 scripts/docs.py --check`，口头说明"把某个 ✅ 的证据路径改错会被当场拦下" | 门禁真实性。**新素材**：门禁体系自身经历了 **BUG-011/014/017/018 四轮"被攻破→加固"**，最近两轮（017/018）是 rev **主动构造绕过向量的红队自测**——守卫不是摆设，是被反复攻击后加厚的 | **不现场改文件**；改为展示 BUG-011 修复 commit `5a58c64`——"门禁自己也出过 bug（里程碑签核检查曾恒真），被 DV 发现并关单" |
| 9 | 浏览器打开 `doc/report.html` | 全景收尾，指出页脚"数字由 `report.py` 机械注入、生成区禁止手改" | — |

---

# 预期追问 Q&A（≥16 条）

> 每条给「承认什么 + 替代方案 + 代价」，不含糊带过。数字指向数据基线 / `report.html` / `doc/evidence/`。

**Q1 · scoreboard 只有几十行、只做读写计数，比对到底在哪？**
承认 `ppa_scoreboard.sv` 不是集中式记分板（CSR 镜像集中比对是标注的 TODO）。真正比对分散在两处：自检序列的 `chk_eq`（`tb/` 内多处调用）与 core-agent driver 内建的**唯一参考模型** `predict()`（`tb/uvm/core_agent/ppa_core_seq_item.sv`，从 spec 逐条推导）。原来另有一份 `ppa_ref_model.sv` 是死代码，已按 BUG-016 删除以消除双份实现漂移。代价：检查逻辑分散、跨组件追溯成本高。

**Q2 · 没有 RAL / `uvm_reg`，寄存器验证怎么保证？为什么不用？**
承认无 RAL。地址/常量在 `ppa_reg_defs.sv` package 单点定义，寄存器行为由针对性场景 + SVA 覆盖。不用的原因是本设计只有 11 个 CSR、无镜像预测需求，RAL 的 mirror/predictor 收益低于其建模成本。代价：无自动 mirror/predictor，寄存器建模靠手写，规模一旦扩大会吃力。

**Q3 · 没有 virtual sequence / p_sequencer，多 agent 怎么编排？**
承认没有。多 agent 激励由 `ppa_base_test` 的模板方法 `main_seq()` 组织。代价：多 agent 并发编排能力弱，复杂并发场景表达力受限——本项目的场景并发度低，尚未触到这个上限。

**Q4 · 功能覆盖率只有 1 个 covergroup、3 个 coverpoint，SCORE 是不是虚高？**
关键澄清：验收口径是 spec §0 适配 7 的**代码 + 断言六类**，功能覆盖率**不在判据内**。所以 SCORE 是**代码域水位，不代表功能空间覆盖**——这是本环境最该被追问、也最该主动交代的一条（`report.html` 诚实专栏第 5 条用警示底色标出）。功能覆盖率单薄是真实短板，不拿代码覆盖率的高分掩盖它。

**Q5 · 随机化只有 `$urandom` + 多 seed、没有 constraint 块，算约束随机吗？**
不算工业级 CRV，如实承认。随机空间靠 seed 数量（回归条目见基线，含多 seed 追加）而非约束建模。代价：随机深度受 seed 数量限制，约束驱动的定向随机能力缺失。后续方向就是补 constraint + 功能覆盖率闭环。

**Q6 · TOGGLE 只高于门槛零点几个点，过滤 PRDATA 高位是不是凑数？**
承认 TOGGLE 是六类里余量最小的一类。过滤对象（PRDATA 高位 + PREADY）在 `coverage-exclude-registration.md` 逐条登记了"结构不可达"依据、经 rev 逐位复核。反造假红线是"可用激励覆盖却排除一律禁止"。代价/边界：若设计变更使这些位变得可激励，过滤即失效、须重估——这条写进了诚实专栏脚注。

**Q7 · 测量域选 `tb_top` 子树，是不是自己挑了个有利的域？**
`tb_top` 是包含全部被测 RTL 例化的顶层作用域，是自然的完整测量域，不是挑出来的有利子集。反证：**M1 那个点用的是模块聚合域（mod5+mod7），和后三点口径不同**，我们没有把它硬拉进同一条折线，而是单独 marker、注明"口径不同、不可同轴比较"——如果想美化，恰恰应该藏掉这个差异。

**Q8 · 只有 1 个真 RTL bug，是验证太弱还是设计太简单？**
都不是。18 条缺陷里 6 条是 spec 歧义——传统流程里它们会以 RTL bug 形式爆发，本项目把它们前置到仲裁阶段消灭了（r8/r9 甚至发生在 RTL 写出来之前）。BUG-009 是反例：同样是争议，rev 判 RTL 错，DE 改了两轮（首修被 DV 驳回）。"真 RTL bug 少"是"歧义前置"的结果，不是"没验出来"。

**Q9 · 6 个 spec 歧义都以改 spec 收场，是不是在改规格迁就 RTL？**
不是迁就 RTL，是消除歧义。每次修改都走"登记 → rev 仲裁 → orch 应用 + pin"，有审计链；且**8 次闭环修订里 2 次（r8/r9）在 RTL 写出来之前就裁决了**，谈不上迁就已有实现。反例仍是 BUG-009：rev 判 RTL 错、改的是 RTL 不是 spec。改 spec 的都是"原文本身没定义清楚"的地方。

**Q10 · AI agent 写的，怎么保证不是自问自答？**
三道锁：① **实例隔离**——同模块 DE 与 DV、arch 与 rev 必为不同实例，交付即终止，任务卡禁止粘贴彼此推理；② **事实源锚定**——DV 的 checker 只准从 spec 推导、不许照抄 RTL；③ **机械门禁 + 人工审阅**——没有 log 就没有 ✅，且这轮排查正是**用户人工**翻代码触发的。但要承认边界：隔离切不断"同模型对同一 spec 的共同误读"，所以歧义前置登记 + rev 锚定 spec 审查同样是这套防线的一部分。

**Q11 · FSM 复位弧要另出 vdb 合并，是不是在掩盖覆盖不到？**
不是。VCS O-2018 共享 `cm_dir` 时会丢弃异步复位弧，这是**工具限制**，不是覆盖不到。处理办法是 `make covreset` 用独立 vdb 单独收复位弧，再 urg 合并——`make cov` 现场就能展开看到 FSM 100%。掩盖的做法恰恰相反：那会是"不提复位弧、让 FSM 停在 60%"。

**Q12 · M1 签核文件名不合规、加上 BUG-011 让门禁恒真——M1 的签核到底算不算数？**
分两件事，都如实讲。**签核实质成立**：`rev-review-M1.md` 有 129 行完整记录，含审查人、被审 HEAD、三条硬条件逐条验算。**机械检测确实漏了**：BUG-011 修复后的 glob 与旧命名不匹配（已 CLOSED，commit `5a58c64`）。**我们选择不改历史证据文件名**——证据文件的不可变性优先于表面整洁——改为在 `doc/evidence/README.md` 补命名沿革说明。"选择不改"本身是个原则性判断，不是疏忽。

**Q13 · ASSERT 100% 的口径是什么？**
用 rev 裁决原文（`doc/evidence/v0.5.3/review-bug-013-014.md` §C）：「PPA-Lite 域内共 88 条断言实例（源码 49 条 `assert property` 按模块例化展开），32 条回归全部触发、零失败，ASSERT 覆盖率 100%（88/88，urg 合并 32 次仿真 + 复位独立库）；VCS 汇总行 `91 assertions, 88 with attempts` 中的差额 3 条全部是 UVM-1.2 库的立即断言，位于测量域（tb_top 子树）之外。」红线：写"ASSERT 100%"必须同时给分母 **88** 与测量域 `tb_top`；差额 3 条恒定（跨 4 个里程碑差值始终为 3），是度量定义差异（立即断言不计入并发 attempts），不是域内有断言没触发。

**Q14 · `make lint` 现在还报错？为什么不用 SpyGlass？**
如实说：`make lint` 至今 `exit 1`（VCS `+lint`）。本轮只修了 3 处，其余是登记豁免（见基线 `lint 豁免`），全部经 rev 复核。**不说"lint 干净/清零"**。不用 SpyGlass 是因为本地 VM 未部署——spec §0 适配 8 已写明"SpyGlass 部署后换后端、入口 `make lint` 不变"。代价：当前 lint 后端较弱、豁免依赖人工登记。

**Q15 · rev 审查时实跑 lint 发现处告警从未登记（BUG-012），你们的 lint 门禁是不是形同虚设？**
承认当时 lint 门禁**依赖人工自觉、缺机械对账**，这是已知短板。诚实点在于：这个漏登是**项目自己的 rev 在审查别的事时顺手实跑 lint 发现的**，不是外部指出的——审查机制在工作。**已闭环**（BUG-012 CLOSED）：现在告警全部登记、12 条豁免全部经 rev 复核批准（见基线）。仍不写"lint 干净"，因为 `make lint` 还 `exit 1`。

**Q16（必答）· 你们的断言检查器 `svacheck` 自己被绕过了四次（BUG-014 原始盲区 + 017 三向量 + 018 两向量），怎么还敢说证据链可信？**
正面回答：**恰恰因为它被反复攻击、每次都被堵。** 四轮绕过——BUG-014（原始盲区：断言失败不改退出码）、BUG-017（三条向量：不校验 attempts/总数、`::` 层次名失明、多 Summary 取末条）、BUG-018（两条向量：基线文件无守卫、真实失败行喂层 1 不命中）——**每一轮都是项目自己的 rev 红队主动构造的，不是外部指出的**；发现即登记缺陷、闭环修复 + 负向复验（构造能骗过判定的样例、修完再证明骗不过了）。"守卫被攻破 → 堵上 → 再攻"这个循环本身，就是证据链可信度的来源——一个从没被人认真攻击过的门禁，才最不可信。**同时如实承认**：BUG-018 的两条向量当前不可利用（故未阻断 BUG-017 关单），但状态**以 `doc/bugs.md` 实时状态为准**（写作时 OPEN，可能已被关单实例复验闭环）。

**Q17 · 你们说"断言失败会让回归变红"，可它过去真拦住过吗？**
两段式回答，一句都不能少。**现在**：断言失败会让回归变红，有 BUG-014 修复的负向实验背书（`-assert verbose` 原生计数 + 引擎行双层，fail-closed，单点在 `svacheck.py`）。**过去**：4 个里程碑期间 49 条断言对回归的拦截力**实际为 0**——动作块一律 `else $error`，而回归只看 UVM_ERROR/FATAL，实测同一份 log 断言真失败却判 PASS 还能登成 ✅。**历史清白是事后复算出来的**（定位证据 commit → `git archive` 重建源码树 → 按 TEST+SEED 重跑，带阳性对照与保真度对照），**不是当时流程保障的**。

**Q18 · 覆盖率证据有几份、都交叉校验过吗？回扫了多少份 log？**
如实纠偏，不夸大。覆盖率摘录共 4 份归档，其中**参与"摘录 N/N PASS ⇄ 回归摘要"机械交叉校验的是 3 份**——v0.1.7 因首测/复测两个声明并存被降级为说明（`report.py --check` 第 2 项会打这条降级 warn）。断言历史回扫的**具体份数不写进对外材料**（回扫清单未落盘、不可审计），我们用跨 M1/M2/M3/M4 的 5 份抽样重放独立支撑"0 漏判"这个结论，而不是引用一个不可复核的总数。

**Q19 · 这套材料里的数字，会不会和真值源脱节？**
不会静默脱节。`report.html` / `README.md` / 本讲稿的数字都进 `report.py` 的生成区或 provenance，`make report-check` 守新鲜度——生成区一旦过期，CI 硬门禁即红。讲稿正文一律"指向数据基线块"、不逐处重抄。唯一手写的数字是 spec 结构常量（如 CSR 数、FSM 态数、地址窗口）与 rev 裁决引用句（如 ASSERT 88/88），其余全部现算。
