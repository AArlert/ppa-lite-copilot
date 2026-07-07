# CLAUDE.md

PPA-Lite（APB 包处理加速器）的 IC 设计与验证项目。全部工作围绕 `doc/spec.md` 展开。
核心纪律：**厚存储 · 薄读口，机械交脚本 · 语义留 Agent，单一事实源 + 文档守卫**。

## 0. 角色与调度（orch = 主会话）

主会话即 orchestrator（orch）：**纯指挥家**——拆解任务、派单与回收核对、维护记忆系统、把关里程碑，**不产出技术工件**（架构、spec 提案、design-prompt 一律归 arch）。专业工作派发给 `.claude/agents/` 下的角色：

| 角色 | 职责 | 边界 |
| --- | --- | --- |
| `arch` | 架构文档、spec 修改提案、design-prompt、feature-matrix 行、接口定义 | 不写 rtl/tb 实现；**对外可见行为必须进 spec，不得只写在 design-prompt**（行为泄漏禁区）；spec 只能提案，经 rev 仲裁后由 orch 应用并 pin |
| `de` | RTL 设计 + RTL 内部不变量断言（rtl/） | 不改 tb/、testplan；编译+lint 自检 |
| `dv` | UVM 环境、接口/协议 SVA（tb/）、testplan 场景、仿真执行与证据 | checker/SVA 只准从 spec（含第 0 章与修改记录）推导，禁止照抄 RTL 行为 |
| `rev` | arch 交付门禁、代码/checker 审查、仲裁、里程碑签核 | 只读分析 + 书面记录，不直接改代码 |

**实例隔离（硬规则）**：同一模块的 DE 与 DV 必须不同实例；arch 与 rev 必须不同实例；实例交付即终止。任务卡里禁止粘贴其他实例的推理过程——只允许共享 spec、接口文件、条目 ID。目的：切断共模错误传播（注意其边界：隔离切不断同模型对同一 spec 的共同误读，所以歧义前置登记 + rev 锚定 spec 的审查同样重要）。

档位选择省 token：机械改动低档（haiku）、常规编码中档（sonnet）、架构/疑难调试/仲裁高档（opus，agents 默认）；经 Agent 调用的 model 参数指定。**派单前用 skill `/dispatch` 组卡**；交付按各角色 md 的"交付汇报"固定格式回收。

## 1. 仓库结构

```
doc/       spec.md（单一事实源）+ 记忆系统 + bugs.md + lint-waivers.md + design-prompt/ + evidence/
rtl/       RTL 源码（按模块组织；含 DE 的内部断言）
tb/        UVM 验证环境（一类一文件）+ sva/（DV 的接口/协议断言，bind 挂接）
sim/       VCS 仿真入口（Makefile、filelist、回归列表）
scripts/   机械工作脚本（docs.py / bump.py / regress.py / evidence.py）
.claude/   agents（arch/de/dv/rev）与 skills（handover/dispatch/evidence/closeout）
```

## 2. 语言与风格

- 注释、文档、commit message 用简体中文；标识符用英文；SystemVerilog 遵循 lowercase_with_underscores。
- UVM 一个类一个文件，由 `*_pkg.sv` 汇总 `include`；`tb/uvm/env/ppa_reg_defs.sv` 是地址/常量的唯一定义点，禁止在别处硬编码寄存器地址。

## 3. 记忆系统 ★

**接手两步**：`make handover`（版本、状态首行、最新交接块、testplan/feature-matrix 统计、未关闭缺陷）+ `make next`（机械推导的下一步行动清单）。禁止靠通读文件来接手。

三个滚动文件（doc/ 下）：

1. `status.jsonl` — 首行 = 当前总览（date/version/summary ≤200 字符）；历史快照在下，新的在上。
2. `log.md` — 交接日志，块头 `## [版本] 日期 标题`，新的在上；仓库内最多 4 块，超限由脚本归档。
3. `testplan.md` — 场景真值表，状态位 ✅/❌/⚠️/🔲（✅ 及证据由 evidence.py 回填）。

