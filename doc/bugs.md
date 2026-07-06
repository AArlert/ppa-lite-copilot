# 缺陷登记表

> 流程见 CLAUDE.md §4.3：发现即登记（禁止只在对话里传递）→ orch 派单 → 修复回填 → **复验关单（关单人 ≠ 修复人）**。
> 状态：`OPEN / FIXING / FIX_READY / VERIFYING / CLOSED / TB_BUG / SPEC_CHANGED / WONTFIX`。
> CLOSED 必须填复验证据（doc/evidence/ 路径，docs-check 校验）。最小复现写完整命令（含 TEST+SEED）。

| ID | 日期 | 版本 | 疑似归属 | 现象摘要 | 最小复现 | spec 依据 | 根因/裁决 | 修复 commit | 状态 | 复验证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BUG-001 | 2026-07-06 | 0.1.0 | spec 歧义 | PKT_LEN_EXP 复位值 0，§9.1 说"若已配置"则不符报 length_error，但"已配置"未定义（0 是否表示未配置？） | 静态歧义，无需仿真 | §5.2 §9.1 | 暂定：exp_pkt_len=0 视为未配置（ref model 已按此实现），待 rev 仲裁后写入 spec 修改记录 | - | OPEN | - |
| BUG-002 | 2026-07-06 | 0.1.0 | spec 歧义 | pkt_len 越界（如 3 或 33）时 res_payload_sum/xor 及读取拍数行为未定义 | 静态歧义，无需仿真 | §3.2 §7.3 §9.2 | 暂定：ref model 对非法包长不比对 sum/xor，只比对错误标志，待仲裁 | - | OPEN | - |
