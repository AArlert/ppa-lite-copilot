# rev 审查记录：M1 toggle 覆盖率口径 + lint 豁免 #7 追加 4 处

- 日期：2026-07-10
- 审查员：rev（与登记人 DV/orch 不同实例）
- 版本：0.1.9
- 审查对象：
  1. M1 toggle 覆盖率口径裁决（结构性零翻转位豁免 + 真实缺口顺延）——材料 `doc/evidence/v0.1.7/coverage-summary-M1.md`（复测节，重点第 103-136 行 toggle 缺口逐项根因）
  2. lint 豁免登记 #7 追加 4 处复核——材料 `doc/lint-waivers.md` #7 行（`tb/uvm/env/m3_stub_driver.sv:71,74,77,87`）
- 裁决基准：`doc/spec.md`（第 0 章适配表优先）+ CLAUDE.md §4.1/§5/§7
- 环境探测：`command -v vcs` = /home/synopsys/vcs-mx/O-2018.09-SP2/bin/vcs（探测到）；`xcov`/`xdebug` 未打包出可执行 CLI（探测不到），故覆盖率裁决基于已归档的 urg 解析产物 + spec 锚点，`sim/out/urgReport/` 为非版本控制仿真产物、可按需重生成复核。

---

## 一、裁决对象 1：M1 toggle 覆盖率口径

### 1.1 判据依据（门槛归属厘清——本裁决锚点）

- spec §0 #7：六类 `line+cond+fsm+tgl+branch+assert`，合格线 ≥90% —— 项目级/口径定义，不等于逐里程碑门槛。
- spec §11.5（Lab4=M4）必做验收 #2：「五类覆盖率等级验收…≥90% 合格」＋第 7 周「统计基线／分析缺口／准备过滤清单」＋选做 #4「覆盖率过滤登记表，逐条列过滤对象/行数/原因/结论，未登记不得过滤」。**覆盖率 ≥90% 的验收动作与过滤登记机制，spec 明文挂在 M4，不在 M1。**
- spec §11.2（Lab1=M1）必做验收项仅三条功能项（APB 读写时序 / PKT_MEM 写映射 / RES_* 读通路），**无覆盖率门槛**；其中 #1 只要求「读 CTRL/CFG/STATUS **默认值**」，不要求 CFG/PKT_LEN_EXP 写通路。
- CLAUDE.md §4.1 M 完成三条硬条件：①RTL 就绪＋feature-matrix 场景全 ✅ ②regress 100% PASS＋证据 ③rev 审查记录——**覆盖率 ≥90% 不在 M1 三条硬条件之列**。
- CLAUDE.md §4.1 版本累积：「进入新 M 后允许回修旧 M 问题」——支持缺口顺延。

### 1.2 总裁决

**toggle 73.32%（437/596）不构成 M1 tag 的阻塞项。** 依据：覆盖率 ≥90% 验收按 spec §11.5 属 M4 门槛，M1 阶段覆盖率为「测量＋登记缺口」性质；其余五类（line 94.92% / cond 91.30% / branch 95.12% / assert 100%）均已 ≥90%，fsm 结构性 N/A，健康度良好。
本裁决仅解除「覆盖率」这一项对 M1 的顾虑；M1 能否打 tag 仍需 orch/rev 在里程碑签核时独立核对三条硬条件（regress 现为 10/10 PASS、feature-matrix 关联场景全 ✅、review-M1 记录）。

### 1.3 a. 结构性 26 bit —— 准予登记豁免（可不计入分母）

根因已逐条对齐 spec 核实通过：

- `PRDATA[31:8]`（24 bit）：spec §5.2 全部寄存器字段位宽 ≤8 bit（RES_PKT_TYPE/SUM/XOR 的 `[7:0]` 为最宽），且 §5.2 明文「未列出的位域读回为 0」，PRDATA 高 24 位在 M1 寄存器表下永远输出 0，非激励可改——成立。
- `PREADY`：spec §4.1「PREADY 固定为 1」，恒定值不允许翻转——成立。
- `rst/rst_n`（含 mod7 同类 2 bit）：单次复位释放，无运行中二次复位场景，`1→0` 方向天然不出现——结构性成立。

这 26 bit 数量级属结构性/契约性零翻转，比照 lint-waivers 方式登记覆盖率过滤豁免、不计入达标分母，符合 spec §0 #5（过滤登记改用 markdown 表）与 §11.5 选做 #4。**正式「扣分母」效力归属 M4 签核**——M1 阶段先登记生效，M4 覆盖率闭环时随《覆盖率过滤登记表》一并终审。

### 1.4 b. 真实缺口 45+ bit —— 非 M1 收官必须闭合项，准予顺延，但须登记跟踪

依据：①这些信号（CFG/PKT_LEN_EXP 写通路、CTRL.enable 及 IRQ_EN 的 1→0 回落沿、M3 stub 结果字段多样性）均不在 §11.2 M1 三条必做验收范围内（M1 #1 仅读默认值）；②按 §4.1 版本累积，将随 M2/M3 配置流程与真实结果值多样性自然收窄。
**顺延不等于遗忘**：要求以「顺延」结论登记入同一张过滤表（结论栏区分「豁免」vs「顺延M2M3」），作为 M4 覆盖率闭环的待办清单强制回访——若 M4 时仍未覆盖且无结构性理由，不得再豁免、须补场景闭合。

