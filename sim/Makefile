# PPA-Lite 仿真入口（Synopsys VCS/VCS_MX + Verdi 2018，UVM-1.2）
# 常用:
#   make smoke                          冒烟
#   make run TEST=<test> SEED=<n>       单测（FSDB=1 抓波形，COV=1 收覆盖率）
#   make regress [COV=1]                一键回归 → ../sim/result_summary.txt
#   make cov                            urg 覆盖率报告（out/urgReport）
#   make lint                           轻量 lint（VCS +lint；SpyGlass 到位后换后端，入口不变）
#   make verdi TEST=<test> SEED=<n>     看波形
.PHONY: compile run smoke regress cov lint verdi clean

TEST ?= ppa_smoke_test
SEED ?= 1
VERB ?= UVM_MEDIUM
COV  ?= 0
FSDB ?= 0
OUT  ?= out

VCS      := vcs
FLISTS   := -f flist/rtl.f -f flist/tb.f
VCS_OPTS := -full64 -sverilog -timescale=1ns/1ps -ntb_opts uvm-1.2 \
            -debug_access+all -kdb +vcs+lic+wait \
            -o $(OUT)/simv -l $(OUT)/comp.log
SIM_OPTS := +UVM_TESTNAME=$(TEST) +ntb_random_seed=$(SEED) +UVM_VERBOSITY=$(VERB) \
            -l $(OUT)/$(TEST)_$(SEED).log

# 覆盖率口径：spec Lab4 五类 + assert（断言纳入验收，见 spec 第 0 章适配表）
ifeq ($(COV),1)
CM       := -cm line+cond+fsm+tgl+branch+assert -cm_dir $(OUT)/cov.vdb
VCS_OPTS += $(CM)
SIM_OPTS += $(CM) -cm_name $(TEST)_$(SEED)
endif

ifeq ($(FSDB),1)
VCS_OPTS += +define+DUMP_FSDB
endif

compile:
	@mkdir -p $(OUT)
	$(VCS) $(VCS_OPTS) $(FLISTS)

run: compile
	$(OUT)/simv $(SIM_OPTS)

smoke:
	@$(MAKE) run TEST=ppa_smoke_test SEED=1

regress:
	@python3 ../scripts/regress.py regress/regress.list $(if $(filter 1,$(COV)),COV=1)

cov:
	urg -full64 -dir $(OUT)/cov.vdb -report $(OUT)/urgReport
	@echo "覆盖率报告: sim/$(OUT)/urgReport"

# 轻量 lint：VCS +lint 全类目编译检查，DE 交付前必过（告警要么修复、
# 要么登记 doc/lint-waivers.md 由 rev 复核）。SpyGlass 部署后仅替换本目标实现。
lint:
	@mkdir -p $(OUT)
	$(VCS) -full64 -sverilog -timescale=1ns/1ps -ntb_opts uvm-1.2 +vcs+lic+wait \
	       +lint=all,noVCDE $(FLISTS) -o $(OUT)/simv_lint -l $(OUT)/lint.log
	@if grep -q "Lint-" $(OUT)/lint.log; then \
	    grep "Lint-" $(OUT)/lint.log | head -50; \
	    echo "lint 有告警：修复，或登记 doc/lint-waivers.md 后由 rev 复核"; exit 1; \
	else echo "lint 干净: sim/$(OUT)/lint.log"; fi

verdi:
	verdi -ssf $(OUT)/wave.fsdb &

clean:
	rm -rf $(OUT) csrc simv* *.daidir ucli.key vc_hdrs.h novas.* verdiLog nWaveLog
