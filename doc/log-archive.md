# 交接日志归档

> 默认不读。仅在追溯历史时用 grep 定位（如 `grep -n "\[0.1" doc/log-archive.md`）。
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
