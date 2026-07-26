# rev 审查记录：lint 豁免 #12 复核 + BUG-012 复验关单

## 0. 审查人身份与被审对象

| 项 | 值 |
| --- | --- |
| 审查人 | rev 实例（本次会话），**与豁免 #12 登记人/BUG-012 修复人（DV 实例）不同实例**，符合 CLAUDE.md §0 实例隔离与 §4.3「关单人 ≠ 修复人」 |
| 审查日期 | 2026-07-26 |
| 被审 HEAD | `615f31a`（feat: 成果展示层基座——scripts/report.py 机械抽数 + BUG-012 lint 登记补齐） |
| 工作区状态 | 开工时仅 `doc/bugs.md` 一处状态回填（`- / OPEN / -` → `615f31a / FIX_READY / -`），其余干净 |
| 版本 | v0.5.1 / M5 |
| 审查对象 | ① `doc/lint-waivers.md` 豁免 #12（7 处 Lint-[SVA-DIU]）② 同表 #11 复核栏注记撤销 ③ `doc/lint-waivers-archive.md` #8 行号订正 ④ `tb/uvm/test/ppa_m2_01_test.sv` / `ppa_m2_02_test.sv` 三处 `8'(...)` 源码改动 ⑤ `doc/bugs.md` BUG-012 关单判定 |
| 判据 | CLAUDE.md §7（lint 门禁）、§4.3（缺陷闭环 / 关单人≠修复人 / CLOSED 须带复验证据）、spec.md §0 适配 8；同类先例 lint-waivers-archive #1/#2/#3/#4/#6/#8/#9、bugs-archive BUG-006 |
| 工具探测 | `command -v vcs` → `/home/synopsys/vcs-mx/O-2018.09-SP2/bin/vcs`（**探测到，必须真跑**，CLAUDE.md §5）；`command -v xcov` / `xdebug` → 未安装，本轮不用 xverif |
| 操作纪律 | 全程**零 git 写操作**。两次临时篡改源码做负向验证，均按 `cp` 备份 → 改 → 验 → `cp` 还原 → `sha256sum -c` 比对执行，比对全部「成功」；未使用 checkout/restore/stash/reset/clean |
| 结论 | **豁免 #12：批准。三处 `8'(...)` 直接改源码处置：认可。两处笔误订正：认可。BUG-012：准予关单（CLOSED）。** 另附 1 项须另行登记的新发现（见 §7 遗留风险 R1） |

---

## 1. A —— 独立复算 lint 对账（先自己跑，后看别人的结论）

### 1.1 复现命令（真实执行）

```bash
export VCS_HOME=/home/synopsys/vcs-mx/O-2018.09-SP2
export VERDI_HOME=/home/synopsys/verdi/Verdi_O-2018.09-SP2
export LM_LICENSE_FILE=27000@icarray-virtual-machine
export PATH=$VCS_HOME/bin:$VERDI_HOME/bin:$PATH
make -C /home/icarray/Desktop/code/ppa-lite-copilot/sim lint
# 实测 exit 1（见到本仓库范围告警即退 1，属 sim/Makefile:91-94 的预期行为，非跑挂）
# 完整 log：sim/out/lint.log（7864 行）
```

去重口径（本审查人自行实现，未复用登记人的统计脚本）：扫描 log 中每一行 `^Lint-\[XXX\]`，取**紧邻下一行**若匹配 `^\.\./(rtl|tb)/<文件>, <行号>` 则记为一处，集合去重键 = `(类别, 文件, 行号)`。仓库外（VCS 自带 UVM-1.2 库）告警不计入，与 `sim/Makefile:84-86` 声明的判定范围一致。

### 1.2 实测结果（HEAD `615f31a`）

本仓库范围原始条目 **81**，按 (类别,文件,行号) 去重后 **81**（无重复项）。

| 类别 | 处数 |
| --- | --- |
| Lint-[NS] | 32 |
| Lint-[SVA-DIU] | 45 |
| Lint-[WMIA-L] | 4 |
| **合计** | **81** |

逐文件实测明细：

