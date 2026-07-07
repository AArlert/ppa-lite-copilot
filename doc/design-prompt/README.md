# design-prompt（模块设计输入，arch 撰写）

每个 RTL 模块一份 `<模块名>.md`，是派发 DE 任务时的**完整设计输入**：DE 实例只拿 design-prompt + spec 相关章节开工，不接收其他实例的推理过程（CLAUDE.md §0/§4.3）。

- **写者 = arch**（orch 不产出技术工件）；格式见 `_template.md`。
- **rev 门禁**：design-prompt 经 rev 审查（spec 锚点逐条核对 + 行为泄漏检查）后，orch 才可据此派 DE。
- **行为泄漏禁区**：只写"要做什么、边界是什么、依据在哪"，不写实现方案；**对外可见行为只准引用 spec，不准在此新定义**——需要新行为先走 spec 修改提案（rev 仲裁 → orch 应用 + pin）。
- spec 修改后，受影响的 design-prompt 必须同步（CLAUDE.md §8）。

计划中的文件：`apb_slave_if.md`、`packet_sram.md`、`packet_proc_core.md`、`ppa_top.md`（随各 M 启动时由 arch 补齐；`make next` 会提示缺哪份）。
