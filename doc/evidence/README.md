# 证据链目录

> testplan/bugs 里每个 ✅/CLOSED 都指向本目录下一个真实文件，docs-check 机械校验存在性。

约定：

- 路径：`doc/evidence/v0.M.P/<场景ID或BUG-ID>.log`；里程碑级证据（回归摘要、覆盖率摘要、rev 审查记录）放 `doc/evidence/v0.M.P/` 根下。
- 内容 = 仿真 log **摘录**（不是全量 log），**由 `make evidence` / scripts/evidence.py 机械生成**：首行完整复现命令（含 TEST、SEED）、生成戳、UVM report summary 与关键检查行。禁止手写；全量 log/波形/覆盖率 HTML 不入库（.gitignore 已拦）。
- 回归证据：`sim/result_summary.txt` 在里程碑收尾时复制为 `doc/evidence/v0.M.P/result_summary.txt`。
- 覆盖率证据：urg 报告的 summary 文本（如 urgReport/summary.txt）摘录入库，GUI 报告本地留存。
