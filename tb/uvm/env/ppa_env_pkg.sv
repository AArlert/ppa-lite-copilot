// 环境包：scoreboard + 覆盖 + env
// 注：期望值参考模型不在本包——收敛到 core-agent 的 ppa_core_seq_item.sv::predict() 单点实现
// （原 env 内另有一份 golden 计算的独立参考模型文件，零调用死代码，已按 BUG-016 删除）。
package ppa_env_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  import ppa_reg_defs_pkg::*;
  import apb_agent_pkg::*;

  `include "ppa_scoreboard.sv"
  `include "ppa_cov.sv"
  `include "m3_stub_driver.sv"
  `include "ppa_env.sv"

endpackage
