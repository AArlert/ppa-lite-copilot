// packet_proc_core 单元级 agent：sequencer + 自检 driver（active）
class ppa_core_agent extends uvm_agent;

  `uvm_component_utils(ppa_core_agent)

  ppa_core_sequencer sqr;
  ppa_core_driver    drv;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    sqr = ppa_core_sequencer::type_id::create("sqr", this);
    drv = ppa_core_driver::type_id::create("drv", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    drv.seq_item_port.connect(sqr.seq_item_export);
  endfunction

endclass
