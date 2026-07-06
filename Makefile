# PPA-Lite 根 Makefile：文档机械层入口 + 仿真入口转发（仿真在 sim/ 执行）
.PHONY: handover docs-check docs-archive bump bump-minor smoke run regress cov verdi clean

# ---- 文档 / 记忆系统 ----
handover:
	@python3 scripts/docs.py --handover

docs-check:
	@python3 scripts/docs.py --check

docs-archive:
	@python3 scripts/docs.py --archive

bump:
	@python3 scripts/bump.py

bump-minor:
	@python3 scripts/bump.py minor

# ---- 仿真（本地 VM，需 VCS/Verdi 环境）----
smoke run regress cov verdi clean:
	@$(MAKE) -C sim $@ $(MAKEFLAGS_PASS)
