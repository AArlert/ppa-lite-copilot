---
name: evidence
description: 登记仿真证据——用 evidence.py 从仿真 log 机械生成证据文件并自动回填 testplan/bugs。任何场景要置 ✅ 或缺陷要 CLOSED 之前执行。
---

# 证据登记流程（机械生成，禁止手写证据文件）

1. 前提：仿真已真实跑完（`command -v vcs` 有效的环境）。FAIL 的 log 不登证据——场景置 ❌/⚠️，疑似缺陷走 bugs.md。
2. 场景证据：`make evidence SCEN=<场景ID> TEST=<uvm测试> SEED=<n>`
   —— 脚本校验 UVM_ERROR/FATAL=0、抽取 report summary 与关键检查行、写 `doc/evidence/v<版本>/<ID>.log`（首行=复现命令）、自动回填 testplan 行（✅/证据/复现），最后跑一遍 docs-check。
3. 缺陷复验关单：`make evidence BUG=<BUG-ID> TEST=<..> SEED=<n>`（自动置 CLOSED + 复验证据；关单人 ≠ 修复人）。
4. 脚本拒绝时（log 缺失 / FAIL / 找不到表行）按真实情况处理，不得绕过脚本手工造文件。
5. 里程碑级证据仍为人工三件：`sim/result_summary.txt` 复制入 evidence 目录、覆盖率 summary 摘录、rev 审查记录。
