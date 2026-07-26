# PPA-Lite 根 Makefile：文档机械层入口 + 仿真入口转发（仿真在 sim/ 执行）
.PHONY: handover next docs-check docs-archive bump bump-minor evidence \
        report report-json report-sync report-check \
        smoke run regress cov lint verdi clean

# ---- 文档 / 记忆系统 ----
handover:
	@python3 scripts/docs.py --handover

next:
	@python3 scripts/docs.py --next

docs-check:
	@python3 scripts/docs.py --check

docs-archive:
	@python3 scripts/docs.py --archive

bump:
	@python3 scripts/bump.py

bump-minor:
	@python3 scripts/bump.py minor

# 证据机械生成（本地 VM 仿真后）：make evidence SCEN=M1-01 TEST=xx SEED=n
#                     缺陷复验关单：make evidence BUG=BUG-003 TEST=xx SEED=n
evidence:
	@python3 scripts/evidence.py $(if $(SCEN),--scen $(SCEN)) $(if $(BUG),--bug $(BUG)) \
		--test $(TEST) --seed $(SEED) $(if $(LOG),--log $(LOG))

# ---- 成果数据（展示材料的唯一取数口；数字一律现算，禁止手写入库）----
report:                       # 打印成果数据（人读）
	@python3 scripts/report.py --summary

report-json:                  # 结构化 JSON（默认 stdout 不落盘）
	@python3 scripts/report.py --json --pretty

# 不在此处罗列目标文件：清单由 report.py 的 TARGETS 单点定义，与 --check 同源
# （分两处各写一份必然漂移——曾出现讲稿"检查得到、同步不到"）
report-sync:                  # 重新注入全部展示材料的生成区
	@python3 scripts/report.py --inject

report-check:                 # 七项校验（含生成区新鲜度、静态数字比对、源码注释⇄交付状态）
	@python3 scripts/report.py --check

# ---- 仿真（本地 VM，需 VCS/Verdi 环境）----
smoke run regress cov lint verdi clean:
	@$(MAKE) -C sim $@ $(MAKEFLAGS_PASS)
