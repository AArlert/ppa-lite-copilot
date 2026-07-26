# 证据链目录

> testplan/bugs 里每个 ✅/CLOSED 都指向本目录下一个真实文件，docs-check 机械校验存在性。

约定：

- 路径：`doc/evidence/v0.M.P/<场景ID或BUG-ID>.log`；里程碑级证据（回归摘要、覆盖率摘要、rev 审查记录）放 `doc/evidence/v0.M.P/` 根下。
- 内容 = 仿真 log **摘录**（不是全量 log），**由 `make evidence` / scripts/evidence.py 机械生成**：首行完整复现命令（含 TEST、SEED）、生成戳、UVM report summary 与关键检查行。禁止手写；全量 log/波形/覆盖率 HTML 不入库（.gitignore 已拦）。
- 回归证据：`sim/result_summary.txt` 在里程碑收尾时复制为 `doc/evidence/v0.M.P/result_summary.txt`。
- 覆盖率证据：urg 报告的 summary 文本（如 urgReport/summary.txt）摘录入库，GUI 报告本地留存。

## rev 审查记录的命名沿革

里程碑签核记录的命名规范自 **M2 起**统一为 `review-m<N>-milestone.md`（小写 m），`scripts/docs.py --next` 的里程碑硬条件③按此 glob 机械核对（见 BUG-011）。

**M1 采用的是规范确立之前的旧命名 `v0.1.6/rev-review-M1.md`**，因此 `--next` 的 glob 对它不匹配。这是命名不一致，不是签核缺失——该文件 129 行，含审查人身份声明（与 DE/DV 隔离）、被审 HEAD `ff6b50e`、M 完成三条硬条件逐条独立验算，实质与 M2–M4 的签核记录等价。

**处置：不改历史证据文件名。** 证据文件的不可变性优先于表面整洁——改名会让 `log-archive.md` 等既有引用变成死链，也违背"证据一经归档即不可变"的原则。以本节说明代替改名。

其余非里程碑类记录（门禁 `rev-gate-*` / 仲裁 `review-*-arbitration` / 豁免复核 `review-lint-waiver-*` / 工具与数据层审查 `review-report-tool` 等）不参与里程碑 glob，命名只需自述其对象，**但不得以 `review-m<数字>` 开头**，以免被里程碑签核检查误命中。
