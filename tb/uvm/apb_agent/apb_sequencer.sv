// APB sequencer（无扩展逻辑，占位以便将来加仲裁/上锁策略）
class apb_sequencer extends uvm_sequencer #(apb_seq_item);

  `uvm_component_utils(apb_sequencer)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

endclass
