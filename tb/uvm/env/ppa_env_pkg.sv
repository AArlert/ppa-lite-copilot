// 环境包：参考模型 + scoreboard + 覆盖 + env
package ppa_env_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  import ppa_reg_defs_pkg::*;
  import apb_agent_pkg::*;

  `include "ppa_ref_model.sv"
  `include "ppa_scoreboard.sv"
  `include "ppa_cov.sv"
  `include "ppa_env.sv"

endpackage
