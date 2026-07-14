// packet_proc_core 单元级 sequencer
class ppa_core_sequencer extends uvm_sequencer #(ppa_core_seq_item);
  `uvm_component_utils(ppa_core_sequencer)
  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction
endclass
