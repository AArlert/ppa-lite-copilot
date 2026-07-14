// packet_proc_core 单元级验证包（M2 独立 TB）：一个类一个文件，此处汇总 include
package ppa_core_agent_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"
  import ppa_reg_defs_pkg::*;

  `include "ppa_core_seq_item.sv"
  `include "ppa_core_sequencer.sv"
  `include "ppa_core_driver.sv"
  `include "ppa_core_seq_lib.sv"
  `include "ppa_core_agent.sv"
  `include "ppa_core_env.sv"

endpackage
