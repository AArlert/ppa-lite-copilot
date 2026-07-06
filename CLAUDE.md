# CLAUDE.md

PPA-Lite（APB 包处理加速器）的 IC 设计与验证项目。全部工作围绕 `doc/spec.md` 展开。
核心纪律：**厚存储 · 薄读口，机械交脚本 · 语义留 Agent，单一事实源 + 文档守卫**。

## 0. 角色与调度（orch = 主会话）

主会话即 orchestrator（orch）：拆解任务、调度 subagent、维护记忆系统、把关里程碑。专业工作派发给 `.claude/agents/` 下的角色：

| 角色 | 职责 | 边界 |
| --- | --- | --- |
| `de` | RTL 设计（rtl/） | 不改 tb/，不改 testplan 状态位 |
| `dv` | UVM 验证（tb/、testplan） | 参考模型/检查器只准从 spec（含第 0 章与修改记录）推导，禁止照抄 RTL 行为 |
| `rev` | 审查（代码/checker/里程碑签核） | 只读 + 出具审查记录，不直接改代码 |

**DE/DV 实例隔离（硬规则）**：同一模块的设计与验证必须由**不同的 subagent 实例**完成——DE 实例交付 RTL 后即终止，DV 任务必须新起实例，禁止向 DV 实例粘贴 DE 实例的推理过程（只允许共享 spec/errata/接口文件）。目的：切断共模错误传播。

按任务难度选 subagent 档位以节省 token：机械改动用低档，常规编码用中档，架构/疑难调试用高档。

## 1. 仓库结构

```
doc/       spec.md（单一事实源）+ 记忆系统 + bugs.md 缺陷登记 + design-prompt/ 模块设计提示 + evidence/ 证据链
rtl/       RTL 源码（按模块组织，不按 lab 组织）
tb/        UVM 验证环境（一个类一个文件）
sim/       VCS 仿真入口（Makefile、filelist、回归列表）
scripts/   机械工作脚本（docs.py / bump.py / regress.py）
.claude/   agents（de/dv/rev）与 skills（handover/closeout/evidence）
```

## 2. 语言与风格

- 注释、文档、commit message 用简体中文；标识符用英文；SystemVerilog 遵循 lowercase_with_underscores。
- UVM 一个类一个文件，由 `*_pkg.sv` 汇总 `include`；`tb/uvm/env/ppa_reg_defs.sv` 是地址/常量的唯一定义点，禁止在别处硬编码寄存器地址。

## 3. 记忆系统 ★

**接手第一步**：`make handover`（= `python3 scripts/docs.py --handover`），输出当前版本、status 首行、log 最新块、testplan/feature-matrix 统计。禁止靠通读文件来接手。

三个滚动文件（doc/ 下）：

1. `status.jsonl` — 首行 = 当前总览（JSON：date/version/summary，summary ≤ 200 字符）；其余行为历史快照，新的在上。
2. `log.md` — 交接日志，块以 `## [版本] 日期 标题` 开头，新的在上；仓库内最多保留 4 块，多了由脚本归档。
3. `testplan.md` — 场景真值表，状态位 ✅/❌/⚠️/🔲。

归档件 `log-archive.md` / `status-archive.jsonl` **默认不读**，只在追溯历史时 grep。

**Token 纪律**：用 grep/rg 定位再精读，不通读大文件；不读归档件；不读已 ✅ 的条目细节；spec.md 按章节号定位（`grep -n "^#" doc/spec.md` 取目录）。

## 4. 开发工作流

1. `make handover` 接手
2. 先在 `testplan.md` 登记/更新目标场景（编码之前）
3. DE 写 RTL / DV 写 TB（分实例，见 §0）
4. 本地仿真：`make smoke` / `make run TEST=xx SEED=n` / `make regress`
5. 依 §4.2 登记证据，更新 testplan 状态位（🔲/❌ → ✅）
6. `make bump`（见 §4.1）
7. `log.md` 顶部加新块 + `status.jsonl` 首行更新（做了什么/没做什么/下一步/验证方式）
8. `make docs-check` 通过
9. commit（pre-commit 软门禁会再跑一次 --check）

一步收尾入口：调用 skill `/closeout`。

### 4.1 版本与里程碑

- 版本 `0.M.P` 存于根目录 `version.json`（脚本 `make bump` 改 patch，`make bump-minor` 进入下一 Milestone，或 `python3 scripts/bump.py 0.3.2` 显式指定）。所有实质性变更都要 bump；里程碑完成时打 git tag `v0.M.P`。
- Milestone = spec 的 Lab：M1=Lab1 … M4=Lab4。**选做项按必做对待**。
- **M 完成判据（三条硬条件）**：① feature-matrix 中该 M 全部条目 ✅；② `make regress` 100% PASS 且证据已归档；③ rev 出具审查记录（存 doc/evidence/）。
- 版本累积：0.2.x 包含 0.1.x 的全部内容；进入新 M 后允许回头修复旧 M 的问题，在 log.md 说明并补证据即可，不回退版本号。

### 4.2 证据规则 ★（防验证造假）

