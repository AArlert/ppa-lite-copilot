# 审查记录：BUG-013 / BUG-014 复验关单 + 91/88/3 断言口径裁定

## 0. 审查人身份、范围与纪律声明

- **审查人 = rev 实例（本会话），≠ 修复人。** BUG-013 修复 commit `a039413`（DV + orch），BUG-014 修复 commit
  `461aebc`（DV + orch）。本实例本轮**未改动 `rtl/` `tb/` `scripts/` `sim/` 的任何一行源码**；写权限仅用于
  本记录与 `doc/bugs.md` 两行的「根因/裁决 / 状态 / 复验证据」三格。满足 CLAUDE.md §4.3「关单人 ≠ 修复人」。
- **被审 HEAD**：`6a9d934`（v0.5.3 / M5）。工作区另有一处**非本实例**的在途改动 `rtl/apb_slave_if.sv`
  （BUG-015，另一实例负责）。已核 `git diff`：纯注释、去注释后代码逐字等同，本轮全部仿真在含该改动的
  工作区上执行，不影响任何结论。
- **环境**：VCS-MX O-2018.09-SP2 + Verdi 2018（本地 VM）。非登录 shell 不继承环境变量，全程显式
  `export VCS_HOME=/home/synopsys/vcs-mx/O-2018.09-SP2 VERDI_HOME=/home/synopsys/verdi/Verdi_O-2018.09-SP2
  LM_LICENSE_FILE=27000@icarray-virtual-machine`。
- **临时篡改纪律**：全程**零 git 写操作**（无 checkout/restore/stash/reset/clean）。入库文件只临时动过两个：
  `sim/flist/tb.f`（追加一行指向**仓库外**的负向对照文件）、`sim/result_summary.txt`（被回归脚本重写）。
  两者均字节备份 + 还原 + sha256 校验：

```
$ sha256sum -c $SP/bak/pre.sha256
sim/result_summary.txt: 成功
sim/flist/tb.f: 成功
sim/flist/rtl.f: 成功
$ git status --short
 M rtl/apb_slave_if.sv          # 另一实例的在途改动，非本实例产生
```

---

## A. BUG-014 复验（证据链完整性）

### A1. 独立制造真实断言失败

**不复用修复人的做法。** 本实例的负向对照是一条**写在仓库外**、经 `FLISTS`/flist 注入编译的 bind 断言，
因此仓库源码在实验期间保持字节不变；且刻意做成**两种形态**（带 `else $error` / **无动作块**），用来检验
「判定与动作块无关」这一主张：

```systemverilog
// /tmp/.../scratchpad/rev_neg_sva.sv（不入库）
module rev_neg_sva (input logic clk, input logic rst_n, input logic busy_o);
  a_rev_neg_with_action: assert property (@(posedge clk) disable iff (!rst_n) !busy_o)
    else $error("REV-NEG: busy_o 非 0（有动作块形态）");
  a_rev_neg_no_action:   assert property (@(posedge clk) disable iff (!rst_n) !busy_o);
endmodule
bind packet_proc_core rev_neg_sva u_rev_neg_sva (.clk(clk), .rst_n(rst_n), .busy_o(busy_o));
```

**(1) 缺陷现象独立复现**（证明修复前的判定确实会放过）：

```
$ make run TEST=ppa_m2_04_test SEED=1 OUT=out_neg FLISTS="-f flist/tb.f -f flist/rtl.f $SP/rev_neg_sva.sv"
$ ./out_neg/simv +UVM_TESTNAME=ppa_m2_04_test +ntb_random_seed=1 ... -assert verbose -l out_neg/ppa_m2_04_test_1.log
simv 退出码 = 0                    ← 断言真实失败，退出码仍为 0
UVM_ERROR :    0
UVM_FATAL :    0
Summary: 95 assertions, 92 with attempts, 2 with failures
"…/rev_neg_sva.sv", 14: tb_top.u_packet_proc_core.u_rev_neg_sva.a_rev_neg_no_action: started at 75000ps failed at 75000ps
"…/rev_neg_sva.sv", 10: tb_top.u_packet_proc_core.u_rev_neg_sva.a_rev_neg_with_action: started at 75000ps failed at 75000ps
Error: "…/rev_neg_sva.sv", 10: …a_rev_neg_with_action: at time 75000 ps
```

即：`UVM_ERROR=0` + `UVM_FATAL=0` + `simv/make 退出码 0`，修复前的单腿判定必判 PASS。**BUG-014 描述属实。**
无动作块的那条同样打出引擎失败行 → 「判定与动作块无关」成立。

**(2) `regress.py` 判 FAIL 且退出码 1**（走完整 `make -C sim clean` → 编译 → 仿真 → 判定链路）：

```
$ python3 scripts/regress.py $SP/mini.list ;  echo 退出码=$?
退出码=1
PPA-Lite 回归结果  日期=2026-07-26  通过=1/2  （其中 1 条因 SVA 断言失败）
FAIL   ppa_m2_04_test SEED=1  [SVA失败: 2 条断言/4 次]
PASS   ppa_m1_01_test SEED=1
```

第二条 `ppa_m1_01_test` 是**同一次编译内的自带阴性对照**：注入的断言在场但该测试不驱动 core 进 PROCESS，
故不失败 → 仍判 PASS。说明不是「注入即全红」的粗暴行为。

**(3) `evidence.py` 拒登且退出码 1**：

