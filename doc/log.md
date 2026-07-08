# 交接日志

> 新块加在最上方，块头格式 `## [版本] 日期 标题`。仓库内最多 4 块，超限由 `make docs-archive` 移入 log-archive.md。
> 每块必答四问：做了什么 / 没做什么 / 下一步 / 如何验证。

## [0.1.4] 2026-07-09 本地 VCS 环境打通 + BUG-001/002 裁决落地 spec（r4/r5）+ xverif 全局部署

**做了什么**
- **本地 VM 仿真环境首次闭环**：`make smoke` PASS（UVM_ERROR/FATAL=0，TB-only）、`make run FSDB=1` 生成波形、`make lint` 机制验证 OK。修了三个环境坑：① `$VCS_HOME/etc/uvm-1.2/dpi/uvm_hdl_vcs.c:34` 弯引号致 GCC 11 报错（已改，`.orig` 备份同目录）；② Ubuntu 22.04 g++ 默认 `--as-needed` 致 VCS 链接失败 → sim/Makefile 加 `LD_FIX`；③ FSDB 系统任务需 Verdi PLI → sim/Makefile 加 `NOVAS`（-P novas.tab pli.a）
- **BUG-001/002 rev 裁决（2026-07-08）由 orch 落地**：spec r4（§5.2/§9.1：exp_pkt_len=0=未配置跳过比对）、r5（§7.3 新增非法包长行为：sum/xor UNSPECIFIED、读拍钳位 min(ceil(pkt_len/4),8)、length_error 第 0 拍判定），已 `--pin-spec`；testplan M2-02/M2-06 描述同步；bugs.md 两单回填"已应用"
- **xverif 验证工具箱部署**：`/home/open_tools/xverif`（Verdi 2018 适配），skill 装 `~/.claude/skills/xverif`（xwiki 记忆系统按用户决定不装）；已用本项目真实 FSDB 实测 xdebug value.at 闭环。部署/重建细节见 `/home/open_tools/xverif/DEPLOYMENT-LOG.md`

**没做什么**
- M1 design-prompt（apb_slave_if / packet_sram）仍缺，未派 arch；RTL 仍为零，全部场景 🔲
- lint 抓到 TB 一条 `Null statement` 告警未处理（待下轮 DV/DE 修复或登记 lint-waivers.md）
- 未试 `make evidence` 全链路（等首个真实场景 PASS 时走）

**下一步**
- 按 `make next`：派 arch 写 apb_slave_if / packet_sram design-prompt（高档）→ rev 门禁 → 派 DE
- BUG-001/002 已 SPEC_CHANGED 终态，后续 DE/DV 直接引用 spec r4/r5 条文，不再引用 bug 单

**如何验证**
- 本地 VM：`cd sim && make smoke`（UVM_ERROR/FATAL=0）、`make run TEST=ppa_smoke_test SEED=2 FSDB=1`（out/wave.fsdb 生成）
- `python3 scripts/docs.py --check` 通过；`grep -n "r4\|r5" doc/spec.md` 可见裁决条文；xverif：`/home/open_tools/xverif/tools/xbit conv "8'shff"`

## [0.1.3] 2026-07-07 工作流 v2：orch 纯指挥家 + arch 角色 + 脚本指路 + SVA/lint 落地

**做了什么**
- 角色重构：orch 收窄为**纯指挥家**（不产出技术工件）；新增 `arch`（spec 修改提案/design-prompt/feature 分解/接口定义；**行为泄漏禁区**——对外可见行为必须进 spec；交付过 rev 门禁后才可派 DE）；rev 增加 arch 交付门禁职责；de/dv 分工加断言（DE 内部不变量 / DV 接口协议 SVA）
- 脚本指路：`make next`（docs.py --next 读三表机械推导下一步：缺陷推进/待派单/里程碑缺口/三条硬条件核对）；`make bump` 自动在 status/log 插 TODO 骨架（date/version 脚本写死，docs-check 拦未填的 TODO）
- 证据机械化：`make evidence`（scripts/evidence.py 校验 0 error → 抽摘录 → 写证据文件 → 自动回填 testplan ✅/bugs CLOSED），**禁止手写证据文件**
- feature-matrix 去状态位：变纯 arch 工件；交付由 rtl/ 文件现算、验证由 testplan 现算（handover/next 展示，不落盘）；docs-check 改查幽灵引用与关联场景必填
- SVA 纳入验收：tb/sva/ 目录约定（bind 挂接、只引端口、每条 property 注明章节号）；覆盖率口径扩为六类（+assert）；spec 第 0 章新增适配 7/8，修改记录 r3，已重新 pin
- lint 落地：`make lint`（VCS +lint，SpyGlass 部署后换后端入口不变）+ doc/lint-waivers.md 登记表（DE 登记、rev 复核）
- 环境探测硬规则（CLAUDE.md §5）：`command -v vcs` 探测到就必须真跑闭环，探测不到才允许声明未跑

**没做什么**
- tb/sva/ 下暂无实际断言文件（随 M1 DV 派单产出）；lint/仿真/evidence.py 未在真实 VCS 环境跑过（本容器无 VCS，evidence.py 以合成 log 测试）
- BUG-001/002 仍 OPEN 待仲裁；M1 design-prompt 仍缺（make next 已列为待办）

**下一步**
- 本地 VM：`make smoke` 验证 TB 骨架 + `make lint` 试跑 + 任选一景试 `make evidence` 全链路
- 按 `make next` 清单：派 rev 仲裁 BUG-001/002 → 派 arch 写 apb_slave_if/packet_sram design-prompt → rev 门禁 → 派 DE

**如何验证**
- 本容器 `make docs-check` / `make handover` / `make next` 通过；故障注入测试：bump 骨架插入与 TODO 拦截、evidence 场景登记/FAIL 拒绝/复验关单、feature-matrix 幽灵引用拦截、rtl 文件出现后交付状态自动翻转与 next 转派 DV，全部按预期

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