| 类别 | 文件 | 处数 | 行号 |
| --- | --- | --- | --- |
| NS | tb/tb_top.sv | 1 | 20 |
| NS | tb/uvm/apb_agent/apb_driver.sv | 4 | 20,21,46,49 |
| NS | tb/uvm/apb_agent/apb_monitor.sv | 1 | 23 |
| NS | tb/uvm/core_agent/ppa_core_driver.sv | 10 | 29,30,47,52,63,76,81,88,90,110 |
| NS | tb/uvm/env/m3_stub_driver.sv | 12 | 26,35,41,43,50,52,57,59,71,74,77,87 |
| NS | tb/uvm/test/m3_seq_lib.sv | 2 | 329,344 |
| NS | tb/uvm/test/m4_seq_lib.sv | 2 | 309,311 |
| SVA-DIU | rtl/apb_slave_if.sv | 8 | 268,273,278,283,290,295,300,306 |
| SVA-DIU | rtl/packet_proc_core.sv | 9 | 282,287,292,297,302,308,313,321,326 |
| SVA-DIU | rtl/packet_sram.sv | 5 | 61,65,70,74,80 |
| SVA-DIU | rtl/ppa_top.sv | 6 | 166,170,174,178,182,187 |
| SVA-DIU | tb/sva/apb_protocol_sva.sv | 4 | 21,27,32,38 |
| SVA-DIU | tb/sva/apb_slave_if_sva.sv | 6 | 51,57,63,68,73,78 |
| SVA-DIU | tb/sva/packet_proc_core_sva.sv | 7 | 24,29,34,40,45,51,56 |
| WMIA-L | tb/uvm/apb_agent/apb_seq_item.sv | 4 | 10,11,12,13 |

### 1.3 与两张登记表逐条对账（自算差集）

把 `doc/lint-waivers.md`（#10/#11/#12）+ `doc/lint-waivers-archive.md`（#1..#9）的对象列逐条誊录成 `(类别, 文件, 行号)` 集合（共 15 条 文件×类别 记录，展开 81 处），与实测集合做双向差集：

```
实测去重处数: 81
登记表覆盖处数(去重): 81
实测未被登记(差集 实测-登记): 空
登记但实测无(幽灵登记 登记-实测): 空
```

**回答任务卡三问**：

- 当前实测总处数 = **81 处**。
- 登记表覆盖 = **81 处**（#1..#12 共 12 条豁免）。
- 差集 = **空**（双向皆空：既无未登记的实测告警，也无指向不存在告警的幽灵登记）。

**独立交叉校验**：`python3 scripts/report.py --json` 从**登记表侧**独立解析出 `results.waivers.sites_total = 81`，与本审查人从 **lint log 侧**独立统计的 81 完全一致；两条取数路径互不依赖，同时命中同一数字，佐证对账无误。

### 1.4 负向验证：BUG-012 自述的「修复前 84 处」是否属实

登记表与 bug 条目均称修复前 84 处、修复后 81 处。本审查人不接受口头数字，做了受控复现：

```bash
# 1) 字节级备份 + 记录 sha256（不动 git）
cp tb/uvm/test/ppa_m2_01_test.sv tb/uvm/test/ppa_m2_02_test.sv <scratchpad>/bak/
sha256sum tb/uvm/test/ppa_m2_0{1,2}_test.sv > <scratchpad>/head_sha.txt
# 2) 只读取出修复前内容（git show 是只读操作）
git show 615f31a^:tb/uvm/test/ppa_m2_01_test.sv > <scratchpad>/prefix/ppa_m2_01_test.sv
git show 615f31a^:tb/uvm/test/ppa_m2_02_test.sv > <scratchpad>/prefix/ppa_m2_02_test.sv
# 3) 覆盖为修复前状态 → 跑 lint（独立 OUT，不污染 out/）
cp <scratchpad>/prefix/*.sv tb/uvm/test/ ; make -C sim lint OUT=out_neg
# 4) 立即还原 + 校验
cp <scratchpad>/bak/*.sv tb/uvm/test/ ; sha256sum -c <scratchpad>/head_sha.txt
```

`diff` 确认修复前后两文件**仅**这 3 行不同（各多一行中文注释 + `8'(...)` 包裹），且修复前的 `foreach` 分别正落在 `ppa_m2_01_test.sv:31`、`ppa_m2_02_test.sv:27` 与 `:42`——与 BUG-012 现象列所记行号逐字一致。

lint 复跑结果：

| 状态 | 去重处数 | NS | SVA-DIU | WMIA-L |
| --- | --- | --- | --- | --- |
| 修复前（`615f31a^` 的两个 test 文件） | **84** | 32 | 45 | **7** |
| 修复后（HEAD） | **81** | 32 | 45 | **4** |

集合差：

```
修复前独有: [('Lint-[WMIA-L]', '../tb/uvm/test/ppa_m2_01_test.sv', 31),
             ('Lint-[WMIA-L]', '../tb/uvm/test/ppa_m2_02_test.sv', 27),
             ('Lint-[WMIA-L]', '../tb/uvm/test/ppa_m2_02_test.sv', 42)]
修复后独有: []
```

即：修复**恰好**消掉那 3 处，**没有**新增任何一处、也没有让别处行号漂移。「84 → 81」属实。

还原后 `sha256sum -c` 两文件均「成功」，`git status --short` 仍只有 `doc/bugs.md` 一行；临时产物 `sim/out_neg/` 已 `rm -rf` 清除。

### 1.5 一处须如实记录的口径说明（不影响结论）