```
$ python3 scripts/evidence.py --scen REV-NEG-PROBE --test ppa_m2_04_test --seed 1 ; echo 退出码=$?
log 判定 FAIL（SVA失败: 2 条断言/4 次）——FAIL 不登证据，去 bugs.md 登缺陷
失败断言明细:
  a_rev_neg_no_action    …:14  @75000ps  (tb_top.u_packet_proc_core.u_rev_neg_sva.a_rev_neg_no_action)
  a_rev_neg_with_action  …:10  @75000ps  (…a_rev_neg_with_action)
  …
退出码=1
$ ls doc/evidence/v0.5.3        # 拒登时不产生任何证据文件
ls: 无法访问 'doc/evidence/v0.5.3': 没有那个文件或目录
```

**A1 结论：通过。** 三项（判 FAIL / 退出码 1 / 拒登）全部以真实输出坐实。

**附带核**：新摘录格式端到端可用，且**摘录本身可被 svacheck 独立复判**（探针文件已删除，未回填 testplan）：

```
$ python3 scripts/evidence.py --scen REV-PROBE-FMT --test ppa_m2_04_test --seed 1
证据已生成: doc/evidence/v0.5.3/REV-PROBE-FMT.log
testplan.md 中未找到 ID 为 REV-PROBE-FMT 的表行     ← 未找到即不写 testplan，工作区未被污染
## SVA 断言汇总（VCS -assert verbose 原生计数，0 failures 才登证据）
Summary: 91 assertions, 88 with attempts, 0 with failures
$ python3 scripts/svacheck.py doc/evidence/v0.5.3/REV-PROBE-FMT.log
CLEAN     doc/evidence/v0.5.3/REV-PROBE-FMT.log
```

### A2. 误伤（假阳）与漏报（假阴）——自建语料

#### A2-a 误伤：结论成立，但**修复人给的支撑证据是虚的**

我自建三类语料，全部判 CLEAN：

| 语料 | 来源 | 判定 |
| --- | --- | --- |
| 33 份真实 log（32 回归 + comp.log） | 本机实跑产出 | 全 CLEAN，退出码 0 |
| 真实 VCS 编译错误 log（`Error-[SE] Syntax error`） | 现编一个语法错文件真跑 vcs 得到 | CLEAN |
| 我自建的 13 行对抗样例 | 见下 | CLEAN |

对抗样例（比修复人那 7 类更贴边，含**引用形态**与**近似形态**）：

- `UVM_INFO …[CHK] length_error_o=1 type_error_o=0 chk_error_o=1 期望一致`（信号名在正文）
- `UVM_INFO …[FSM] 状态进入 ERROR_STATE，随后回 IDLE`
- `UVM_ERROR :    0` / `UVM_FATAL :    0`
- 真实 `not finished` 尾巴行（逐字取自真实 log）
- **近似形态**：`"../rtl/packet_proc_core.sv", 326: tb_top.u_packet_proc_core.a_format_ok_consistency: started at 85000ps succeeded at 85000ps`（`succeeded` 而非 `failed`）
- **引用形态**：`UVM_INFO …[HIST] 历史记录: "../rtl/packet_proc_core.sv", 326: tb_top.u.a_y: started at 85000ps failed at 85000ps`（被前缀顶开，非行首）
- **引用形态**：`# 文档引用: Summary: 91 assertions, 88 with attempts, 3 with failures`
- `*Verdi* Error: …`、`Error: "../tb/x.sv", 12: 这里没有层次名 at time 5 ns`

**误伤结论：0 处误伤，成立。**

但**必须记一笔诚实性问题**：commit `461aebc` message 与 `doc/log.md` 第 11 行称
「最强实证是全回归 32/32 PASS——**这 32 份 log 遍布这些信号名**，一条未被误伤」。实测**不成立**：

```
$ cd $SP/outlogs && for p in length_error type_error chk_error ERROR_STATE; do
      printf '%-14s 出现行数=%s\n' $p "$(grep -h $p *.log | wc -l)"; done
length_error   出现行数=0
type_error     出现行数=0
chk_error      出现行数=0
ERROR_STATE    出现行数=0
$ grep -c "length_error\|type_error\|chk_error" <(UVM_VERBOSITY=UVM_HIGH 跑出的 log)
0                                   # 提到 UVM_HIGH 仍为 0
$ grep -rh "length_error\|type_error\|chk_error\|ERROR_STATE" doc/evidence/ --include=*.log | wc -l
0                                   # 33 份归档摘录里同样一次都没有
$ grep -rn "ERROR_STATE" rtl/ tb/ | wc -l
0                                   # ERROR_STATE 这个名字在本仓库根本不存在
```

那 187 处信号名只存在于**源码**里，不在 log 里。所以「32/32 PASS」对**这几个模式**的误伤零证明力，
是一句典型的过度归因。**结论本身没错（我用自己的语料重新立住了），但那句支撑话必须从对外材料里删掉**——
它正是 §4.2 要防的那类「听上去很硬、实际不成立」的表述。

#### A2-b 漏报：我构造出了**能骗过判定**的样例（重大发现，如实记）

**漏报 1（可复现，已实测）：`$assertoff` / 断言被摘出编译 → 真违例但判 CLEAN。**

```systemverilog
module mb3;
  a_never_bad: assert property (@(posedge clk) !bad) else $error("bad 置起");
  initial begin $assertoff(0, mb3); … bad = 1; … end   // 真实违例发生
endmodule
```
```
$ ./simv3 -assert verbose -l run_assertoff.log ; grep Summary run_assertoff.log
Summary: 2 assertions, 0 with attempts, 0 with failures
$ python3 scripts/svacheck.py …/run_assertoff.log ; echo 退出码=$?
CLEAN     …/run_assertoff.log
退出码=0
```

