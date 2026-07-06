---
name: evidence
description: 登记仿真证据——把一次仿真结果转成 doc/evidence/ 下的证据文件并回填 testplan/bugs。任何场景要置 ✅ 或缺陷要 CLOSED 之前执行。
---

# 证据登记流程

1. 确认仿真 log 真实存在（sim/out/<TEST>_<SEED>.log），且 UVM report summary 中 UVM_ERROR/UVM_FATAL 均为 0（FAIL 就不要登证据，去 bugs.md 登缺陷）。
2. 创建 `doc/evidence/v<当前版本>/<场景ID或BUG-ID>.log`，内容为**摘录**：
   - 首行：完整复现命令，如 `make run TEST=ppa_smoke_test SEED=42`（必须含 TEST 与 SEED）
   - UVM report summary 段
   - 与该场景检查点直接相关的 PASS/比对行（用 grep 从原始 log 摘）
3. 回填 testplan 行：状态 ✅、证据列填相对路径（doc/evidence/...）、复现列填与首行一致的命令。缺陷复验则回填 bugs.md 的复验证据列并置 CLOSED（关单人 ≠ 修复人）。
4. `make docs-check` 验证证据链通过。
5. 里程碑收尾时额外复制：`sim/result_summary.txt` → `doc/evidence/v0.M.P/result_summary.txt`；覆盖率 summary 文本一并摘录。
