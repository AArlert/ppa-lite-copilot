---
name: closeout
description: 工作周期收尾——按固定顺序更新 testplan/版本/日志/状态并过门禁。每次实质性工作结束、commit 之前执行。
---

# 收尾流程（顺序固定，不可跳步）

1. **testplan/bugs/feature-matrix 状态位**：依据本周期的仿真证据更新（无证据不得 ✅/CLOSED，见 CLAUDE.md §4.2）。新产生的证据先按 /evidence 流程登记。
2. **bump**：`make bump`（里程碑完成用 `make bump-minor`，并核对 CLAUDE.md §4.1 三条硬条件 + rev 签核记录，然后 `git tag v0.M.P`）。
3. **log.md**：顶部加新块 `## [新版本] 日期 标题`，必答四问——做了什么 / 没做什么 / 下一步 / 如何验证。写给"完全没看过本次对话的接手者"。
4. **status.jsonl**：首行更新为当前总览（date/version/summary，≤200 字符；细节留给 log 块）。
5. **归档检查**：`make docs-archive`（无需归档时自动跳过）。
6. **门禁**：`make docs-check` 必须通过；不通过就修到通过，禁止 --no-verify 绕过后提交。
7. **commit**：中文 Conventional Commits，源码+测试+文档同一提交。