要害：**判定只看第三个数（failures），完全不看第二个数（attempts）**。`0 with attempts` 就写在同一行里、
信息完全可得，却被忽略。同一形态还包括「有人把 `tb/sva/*.sv` 从 flist 里摘掉」——总数掉下来、
failures 仍是 0 → 依旧 CLEAN、回归依旧全绿。当前仓库没有 `$assertoff`（`grep -rn '\$assert' tb/ rtl/ sim/`
无命中），所以**今天不成立、但机制上敞着**。
**建议加固**：`attempted > 0` 作为硬条件（与「缺汇总行即 FAIL」同级 fail-closed）；更强的做法是把
每代的期望实例数（当前 91/88）落成基线，掉数即 FAIL。

**漏报 2（层 1/1b 对 `::` 层次名结构性失明）。** 类作用域断言（如 UVM 库里的立即断言、DV 未来写在 UVM
组件里的 `assert(...)`）失败时，引擎行的层次名形如 `p::\chk::check .unnamed$$_0`，含 `::` 与空格，
而两条正则的 hier 段是 `[^\s:]+`：

```
$ python3 - <<'PY'   # 对一份真有 2 次类内立即断言失败的 log 逐层拆解
层1 (started/failed at) 命中: 0
层1b (Error:/Fatal:)   命中: 0
层2 (Summary)          命中: {'total': 2, 'attempted': 1, 'failed': 1}
PY
```

净效果安全（层 2 兜住了，判 SVA_FAIL），但 `svacheck.py` 文件头「层 1 …是主锚点…**不依赖任何编译选项**，
fail-closed」这句对该类**不成立**——该类唯一起作用的是依赖 `-assert verbose` 的层 2。
**建议加固**：hier 段放宽到允许 `:` 与转义标识符里的空格。

**漏报 3（`SUMMARY_RE` 取最后一条）。** `scan_text()` 对多条 Summary「取最后一条」。拼接 log（先失败后干净）
即可骗过：

```
$ cat two_summaries.log
Summary: 91 assertions, 88 with attempts, 5 with failures
--- 第二次运行 ---
Summary: 91 assertions, 88 with attempts, 0 with failures
$ python3 scripts/svacheck.py two_summaries.log ; echo 退出码=$?
CLEAN     …/two_summaries.log
退出码=0
```

标准流程下 `-l` 是覆盖写、不会拼接，**现实性低**；但 `evidence.py --log <任意路径>` 能指向任意文件，
且与漏报 2 组合（层 1 失明 + 末条汇总干净）就是一条完整的逃逸路径。
**建议加固**：改为「任一条 Summary 的 failures>0 即失败」（取 max，不取 last）。

**三条均为新机制自身的加固项，不是 BUG-014 所报缺陷的残留**，处置见 §D。

### A3. fail-closed 实测：去掉 `-assert verbose` 后判定**变严格（安全）**

| 场景 | 现象 | `regress.py` 判定 |
| --- | --- | --- |
| 有断言失败 + 去掉 `-assert verbose` | 引擎失败行**照常打印**（模块作用域并发断言不依赖该选项） | `('FAIL', 'SVA失败: 2 条断言/4 次')` |
| 干净仿真 + 去掉 `-assert verbose` | 无 `Summary:` 行 | `('FAIL', '缺 VCS 断言汇总行（-assert verbose 未生效？）')` |

```
$ ./out_neg/simv … -l out_neg/noverbose_fail.log     # 无 -assert verbose
$ python3 -c "…regress.parse_log('sim/out_neg/noverbose_fail.log')"
('FAIL', 'SVA失败: 2 条断言/4 次')
$ ./out_rev/simv … -l out_rev/noverbose_clean.log    # 干净 + 无 -assert verbose
('FAIL', '缺 VCS 断言汇总行（-assert verbose 未生效？）')
$ python3 scripts/evidence.py --scen … --log sim/out_rev/noverbose_clean.log ; echo 退出码=$?
log 中找不到 VCS 断言汇总行 'Summary: N assertions, ...'——无法证明 SVA 断言零失败，拒登证据。…
退出码=1
```

**结论：变严格，fail-closed 成立。** 一处口径提醒：fail-closed 落在 `regress.py`/`evidence.py`，
**不在 `svacheck.py` 的 CLI 里**——CLI 对无汇总行的 log 打 `CLEAN [无原生汇总行: …]` 且退出码 0。
用 CLI 直接回扫旧 log 会得到「一片 CLEAN」的**无信息量结论**（正是修复人证伪的那条错误路径），
提示语已标注，但任何人引用 CLI 输出时必须知道这一点。

### A4. 历史回扫方法学复核（本项最重）

#### (1) 「扫归档摘录无效」这个前提——**属实，且我独立坐实了**

```
$ grep -l "failed at\|started at\|Summary:.*assertions" $(find doc/evidence -name "*.log") | wc -l
0                                        # 33 份归档摘录里，断言信息一条都没有
$ git show a039413:scripts/evidence.py | grep -n "KEY_LINE_RE\s*=" -A1
25:KEY_LINE_RE = re.compile(r"(?i)\b(pass|match|compare ok|check ok)\b")
```

