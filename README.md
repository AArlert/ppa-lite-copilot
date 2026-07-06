# ppa-lite-copilot

PPA-Lite（APB 包处理加速器）的 IC 设计与验证项目：SystemVerilog RTL + UVM 验证 + AI agent 工作流（DE/DV/REV 角色分离、证据链驱动、低 token 记忆系统）。

- 规格：`doc/spec.md`（单一事实源；原件存档于 commit `b542407`）
- 工作流总纲：`CLAUDE.md`
- 工具链：本地 Synopsys VCS/VCS_MX + Verdi 2018（UVM-1.2）

## 快速开始

```bash
git config core.hooksPath .githooks   # 首次克隆后启用文档软门禁

make handover      # 接手：版本 + 状态 + 最新日志块 + testplan/缺陷统计
make smoke         # 冒烟测试（需本地 VCS）
make run TEST=ppa_smoke_test SEED=42 FSDB=1
make regress       # 一键回归 → sim/result_summary.txt
make cov           # urg 覆盖率报告
make docs-check    # 文档结构 + 证据链守卫（pre-commit/CI 同款）
```

## 目录

```
doc/       spec、记忆系统（status.jsonl/log.md/testplan.md）、bugs.md、design-prompt/、evidence/
rtl/       RTL（按模块组织）
tb/        UVM 环境（一类一文件：apb_agent / env / test）
sim/       VCS Makefile、filelist、回归列表
scripts/   docs.py（handover/check/archive）、bump.py、regress.py
.claude/   agents（de/dv/rev）与 skills（handover/closeout/evidence）
```

## 里程碑与版本

版本 `0.M.P`（`version.json`）：M 对应 spec 的 Lab1–4，P 为里程碑内迭代；选做项按必做对待。M 完成 = feature-matrix 全 ✅ + `make regress` 100% PASS 证据 + rev 审查记录，然后 `make bump-minor` + 打 tag。

| Milestone | 范围 | 模块 |
| --- | --- | --- |
| M1 | Lab1：APB 接口与寄存器 | apb_slave_if + packet_sram |
| M2 | Lab2：包处理核 | packet_proc_core |
| M3 | Lab3：系统集成 | ppa_top |
| M4 | Lab4：回归与覆盖率闭环 | 全系统 |

## 核心纪律

厚存储 · 薄读口，机械交脚本 · 语义留 Agent，单一事实源 + 文档守卫。
没有仿真 log 就没有 ✅——testplan/bugs 的每个通过项都必须指向 `doc/evidence/` 下带复现命令（TEST+SEED）的证据文件，由 `make docs-check` 机械校验。
