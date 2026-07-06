# PPA-Lite 仿真入口（Synopsys VCS/VCS_MX + Verdi 2018，UVM-1.2）
# 常用:
#   make smoke                          冒烟
#   make run TEST=<test> SEED=<n>       单测（FSDB=1 抓波形，COV=1 收覆盖率）
#   make regress [COV=1]                一键回归 → ../sim/result_summary.txt
#   make cov                            urg 覆盖率报告（out/urgReport）
#   make verdi TEST=<test> SEED=<n>     看波形
.PHONY: compile run smoke regress cov verdi clean

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

# 五类覆盖率口径与 spec Lab4 对齐：line+cond+fsm+tgl+branch
ifeq ($(COV),1)
CM       := -cm line+cond+fsm+tgl+branch -cm_dir $(OUT)/cov.vdb
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

verdi:
	verdi -ssf $(OUT)/wave.fsdb &

clean:
	rm -rf $(OUT) csrc simv* *.daidir ucli.key vc_hdrs.h novas.* verdiLog nWaveLog
