---
name: closeout
description: 工作周期收尾——bump 生成骨架、填语义、过门禁、提交、推送。每次实质性工作结束、commit 之前执行。
---

# 收尾流程（顺序固定，不可跳步）

1. **证据核对**：本周期的场景证据应已由 `make evidence` 登记（testplan/bugs 状态由脚本回填过）；有遗漏先补。里程碑收尾另需三件人工证据（见 /evidence 第 5 条）+ rev 签核 + 核对 `make next` 显示三条硬条件已齐。
2. **bump**：`make bump`（里程碑完成用 `make bump-minor`，随后 `git tag v0.M.P`）。脚本会自动在 status.jsonl / log.md 顶部插入 TODO 骨架（date/version 已写好）。
3. **填 log.md 首块四问**：做了什么 / 没做什么 / 下一步 / 如何验证。写给"完全没看过本次对话的接手者"。
4. **填 status.jsonl 首行 summary**：≤200 字符总览，细节留给 log 块。
5. **归档检查**：`make docs-archive`（无需归档时自动跳过）。
6. **门禁**：`make docs-check` 必须通过（TODO 未填会被拦）；修到通过，禁止 --no-verify 绕过。
7. **commit**：中文 Conventional Commits，源码+测试+文档同一提交。
8. **push**：`git push`（CLAUDE.md §6，用户长期授权，无需每次再问）。失败（网络/冲突/认证）如实汇报，不静默跳过、不 force push；冲突需先 fetch+rebase 或询问用户，不擅自覆盖远端。
