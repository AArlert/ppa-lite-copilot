// TB 编译清单（路径相对 sim/），顺序：接口 → 常量包 → agent 包 → env 包 → test 包 →
// 接口/协议 SVA（bind，需 DUT 模块与 reg_defs 均可见）→ 顶层
+incdir+../tb/uvm/apb_agent
+incdir+../tb/uvm/env
+incdir+../tb/uvm/core_agent
+incdir+../tb/uvm/test
../tb/apb_if.sv
../tb/m3_stub_if.sv
../tb/ppa_core_if.sv
../tb/uvm/env/ppa_reg_defs.sv
../tb/uvm/apb_agent/apb_agent_pkg.sv
../tb/uvm/env/ppa_env_pkg.sv
../tb/uvm/core_agent/ppa_core_agent_pkg.sv
../tb/uvm/test/ppa_test_pkg.sv
../tb/sva/apb_protocol_sva.sv
../tb/sva/apb_slave_if_sva.sv
../tb/sva/packet_proc_core_sva.sv
../tb/tb_top.sv