BUG-012 现象列写「11 条豁免仅覆盖 74 处，10 处从未登记」。**这个 74/10 只在「已按当前行号订正 #8」的前提下成立**：修复前的 #8 对象列还是 BUG-009 修复前的旧行号（278,283,288,293,298,304,309,317,322），若按严格 `(类别,文件,行号)` 匹配，当时的未匹配项其实是 **19** 处（10 处真·未登记 + 9 处 #8 行号漂移导致对不上）。

这不是隐瞒：`doc/lint-waivers.md` 第 15 行的补登记说明已明写「已登记的 74 处（**含本次订正 #8 行号后按当前行号匹配**）」。按「同文件同类别同断言名、仅行号漂移」计为已覆盖是合理口径（#8 九条断言名与处数均未变）。本审查人接受该口径，仅在此记录以免后人按严格口径复算时对不上数。

---

## 2. B —— 豁免 #12 复核（7 处 Lint-[SVA-DIU]，`tb/sva/packet_proc_core_sva.sv`）

### 2.1 逐行读源码（7 处逐一核对）

| 行 | 断言名 | 写法 | spec 锚点（源码注释自述） |
| --- | --- | --- | --- |
| 24 | a_busy_after_start | `assert property (@(posedge clk) disable iff (rst) (start_i && !busy_o) \|=> busy_o)` | §7.2/§7.4/§10.3(M2-03) |
| 29 | a_busy_done_excl | 同上句式，`!(busy_o && done_o)` | §7.4 |
| 34 | a_rden_only_in_process | 同上句式，`mem_rd_en_o \|-> busy_o` | §7.4 |
| 40 | a_process_len_clamp | 同上句式，`$rose(busy_o) \|-> ##[1:8] !busy_o` | §7.3(r8) |
| 45 | a_done_hold | 同上句式，`(done_o && !start_i) \|=> done_o` | §7.2/§10.3(M2-03) |
| 51 | a_restart_clears | 同上句式，`(done_o && start_i) \|=> (busy_o && !done_o)` | §7.2/§10.3(M2-03) |
| 56 | a_format_ok_def | 同上句式，`done_o \|-> (format_ok_o == !(length_error_o \|\| type_error_o \|\| chk_error_o))` | §5.2 |

7 处一一对应实测告警行号 24/29/34/40/45/51/56，无多无少。

### 2.2 「与已批准的 #3/#4 同写法同根因」是否成立 —— **成立**

复位信号写法逐文件核对（这是 #3/#4 原因列的核心论据「用单一信号 rst 规避更实质的 Lint-[SVA-CE]」）：

| 豁免 | 文件 | 复位信号定义 | disable iff 形式 |
| --- | --- | --- | --- |
| #12（本次） | tb/sva/packet_proc_core_sva.sv:19-20 | `logic rst; assign rst = !rst_n;` | `disable iff (rst)` ×7 |
| #3（已批准） | tb/sva/apb_protocol_sva.sv:17-18 | `logic rst; assign rst = !presetn;` | `disable iff (rst)` ×4 |
| #4（已批准） | tb/sva/apb_slave_if_sva.sv:30-31 | `logic rst; assign rst = !PRESETn;` | `disable iff (rst)` ×6 |
| #1/#2/#8/#9（已批准，RTL 侧） | packet_sram.sv:58 / apb_slave_if.sv:265 / packet_proc_core.sv:279 / ppa_top.sv:163 | 同为 `assign rst = !<复位>;` | `disable iff (rst)` ×5/8/9/6 |

三个 tb/sva 文件连注释都是同一句式（「disable iff 要求引用单一信号而非复合表达式（避免 Lint-[SVA-CE]…）」）。**同类别、同根因、同写法的判断成立**，且 #12 与 #3/#4 同属 DV 交付的 bind SVA（`tb/sva/README.md` 约定），归属一致。

VCS 消息体亦确认本告警**无缺陷内容**，只是陈述「用了 disable iff」：

```
Lint-[SVA-DIU] Disable iff used
../tb/sva/packet_proc_core_sva.sv, 24
packet_proc_core_sva
  Disable iff is used in assertion 'a_busy_after_start: assert
  property(@(posedge clk) disable iff (rst) ((start_i && (!busy_o)) |=> busy_o)) ...
```

### 2.3 是「真不可修复/等价必要」还是「能修但图省事」—— 负向实验判定

本项目有 `Lint-[ULCO]` 直接改源码不豁免的先例（BUG-006），标准是**能修就修**。本审查人不接受纸面论证，做了受控实验：把 7 处 `disable iff (rst)` 全部剥除（`cp` 备份，字符串替换 7 处，剥除后文件内 `disable iff` 仅剩注释里那 1 次出现），重编译并复跑 `ppa_m2_09_reset_test SEED=1`（该 test 的设计目的正是在 PROCESS 态与 DONE 态各注入一次异步复位，见文件头注释）：

