# M4 里程碑签核审查记录

- 版本：0.4.1（version.json 现值：version=0.4.1 / milestone=M4）
- 审查人：rev（全新实例，未参与本周期 DE/DV 工作，未做过本周期任何仲裁，未预先复核 lint 豁免 #10/#11；本周期无 arch 实例）
- 日期：2026-07-16
- 判据出处：CLAUDE.md §4.1「M 完成判据（三条硬条件）」、spec §11.5（Lab4 必做 1-3 + 选做 4-5）、§0 适配 7（六类覆盖率口径 ≥90%）、§12.3 Lab4 评分细目（选做4 抽查过滤项与 exclude 配置一致）。
- 结论：**通过（签核）**。三条硬条件均由本人独立现算/复跑核验为真；32/32 回归本人在本地 VM 真实复现，六类覆盖率经本人独立 urg 复算逐类与归档数值完全一致；覆盖率过滤登记逐条属合法两类、与 exclude 配置一致、无"可达却排除"造假项；BUG-011 修复复验通过并关单。遗留风险见文末，均为低风险、不阻塞签核。

**核验环境**：本地 VM，VCS-MX O-2018.09-SP2（`command -v vcs` 命中 `/home/synopsys/vcs-mx/O-2018.09-SP2/bin/vcs`）；本 shell 自行 export VCS_HOME/VERDI_HOME/LM_LICENSE_FILE(27000@icarray-virtual-machine)/PATH 后闭环成功。xverif（xcov/xdebug）未在 PATH（`command -v` 未命中，部署在 /home/open_tools/xverif 但无 bin 转发），故覆盖率核验直接用 urg text 报告逐类比对，未借 xcov。

---

## A. 三条硬条件独立验算

### 判据①：M4 的 RTL 就绪且 feature-matrix 关联场景全 ✅

**结论：满足。** M4 为回归/覆盖率里程碑，feature-matrix F4-1/F4-2 模块列为「(全系统)」、无新 RTL（`make handover` 现算 M4 RTL 交付 0/0，符合 M4 定义）。

- `make handover` / `make next` 本人实跑（未采信表格状态位或转述）：testplan 现算 M4 ✅10/10、无 ❌/⚠️/🔲；feature-matrix 现算 M4 验证 ✅2/2。
- feature-matrix（doc/feature-matrix.md:21-22）：F4-1「回归清单整理 + result_summary.txt 生成链路」§11.5/§12.4 关联 M4-01；F4-2「覆盖率收集/合并/报告与缺口修复（含 assert）」§11.5 关联 M4-02 M4-04。无幽灵引用。
- 关联场景证据逐条核对（存在性 + 首行复现命令 + UVM 错误计数）：
  - M4-01 → doc/evidence/v0.4.1/M4-01.log（首行 `make run TEST=ppa_m3_07_reset_test SEED=1`，UVM_ERROR/FATAL=0）。
  - M4-02 → doc/evidence/v0.4.0/coverage-summary.md（六类摘录，见判据②覆盖率复算）。
  - M4-03 → doc/evidence/v0.4.1/M4-03.log（首行 `make run TEST=ppa_smoke_test SEED=1`，UVM_ERROR/FATAL=0）。
  - M4-04 → doc/evidence/v0.4.0/coverage-exclude-registration.md（见 B 项审计）。
  - M4-05 → doc/evidence/v0.4.1/M4-05.log（首行 `make run TEST=ppa_m3_05_test SEED=1`，UVM_ERROR/FATAL=0）。
  - M4-02a..e → doc/evidence/v0.4.0/M4-02a..e.log，五份首行均为对应 `make run TEST=... SEED=1` 复现命令，UVM_ERROR/FATAL 均为 0。
- 必做1「Lab1-3 必做场景各 ≥1 条 testcase」核对 sim/regress/regress.list：M1-01/02/03、M2-01/02/03、M3-01/02/03 九个必做场景各有 ppa_m{1,2,3}_0{1,2,3}_test 在列；选做（§0 适配2 按必做对待）M1-04/05、M2-04/05/06、M3-04/05 亦全部在列。

### 判据②：`make regress` 100% PASS 且证据归档

**结论：满足。**

