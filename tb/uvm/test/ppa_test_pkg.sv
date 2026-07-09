// 测试包：所有 uvm_test 在此汇总
package ppa_test_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  import ppa_reg_defs_pkg::*;
  import apb_agent_pkg::*;
  import ppa_env_pkg::*;

  `include "ppa_base_test.sv"
  `include "ppa_smoke_test.sv"
  `include "m1_seq_lib.sv"
  `include "ppa_m1_01_test.sv"
  `include "ppa_m1_02_test.sv"
  `include "ppa_m1_03_test.sv"
  `include "ppa_m1_04_test.sv"
  `include "ppa_m1_05_test.sv"
  `include "ppa_m1_06_test.sv"

endpackage