```
"../tb/sva/packet_proc_core_sva.sv", 45: tb_top.u_packet_proc_core.u_packet_proc_core_sva.a_done_hold:
    started at 155000ps failed at 165000ps
	Offending 'done_o'
Error: "../tb/sva/packet_proc_core_sva.sv", 45: ... a_done_hold: at time 165000 ps
packet_proc_core: DONE 态 done_o 未按 §7.2 保持
```

即：DONE 态注入异步复位时，`a_done_hold`（`done_o && !start_i |=> done_o`）的 in-flight 义务被复位清 `done_o` 打断，**产生一条纯属虚假的断言失败**。`disable iff (rst)` 正是用来在复位期作废 in-flight attempt 的机制，**语义承重、非装饰**。实验后立即还原，`sha256sum -c` 校验「成功」，`sim/out_sva/` 已清除。

其余可能的「修法」逐一否决：

1. **改用前件守卫**（如 `rst_n |-> ...` 或 `rst_n throughout ...`）：不等价——只约束触发时刻，不作废已启动的 attempt，上面那条 a_done_hold 假失败依然存在；且表达式变复杂，多半反而触发 `Lint-[SVA-CE]`。
2. **`$assertoff/$asserton` 由 TB 在复位期全局关断**：把局部、可审计的复位屏蔽换成全局机制，粒度更粗（连不需要屏蔽的断言一起关）、跨文件耦合，工程上更差。
3. **工具层压制**（`+lint=all,noVCDE,noSVA-DIU`）：会把该类别在**全仓库**永久隐藏，包括将来真正需要审视的用法，并一次性作废 #1/#2/#3/#4/#8/#9/#12 七条豁免的审计痕迹。比登记豁免**更不可接受**。

对照：本次 3 处 `Lint-[WMIA-L]` 的修法是加 `8'(...)`，是**纯语法标注、零语义变化**，所以「能修就修」；`disable iff` 的移除**必然改变断言语义**，不在「能修」之列。两者处置不同不是双标，是同一标准（「无语义代价即修，有语义代价才豁免」）的一致应用。

### 2.4 一致性检查

同根因的 SVA-DIU 豁免共 7 条、45 处，其中 #1/#2/#3/#4（2026-07-09 批准）、#8（2026-07-13）、#9（2026-07-14）共 38 处已获批。在写法、根因、必要性论证完全相同的情况下驳回 #12 的 7 处，将是无依据的不一致裁决。

### 2.5 补充核实：#12 是纯登记补齐，未夹带断言内容变更

`git log --oneline -- tb/sva/packet_proc_core_sva.sv` 仅一条 `7bd737a`（M2 收官），HEAD `615f31a` 的改动清单里**没有**该文件。因此 #12 是对 M2 就已存在、且随 M2/M3/M4 全部回归通过的既有断言做**登记补齐**，不涉及任何断言语义变更。

### 2.6 B 项结论：**批准**

依据：CLAUDE.md §7 / spec §0 适配 8；写法与根因与已批准的 #3/#4（及 #1/#2/#8/#9）逐项一致（§2.2）；负向实验证明 `disable iff` 语义承重、移除会造成假失败（§2.3）；三条替代修法均劣于登记豁免（§2.3）；驳回将造成与 38 处已批准豁免的裁决不一致（§2.4）。

---

## 3. C —— 3 处 Lint-[WMIA-L] 「直接改源码」处置复核

### 3.1 「根因与 #6 不同」的判定 —— **成立**

对照两者的 VCS 消息体（前者取自本审查人 §1.4 的修复前 log，后者取自 #6 原因列并经 log 复核）：

```
# 本次 3 处（ppa_m2_01_test.sv:31）——报在测试自己的源码行上
../tb/uvm/test/ppa_m2_01_test.sv, 31
  Width mismatch between LHS and RHS is found in assignment:
  The following 32-bit wide expression is assigned to a 8-bit LHS target:
  Source info: n3.payload[i] = (i + 1);
  Expression: n3.payload[i]
```

而 #6（`tb/uvm/apb_agent/apb_seq_item.sv:10-13`）展开定位到 `uvm_pkg::uvm_object::__m_uvm_status_container.status = 1;`——UVM-1.2 库 `uvm_macros.svh` 里 `` `uvm_field_int`` 宏的**内部**赋值，调用点无法通过改写消除。

**一个报在自己写的语句上（可在调用点修）、一个报在库宏内部实现上（调用点不可控）——根因确实不同，判定成立。** 依本项目 BUG-006 已确立的先例（`Lint-[ULCO]` 6 处判定为可修复、直接加 `int'(...)` 不占豁免），可修的就该修，不该占豁免额度。处置方向正确。

### 3.2 行为等价性 —— **独立确认（值域证明，不依赖回归 PASS）**

这是本项目对外将宣称「零回归」的那一条，故本审查人不以回归 PASS 为据，改以值域与类型逐项证明：