- 本人独立复跑（本地 VM，自设环境变量）`make -C sim regress COV=1`：**32/32 PASS**，UVM_ERROR/FATAL=0。复算产出 sim/result_summary.txt 与归档 `doc/evidence/v0.4.1/result_summary.txt` 逐行 `diff` **完全一致**。
- 三处 result_summary 一致性核对：`doc/evidence/v0.4.0/result_summary.txt` = `doc/evidence/v0.4.1/result_summary.txt` = `sim/result_summary.txt`（均 32/32，日期 2026-07-16），三者 `diff` 全部为空。
- 32 条构成：ppa_smoke ×1 + M1(01~09)×9 + M2(01~07)×7 + M3(01~05)×5 + 随机/复位补强 [m2_08_rand×3seed、m2_09_reset×1、m1_10_rand×2seed、m3_06_rand×3seed、m3_07_reset×1]=10。与 testplan/regress.list 双向对应。
- BUG-007（脏 out 假失败）修复已生效：regress.py 每轮先 `make clean`；本人复跑首跑即 32/32，无假失败。
- 抽跑复现：本次全量 32 条即为本人从零编译+仿真的独立复现（regress.py 逐测重编译），等价于对每条 TEST+SEED 的可复现性验证。

### 判据③：rev 审查记录存 doc/evidence/

**结论：满足。** 本记录即 `doc/evidence/v0.4.1/review-m4-milestone.md`（小写 review-m4- 前缀，对齐 v0.2.3/v0.3.0 命名约定与 BUG-011 修复后 docs.py 的 `review-m{mnum}*.md` 匹配模式）。

### 覆盖率判据核验（§11.5-必2 / §0 适配7，六类 ≥90）—— 本人独立 urg 复算

方式：本人 `make -C sim regress COV=1 && make -C sim covreset && make -C sim cov` 全量复算（rc=0），另 `urg -format text` 生成文本报告逐类抄读，与归档 `coverage-summary.md` 逐格比对。

urg hierarchy 顶层实例 `tb_top`（= 设计+验证环境域，M4-02 验收口径）本人复算实测：

| 类别 | 本人复算实测 | 归档 coverage-summary.md | 一致 | ≥90 |
| --- | --- | --- | --- | --- |
| LINE   | 100.00 | 100.00 | ✅ | ✅ |
| COND   | 94.35  | 94.35  | ✅ | ✅ |
| TOGGLE | 90.42  | 90.42  | ✅ | ✅ |
| FSM    | 100.00 | 100.00 | ✅ | ✅ |
| BRANCH | 100.00 | 100.00 | ✅ | ✅ |
| ASSERT | 100.00 | 100.00 | ✅ | ✅ |
| **SCORE** | **97.46** | **97.46** | ✅ | ✅ |

- 全域 Total Coverage Summary（含 UVM 库，仅对照）本人复算实测：SCORE 86.45 / LINE 42.63 / COND 94.35 / TOGGLE 90.16 / FSM 100.00 / BRANCH 78.00 / ASSERT 100.00 —— 与 coverage-summary.md §2 完全一致。
- 子实例复算（hierarchy.txt）逐条与 §3 吻合：u_ppa_top 96.88、u_apb 95.63、u_core 97.59、u_sram 100.00、u_apb_slave_if 96.55、u_packet_proc_core 99.35（六类分列均一致）。
- 结论：六类全部 ≥90（最紧为 TOGGLE 90.42），SCORE 97.46 ≥95（优良档），满足 §11.5-必2 / §0 适配7 的 M4-02 判据。**归档覆盖率数值经独立复算 100% 复现，无编造。**

---

## B. M4-04 覆盖率过滤登记审计（反造假重点）

审 `coverage-exclude-registration.md` × `sim/cov_exclude/cov_domain.cfg` × `sim/cov_exclude/coverage_exclude.el`，并以本人复算的 urg modinfo 实测数交叉验证。

### B.1 逐条合法性（两类：设计域外 / spec 强制常量·协议非法态）

- A-1/A-2/A-3（域外）：uvm_pkg、uvm_custom_install_recording、uvm_custom_install_verdi_recording —— 第三方库/VCS 录制骨架，非设计+验证代码，§0 适配7 六类口径针对设计+验证环境域，合法域外。**成立**。
- B-1 PRDATA[31:8]（toggle）：spec §5.2 完整寄存器表最宽可读字段为 res_pkt_type[7:0]/res_payload_sum[7:0]/res_payload_xor[7:0]，**无任何 CSR 字段落在 bit≥8**（本人读 §5.2 逐字段确认），PRDATA[31:8] 结构性 tie-low，合规激励不可翻转。**成立**。
- B-2 PREADY（toggle）：spec §4.1「PREADY 固定为 1，不引入等待状态」，永不翻转。**成立**。
- B-3/B-4：apb_if 接口 prdata[31:8]/pready 直连 DUT，同 B-1/B-2。**成立**。
- B-5 COND `PSEL=0 && PENABLE=1`：spec §4.1 两段式 SETUP(PSEL=1,PENABLE=0)→ACCESS(PSEL=1,PENABLE=1)，PENABLE 仅在 PSEL 有效后拉高，PSEL=0&PENABLE=1 为 APB 协议非法态，且 apb_protocol_sva 主动禁止。**成立**。