修复前的摘录规则 = 「UVM Report Summary 前后 15 行」+「含 pass/match/compare ok/check ok 或场景 ID 的行」。
断言引擎行 `"file", 45: hier: started at … failed at …` 一个词都不沾，**在设计上必被丢弃**。
所以「扫摘录得 0 漏判」的信息量确实为零。**修复人对 orch 方法的证伪成立**，这是本轮最有价值的一次纠偏。

#### (2) 替代方法**成立**，其两个对照**基本足够**，但有两条前提须写明

方法：`git log --diff-filter=A` 定位添加该证据的 commit → `git archive` 重建源码树 → 按证据首行 TEST+SEED 重跑。

- **选树可靠性**（修复人未验、我补验）：抽查 4 份证据，`git log --oneline -- <file>` 均为 **1 条 commit**
  ——证据文件自加入后从未被改过，`--diff-filter=A` 选出的就是唯一的树。选树无歧义。
- **阳性对照（attempts 非零）**：**必要且到位**。它排除的正是我在 A2-b 漏报 1 里做出来的退化场景
  （断言没编进去/被关断 → 0 failures 但毫无意义）。若无此对照，「0 漏判」等于没说。
  唯一可加强处：用「attempts == 该代的期望数」而非「非零」；不过实测各代 attempts 恰为结构常量
  （见 §C），弱形式在本例中已足够。
- **保真度对照（UVM severity 计数一致）**：方向对，但只比 4 个整数，**偏弱**。我把它加强成
  **摘录「关键检查行」逐行逐字比对**，结果全中（见下表）。加强后的对照足以支撑「重放的是同一次
  仿真所对应的行为」。
- **两条须写明的前提**：① 证据摘录必须产自该 commit 的树（本项目 `/closeout` 自包含提交保证了这点，
  但这是**流程约定**，不是重放本身证明的）；② 工具链未变（同一台 VM、同一 VCS O-2018.09-SP2）。

#### (3) 我自己抽样重做 5 份（M1×2 / M2 / M3 / M4，各里程碑均覆盖）

| 证据 | 添加 commit | TEST/SEED | 当年选项重跑 | 原生汇总（补跑 `-assert verbose`） | svacheck | UVM severity 归档 vs 重放 | 关键检查行逐字命中 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v0.1.6/M1-05 | `5c9d864` | ppa_m1_05_test/1 | rc=0 | `26 assertions, 23 with attempts, 0 with failures` | CLEAN | 10/0/0/0 = 10/0/0/0 | 5/5 |
| v0.1.7/M1-08 | `e167696` | ppa_m1_08_test/1 | rc=0 | `26 assertions, 23 with attempts, 0 with failures` | CLEAN | 10/0/0/0 = 10/0/0/0 | 5/5 |
| v0.2.3/M2-04 | `7bd737a` | ppa_m2_04_test/1 | rc=0 | `42 assertions, 39 with attempts, 0 with failures` | CLEAN | 5/0/0/0 = 5/0/0/0 | 0/0（注） |
| v0.3.0/M3-03 | `2cc0b5f` | ppa_m3_03_test/1 | rc=0 | `91 assertions, 88 with attempts, 0 with failures` | CLEAN | 8/0/0/0 = 8/0/0/0 | 3/3 |
| v0.4.0/M4-02d | `2e6bfed` | ppa_m2_09_reset_test/1 | rc=0 | `91 assertions, 88 with attempts, 0 with failures` | CLEAN | 7/0/0/0 = 7/0/0/0 | 2/2 |

> 注：M2-04 的归档摘录「关键检查行」为空段（`KEY_LINE_RE` 在 core-agent 类测试里无命中）——这是**摘录质量**
> 的既有短板，不是重放缺陷；对这类样本保真度只能退回到 severity 计数（见 §D 的 R7）。

**5 份全部：0 断言失败、attempts 非零、保真度对照全中。与修复人「0 漏判」的结论一致。**

#### (4) 对残余边界的认定

修复人自述的边界——「重放验证的是当年源码在当年 TEST+SEED 下的断言行为，不是当年那次仿真进程的字节级
重演，原始全量 log 已不存在」——**我认**，表述准确、没有夸大。**但要补两条**（上文 (2) 已列）：
证据产自同 commit 的树这一点靠的是流程约定；工具链未变这一点靠的是同机同版本。
另有一条**可审计性**问题：「共回扫 261 份 log」这个数**在仓库里无法重建**（`doc/evidence` 下只有 33 份摘录，
回扫清单未落盘）。结论我用自己的 5 份抽样独立支持，但**「261」这个数字不具备可审计性，不得进对外材料**。

### A5. 用新判定的全回归（本实例独立实跑）

```
$ python3 scripts/regress.py ; echo 退出码=$?
PPA-Lite 回归结果  日期=2026-07-26  通过=32/32
退出码=0
$ diff $SP/bak/result_summary.txt sim/result_summary.txt && echo 逐字一致
逐字一致                                    # 与 HEAD 入库的摘要完全相同
$ grep -h "^Summary:" sim/out/*.log | sort | uniq -c
     32 Summary: 91 assertions, 88 with attempts, 0 with failures
```

另核 `regress.py` 新增的 reason 后缀不破坏下游解析（其 docstring 的自述主张）：

```
RES_ROW 匹配=True   PASS   ppa_m2_04_test SEED=1
RES_ROW 匹配=True   FAIL   ppa_m2_04_test SEED=1  [SVA失败: 2 条断言/4 次]
RES_ROW 匹配=True   FAIL   ppa_m1_01_test SEED=1  [缺 VCS 断言汇总行（-assert verbose 未生效？）]
RES_ROW 匹配=True   NOLOG  ppa_x_test SEED=1
```