1. **LHS 类型**：`tb/uvm/core_agent/ppa_core_seq_item.sv:11` 声明 `bit [7:0] payload [];`——8 位**无符号**动态数组。
2. **循环变量值域（由构造决定，非猜测）**：三处改动的紧邻上一行都是 `payload = new[28];`，SV `foreach` 遍历 28 元素动态数组，下标 `i ∈ [0, 27]`。
   - `ppa_m2_01_test.sv:32` `8'(i + 1)`：RHS 值域 **[1, 28]**；
   - `ppa_m2_02_test.sv:28` `8'(i)`：RHS 值域 **[0, 27]**；
   - `ppa_m2_02_test.sv:44` `8'(i)`：RHS 值域 **[0, 27]**。
   三者全部 ⊆ [0, 255]，`8'(...)` 位宽转换**不截掉任何有效位**，位模式与改前逐位相同。
3. **符号性**：`8'(int)` 结果为 8 位有符号，赋给无符号 `bit [7:0]` 保持位模式；且值域内 bit[7] 恒为 0，连符号扩展/截断的交互都不存在。
4. **无后续覆写**：三个都是 directed item（`mk()` 只负责 new + 命名），`grep randomize` 在 `ppa_m2_base_test.sv` / `ppa_m2_01_test.sv` / `ppa_m2_02_test.sv` 中**无命中**，payload 写入后不会被随机化覆盖。
5. **下游一致**：期望值由 `ppa_core_seq_item.sv:95-100` 的 `predict()` 从**同一个** payload 数组现算，激励位模式不变 ⇒ 期望 sum/xor 不变；场景意图（N-3 满 28B 图案 / E-2-len33 / E-len100）原样保留。
6. **实测佐证**（§1.4）：修复前后集合差 = 恰好那 3 处消失、后集无任何独有项——修改没有顺手改动别的东西，也没把告警挪到别处。
7. **写法有仓内先例**：`ppa_m2_08_rand_test.sv:33/72-79`、`m4_seq_lib.sv:128/130` 早已是 `8'($urandom)` / `8'($urandom_range(...))` 同款写法；`ppa_m2_09_reset_test.sv:26/38` 本来就是 `8'(i + 1)`。本次是向既有写法看齐，非发明新风格。

**结论：三处改动行为等价，激励一字节未变。** 此结论由值域与类型独立推出，回归 32/32 PASS 只是旁证。

### 3.3 C 项结论：**认可（不应走豁免，直接改源码正确）**

若判定其与 #6 同根因而该走豁免，才是错的——#6 的不可修性来自 UVM 库内部，本处完全在仓库代码可控范围，加一个零语义代价的位宽转换即可清除。登记人的判定与处置均正确。

---

## 4. D —— 两处笔误订正复核

### 4.1 归档件 #8 行号订正（`rtl/packet_proc_core.sv`）—— **与实测一致，订正成立**

| 来源 | 行号 |
| --- | --- |
| 订正前（登记时刻，BUG-009 修复前） | 278, 283, 288, 293, 298, 304, 309, 317, 322 |
| 订正后（本次登记人所填） | 282, 287, 292, 297, 302, 308, 313, 321, 326 |
| **本审查人实测**（§1.2） | **282, 287, 292, 297, 302, 308, 313, 321, 326** |

订正后与实测**逐个吻合**，订正前的 9 个值**无一命中**。处数 9、断言名 9 条（a_state_legal/a_busy_done_mutex/a_rden_only_process/a_word_cnt_bound/a_word_cnt_incr/a_process_ignores_start/a_process_outputs_clear/a_algo_mode0_no_chkerr/a_format_ok_consistency）、根因、结论均未变，仅行号随 BUG-009 修复后移——属纯笔误订正，不构成豁免效力变更，无需重新批准。

机械层佐证：`report.py --json` 的 `results.waivers.sites_line_drift = []`（该字段按各类别的代码特征逐行回查现文件，#8 现为 9/9 命中），确认订正后无残留漂移。

### 4.2 #11 复核栏注记撤销（L29 是否即 L30）—— **撤销成立，原注记确系错误**

读 `tb/uvm/core_agent/ppa_core_driver.sv`：

```
28	    vif.drv_cb.exp_pkt_len_i <= 6'd0;
29	    wait (vif.rst_n === 1'b1);
30	    @(vif.drv_cb);
31	    forever begin
```

L29 与 L30 是**两条独立语句**（一条 `wait(...)` 复位释放等待，一条 clocking-block 沿等待），各自都是「仅含时序控制、无其他动作」的语句，各自独立触发 Lint-[NS]。本审查人 §1.2 实测该文件的 NS 告警行号为 `29,30,47,52,63,76,81,88,90,110`——**29 与 30 同时出现**，与 #11 对象列所登记的 10 处完全一致。

