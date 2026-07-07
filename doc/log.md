# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.1.2] 2026-07-07 Agent 工作流强化：/dispatch 派单技能 + 机械守卫升级

**做了什么**
- 新增 skill `/dispatch`：派单卡模板（档位选择/五类卡型输入清单/隔离自查/回收核对），把 §0 实例隔离从"纪律"变成"操作步骤"；CLAUDE.md §0 档位映射落地（低 haiku/中 sonnet/高 opus，经 Agent model 参数）
- de/dv 增加"交付汇报"固定格式（orch 依此回收核对）；rev 补 Edit 工具（限审查记录、bugs.md 裁决与状态列、详情页仲裁段——原先只有 Write，改单元格要整文件重写）
- docs-check 新增守卫：log 首块版本须同步 version.json；✅ 的 .log 证据首行须含 TEST+SEED 复现命令；feature-matrix ✅ 须至少 1 条关联场景已 ✅；FIX_READY/VERIFYING/CLOSED 须回填修复 commit；doc/bugs/ 详情页双向校验（引用存在+无孤儿）；testplan/feature-matrix/bugs 重复 ID 拦截
- `--pin-spec` 防悄改：spec 正文相对 git HEAD 有改动而"修改记录"表未增行时拒绝钉住
- regress.py 修复 COV=1 被误当列表路径的缺陷；列表格式错误带行号报错。CI 增加 handover 冒烟步骤

**没做什么**
- 未动 rtl/tb/sim 功能代码；0.1.1 遗留项（本地 make smoke、BUG-001/002 仲裁、M1 design-prompt）原样待办
- 新守卫尚无真实 ✅ 条目可检（testplan 全 🔲），正确性以故障注入测试为准

**下一步**
- 同 0.1.1：本地 `make smoke` → 仲裁 BUG-001/002 → 写 M1 design-prompt；首次派 DE 时走 `/dispatch` 流程实测派单卡

**如何验证**
- `make docs-check` / `make handover` 本容器通过；11 组故障注入测试（版本失步/伪证据首行/✅联动/缺修复 commit/孤儿详情页/引用缺失/重复 ID/pin-spec 悄改拒绝与登记放行/回归列表格式/COV 参数）全部按预期拦截或放行

## [0.1.1] 2026-07-06 接入 xverif 工具箱说明与缺陷详情页机制

**做了什么**
- CLAUDE.md §5：登记本地 VM 的 xverif 验证调试工具箱（xdebug/xcov/xloc/xbit/xsva，经 Bash 调用，`command -v` 探测）；明确其 skill/MCP 装用户级 `~/.claude/`，不入仓库
- de/dv/rev 三个 agent 各加一行 xverif 调用指引（各自常用子工具不同）
- CLAUDE.md §4.3（借鉴 xverif 的 xwiki issue 页机制）：复杂缺陷可开 `doc/bugs/<BUG-ID>.md` 详情页承载调试过程（候选根因/已排除项/下一步取证），bugs.md 表保持一行摘要+链接，状态仍以表为准

**没做什么**
- xverif 的本机安装（make 编译、PATH、skill 拷贝、MCP 注册、sync_agent_env.py）是用户 VM 侧操作，仓库不含
- 未采用 xwiki 做项目记忆——与现有三文件记忆系统职责重叠且会制造第二事实源，评估结论见本次对话
- 0.1.0 遗留项（本地 make smoke、BUG-001/002 仲裁、M1 design-prompt）原样待办

**下一步**
- 同 0.1.0：本地 `make smoke` → 仲裁 BUG-001/002 → 写 M1 design-prompt 派 DE
- 用户 VM 装好 xverif 后跑一次 `xdebug -h` 确认 PATH 生效

**如何验证**
- `make docs-check` 本容器通过；本次为纯文档变更，无仿真项

## [0.1.0] 2026-07-06 仓库脚手架初始化

**做了什么**
- 原版 spec 单独存档（commit b542407），随后改造为适配版：新增第 0 章偏离表 + 修改记录，正文未动
- 记忆系统三文件 + 归档件 + feature-matrix + bugs.md 建立；docs.py（handover/check/archive/pin-spec）、bump.py、regress.py 完成并自测
- CLAUDE.md：角色调度、DE/DV 实例隔离、任务流转与缺陷闭环、证据规则、版本判据全部成文
- `.claude/agents/`（de/dv/rev）与 `.claude/skills/`（handover/closeout/evidence）就绪
- UVM 骨架（apb agent + env + ref model + smoke test，一类一文件）与 sim/Makefile（VCS+UVM-1.2+五类覆盖率+fsdb）完成
- 门禁：pre-commit 软门禁 + GitHub Actions 硬门禁（均跑 docs.py --check）

**没做什么**
- 未写任何 RTL（rtl/ 为空）；design-prompt 只有目录结构与模板，内容待 orch/DE 撰写
- UVM 骨架与 sim/Makefile **未经本地 VCS 编译**，正确性未验证（本容器无 VCS）
- ppa_ref_model 中 PKT_LEN_EXP=0 视为"未配置"是暂定假设，对应 BUG-001 待仲裁

**下一步**
1. 本地 VM 执行 `make smoke` 验证 TB 骨架可编译可跑（预期 UVM 报告 0 error 即通过）
2. 仲裁 BUG-001/BUG-002（spec 歧义），必要时修 spec + pin
3. 撰写 doc/design-prompt/apb_slave_if.md 与 packet_sram.md，派 DE 启动 M1

**如何验证**
- `make handover` / `make docs-check` 在本容器已通过
- 仿真侧一切结论以本地 VCS log 为准
