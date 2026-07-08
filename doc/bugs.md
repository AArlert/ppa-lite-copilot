# 缺陷登记表

> 流程见 CLAUDE.md §4.3：发现即登记（禁止只在对话里传递）→ orch 派单 → 修复回填 → **复验关单（关单人 ≠ 修复人）**。
> 状态：`OPEN / FIXING / FIX_READY / VERIFYING / CLOSED / TB_BUG / SPEC_CHANGED / WONTFIX`。
> CLOSED 必须填复验证据（doc/evidence/ 路径，docs-check 校验）。最小复现写完整命令（含 TEST+SEED）。

| ID | 日期 | 版本 | 疑似归属 | 现象摘要 | 最小复现 | spec 依据 | 根因/裁决 | 修复 commit | 状态 | 复验证据 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BUG-001 | 2026-07-06 | 0.1.0 | spec 歧义 | PKT_LEN_EXP 复位值 0，§9.1 说"若已配置"则不符报 length_error，但"已配置"未定义（0 是否表示未配置？） | 静态歧义，无需仿真 | §5.2 §9.1 | rev 裁决（2026-07-08）：确认 `exp_pkt_len==0` = 未配置、跳过 exp 比对；`!=0` 才做一致性检查。依据：合法 pkt_len∈[4,32]（§3.2），0 恒在合法域外，故 0 作哨兵不与任何合法包冲突；若把 0 当"已配置须匹配"，则 §10.1 N-1/N-2/N-3 未写 PKT_LEN_EXP 的合法包将全部误报 length_error 且 format_ok=0，与其期望结果矛盾；附录 B.1 的一致性检查示例用非零 exp=8 亦印证 exp≠0 才生效。§9.1"若已配置"措辞歧义，需 spec 明文（§9.1 length_error 触发条件、§5.2 PKT_LEN_EXP 说明列同改）。**orch 已应用（2026-07-09，spec 修改记录 r4）并重新 pin；testplan M2-06 已同步**。 | - | SPEC_CHANGED | - |
| BUG-002 | 2026-07-06 | 0.1.0 | spec 歧义 | pkt_len 越界（如 3 或 33）时 res_payload_sum/xor 及读取拍数行为未定义 | 静态歧义，无需仿真 | §3.2 §7.3 §9.2 | rev 裁决（2026-07-08）：非法 pkt_len（<4 或 >32）时 (1) res_payload_sum/res_payload_xor 为 UNSPECIFIED/don't-care，验证侧不比对（依据 §10.2 E-1/E-2 只约束 length_error=1/format_ok=0/done=1/不卡死，未规定 sum/xor，与 §10.1 N-2 明列 sum/xor 形成对照）；(2) 读取拍数必须钳在 8-word 窗口内（§6.1 窗口=0x040~0x05C 共 8 word，rd_addr 3-bit=0..7，§2.3），即 §7.3 的 ceil(pkt_len/4) 读拍公式对 pkt_len>32（如 33 需 9 拍/读 Word8）越界，须钳到 ≤8 拍以免读越 SRAM 窗口/卡死。length_error 于第 0 拍即判定（§7.3）。§7.3 读时序默认 pkt_len∈[4,32]，须补明非法长的 sum/xor 与读拍钳位规则。**orch 已应用（2026-07-09，spec 修改记录 r5）并重新 pin；testplan M2-02 已同步**。 | - | SPEC_CHANGED | - |
