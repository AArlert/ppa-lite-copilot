// APB agent 包：一个类一个文件，此处统一汇总
package apb_agent_pkg;

  import uvm_pkg::*;
  `include "uvm_macros.svh"

  `include "apb_seq_item.sv"
  `include "apb_sequencer.sv"
  `include "apb_driver.sv"
  `include "apb_monitor.sv"
  `include "apb_agent.sv"
  `include "apb_seq_lib.sv"

endpackage