### 1.5 c. 覆盖率过滤登记表路径/格式建议（供 orch 落地，rev 不代改）

新建 `doc/coverage-waivers.md`，表头对齐 spec §11.5 选做 #4 要求列 + 仿 lint-waivers.md 复核列：

| # | 过滤对象（模块/信号[位]） | 位数 | 原因 | 结论（豁免/顺延M2M3/待修） | 复核（rev/日期） |

- 结构性 26 bit 三类各一行，结论=豁免（附 spec 锚点 §5.2 / §4.1 / 复位结构性）。
- 真实缺口按三组（CSR 写通路 / CTRL·IRQ 回落沿 / M3 stub 结果多样性）登记，结论=顺延M2M3，复核列留「M4 回访」。
- 沿用 lint-waivers.md「登记人=DV，复核人=rev，未复核不生效」纪律；可纳入 docs-check 滚动归档口径（M4 前不会超限，非必须）。

---

## 二、裁决对象 2：lint 豁免 #7 追加 4 处（`m3_stub_driver.sv:71,74,77,87`）

### 2.1 判据依据

CLAUDE.md §7（lint 门禁——`make lint` 干净或告警登记豁免经 rev 复核）；spec §0 #8；豁免成立标准参照 #1~#7 首批已批准先例（误报/不可控/修复即破坏语义，且无隐藏真实缺陷）。

### 2.2 核实方式

已逐行读源码 `tb/uvm/env/m3_stub_driver.sv` 核对四处（71/74/77/87）均为独立 `@(vif.drv_cb);` clocking-block 同步等待语句，无其他动作，故触发 `Lint-[NS] Null statement`，与首批 8 处（26/35/41/43/50/52/57/59，rev 2026-07-09 已批准）**同类别、同根因**。

### 2.3 逐处根因（属实、语义必要）

- L71（`read_sram` 内）：驱动 `rd_en/rd_addr` 前对齐 clocking 沿；
- L74：等一拍使物理信号与 `packet_sram` 组合读结果稳定后再采样 `rd_data`（spec §2.3 M2 注 r6 组合读、无寄存延迟）；
- L77：撤销后再等一拍，顺带驱动 `rd_en=0` 分支（亦贡献 branch/toggle 覆盖）；
- L87（`watch_start_pulse` 的 repeat 循环内）：逐拍对齐以采样 `start_pulse`（旁路观测 `start_o`，仅持续 1 拍的 ACCESS 窗口，spec §5.2 CTRL.start）。

去掉任一处即破坏与 M3 结果输入 / packet_sram 读口 / start_o 观测窗口的同拍驱动时序，属标准 UVM clocking-block 惯用法，无法在调用点消除。无隐藏真实缺陷。

### 2.4 结论

**批准追加 4 处豁免。** #7 行豁免范围由首批 8 处扩为全 12 处。

后续动作建议（orch 落地）：将 `doc/lint-waivers.md` #7 结论栏由「豁免（追加 4 处待复核）」更新为「豁免（全 12 处）」，复核栏补「追加 4 处 rev 2026-07-10 批准」。rev 不代改该表，回给 orch 与版本 bump 统一落笔。

---

## 三、batch 结论（供 orch 决定是否打 M1 tag）

1. **覆盖率**：toggle 73.32% **不阻塞 M1 tag**（覆盖率 ≥90% 验收按 spec §11.5 归 M4；M1 三条硬条件不含覆盖率）。前提：orch 落地 `doc/coverage-waivers.md`——结构性 26 bit 登记豁免、真实 45+ bit 登记顺延M2M3（M4 强制回访）。
2. **lint #7 追加 4 处**：**批准豁免**，根因成立。

放行条件（M1 tag 仍需 orch/rev 在里程碑签核时独立确认，不在本卡范围）：三条硬条件——feature-matrix 关联场景全 ✅、`make regress` 10/10 PASS 证据归档、M1 里程碑 review 记录出具。此二裁决通过后，覆盖率与 lint 两项顾虑即清除。

## 四、遗留风险

- 低。toggle 缺口已分类清楚（26 bit 结构性不可闭合 + 45+ bit 可闭合缺口顺延），无一指向 M1 功能/协议语义缺陷；四处 lint 告警均为 VCS `+lint=all` 对标准 UVM clocking-block 惯用法的提示性误报。
- 待办跟踪（非阻塞）：`doc/coverage-waivers.md` 未落地前，M4 覆盖率闭环缺书面待回访清单，建议随本轮 orch 落地一并建立，避免 M4 时晚发现。

## 五、复现/核实方式

- 覆盖率数据复核：`cd sim && make regress COV=1 && make cov`（urg 生成 out/urgReport；本记录基于该产物解析与 spec §5.2/§4.1/§11.5 锚点）。
- lint 四处核实：`Read tb/uvm/env/m3_stub_driver.sv`（L71/74/77/87）+ `cd sim && make clean && make lint`（out/lint.log 判定范围内 Lint-[NS] 计数）。
- spec 锚点：`doc/spec.md` §0 #7/#8、§4.1、§5.2、§11.2、§11.5。
