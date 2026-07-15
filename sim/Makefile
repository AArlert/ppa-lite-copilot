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
FLISTS   := -f flist/tb.f -f flist/rtl.f
# 本 VM 适配：Ubuntu 22.04 的 g++ 默认 -Wl,--as-needed，会剔除 libvcsnew.so 依赖的
# snps*/vfs_* 库导致链接失败（VCS 2018 官方支持的老发行版无此默认），必须显式关闭
LD_FIX   := -LDFLAGS "-Wl,--no-as-needed"
# Verdi PLI（novas.tab + pli.a）：注册 $fsdbDump* 系统任务，FSDB 抓波形必需
NOVAS    := -P $(VERDI_HOME)/share/PLI/VCS/LINUX64/novas.tab \
            $(VERDI_HOME)/share/PLI/VCS/LINUX64/pli.a
VCS_OPTS := -full64 -sverilog -timescale=1ns/1ps -ntb_opts uvm-1.2 \
            -debug_access+all -kdb +vcs+lic+wait $(LD_FIX) $(NOVAS) \
            -o $(OUT)/simv -l $(OUT)/comp.log
SIM_OPTS := +UVM_TESTNAME=$(TEST) +ntb_random_seed=$(SEED) +UVM_VERBOSITY=$(VERB) \
            -l $(OUT)/$(TEST)_$(SEED).log

# 覆盖率口径：spec Lab4 五类 + assert（断言纳入验收，见 spec 第 0 章适配表）
ifeq ($(COV),1)
CM       := -cm line+cond+fsm+tgl+branch+assert -cm_dir $(OUT)/cov.vdb
VCS_OPTS += $(CM)
SIM_OPTS += $(CM) -cm_name $(TEST)_$(SEED)
# 可选覆盖率测量域过滤（M4-04）：CMHIER=<cfg> 传入 VCS -cm_hier（编译+仿真同传），
# 只统计 tb_top 子树、排除 UVM-1.2 库骨架（cfg 见 cov_exclude/cov_domain.cfg）。
# 缺省不传，保持既有全域采集；域覆盖率亦可直接读 urg hierarchy 的 tb_top 顶层实例行。
ifneq ($(CMHIER),)
VCS_OPTS += -cm_hier $(CMHIER)
SIM_OPTS += -cm_hier $(CMHIER)
endif
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

# 复位测试独立覆盖库（M4-02d/e）：ppa_m2_09/ppa_m3_07 各自独立编译+仿真出全量 vdb。
# 原因：VCS O-2018 共享单一 -cm_dir 多 run 累积时，**异步复位 FSM 转移弧**
# （PROCESS→IDLE / DONE→IDLE）在累积并集里不稳定丢弃（同一 test 写独立全量 vdb 能
# 正确记录，已实测确认）；urg 报告期多路 -dir 合并取并集为标准做法，故复位测试另出
# 独立 vdb 与主回归库一并合并，保真记录 FSM 复位弧。功能正确性由测试内 UVM 断言与
# STATUS 清零核对保证（复位注入 test 本身在主回归中已 PASS）。
covreset:
	@$(MAKE) run TEST=ppa_m2_09_reset_test  SEED=1 COV=1 OUT=cov_reset_m2 >/dev/null
	@$(MAKE) run TEST=ppa_m3_07_reset_test  SEED=1 COV=1 OUT=cov_reset_m3 >/dev/null
	@echo "复位测试独立覆盖库已生成: sim/cov_reset_m2/cov.vdb sim/cov_reset_m3/cov.vdb"

# 覆盖率合并报告：主回归共享库 + 复位测试独立库（若存在）报告期并集
cov:
	@dirs="$(OUT)/cov.vdb"; \
	 for d in cov_reset_m2/cov.vdb cov_reset_m3/cov.vdb; do [ -d $$d ] && dirs="$$dirs -dir $$d"; done; \
	 echo "urg 合并: $$dirs"; \
	 urg -full64 -dir $$dirs -report $(OUT)/urgReport
	@echo "覆盖率报告: sim/$(OUT)/urgReport"

# 轻量 lint：VCS +lint 全类目编译检查，DE 交付前必过（告警要么修复、
# 要么登记 doc/lint-waivers.md 由 rev 复核）。SpyGlass 部署后仅替换本目标实现。
# 判定范围限定 ../rtl/ ../tb/（本仓库文件）：+lint=all 连供应商 UVM-1.2 库头文件也一并
# 扫描，那部分噪音不受本仓库控制、DE/DV 无法修复也不该登记豁免，故不计入通过/失败判定
# （原始完整 log 仍写入 $(OUT)/lint.log 供需要时查阅，BUG-005/BUG-006 记录了此边界）。
lint:
	@mkdir -p $(OUT)
	$(VCS) -full64 -sverilog -timescale=1ns/1ps -ntb_opts uvm-1.2 +vcs+lic+wait $(LD_FIX) \
	       +lint=all,noVCDE $(FLISTS) -o $(OUT)/simv_lint -l $(OUT)/lint.log
	@if grep -A1 '^Lint-\[' $(OUT)/lint.log | grep -qE '^\.\./(rtl|tb)/'; then \
	    grep -A1 '^Lint-\[' $(OUT)/lint.log | grep -B1 -E '^\.\./(rtl|tb)/'; \
	    echo "lint 有告警（本仓库文件范围内）：修复，或登记 doc/lint-waivers.md 后由 rev 复核"; exit 1; \
	else echo "lint 干净（../rtl/ ../tb/ 范围内0告警）: sim/$(OUT)/lint.log"; fi

verdi:
	verdi -ssf $(OUT)/wave.fsdb &

clean:
	rm -rf $(OUT) csrc simv* *.daidir ucli.key vc_hdrs.h novas.* verdiLog nWaveLog
