# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.2.2] 2026-07-10 DE 交付 packet_proc_core RTL（本地真跑通过）

**做了什么**
- 派全新 DE 实例（Sonnet 5）实现 `rtl/packet_proc_core.sv`：3 态 FSM（IDLE/PROCESS/DONE）、字计数器驱动 `mem_rd_addr_o`、第 0 拍同拍组合读提取头部（r6）、三类错误并行判定（length/type/chk）、payload sum/xor 逐拍累加（末拍含本拍贡献）、`res_pkt_len_o` 恒 = Byte0[5:0]（BUG-P2/r9）、读拍钳位 [1,8]（BUG-P1/r8）。逐条对照 design-prompt 无新增对外可见行为。
- 新增 9 条内部不变量断言（FSM 合法编码、busy/done 互斥、mem_rd_en_o 仅 PROCESS 拍、读拍计数边界、PROCESS 忽略 start、PROCESS 期间输出保持清零、algo_mode=0 时 chk_error 恒 0、DONE 态 format_ok 一致性）。
- `sim/flist/rtl.f` 按文件自身约定取消注释纳入编译（模块尚未接入 tb_top，仍是独立 top 编译自检，不影响现有仿真）。
- 本地 VM 真跑：`make -C sim compile` 0 error/0 warning；`make -C sim lint` 判定范围内新增 9 条 `Lint-[SVA-DIU]`（与已批准的 #1/#2 同类同因，`disable iff` 屏蔽复位期断言的标准写法），登记 `doc/lint-waivers.md` 豁免 #8（登记人=DE，待 rev 复核）；`make smoke` 复跑两次均 PASS，无回归。orch 抽查 RTL 逻辑（读拍钳位边界、pkt_len=0/>63 两个裁决角点、清零/累加时序）与 design-prompt/spec 对照未见矛盾。

**没做什么**
- 未派 DV：本轮只到 RTL 交付，M2-01~06 场景尚未落地，testplan 仍是 🔲。
- lint 豁免 #8 未经 rev 复核，不构成正式豁免。
- 模块未接入 `tb_top.sv`（仍连 `m3_stub_if`），接入属 DV/集成职责，design-prompt"明确不做"已排除。
- "配置取样点"（algo_mode/type_mask/exp_pkt_len 帧中改写时取样行为）仍未登记/未提案，DE 自认输入取当拍活值，未做特殊处理；不阻塞当前 M2-01~06 场景。

**下一步**
- 派 rev 复核 lint 豁免 #8（可与后续 DV 阶段的门禁合并，或单独一轮）。
- 派全新 DV 实例：输入 = spec §7/§9/§10 相关章节 + `doc/spec.md` §2.3 端口表 + testplan M2-01~06，不接收 DE 推理过程；建场景 + 接口 SVA，需先建立 M2 独立 TB 或替换 `m3_stub_if` 桩驱动才能跑通。
- DV 编 checker 前先处理"配置取样点"未决项（登记 bugs.md 或 arch 出提案）。

**如何验证**
- `cat rtl/packet_proc_core.sv`；`grep -n "^| 8" doc/lint-waivers.md` 确认豁免 #8 待复核。
- 本地 VM：`make -C sim compile`（0 error/0 warning）、`make -C sim lint`（判定范围内仅 #1~#8 已登记告警）、`make smoke`（PASS）。
- `python3 scripts/docs.py --check` 通过。

## [0.2.1] 2026-07-10 M2 packet_proc_core design-prompt 交付 + rev 门禁通过 + spec r8/r9 落地

**做了什么**
- 派 arch 新实例（Fable 5）撰写 `doc/design-prompt/packet_proc_core.md`：spec §2.3/§7/§9/§10/§11.3 等章节逐条锚点、功能要求对应 testplan M2-01~M2-06、边界约束、内部断言建议、明确不做。撰写中发现两处 spec 空白，未擅自拍板，转成修改提案 P1/P2 交 rev 仲裁。
- 派 rev 新实例（Fable 5）做 design-prompt 门禁（spec 锚点核对+行为泄漏检查）+ 仲裁 P1/P2，书面记录 `doc/evidence/v0.2.0/rev-gate-packet_proc_core.md`：
  - **门禁：通过（有条件）**——无行为泄漏、无锚点失配、feature 分解无遗漏。
  - **P1 裁决**：§7.3 r5 读拍数公式 `min(ceil(pkt_len/4),8)` 在 pkt_len=0 时算出 0 拍，与"第 0 拍必然发生"矛盾；裁决补下界，钳位区间改为 [1,8]（`min(max(ceil(pkt_len/4),1),8)`），pkt_len=0 帧 PROCESS 仅第 0 拍即进 DONE。
  - **P2 裁决**：`res_pkt_len_o` 6-bit vs pkt_len 8-bit，非法大包长（>63）取值未定义；裁决恒 = Byte0[5:0]（低 6 位截断），不并入 r5 UNSPECIFIED 集合，pkt_len>63 时必伴 length_error=1，可验可比对。
- orch 落地两条裁决入 spec.md：新增修改记录 `r8`（P1，§7.3 读拍数下界）、`r9`（P2，§3.4/§2.3/§5.2 res_pkt_len 截断定义），`--pin-spec` 重新钉住；同步 `packet_proc_core.md` 两处受影响文字（P1 临时底线句、P2 待决句）改为引用 r8/r9，"已裁决歧义"补齐 BUG-P1/P2 两条，"未决"清空（仅剩非阻塞的配置取样点，待后续登记）；`doc/testplan.md` M2-02 期望列补充 [1,8] 区间与建议追加激励（pkt_len=0、pkt_len>63）。

**没做什么**
- 未派 DE：门禁虽通过但本轮未启动 RTL 实现，design-prompt 交付即停，等待下一轮派单。
- 遗留风险（非阻塞，rev 记录第五节指出）：配置取样点（algo_mode/type_mask/exp_pkt_len 帧中改写时的取样行为）无正式提案、bugs.md 未登记；当前 M2-01~06 场景不涉及，不阻塞派单，但需在 DV 编 checker 前补登记，避免 DE/DV 默认假设（寄存采样 vs 组合直通）不一致产生假 mismatch。
- testplan M2-02 只更新了期望描述文字，未新增激励用例条目（pkt_len=0/>63 是否单独开场景留给后续 DV 实例决定）。

**下一步**
- 派全新 DE 实例：输入 = `doc/design-prompt/packet_proc_core.md`（已过 rev 门禁）+ spec §7/§9/§2.3 相关章节，实现 packet_proc_core RTL。
- DE 交付后派全新 DV 实例建 M2-01~M2-06 场景 + 接口 SVA（不接收 DE 推理过程）。
- 责成后续 arch/orch 实例为"配置取样点"行为登记 bugs.md 或出正式提案，在 DV 编写相关 checker 前裁决。

**如何验证**
- `cat doc/design-prompt/packet_proc_core.md` 核对已裁决歧义节含 BUG-P1/r8、BUG-P2/r9，未决项清空。
- `cat doc/evidence/v0.2.0/rev-gate-packet_proc_core.md` 看门禁与仲裁全文。
- `grep -n "^| r[89]" doc/spec.md`；`grep -n "r8\|r9" doc/spec.md`（§7.3/§3.4/§2.3/§5.2 均已引注）；`python3 scripts/docs.py --check` 通过（含 spec pin 校验）。

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

