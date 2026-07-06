# design-prompt（模块设计输入）

每个 RTL 模块一份 `<模块名>.md`，是派发 DE 任务时的**完整设计输入**：DE 实例只拿 design-prompt + spec 相关章节开工，不接收 orch/DV 的推理过程（CLAUDE.md §0/§4.3）。

- 内容由 orch（或上一轮 DE）在派单前撰写/更新，格式见 `_template.md`。
- 只写"要做什么、边界是什么、依据在哪"，不写实现方案——实现自由度留给 DE。
- spec 修改后，受影响的 design-prompt 必须同步（CLAUDE.md §8）。

计划中的文件：`apb_slave_if.md`、`packet_sram.md`、`packet_proc_core.md`、`ppa_top.md`（随各 M 启动时补齐）。