原注记「所记 29 实为 L30（行号微差）」是误判，**撤销正确**；#11 的处数 10、结论、效力均不变。

**附带发现（非阻塞，不要求本轮处理）**：#11 的**对象列**至今把这 10 处统一描述为「`@(vif.drv_cb);` 时钟块同步等待」，而 L29 实为 `wait (vif.rst_n === 1'b1);`。两者同属 Lint-[NS]、同根因（#5 早已把 `wait(vif.presetn===1'b1);` 纳入同一豁免理由），故豁免范围/处数/结论不受影响；复核栏的撤销注记现已把事实写对。建议下次触及该表时顺手把对象列措辞补一句「其中 L29 为 `wait(...)` 复位释放等待」，不必为此重新复核。

---

## 5. E —— BUG-012 关单判定

### 5.1 关单前提核对

| 条件（CLAUDE.md §4.3 / §7） | 核对结果 |
| --- | --- |
| 关单人 ≠ 修复人 | 修复人/登记人 = DV 实例；关单人 = 本 rev 实例。**满足** |
| 修复 commit 已回填 | `615f31a`（工作区已回填，docs.py `BUG_STATES_NEED_COMMIT` 要求）。**满足** |
| 条目自述的每一项事实经独立复现 | 84（修复前）/ 81（修复后）/ 差集恰为所列 10 处 / 3 处 WMIA-L 精确消除且无副作用 / #8 行号 / #11 撤销——**逐项复现，无一处对不上**（§1.4、§4） |
| §7 lint 门禁条件成立 | 「告警登记 `doc/lint-waivers.md` 经 **rev 复核**」——#12 于本记录获批后，81 处告警 12 条豁免**全部经 rev 复核批准**，`report.py` 的 `all_reviewed` 转 true（§6）。**满足** |
| CLOSED 须带复验证据（doc/evidence/ 路径） | 本记录 `doc/evidence/v0.5.1/review-lint-waiver-12.md`。**满足** |

### 5.2 复验证据的形式

BUG-012 是静态门禁类缺陷，无对应 UVM 仿真场景，走 **BUG-011 的先例**（同为 infra 类、以 rev 审查记录作复验证据关单）。本记录内含全部复现命令与真实输出（lint 两态实测、负向实验、机械层输出），可独立复算，符合 §4.2「没有 log 就没有 ✅」的实质要求——本记录的每个数字都能由记录内命令重跑得到。

### 5.3 判定：**准予关单，置 CLOSED**

已由本审查人在 `doc/bugs.md` 落盘：状态 `FIX_READY` → `CLOSED`，复验证据列填 `doc/evidence/v0.5.1/review-lint-waiver-12.md`，并在根因/裁决列末尾追加 rev 复验关单段（仅改这三处格子，未动其他条目/列）。同时把 `doc/lint-waivers.md` #12 的复核栏由「待 rev 复核」改为批准结论（格式对齐 #10/#11）。

### 5.4 关单后，对外材料的准确措辞（提示 arch）

BUG-012 现象列曾写明「在补齐并经 rev 复核之前，对外展示材料不得出现任何『lint 告警全部登记/清零/干净』类表述」。该限制现已解除，但**准确的说法只有一种**：

- ✅ 可写：「`make lint`（VCS `+lint=all,noVCDE`）本仓库范围 **81 处**告警，**12 条豁免全部经 rev 复核批准**，无未登记项」。
- ❌ 不可写：「lint **干净 / 零告警 / 清零**」——`make lint` 至今 exit 1（有告警即退 1，见 `sim/Makefile:91-94`），说「干净」是假话。
- ❌ 不可写：「lint 告警全部**修复**」——81 处是**豁免**不是修复；本轮只修了 3 处 WMIA-L。

---

## 6. F —— 机械层验证（改动落盘后的真实输出）

### 6.1 `python3 scripts/report.py --json` 的 waiver 字段

```
AFTER reviewed: 12 / 12
AFTER all_reviewed: True
AFTER pending_review: []
AFTER sites_total: 81
AFTER by_category: {'NS': 4, 'SVA-DIU': 7, 'WMIA-L': 1}
AFTER sites_line_drift: []
```

改动前基线（同一命令、同一机器，落盘前采集）：

```
BEFORE reviewed: 11 / 12
BEFORE all_reviewed: False
BEFORE pending_review: ['12']
BEFORE sites_total: 81
```

`reviewed` 11/12 → **12/12**、`pending_review` `['12']` → **清空**、`all_reviewed` False → **True**，与任务卡预期一致。`sites_total` 保持 81 不变（本次只改复核栏，不动对象列，处数本就不该变——这一点同时反证我没有误改对象列）。

注：`report.py` 判「已复核」的口径是 `复核（rev/日期）` 列**非空 + 含「批准」+ 不以「待」开头**（`scripts/report.py:895-896`，比 docs.py 的归档口径严），本次填入的批准文本满足该口径。