`make bump` 会自动在 status/log 顶部插入 TODO 骨架（date/version 脚本写好），agent 只填语义；docs-check 拦截未填的 TODO。归档件 `log-archive.md` / `status-archive.jsonl` **默认不读**，只在追溯历史时 grep。

**Token 纪律**：用 grep/rg 定位再精读，不通读大文件；不读归档件；不读已 ✅ 的条目细节；spec.md 按章节号定位（`grep -n "^#" doc/spec.md` 取目录）。

## 4. 开发工作流（脚本指路：`make next` 告诉你现在该干什么）

1. `make handover` + `make next` 接手。
2. 按 next 清单派单（/dispatch 组卡）：缺设计输入 → 派 arch（交付过 rev 门禁）→ 派 DE → 派全新 DV。
3. DV 编码之前先在 testplan.md 登记/更新场景行。
4. 仿真（见 §5 环境探测）：`make smoke` / `make run TEST=xx SEED=n` / `make regress`。
5. PASS 后 `make evidence SCEN=<ID> TEST=<..> SEED=<n>` 机械生成证据并自动回填。
6. 收尾走 skill `/closeout`：`make bump` → 填 log 四问 + status summary → `make docs-check` → commit。

### 4.1 版本与里程碑

- 版本 `0.M.P` 存于 `version.json`（`make bump` 改 patch，`make bump-minor` 进下一 Milestone，或 `python3 scripts/bump.py 0.3.2` 显式指定）。所有实质性变更都要 bump；里程碑完成时打 git tag `v0.M.P`。
- Milestone = spec 的 Lab：M1=Lab1 … M4=Lab4，**选做项按必做对待**（新项目的 M 定义由 arch 在项目计划中给出）。
- **M 完成判据（三条硬条件，`make next` 机械核对）**：① 该 M 的 RTL 全部就绪且 feature-matrix 关联场景全 ✅（交付/验证状态均由脚本现算，不落盘）；② `make regress` 100% PASS 且证据归档；③ rev 审查记录存 doc/evidence/。
- 版本累积：0.2.x 包含 0.1.x 全部内容；进入新 M 后允许回修旧 M 问题，log 说明并补证据即可，不回退版本号。

### 4.2 证据规则 ★（防验证造假）

- **没有仿真 log 就没有 ✅**。证据一律 `make evidence` 机械生成：脚本校验 UVM_ERROR/FATAL=0、抽取摘录、写 `doc/evidence/v0.M.P/<ID>.log`（首行=含 TEST+SEED 的复现命令）、回填 testplan/bugs。**禁止手写证据文件**。
- 回归证据 `sim/result_summary.txt` 随里程碑复制入 evidence 目录；里程碑另需覆盖率 summary 摘录与 rev 审查记录（人工三件，见 /evidence）。
- Agent 汇报必须与 log 一致；仿真没跑、跑挂了，如实写 ❌/⚠️，不许"应该能过"。

### 4.3 任务流转与缺陷闭环 ★

正常流转（无缺陷）：

```
orch 按 make next 选目标 → 派 arch 补 doc/design-prompt/<模块>.md → rev 门禁（spec 锚点+行为泄漏）
→ 派 DE 实例（输入 = design-prompt + spec 章节）→ DE 交付 RTL+内部断言（编译+lint 自检）
→ 派全新 DV 实例（输入 = spec 章节 + 端口定义 + testplan 行，不含 DE/arch 的推理）
→ DV 建场景+接口 SVA 跑仿真 → PASS：make evidence 登记回填 → rev 抽查/里程碑签核 → /closeout
```

缺陷闭环：

1. **登记**：发现 mismatch（通常是 DV），先自查激励/检查器；仍疑似缺陷就在 `doc/bugs.md` 登记——最小复现（TEST+SEED）、现象、期望及 spec 章节依据。**禁止只在对话里口头传递**。调试过程超出一行的开 `doc/bugs/<BUG-ID>.md` 详情页，表格行留摘要+链接。
2. **派单**：orch 按疑似归属派单——疑似 RTL → 新 DE 实例；疑似 TB → DV 自修（rev 复核）；疑似 spec 歧义 → rev 仲裁。
3. **修复**：DE 只拿 bug 条目 + spec + 接口定义去修，回填根因与修复 commit，状态 → FIX_READY。
4. **复验关单**：DV 用登记的 TEST+SEED 复跑 + 相关回归，`make evidence BUG=<ID> TEST=<..> SEED=<n>` 机械关单。**关单人 ≠ 修复人**。
5. **仲裁**：DE/DV 各执一词时 rev 以 spec 为准裁决；spec 歧义走 §8 修改流程，bug 置 SPEC_CHANGED，裁决衍生的新场景补进 testplan。