---

## B. BUG-013 复验（注释腐烂订正 + 源码守卫）

### B①. 订正后的措辞是否属实——**逐条核实交付事实，不采信注释自述**

| 订正后的主张 | 我的核实方式 | 结果 |
| --- | --- | --- |
| `packet_proc_core` 已于 0.2.2 交付（`b4fb27e`） | `git log --diff-filter=A -- rtl/packet_proc_core.sv` | `b4fb27e feat: DE 交付 packet_proc_core RTL…（0.2.2）` ✅ |
| rtl.f「下列四个模块均已交付并接入 tb_top」 | 读 rtl.f + `grep` tb_top 例化 | rtl.f 列 4 个；tb_top L51/L89/L111/L131 四处例化齐全 ✅ |
| tb_top「并存三条互不相连的通路」 | 同上 | ①`u_apb_slave_if`+`u_packet_sram`+`m3_stub` ②`u_packet_proc_core` ③`u_ppa_top` ✅ |
| scoreboard：m1_seq_lib **31 处** `uvm_error` 比对点 | `grep -c uvm_error tb/uvm/test/m1_seq_lib.sv` | **31** ✅ |
| scoreboard：m3_seq_lib `chk_eq` **定义于该文件 + 14 处调用** | `grep -n chk_eq` → 15 行，L69 为定义 | 定义 1 + 调用 **14** ✅ |
| scoreboard：m4_seq_lib **8 处调用** | `grep -n chk_eq` → 9 行，L3 为注释提及 | 调用 **8** ✅ |
| scoreboard：ppa_core_driver `chk/chkv` **共 8 个调用点** | `grep -n` → L130-133(4) + L135,136,139,140(4)，L146/L153 为定义 | **8** ✅ |
| scoreboard：tb/sva **17 条断言** | `grep -c "assert property" tb/sva/*.sv` | 6+7+4 = **17** ✅ |
| scoreboard：`golden_calc()` **当前无调用者** | `git grep -n golden_calc tb/` | 仅定义行 + 该注释行，**零调用** ✅ |
| 注释指路 `python3 scripts/report.py --summary` 存在 | 实跑 | 存在并现算出这些数 ✅ |

**九项主张全部属实。** 附带记一笔：BUG-013 **登记条目**（orch 写）里的数字「m1_seq_lib 36 处 /
ppa_core_driver 33 处 / m3+m4 chk_eq 共 24 处」与实测不符，且把 `ppa_ref_model` 列为实际检查落点——
DV 在处置中实查推翻并写对了，同时另开 BUG-016。**处置比任务卡更准确，属正向。**
新注释还自带「上列处数会随 TB 演进漂移；落点路径才是承重部分」的免责句 —— 好实践，避免把注释变成
第二个需要维护的计数表。

### B②. 是否纯注释零语义变更——**机械证明**

对 5 个改动文件取 `a039413^` 与 `a039413` 两版，去掉行注释（含字符串字面量保护）与块注释、规范化空白后比对：

```
tb/tb_top.sv                       去注释后代码等同: True   (原始字节差异: True)
tb/m3_stub_if.sv                   去注释后代码等同: True   (原始字节差异: True)
tb/uvm/env/ppa_env.sv              去注释后代码等同: True   (原始字节差异: True)
tb/uvm/env/ppa_scoreboard.sv       去注释后代码等同: True   (原始字节差异: True)
sim/flist/rtl.f                    去注释后代码等同: True   (原始字节差异: True)

结论: 全部纯注释改动
```

**零语义变更成立**，不依赖「回归 32/32 PASS」这一间接背书（该背书我也独立复现了，见 §A5）。

### B③. 新守卫（`report.py --check` 第 7 项）

**(1) 抓得到它要抓的东西——历史回放复现**

```
$ git archive a039413^ | tar -x -C $SP/prefix_tree   # 修复前的树
$ python3 -c "report.ROOT=…prefix_tree; report.scan_source_markers('M5')"
过期承诺 stale = 9  在途 = 0  开放式留白 = 0  已豁免 = 0
  tb/m3_stub_if.sv:1        [M3]  M3（packet_proc_core）本轮尚未交付
  tb/m3_stub_if.sv:12       [M3]  M3 的设计契约（M3 由后续 Lab2 独立交付
  tb/tb_top.sv:28           [M3]  M3 尚未交付
  tb/tb_top.sv:28           [M3]  尚未交付，由 stub 代行 M3
  tb/tb_top.sv:38           [M3]  M3 尚未交付
  tb/uvm/env/ppa_env.sv:9   [M3]  M3 尚未交付
  tb/uvm/env/ppa_scoreboard.sv:2   [M1]  M1 起由 DV 补齐
  tb/uvm/env/ppa_scoreboard.sv:21  [M1]  TODO(M1
  tb/uvm/env/ppa_scoreboard.sv:22  [M3]  TODO(M3
```

「修复前上报 9 处」复现一致。当前树 **0 处**（`report.py --check` 第 7 项实跑：
「76 个文件 / 1039 行注释，当前 M5：过期承诺 0、登记豁免 0、在途承诺 0、开放式留白 0」）。
注意：`sim/flist/rtl.f` 那处过期措辞**守卫抓不到**（它不是「未完成标记」形态），是 DV 手工查出的
——即 6 处订正里有 1 处天然在守卫射程外。

**(2) 不误伤正常设计留白——我自建 9 条应放行样例，0 误报**