- **没有仿真 log 就没有 ✅**：testplan 状态置 ✅ 必须同时填"证据"列（指向 `doc/evidence/` 下真实存在的文件）和"复现"列（含 TEST 与 SEED 的完整命令）。`make docs-check` 会机械校验。
- 证据文件 = 仿真 log 摘录（UVM report summary + 关键检查行），文件首行写复现命令。目录约定：`doc/evidence/v0.M.P/<场景ID>.log`。
- 回归证据：`sim/result_summary.txt`（regress 自动生成）随里程碑复制入 evidence 目录。
- Agent 汇报结果必须与 log 一致；仿真没跑、跑挂了，就如实写 ❌/⚠️，不许"应该能过"。

### 4.3 任务流转与缺陷闭环 ★

正常流转（无缺陷）：

```
orch 选目标（feature-matrix/testplan）→ 补齐 doc/design-prompt/<模块>.md
→ 派 DE 实例（输入 = design-prompt + spec 相关章节）
→ DE 交付 RTL + 编译/lint 自检 → orch 派全新 DV 实例（输入 = spec 章节 + 端口定义 + testplan 行，不含 DE 的推理）
→ DV 建场景跑仿真 → PASS：登证据、testplan 置 ✅ → rev 抽查/里程碑签核 → /closeout
```

缺陷闭环（谁给谁、在哪登记、怎么推进）：

1. **登记**：发现 mismatch（通常是 DV），先自查激励/检查器；仍疑似缺陷就在 `doc/bugs.md` 登记条目——最小复现（TEST+SEED）、现象、期望及其 spec 章节依据。**禁止只在对话里口头传递缺陷**，登记后才允许派单。
2. **派单**：orch 按疑似归属派单——疑似 RTL → 新 DE 实例；疑似 TB → DV 自修（rev 复核）；疑似 spec 歧义 → rev 仲裁。
3. **修复**：DE 只拿 bug 条目 + spec + 接口定义去修（不看 DV 检查器的推理），回填根因与修复 commit，状态 → FIX_READY。
4. **复验与关单**：DV 用登记的 TEST+SEED 复跑并带跑相关回归，填复验证据后置 CLOSED。**关单人 ≠ 修复人**，DE 不得自己关单。
5. **仲裁**：DE/DV 各执一词时，rev 以 spec 为准裁决；spec 本身歧义则走 §8 流程修 spec，bug 置 SPEC_CHANGED，并把裁决衍生的新场景补进 testplan。

状态集合：`OPEN / FIXING / FIX_READY / VERIFYING / CLOSED / TB_BUG / SPEC_CHANGED / WONTFIX`。docs-check 校验状态合法性，CLOSED 必须带复验证据路径。

## 5. 仿真环境（本地 VM：VCS/VCS_MX + Verdi 2018，UVM-1.2）

入口在 `sim/`（根 Makefile 已转发）：

```
make smoke                     # 冒烟测试
make run TEST=<uvm测试> SEED=<n> [FSDB=1] [COV=1]
make regress [COV=1]           # 跑 sim/regress/regress.list，生成 result_summary.txt
make cov                       # urg 合并/出报告（sim/out/urgReport）
make verdi TEST=<..> SEED=<n>  # 看波形
```

- 覆盖率口径按 spec Lab4：line+cond+fsm+tgl+branch，≥90% 合格。
- 本远程容器**没有 VCS**：容器内只做编码与文档工作，仿真结论一律以本地 log 为准（见 §4.2）。

## 6. Git 约定

- 中文 Conventional Commits（`feat:` `fix:` `docs:` `chore:` `test:`）。
- 提交自包含：源码 + 测试 + 文档同一提交。
- 只有用户要求时才建 PR。
- 首次克隆后执行 `git config core.hooksPath .githooks` 启用软门禁。

## 7. 质量门禁

- 本地软门禁（pre-commit）：`docs.py --check` —— log 块超量未归档、status 行超限、✅ 无证据、版本不同步、spec.md 被改动，任一触发即拦截。
- CI 硬门禁（GitHub Actions）：同样跑 `docs.py --check`。仿真类硬门禁在本地：`make regress` 100% PASS 是里程碑完成的必要条件。

## 8. 单一事实源

- `doc/spec.md` 是项目规格与单一事实源。原件已单独存档（commit `b542407`）；当前版本**允许修改**（歧义裁决、工程适配），但每次修改必须：① spec 顶部"修改记录"表加条目；② `python3 scripts/docs.py --pin-spec` 重新钉住（docs-check 用 sha256 拦截未登记的悄悄改动）；③ 同步受影响的 testplan / design-prompt / bugs 条目。
- DE 与 DV 对行为的一切主张都引用 spec 章节号（第 0 章适配表优先）；歧义先在 bugs.md 登记（SPEC_CHANGED 路径），仲裁后才改 spec，禁止各自脑补。
- 寄存器地址/常量只在 `tb/uvm/env/ppa_reg_defs.sv`（TB 侧）定义一次；各模块的设计输入放 `doc/design-prompt/<模块>.md`（结构见该目录 README，由 orch/DE 按需撰写）。
