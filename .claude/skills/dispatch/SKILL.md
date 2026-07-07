---
name: dispatch
description: 派单卡组装——orch 派 DE/DV/rev 任务前按固定模板组装输入、选档位、过隔离自查。每次派发 subagent 之前执行。
---

# 派单流程（orch 专用）

## 1. 选档位（Agent 调用的 model 参数；不传则用 agents 默认 opus）

- **低档 haiku**：机械改动——回填表格、搬文件、格式化、按明确指令的小修。
- **中档 sonnet**：常规编码——按模板写场景/序列、结构清晰的 RTL 模块、证据登记。
- **高档 opus**：架构设计、跨模块改动、疑难 debug、仲裁与里程碑签核。

## 2. 组装任务卡（只放清单内的输入，防共模泄漏）

先 `make next` 拿机械推导的行动清单，再按卡型组卡：

| 卡型 | 必给输入 | 禁放内容 |
| --- | --- | --- |
| arch 设计输入 | spec 章节号（或新需求描述）、feature-matrix 范围、_template.md 路径 | orch 对实现/微架构的预设结论 |
| arch spec 提案 | 歧义/适配点的 BUG-ID 或描述、涉及章节号 | 任何一方的期望裁决方向 |
| DE 新功能 | doc/design-prompt/<模块>.md 路径（**须已过 rev 门禁**）、spec 章节号、feature-matrix 编号、接口文件路径 | DV 检查器代码/推理、arch 被打回的草稿 |
| DE 修复 | bugs.md 条目 ID（现象/最小复现/spec 依据）、spec 章节号、相关 rtl 文件路径 | DV checker 的期望值推导、波形分析的推理过程 |
| DV 场景 | testplan 行 ID、spec 章节号、rtl 模块端口定义（模块头，非实现体）、tb/uvm/env/ppa_reg_defs.sv | DE 的实现思路、RTL 内部实现细节、design-prompt |
| DV 复验 | bugs.md 条目 ID、登记的 TEST+SEED、需带跑的回归范围 | DE 修复过程的推理（只给修复 commit 号） |
| rev 门禁/审查/仲裁/签核 | 审查对象清单（文件/条目）、判据出处（spec 章节 / CLAUDE.md §4.1） | 任何一方的口头结论转述（让 rev 自己读原始材料） |

## 3. 派单前自查（逐条确认）

- [ ] 全新实例；不复用做过同一模块另一角色任务的实例；arch 与 rev 分实例（CLAUDE.md §0 硬规则）。
- [ ] 卡内只有文件路径、章节号、条目 ID——没有其他实例的推理过程。
- [ ] 派 DE 新功能前，design-prompt 已过 rev 门禁（行为泄漏检查）。
- [ ] 缺陷派单前已在 bugs.md 登记（禁止口头派单）。
- [ ] 任务卡写明交付判据（rev 门禁通过 / 编译+lint 干净 / 场景 PASS+证据 / 审查记录路径）。

## 4. 回收核对

- 对照角色 md 的"交付汇报"固定格式验收；缺项就退回补齐。
- 证据只认 `make evidence` 生成的文件（首行复现命令+生成戳）；交付/验证状态由脚本现算（`make next` 查看），orch 不维护任何状态位。
- 状态位（testplan/bugs）由 evidence.py 回填；`make docs-check` 过一遍再收单。