放行正确：`M5 尚未交付成果展示层`（在途，合法）、`M1-06 …，M4-02b 同口径`（场景 ID）、
`占位以便将来加仲裁`（守卫对它完全无感）、`TODO: 支持 burst 传输`（开放式留白，只计数）、
`按 BUG-012 补齐 M3 通路的豁免登记`（陈述句，裸「补齐」刻意未收录）、
`M3（packet_proc_core）已于 0.2.2 交付并接入 tb_top`（已交付陈述）。
应报的 3 条（`M3 尚未交付` / `TODO(M1, DV)` / `M2 起由 DV 补齐`）全部命中。**误伤 0。**

**(3) 漏报——我构造的 7 条过期承诺**全部**被放行**

| # | 我写的注释（都是真过期承诺） | 守卫 | 逃逸原因 |
| --- | --- | --- | --- |
| N01 | `packet_proc_core 尚未交付，本接口为其占位` | 放行 | 用**模块名**不用 `M<N>` 编号 |
| N02 | `M3 是包处理核。尚未交付，由 stub 代行。` | 放行 | `。` 切断 `_NEAR` 窗口 |
| N03 | `M3 的 CSR 镜像比对尚未补齐` | 放行 | 「尚未**补齐**」不在 `_UNDONE_V` 里（只认「待补齐」） |
| N04 | `M3（packet_proc_core，详见 doc/design-prompt/packet_proc_core.md）尚未交付` | 放行 | 间隔 > 24 字符 |
| N05 | `TODO: M3 not yet implemented` | 放行（仅计入开放式留白） | 英文措辞 |
| N06 | `M3（packet_proc_core）本轮` / `尚未交付，仅提供桩`（**跨两行**） | 放行 | 逐行扫描，不跨行 |
| N07 | `M3 待定，等 Lab2 再说` | 放行 | 「待定」不在词表 |

**这是本项最需要写清楚的一点**：N04 与 N06 距离**原始缺陷文本只有一步之遥**——原文
`M3（packet_proc_core）本轮尚未交付` 若当初在括号里多写一个文件路径，或换行折了一次，
这道为它而写的守卫就抓不到它。守卫是**精度优先（0 误报）、召回很窄**的设计，作者在
`STALE_MARKER_PATTERNS` 上方的长注释里明确写了这是刻意取舍（避免重演 F10 的失败模式），
逃生口 `report-check:allow-stale-milestone` 也配了 —— **设计意图我认可，不构成关单障碍**。
但边界必须显式化：**「report-check 通过」只等于「不存在 BUG-013 那几种字面形态的过期承诺」，
绝不等于「仓库里没有过期承诺」。** 对外材料不得把它说成后者。建议把本表的召回边界补进
`report.py` 该节的 docstring（属加固项，不是关单条件）。

---

## C. 91 / 88 / 3 的口径落差——裁定

### C1. 三个数分别是什么

| 数 | 含义 | 实证 |
| --- | --- | --- |
| **91** | VCS 运行期已知的断言**实例**总数 = 88（tb_top 域内并发断言）+ 3（uvm_pkg 里的**立即断言**） | URG asserts 报告逐条列出，唯一实例数 = 91 |
| **88** | tb_top 子树内的并发断言实例，**全部被触发** | 源码 49 条 `assert property` 按例化次数展开，见下表 |
| **3** | 那 3 条 uvm_pkg 立即断言 | 见 C2；根因是**度量定义**，不是覆盖漏洞 |

88 的构成（`urg` 逐实例统计，与源码逐条对得上）：

```
  4 tb_top.u_apb_protocol_sva            4 tb_top.u_apb_protocol_sva_top
  8 tb_top.u_apb_slave_if                6 tb_top.u_apb_slave_if.u_apb_slave_if_sva
  9 tb_top.u_packet_proc_core            7 tb_top.u_packet_proc_core.u_packet_proc_core_sva
  5 tb_top.u_packet_sram                10 tb_top.u_ppa_top
  8 tb_top.u_ppa_top.u_apb               6 tb_top.u_ppa_top.u_apb.u_apb_slave_if_sva
  9 tb_top.u_ppa_top.u_core              7 tb_top.u_ppa_top.u_core.u_packet_proc_core_sva
  5 tb_top.u_ppa_top.u_sram                                             合计 = 88
```
（= rtl 8×2 + 5×2 + 9×2 + 10×1 + sva 6×2 + 7×2 + 4×2，与 49 条源码断言的例化展开完全一致。）

### C2. 逐条定位那 3 条

| # | 实例全名 | 源文件 | 域 | 实际执行 |
| --- | --- | --- | --- | --- |
| 1 | `uvm_pkg.\uvm_reg_map::do_read .unnamed$$_0.unnamed$$_1` | `$VCS_HOME/etc/uvm-1.2/reg/uvm_reg_map.svh:2013` `assert($cast(seq,o));` | UVM-1.2 库，**tb_top 域外** | **0 次**（仅当 `adapter.parent_sequence != null` 才走该分支，本项目不走） |
| 2 | `uvm_pkg.\uvm_reg_map::do_write .unnamed$$_0.unnamed$$_1` | 同上 `:2053`，同形态 | 同上 | **0 次** |
| 3 | `uvm_pkg.\uvm_component_name_check_visitor::visit .unnamed$$_0` | `$VCS_HOME/etc/uvm-1.2/base/uvm_traversal.svh` `assert(compiled_regex!=null);` | 同上 | **21 次，21 次成功** |

