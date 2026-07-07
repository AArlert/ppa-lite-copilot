---
name: handover
description: 接手项目——一条命令获取当前版本、状态首行、最新交接块、testplan/feature-matrix 统计与未关闭缺陷。会话开始或恢复工作时先执行。
---

# 接手流程

1. 执行 `make handover`（= `python3 scripts/docs.py --handover`），通读输出。
2. 执行 `make next` 获取机械推导的行动清单（缺陷推进/待派单/里程碑缺口）；只对清单涉及的条目做针对性精读：用 grep 定位到 testplan/bugs/spec 的具体行，再 Read 局部。
3. 禁止：通读 doc/log-archive.md、doc/status-archive.jsonl、已 ✅ 场景的细节、spec 全文（用 `grep -n "^#" doc/spec.md` 取目录后按章节读）。
4. 接手后如与用户任务冲突，以用户任务为准，但先说明冲突点。
