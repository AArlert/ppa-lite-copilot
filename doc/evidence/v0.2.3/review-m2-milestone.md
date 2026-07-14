# M2 里程碑签核审查记录

- 版本：0.2.3（version.json 现值）
- 审查人：rev（全新实例，未参与本次 M2 的 DE/DV 工作，未做过 BUG-009 仲裁）
- 日期：2026-07-14
- 判据出处：CLAUDE.md §4.1「M 完成判据（三条硬条件）」
- 结论：**通过（签核）**。三条硬条件均独立核验为真；覆盖率缺口经裁定不属 M2 判据、不卡关；未见证据造假迹象。遗留风险见文末，须携入 M3/M4，不阻塞本次签核。

---

## 判据①：该 M 的 RTL 全部就绪且 feature-matrix 关联场景全 ✅

**结论：满足。**

- `make handover` / `make next`（本人实跑，未采信转述）：`make next` 输出「M2 三条硬条件已齐 → make bump-minor + git tag v0.3.0 进入下一 M」；feature-matrix 现算 M2 RTL 交付 4/4、验证 ✅4/4；testplan 现算 M2 ✅7/7、无 ❌/⚠️/🔲。
- `doc/testplan.md` M2-01~M2-07 七行逐行核对：状态均 ✅，证据链接 `doc/evidence/v0.2.3/M2-0N.log` 均存在，复现命令 `make run TEST=ppa_m2_0N_test SEED=1` 完整。
- RTL 端序独立核对（不采信 DE 汇报，直接读 `rtl/packet_proc_core.sv`）：组合头字段抽取 `*_eff`（L76-79）、头字段锁存 `always_ff`（L224-227）、payload 字节 `byte*_cur`（L143-146）三处一致为大端（Byte0→[31:24] … Byte3→[7:0]）。与 spec 附录 A（`32'h08_01_00_09`→pkt_len=8/pkt_type=0x01/flags=0/hdr_chk=0x09，MSB 优先）、附录 B.1/B.2/B.3 数值示例吻合。BUG-009 的组合/锁存端序不一致缺陷确已在第二次修复（b8a1890）闭合，头字段两套表示同端序，多字帧 DONE 拍退回锁存值不再取错字节。

## 判据②：`make regress` 100% PASS 且证据归档

**结论：满足。**

- 本人独立复跑 `make -C sim regress`（本地 VM，VCS O-2018.09-SP2）：**17/17 PASS**（smoke + M1×9 + M2×7），逐条 PASS。
  - 首次复跑因我的 fresh shell 未设 `VCS_HOME`/`LM_LICENSE_FILE` 而编译失败（`Cannot find 'vcsMsgReport'`→随后 license 未指向），系环境变量问题、非设计缺陷；补齐 `VCS_HOME=/home/synopsys/vcs-mx/O-2018.09-SP2`、`LM_LICENSE_FILE=27000@icarray-virtual-machine` 后一次通过 17/17。此点记录以说明「独立可复现」。
- 证据归档：`doc/evidence/v0.2.3/result_summary.txt`（17/17，日期 2026-07-14）已入里程碑目录，与我复跑结果一致。
- 单场景/缺陷证据抽查（`doc/evidence/v0.2.3/*.log`）：M2-01~07、BUG-009 共 8 份 log 首行均为含 TEST+SEED 的复现命令，UVM_INFO 计数正常、**UVM_ERROR=0 / UVM_FATAL=0**，UVM Report Summary 完整。BUG-009.log 源 log = `sim/out/ppa_m2_01_test_1.log`，与登记的最小复现 `make run TEST=ppa_m2_01_test SEED=1` 自洽。
  - 各 log「## 关键检查行」段为空，经查 `scripts/evidence.py`（L25 `KEY_LINE_RE=pass|match|compare ok|check ok`，L46）系这些 PASS 场景源 log 未含此类关键字行所致，属正常；防造假由 evidence.py L41-42（UVM_ERROR/FATAL≠0 即 `sys.exit` 拒登）+ L88（源 log 不存在即拒登）机械保证——证据只可能由真实通过的 log 生成。

## 判据③：rev 审查记录存 doc/evidence/

**结论：满足。**

- 本审查记录 `doc/evidence/v0.2.3/review-m2-milestone.md`；配套 `review-bug-009-arbitration.md`（BUG-009 仲裁，独立验算、非桩件）、`coverage-summary.md`（六类覆盖率含未达标项如实记录）、`v0.2.2/review-lint-waiver-8.md`（豁免 #8 复核）。
- `python3 scripts/docs.py --check` 本人实跑：**通过**（docs-check 通过，EXIT=0）。

---

## 覆盖率缺口裁决

**裁定：TOGGLE（59.63~71.44%）/FSM（60.00%）低于 90% 不卡 M2 签核。**