### 6.2 `python3 scripts/report.py --check`

```
[warn] doc/evidence/v0.1.7/coverage-summary-M1.md 中有 2 个互不相同的 N/N PASS 声明 [(7, 7), (10, 10)]（首测/复测并存）→ 降级为 warn，不做等值比对
[warn] doc/report.html 不存在，跳过注入（R3 尚未交付展示材料时属正常）
[warn] README.md 中没有任何 report.py 认识的生成区标记，跳过
[warn] doc/presentation/defense.md 不存在，跳过注入（R3 尚未交付展示材料时属正常）
[warn] doc/report.html 不存在，跳过静态数字比对
[warn] doc/presentation/defense.md 不存在，跳过静态数字比对
[1/6] spec.md sha256 现算比对（本函数独立重算）: 一致 4880faf8135692f2…
[2/6] 覆盖率摘录 ⇄ 回归摘要 交叉校验：4 份，0 处不符，1 处降级 warn
[3/6] regress.list 32 条 == 最新回归摘要 32 条结果行
[4/6] COV_ANCHORS 漏点守卫（本函数独立重扫）: 4 份摘录，0 份缺锚点
[5/6] 生成区新鲜度：已校验 无；跳过 doc/report.html, README.md, doc/presentation/defense.md
[6/6] 静态 data-metric 比对：README.md 无 data-metric 元素，跳过静态数字比对

report-check 通过（6 条 warn）
```

**通过**。warn 由改动前的 7 条降为 6 条——消失的正是 `[warn] lint 豁免 #12 尚未经 rev 复核批准——展示材料不得写"全部经 rev 复核"（CLAUDE.md §7）`。这是本次复核在机械层最直接的可见结果：那句展示材料的禁令已被机械解除。

### 6.3 `make docs-check`

```
docs-check 通过
```

（含 BUG-012 置 CLOSED 后的 `check_evidence` 校验：复验证据列须以 `doc/evidence/` 开头且文件存在，`scripts/docs.py:220-235, 395-396`。）

---

## 7. 遗留风险与建议（供 orch 派单，本审查人不越权登记）

**R1（新发现，建议登记为新缺陷，infra 类，优先级中高）——bind SVA 与 RTL 内部断言的失败不会让 `make regress` 变红。**

§2.3 的负向实验意外证实了一个门禁漏洞：剥除 `disable iff` 后 `a_done_hold` **真实失败**，log 中确有

```
Error: "../tb/sva/packet_proc_core_sva.sv", 45: ... a_done_hold: at time 165000 ps
```

但**同一份 log 的报告摘要里 `UVM_ERROR : 0`、`UVM_FATAL : 0`，`simv` 退出码为 0**。而：

- `scripts/regress.py:15-26` 判 PASS 的唯一依据是 log 中 `UVM_(ERROR|FATAL)` 计数为 0（`:57-59` 另兜底 `rc != 0` 才降为 FAIL，本例 rc == 0）；
- `scripts/evidence.py:41-42` 的登证据前置判定同样只看 `UVM_ERROR/UVM_FATAL`。

因此**任何 SVA `$error` 失败都会被判 PASS 并可正常登记为 ✅ 证据**。本项目共 49 条断言（DE 内部 32 + DV 接口 17，取自 `report.py --json` `verification.sva.total`），目前全部处于「只报不拦」状态。

影响评估（避免夸大）：历史结论**不因此失效**——已闭环的功能缺陷（如 BUG-009 端序）均由 UVM 侧参考模型比对捕获，走的是 UVM_ERROR 通路；且断言覆盖率报告里失败会留痕。但「回归 32/32 PASS + 断言覆盖率 ≥90%」这个组合的说服力**弱于字面**：它并不保证断言全部为真。建议由 orch 登记后派 DV 处置（修法方向由 DV 提，例如 regress/evidence 侧增扫 `^Error: ".*\.sv", \d+:` 形态的断言失败行，或改用 VCS `-assert` 相关选项让断言失败反映到退出码）。

**R2（措辞，非阻塞）**：#11 对象列把 `ppa_core_driver.sv:29` 描述为 `@(vif.drv_cb);`，实为 `wait (vif.rst_n === 1'b1);`。豁免效力不受影响，见 §4.2 建议。

**R3（流程，记录用）**：`tb/sva/packet_proc_core_sva.sv` 的 7 处 SVA-DIU 自 `7bd737a`（M2 收官）起就存在，却穿过了 M2、M3、M4 三次里程碑签核未被登记——说明历次签核的 lint 项核对停留在「本轮新增交付」的局部范围，未做全量 lint ⇄ 登记表对账。补救已完成（差集现为空），且 `report.py` 的 `sites_total` / `sites_line_drift` 已把这项对账机械化。建议把「lint 全量对账差集为空」写进后续里程碑签核清单固定项。

