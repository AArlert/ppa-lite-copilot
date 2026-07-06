// 测试包：所有 uvm_test 在此汇总
package ppa_test_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  import ppa_reg_defs_pkg::*;
  import apb_agent_pkg::*;
  import ppa_env_pkg::*;

  `include "ppa_base_test.sv"
  `include "ppa_smoke_test.sv"

endpackage