状态集合：`OPEN / FIXING / FIX_READY / VERIFYING / CLOSED / TB_BUG / SPEC_CHANGED / WONTFIX`。docs-check 校验状态合法性；FIX_READY/VERIFYING/CLOSED 必须已回填修复 commit，CLOSED 必须带复验证据路径。

## 5. 仿真环境与工具探测 ★

仿真环境部署在**本地 VM**（VCS/VCS_MX + Verdi 2018，UVM-1.2）。任何 agent 开工先探测环境：`command -v vcs`（xverif 用 `command -v xdebug`）：

- **探测到（本地 VM）**：必须真跑闭环——编译、lint、仿真、evidence.py 全部实际执行并以真实输出汇报；**有工具却只"声明未跑"视同违规**。
- **探测不到（远程容器）**：只做编码与文档工作，如实声明未编译/未仿真，结论一律以本地 log 为准（§4.2）。

入口（根 Makefile 已转发 sim/）：

```
make smoke / run TEST=<..> SEED=<n> [FSDB=1] [COV=1] / regress [COV=1] / cov / verdi
make lint                      # VCS +lint 轻量检查；SpyGlass 部署后换后端、入口不变
```

- 覆盖率口径：**六类** line+cond+fsm+tgl+branch+assert，≥90% 合格（spec §0 适配 7）。
- 本地 VM 另有 **xverif 验证调试工具箱**（BLANK2077/xverif，CLI 支持 `--json`）：`xdebug` 波形/设计库、`xcov` 覆盖率、`xloc` UVM log 定位、`xbit` 位运算、`xsva` 断言解释。重度 debug 优先用它而非通读 log；其 skill/MCP 装用户级 `~/.claude/`，不入本仓库。

## 6. Git 约定

- 中文 Conventional Commits（`feat:` `fix:` `docs:` `chore:` `test:`）。
- 提交自包含：源码 + 测试 + 文档同一提交。
- 只有用户要求时才建 PR。
- 首次克隆后执行 `git config core.hooksPath .githooks` 启用软门禁。

## 7. 质量门禁

- 本地软门禁（pre-commit）：`docs.py --check` —— log/status TODO 骨架未填或版本失步、log 块超量未归档、✅ 无证据或 .log 证据首行无复现命令、feature-matrix 幽灵引用/关联场景为空、缺陷单缺修复 commit/复验证据、详情页孤儿、重复 ID、spec.md 被悄改，任一触发即拦截。
- lint 门禁：DE 交付条件——`make lint` 干净，或告警登记 `doc/lint-waivers.md` 经 rev 复核。
- CI 硬门禁（GitHub Actions）：`docs.py --check` + `--handover` 冒烟。仿真类硬门禁在本地：`make regress` 100% PASS 是里程碑完成的必要条件。

## 8. 单一事实源

- `doc/spec.md` 是项目规格与单一事实源。原件已存档（commit `b542407`）；当前版本允许修改，但每次修改必须：① "修改记录"表加条目；② `python3 scripts/docs.py --pin-spec` 重新钉住（未登记的改动会被 sha256 与修改记录增量双重拦截）；③ 同步受影响的 testplan / design-prompt / bugs 条目。
- **修改路径唯一**：任何角色发现歧义/需要新行为 → 登记 bugs.md 或 arch 出提案 → rev 仲裁 → orch 应用 + pin。禁止任何实例直改 spec 正文。
- DE 与 DV 对行为的一切主张引用 spec 章节号（第 0 章适配表优先）；design-prompt 只准约束实现（行为泄漏禁区，见 doc/design-prompt/README.md）。
- 寄存器地址/常量只在 `tb/uvm/env/ppa_reg_defs.sv`（TB 侧）定义一次。
