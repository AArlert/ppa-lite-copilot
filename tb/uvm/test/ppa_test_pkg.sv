// 测试包：所有 uvm_test 在此汇总
package ppa_test_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  import ppa_reg_defs_pkg::*;
  import apb_agent_pkg::*;
  import ppa_env_pkg::*;
  import ppa_core_agent_pkg::*;

  `include "ppa_base_test.sv"
  `include "ppa_smoke_test.sv"
  `include "m1_seq_lib.sv"
  `include "ppa_m1_01_test.sv"
  `include "ppa_m1_02_test.sv"
  `include "ppa_m1_03_test.sv"
  `include "ppa_m1_04_test.sv"
  `include "ppa_m1_05_test.sv"
  `include "ppa_m1_06_test.sv"
  `include "ppa_m1_07_test.sv"
  `include "ppa_m1_08_test.sv"
  `include "ppa_m1_09_test.sv"
  // M2（packet_proc_core 单元级）
  `include "ppa_m2_base_test.sv"
  `include "ppa_m2_01_test.sv"
  `include "ppa_m2_02_test.sv"
  `include "ppa_m2_03_test.sv"
  `include "ppa_m2_04_test.sv"
  `include "ppa_m2_05_test.sv"
  `include "ppa_m2_06_test.sv"
  `include "ppa_m2_07_test.sv"
  `include "ppa_m2_08_rand_test.sv"  // M4-02a 随机帧
  `include "ppa_m2_09_reset_test.sv" // M4-02d 运行中复位
  // M3（ppa_top 集成）
  `include "ppa_m3_base_test.sv"
  `include "m3_seq_lib.sv"
  `include "m4_seq_lib.sv"           // M4 覆盖率闭环集成/CSR 序列
  `include "ppa_m3_01_test.sv"
  `include "ppa_m3_02_test.sv"
  `include "ppa_m3_03_test.sv"
  `include "ppa_m3_04_test.sv"
  `include "ppa_m3_05_test.sv"
  `include "ppa_m3_06_rand_test.sv"  // M4-02b 集成随机帧
  `include "ppa_m3_07_reset_test.sv" // M4-02e 集成运行中复位
  // M4 覆盖率补强（M1 单元 CSR/stub 随机）
  `include "ppa_m1_10_rand_test.sv"  // M4-02c

endpackage