- 依据（本人 grep spec.md 原文核实，未采信 DV 转述）：覆盖率 ≥90% 门槛的验收归属见 spec §11.5「Lab4：集成回归与覆盖率闭环」——`doc/spec.md:663`（章节）、`:682`/`:785`（必做2「五类覆盖率等级验收…≥90% 合格」，评分项 15 分）。CLAUDE.md §4.1 明确 M4=Lab4；故 ≥90% 六类综合是 **M4-02（§11.5-必2）** 的验收目标。
- CLAUDE.md §4.1 的 M2 三条硬条件（RTL 就绪 + 关联场景全 ✅ + regress 100% PASS + rev 审查）**不含**覆盖率门槛。DV 汇报「六类≥90% 是 M4-02 验收目标、非 M2 完成判据」的主张**成立**。
- `coverage-summary.md` 对缺口如实记录（TOGGLE/FSM 主要缺口、packet_proc_core COND 89.47% 临界差 0.53pt），并将成因归为 M2 定向激励（SEED=1 固定图案，多字帧/随机化不足）与 M3 集成场景未触发，判读诚实、未粉饰。设计域 LINE/BRANCH/ASSERT 已达标（packet_proc_core LINE=100/BRANCH=100/ASSERT=100）。
- 故不因覆盖率缺口卡关；但缺口须携入 M4-02 闭环（见遗留风险）。

## 造假与「应过未跑」防线核查

- 未见造假迹象。所有证据 `make evidence` 机械生成，evidence.py 强制 UVM_ERROR/FATAL=0 才登证据；本人独立复跑回归 17/17 复现，与归档 result_summary 一致；仲裁记录独立验算并纠正了 BUG-009.md 一处不严谨推理（校验和自洽对端序对称、不能作端序判据），非照搬。
- BUG-009 生命周期闭环干净：登记（OPEN）→ rev 仲裁（方向A 大端为准，判 RTL bug）→ 首次修复 9c28fea（DE）→ **DV 复验驳回退回 OPEN**（首修遗漏头字段锁存端序，最小复现仍 FAIL/UVM_ERROR=9、回归 12/17）→ 第二次修复 b8a1890（DE，≠首修实例，并独立核实 payload 路径无第三处遗漏）→ CLOSED（复验证据 BUG-009.log）。两 commit 均存在于 git 历史。状态流转合法（OPEN→FIXING→FIX_READY→OPEN→FIX_READY→CLOSED，符合 §4.3 复验 FAIL 退回设计），修复 commit、复验证据齐备。文档明载修复人/关单人分属不同实例（关单人≠修复人纪律）。BUG-008 状态 SPEC_CHANGED、r10 已 pin、testplan 新增 M2-07，闭环一致。

## M2-07 负向观测标注核查

- testplan M2-07 行（`doc/testplan.md:32`）：负向观测「busy 期间写 CFG/PKT_LEN_EXP 不报 PSLVERR」**如实标注**为「需 APB 通路，属集成层，M3 集成 test 覆盖（core 单元级无 PSLVERR 端口）」，未被悄悄判定为已覆盖。M2-07 本行 ✅ 仅覆盖单元级正向（type_mask/exp/algo 活值参与第 0 拍判定，r10 组合取活值），与证据匹配、标注诚实。

---

## 最终签核结论：通过

M2 三条硬条件全部独立核验满足；覆盖率缺口按 spec §11.5/CLAUDE.md §4.1 裁定不属 M2 判据、不卡关；BUG-008/009 闭环干净、状态合法、复验人≠修复人、复验证据真实；无造假迹象。**同意 M2 里程碑签核**，可 `make bump-minor` + 打 tag `v0.3.0` 进入 M3。

### 遗留风险（携入 M3/M4，不阻塞本次签核）

1. **覆盖率缺口（→M4-02）**：TOGGLE 59.63~71.44%、FSM 60.00%、packet_proc_core COND 89.47%。需 M4 随机化/多 seed（补 payload 全字节、type_mask/exp 取值组合翻转）与 M3 集成场景（连续帧重启 DONE→PROCESS、default 回退分支、错误注入）闭合至六类综合 ≥90%。
2. **spec 附录端序未在正文显式化**：BUG-009 仲裁记录已建议 arch 走 §8 在 §3.1/§6.1 补显式 bit 映射澄清注（把附录隐含的大端显式化，非行为变更），并订正附录 B.3（spec.md:881）注释算式笔误（应为 `0x04^0x01^0x00=0x05`）。二者均属澄清/订正、非行为变更，当前未落地；建议 M3 触及 spec 时一并处理，以消除「正文对 word 内 bit 位留白、仅附录数值钉端序」的潜在再歧义。
3. **M2-07 负向契约下沉 M3**：「busy 期间写 CFG/PKT_LEN_EXP 不报 PSLVERR」需 M3 集成层（APB 通路）实测覆盖，避免长期停留「默认未观测」。
4. **BUG-009.md 详情页文档完整性（轻微）**：详情页记至「第二次修复」，未含第二次「复验关单」段落，CLOSED 的复验凭 bugs.md 行 + BUG-009.log（机械生成、有效）。不影响闭环有效性（docs-check 通过），建议后续触及时补一段收尾复验说明。
