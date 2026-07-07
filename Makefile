# PPA-Lite 根 Makefile：文档机械层入口 + 仿真入口转发（仿真在 sim/ 执行）
.PHONY: handover next docs-check docs-archive bump bump-minor evidence \
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

# ---- 仿真（本地 VM，需 VCS/Verdi 环境）----
smoke run regress cov lint verdi clean:
	@$(MAKE) -C sim $@ $(MAKEFLAGS_PASS)