**R4（既有设计，仅记录）**：`make lint` 在有任何本仓库范围告警时即 exit 1，在「告警登记制」下它将长期非零退出，故不能直接作为 CI 硬门禁（CLAUDE.md §7 现也只把 `docs.py --check` 放进 CI，无冲突）。

**R5（并发实例，须在 closeout 前复核）**：本次审查过程中观察到**另一实例正在并发改动 `tb/`**——审查开工时工作区仅 `doc/bugs.md` 一处改动，审查结束时另有 5 个文件出现改动，其 mtime（20:45:23–20:46:07）与本审查人的两处落盘（20:45:32 lint-waivers.md、20:46:34 bugs.md）在时间上交错，确非本审查人所为：

```
 M sim/flist/rtl.f                  M tb/m3_stub_if.sv          M tb/tb_top.sv
 M tb/uvm/env/ppa_env.sv            M tb/uvm/env/ppa_scoreboard.sv
```

已核实这批改动**目前只动注释**（`git diff -U0` 过滤掉注释行与空行后无剩余非注释增删），且经复核不影响本记录结论——把当前工作区（含这批改动）重跑一遍 `make -C sim lint`（独立 `OUT=out_wt`，跑完清除）实测仍为 **81 处**，与 §1.2 的 HEAD 态集合**逐元素完全相同**（双向差集为空）；`report.py --json` 的 `sites_line_drift` 亦仍为 `[]`（豁免 #5 登记的 `tb/tb_top.sv:20` 现仍解析到 `repeat (5) @(posedge pclk);`）。

同一并发实例还在 `doc/bugs.md` 追加了 **BUG-013**（infra，TB 注释与交付状态失步，OPEN）——与本审查人对 BUG-012 行的落盘发生在同一分钟内。已专门核实**未发生互相覆盖**：以 `docs.parse_table()`（转义感知，`scripts/docs.py:94-110`）复解全表，四行 BUG-008/011/012/013 的 ID/状态/修复 commit/复验证据字段均完整正确（BUG-012 = `CLOSED / 615f31a / doc/evidence/v0.5.1/review-lint-waiver-12.md`，BUG-013 = `OPEN / - / -`），`make docs-check` 与 `report.py --check` 在 BUG-013 落盘后复跑仍通过。（顺带一提：BUG-013 最小复现列内含 `git grep -n "尚未交付\|骨架阶段\|TODO(M" tb/`，其 `\|` 已按本仓库约定转义，用不感知转义的朴素 `split("|")` 复核会误判该行列数超标——核对表格时请走 `docs.parse_table()`。）

但须提醒 orch：**本记录的 81 处对账是对「HEAD `615f31a` + 上述注释级改动」这一快照成立的**。若该并发实例后续在 `tb/` 做非注释改动（尤其在 `tb/sva/`、`tb/uvm/apb_agent/`、`tb/uvm/core_agent/`、`tb/uvm/env/m3_stub_driver.sv`、`tb/uvm/test/m3_seq_lib.sv|m4_seq_lib.sv` 这些已登记豁免的文件里增删行），登记表行号会漂移、甚至可能引入新的未登记告警。**closeout 提交前请重跑 `make -C sim lint` 并核对 `report.py --json` 的 `sites_line_drift` 是否仍为空**——这项现已机械化，成本很低。

---

## 8. 结论汇总

| 编号 | 对象 | 结论 | 主要依据 |
| --- | --- | --- | --- |
| A | 全量 lint 对账 | **差集为空**（实测 81 = 登记 81，双向无差） | §1.2/§1.3 实测 + `report.py` 独立取数交叉验证 |
| B | 豁免 #12（7 处 SVA-DIU） | **批准** | §2.2 同 #3/#4 写法根因；§2.3 负向实验证 `disable iff` 语义承重；§2.4 一致性 |
| C | 3 处 WMIA-L 直接改源码 | **认可**（根因判定成立、行为等价独立确认） | §3.1 消息体对比；§3.2 值域/类型证明 + §1.4 集合差 |
| D1 | 归档件 #8 行号订正 | **成立** | §4.1 实测行号逐个吻合 + `sites_line_drift = []` |
| D2 | #11 注记撤销 | **成立**（原注记误判） | §4.2 源码 L29/L30 两条独立语句 + 实测两行皆报 |
| E | BUG-012 | **准予关单 → CLOSED**，复验证据 = `doc/evidence/v0.5.1/review-lint-waiver-12.md` | §5.1 五项前提全满足；关单人=rev≠修复人=DV |
| F | 机械层 | `reviewed 12/12`、`pending_review []`、`all_reviewed true`；`report.py --check` 通过（warn 7→6）；`make docs-check` 通过 | §6 |
| R1 | **新发现**：SVA 失败不拦回归 | 建议 orch 登记新缺陷派 DV | §7 R1，本次负向实验实测 |
