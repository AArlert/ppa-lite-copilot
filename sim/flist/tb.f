// TB 编译清单（路径相对 sim/），顺序：接口 → 常量包 → agent 包 → env 包 → test 包 → 顶层
+incdir+../tb/uvm/apb_agent
+incdir+../tb/uvm/env
+incdir+../tb/uvm/test
../tb/apb_if.sv
../tb/uvm/env/ppa_reg_defs.sv
../tb/uvm/apb_agent/apb_agent_pkg.sv
../tb/uvm/env/ppa_env_pkg.sv
../tb/uvm/test/ppa_test_pkg.sv
../tb/tb_top.sv