### B.2 有无"本应可达却被过滤"（掩盖死码/缺陷）

**无。** 决定性交叉验证：本人复算的 urg modinfo（apb_slave_if 模块 Toggle 段）实测 Total Bits 446 / Covered 396 / 88.79%，未覆盖 50 位；逐位实测唯一未覆盖翻转恰为 `PRDATA[7:0]=Yes/Yes/Yes（已覆盖）`、`PRDATA[31:8]=No/No/No`（24 位×2 方向=48）、`PREADY=No/No/No`（1 位×2=2），48+2=50，与登记表 B 组「扣除后 396/396=100%」算术完全吻合。设计侧数据翻转已饱和，残差纯为 spec 强制常量，无隐藏死码。gap-analysis §2/§3 的 FSM 复位弧、集成域断言、数据高位、地址位均以真实激励闭合（对应 M4-02a..e 补强测试均 PASS），未见"图省事排除"。

### B.3 登记表 × exclude 配置一致性（§12.3 选做4 抽查 ≥2 条）

抽查 4 条，均一致：
- 抽1 B-1 PRDATA[31:8] ↔ coverage_exclude.el `MODULE: apb_slave_if` 下 `Toggle PRDATA [8]`…`[31]`（24 行）。**一致**。
- 抽2 B-2 PREADY ↔ coverage_exclude.el `Toggle PREADY "net PREADY"`。**一致**。
- 抽3 B-3/B-4 apb_if ↔ coverage_exclude.el `MODULE: apb_if` 下 `Toggle prdata [8]`…`[31]` + `Toggle pready "net pready"`。**一致**。
- 抽4 A-1/A-2/A-3 ↔ cov_domain.cfg `+tree tb_top` + `-module uvm_pkg` / `-module uvm_custom_install_recording` / `-module uvm_custom_install_verdi_recording`。**一致**。

**观察（非造假、偏保守，不扣分但记录）**：B-5（COND 协议非法态）登记在册但 coverage_exclude.el 未含对应位级配置行（该文件仅 toggle 排除）；本仓库汇报的域数值直接读 urg hierarchy 的 tb_top 行、并未对 .el/.cfg 做位级扣除（登记表 §B 已声明为「保守实测、B 组仍计为 hole」），故 COND 94.35 是**未扣除 B-5 的保守值**——偏保守方向，不构成数值虚高造假；本人复算 COND=94.35 与之吻合，反证未施加 B-5 排除以抬高数值。B 组 .el 与 A 组 .cfg 在本仓库口径下均为登记/算术佐证，达标不依赖其被 URG 实际应用。

**B 项结论：过滤登记合规，无造假项，登记表与 exclude 配置一致；满足 §11.5-选4 / §12.3 选做4。**

---

## C. lint 豁免 #10/#11 复核

方式：本人读 tb/ 源码对应行，核 Lint-[NS]（Null statement）是否语义必要、有无隐藏缺陷（如 `@(...)` 后本应有的语句体被 `;` 误孤立）。

- **#10**（tb/uvm/test/m3_seq_lib.sv:329,344）：两处均为 `@(top_vif.mon_cb);` 独立 clocking-block 同步等待——L329 在观测 irq_o=1 前对齐采样拍、L344 在观测 irq_o=0 前对齐采样拍（§8.2 irq_o=done_irq|err_irq 组合输出）。系"仅含时序控制、无后续语句体"的标准 SV 惯用法，Lint-[NS] 属误报级；去掉将提前/滞后一拍读到过渡值。功能正确性由 M3-05（irq_o 拉高/写1清除/拉低）PASS 背书，无隐藏缺陷。**批准豁免。**
- **#11**（tb/uvm/test/m4_seq_lib.sv:309,311 + tb/uvm/core_agent/ppa_core_driver.sv:29,30,47,52,63,76,81,88,90,110）：m4_seq_lib L309/311 为 `repeat(N) @(top_vif.mon_cb);` 复位注入拍数/释放后采样对齐；ppa_core_driver 诸行为 `@(vif.drv_cb);`（含 L76/81 `do @(vif.drv_cb); while(...)` 等状态等待、L88 `repeat(2)` 复位脉宽、L90 释放后对齐），均标准 clocking-block 同步等待、无孤儿语句体。功能正确性由 ppa_m2_09_reset/ppa_m3_07_reset PASS + STATUS 清零核对被动保证，无隐藏缺陷。**批准豁免。**（备注：#11 对象列所记 ppa_core_driver.sv「29」实际 `@(vif.drv_cb);` 在 L30，L29 为其上一行；行号微差、不影响判定与豁免范围，建议登记人后续触及时顺手订正为 30。）