**为什么第 3 条也被算进「未触发」**：`-assert verbose` 汇总行的「with attempts」**只统计并发断言**，
立即断言无论执行多少次都不计入。我用独立微基准坐实（不动仓库任何文件）：

```
// 2 条并发断言 + 1 条被调用 3 次的类外立即断言
Summary: 3 assertions, 2 with attempts, 0 with failures
// 再加 1 条从不被调用的立即断言
Summary: 4 assertions, 2 with attempts, 0 with failures
```

即：立即断言进「总数」、永不进「with attempts」。故 91−88=3 是**结构常量**，与激励无关——
这也解释了它为何在每份 log、每个里程碑都恒定（见 C4）。

### C3. 与 M4 归档「ASSERT 100.00%」是否自洽

**自洽的是覆盖率结论，不自洽的是 M4 摘录的计数归属。** 我重跑合并覆盖率独立复算：

```
$ make regress COV=1 && make covreset && make cov      # 32/32 PASS
$ urg -dir out/cov.vdb -dir cov_reset_m2/cov.vdb -dir cov_reset_m3/cov.vdb -format text …
Hierarchical coverage data for top-level instances
 97.46 100.00  94.35  90.42 100.00 100.00 100.00 tb_top      # 与 v0.4.0 摘录逐字一致
Summary for Assertions:  Total 91 / Uncovered 2 / Success 89 / Failure 0 / Without Attempts 2
按域拆分：
  Success           共 89：tb_top 域内 88，域外(uvm_pkg) 1  ← uvm_component_name_check_visitor
  Uncovered         共  2：tb_top 域内  0，域外(uvm_pkg) 2  ← uvm_reg_map do_read/do_write
  Without Attempts  共  2：tb_top 域内  0，域外(uvm_pkg) 2
```

- **`ASSERT 100.00%` 的分母是 88，成立：域内 88/88 全 Success、0 失败、0 未触发。**
  分母是 88 还有一条**独立的历史侧锁死**：M3/v0.3.0 归档的 `assert=94.32`，只有 83/88=94.318→94.32
  这一个解（84/89=94.38、86/91=94.51 都对不上）。
- **须订正**：`doc/evidence/v0.4.0/coverage-summary.md` §5 末句「域内 **89/89** 全 Success；91 总计中
  **2 条**未覆盖为 uvm_pkg 库内建断言（域外）」——域内是 **88** 不是 89，域外 uvm_pkg 是 **3** 条不是 2 条。
  89 = 91−2 的算法把第 3 条 uvm_pkg 断言（name-check visitor）默认划进了域内。
- **「2」与「3」不是同一个量**，对不上是**两种度量定义**造成的，不是漏洞：
  - **2** = URG asserts 的 *Without Attempts*（整场仿真一次都没被**求值**的断言）；
  - **3** = `-assert verbose` 的 91−88（未被计入**并发尝试**的断言，含那条被求值 21 次的立即断言）。
  - 两个集合都**只含 uvm_pkg 库断言**，**域内 88 条无一从未触发**。

### C4. 「是否真有一条域内断言从未触发」——排除

我重放的各代树给出决定性旁证（同一实例、同一台机器实跑）：

```
M1 期 (5c9d864 / e167696): 26 assertions, 23 with attempts   → 差 3
M2 期 (7bd737a)          : 42 assertions, 39 with attempts   → 差 3
M3 期 (2cc0b5f)          : 91 assertions, 88 with attempts   → 差 3
M4 期 (2e6bfed)          : 91 assertions, 88 with attempts   → 差 3
HEAD  (32 份回归 log)     : 91 assertions, 88 with attempts   → 差 3
```

断言总数从 26 涨到 91、跨 4 个里程碑，**差值恒为 3**。若是「某条域内断言从未触发」，
这个差值不可能在设计规模翻 3.5 倍的过程中纹丝不动。**结论：口径差异，无域内断言未触发。**

### C5. 对外材料允许的措辞（可直接引用）

> **「PPA-Lite 域内共 88 条断言实例（源码 49 条 `assert property` 按模块例化展开），32 条回归全部触发、
> 零失败，ASSERT 覆盖率 100%（88/88，urg 合并 32 次仿真 + 复位独立库）；VCS 汇总行 `91 assertions,
> 88 with attempts` 中的差额 3 条全部是 UVM-1.2 库的立即断言，位于测量域（tb_top 子树）之外。」**

配套红线（三条，缺一不可）：

1. **可以**写「ASSERT 覆盖率 100%」，但**必须**同时给出分母 88 与测量域 `tb_top`；单写「91 条断言 100%」
   或「49 条断言 100%」都是错的（分别混淆了实例/域与实例展开）。
2. **可以**写「断言失败会让回归变红」（自 0.5.3 起，有本记录 §A1 的负向实验背书）；
   **必须**同时注明「**过去 4 个里程碑期间 49 条断言对回归的拦截力实际为 0，历史清白是事后复算出来的，
   不是当时流程保障的**」。
3. **不得**写「32 份回归 log 遍布信号名故未被误伤」（§A2-a 实测证伪）、**不得**引用「回扫 261 份 log」
   这个数（§A4(4) 不可审计）、**不得**把「report-check 通过」说成「仓库无过期承诺」（§B③(3)）。
   另按 BUG-012 既有结论，仍**不得**写「lint 干净/清零」。

---

## D. 关单判定

### BUG-013 → **CLOSED**