**C 项结论：#10、#11 均语义必要、无隐藏缺陷，予以批准。**（复核列已在 doc/lint-waivers.md 回填。）

---

## D. BUG-011 复验关单（关单人=rev，修复人=orch，符合关单人≠修复人）

缺陷：docs.py `make next` 里程碑签核检查恒真（`any(生成器)` 误用 + `review-M` 大写模式不匹配 `review-m` 命名）。修复 commit 5a58c64。本人读 scripts/docs.py:505-520 确认修复正确：内层 `any(any(d.glob(f"review-m{mnum}*.md")) for d in ev_dirs)`（内层 any 消费生成器按真实匹配判真）+ 小写模式 `review-m{mnum}*.md`。

- **态1（签核记录落盘前）**：本人跑 `make next` → 输出「**M4 条目全 ✅，还差：rev 里程碑签核（review-m4-milestone.md）**」。符合预期（恒真缺陷已修，正确报缺）。
- **态2（本记录写入 doc/evidence/v0.4.1/review-m4-milestone.md 后）**：见文末「make next 态2 复跑」——输出「**M4 三条硬条件已齐 → make bump-minor + git tag v0.5.0 进入下一 M**」。符合预期（三条硬条件确已齐）。

两态均符合预期，且三条硬条件本人独立核验为真（A 项）。**BUG-011 予以关单：状态 → CLOSED，复验证据 = 本审查记录路径。**（bugs.md 已回填。关单先例格式参照 BUG-007。）

---

## 抽查样本清单（本人实际执行）

1. `command -v vcs / xcov / xdebug`；`make handover`；`make next`（态1）。
2. `diff` 三处 result_summary.txt（v0.4.0 / v0.4.1 / sim）—— 全一致 32/32。
3. `make -C sim regress COV=1`（本人复跑）→ 32/32 PASS，UVM_ERROR/FATAL=0。
4. `make -C sim covreset && make -C sim cov` + `urg -format text` → tb_top 六类逐类比对 coverage-summary.md（全一致）。
5. urg modinfo apb_slave_if Toggle 段逐位实测（446/396/88.79，未覆盖=PRDATA[31:8]+PREADY=50）。
6. 读 spec §4.1/§5.2/§4.2 核 B 组过滤 spec 依据；读 coverage_exclude.el / cov_domain.cfg 抽查 4 条一致性。
7. 读 tb/uvm/test/m3_seq_lib.sv、m4_seq_lib.sv、tb/uvm/core_agent/ppa_core_driver.sv 豁免行。
8. 读 scripts/docs.py:505-520 核 BUG-011 修复；`python3 scripts/docs.py --check`。
9. M4-01/03/05/02a..e 证据 log 首行复现命令 + UVM 错误计数抽查。

## 核验方式与局限

- 覆盖率与回归为**本人在本地 VM 真实全量复算**（非基于现存 vdb 或转述），gold-standard 反造假；数值逐类 100% 复现。
- urg 合并报告 "Number of tests: 34" = 主回归 32 条（含 2 条复位测试 SEED=1）+ covreset 独立库 2 条（同 2 条复位测试重跑，为规避 O-2018 共享 cm_dir 对 async-reset FSM 弧的不稳定丢弃，方法学见 gap-analysis §2.1/coverage-summary §5），非重复计分异常。
- xverif（xcov）未在 PATH，故未借其加速；以 urg text 报告直读替代，结论不受影响。
- 覆盖率域口径取 urg hierarchy tb_top 行（A 组兄弟顶层实例天然被排除），cov_domain.cfg 为等价佐证配置；本人复算的 tb_top 行数值即验收口径来源，方法自洽。

## 遗留风险（低风险，携入 M5/后续，不阻塞本次签核）

1. TOGGLE 90.42 为六类最紧（仅 +0.42 高于 ≥90 线），残差全为 spec 强制常量（PRDATA[31:8]/PREADY）；若后续 RTL 改动 PRDATA 位映射或新增 ≥bit8 可读字段，需同步重估过滤登记与该类水位。
2. `make -C sim lint` 因 flist 顺序问题实测报错（BUG-005），lint 门禁当前依赖手动诊断性 vcs +lint 运行；lint-waivers 表底注已说明，建议后续修 Makefile/flist 顺序使 `make lint` 一键可用。
3. B-5（COND 协议非法态）登记在册但无位级 .el 配置行（偏保守、非造假）；若后续要将域 COND 报为扣除值，需补 .el 并经 O-2018 URG checksum 复核门，当前保守口径已达标、非必需。