依据：① 订正措辞九项主张逐条核实**全部属实**（§B①，含独立重数，未采信注释自述）；② **纯注释零语义变更**
经去注释机械等价证明（§B②），不依赖回归背书；③ 新守卫对**登记形态**真实有效（修复前树 9 处复现、当前树 0 处），
自建 9 条正常留白样例 **0 误伤**（§B③）。缺陷所报的「代码自述与交付状态矛盾」已消除。
残余（不阻断关单，转加固项）：守卫召回窄，我构造的 7 条过期承诺全部逃逸；`sim/flist/rtl.f` 那类措辞在射程外。

### BUG-014 → **CLOSED**

依据：① 缺陷现象**独立复现**（自选断言、自设破坏方式、仓库源码零改动）——`UVM_ERROR=0` + 退出码 0 而断言
真实失败（§A1）；② 新判定 `regress.py` 判 FAIL 退出码 1、`evidence.py` 拒登退出码 1，均实测（§A1）；
③ 去掉 `-assert verbose` 后判定**变严格**，fail-closed 成立（§A3）；④ 误伤 0（自建三类语料，§A2-a）；
⑤ 历史回扫方法学**成立**，其前提（归档摘录零断言信息）我独立坐实，两个对照基本充分（我把保真度对照
加强为关键检查行逐字比对后仍全中），**自抽 5 份跨 M1/M2/M3/M4 重做，结论一致**（§A4）；
⑥ 新判定下全回归 **32/32 PASS**，`result_summary.txt` 与 HEAD 入库版本逐字一致（§A5）。
缺陷条目要求的三件（判定改造 / 历史回扫 / 复跑 32/32）全部达成。

**转 orch 派单的新登记项**（本轮新发现，均**不是** BUG-013/014 的残留，须另开条目，不得与关单混谈）：

- **R1（高）**：`svacheck.py` 不校验 attempts/总数基线 → `$assertoff` 或把 `tb/sva/*.sv` 摘出 flist 即可
  「真违例、判 CLEAN、回归全绿」，实测样例见 §A2-b 漏报 1。建议 `attempted > 0` 升为硬条件，
  并把每代期望实例数落成基线。
- **R2（中）**：层 1/1b 正则的 hier 段 `[^\s:]+` 对 `::` 层次名（类作用域断言）结构性失明，
  实测层 1/1b 命中 0、仅层 2 兜住（§A2-b 漏报 2）；同时 `svacheck.py` 文件头「层 1 …不依赖任何编译选项、
  fail-closed」对该类不成立，docstring 须一并订正。
- **R3（中）**：`SUMMARY_RE` 取最后一条 → 拼接 log「先失败后干净」判 CLEAN（§A2-b 漏报 3）。建议取 max。
- **R4（中·诚实性）**：`461aebc` commit message 与 `doc/log.md` 的「32 份 log 遍布这些信号名，一条未被误伤」
  **与实测相反**（0 次出现，`ERROR_STATE` 在仓库里根本不存在）；「回扫 261 份 log」不可审计。
  两处须在出材料前订正/落盘清单。
- **R5（低）**：`doc/evidence/v0.4.0/coverage-summary.md` §5 末句计数归属错（域内 88 非 89、域外 uvm_pkg
  3 条非 2 条），结论 100% 不变，措辞须订正（§C3）。
- **R6（低）**：`report.py` 源码注释守卫的召回边界（§B③(3) 七条逃逸样例）建议写进该节 docstring。
- **R7（低）**：`evidence.py` 的 `KEY_LINE_RE` 对 core-agent 类测试无命中（M2-04 摘录「关键检查行」为空段），
  削弱摘录的独立复判价值。
- **R8（极低）**：`REVIEW_KIND_RULES` 无「复验关单」类，本记录归入 `other` 并产生一条 warn。
  该 warn 按设计不阻断（`report.py:1011` 注明「归不了类只是分组标签缺失，不影响任何会印出去的数字」）。
  **本实例刻意不改标题去迎合关键字**——为消一条装饰性 warn 而给记录贴错类别，正是本项目要避免的做法；
  要么补规则，要么保留 warn。

## E. 门禁复核（改动后实跑）

```
$ make docs-check
docs-check 通过
$ python3 scripts/report.py --check
[1/7] spec.md sha256 现算比对: 一致 4880faf8135692f2…
[2/7] 覆盖率摘录 ⇄ 回归摘要 交叉校验：4 份，0 处不符，1 处降级 warn
[3/7] regress.list 32 条 == 最新回归摘要 32 条结果行
[4/7] COV_ANCHORS 漏点守卫: 4 份摘录，0 份缺锚点
[5/7] 生成区新鲜度：已校验 无
[6/7] 静态 data-metric 比对：跳过
[7/7] 源码注释 ⇄ 交付状态（rtl/tb/sim，76 文件 / 1039 行注释，当前 M5）：过期承诺 0、…
report-check 通过（6 条 warn）
```

bugs.md 两行改为 CLOSED + 填复验证据路径后复跑，**两道门禁仍通过**：`docs-check 通过`、
`report-check 通过（7 条 warn）`。warn 由 6 增至 7，新增的那条是 §D-R8（本记录标题未命中
`REVIEW_KIND_RULES`，归入 other），按设计不阻断。

本轮**未 bump、未 commit**；除本记录与 bugs.md 两行外未改动任何文件（`git status --short` 仅余
`M doc/bugs.md`、`?? doc/evidence/v0.5.3/` 与另一实例在途的 `M rtl/apb_slave_if.sv`）。
