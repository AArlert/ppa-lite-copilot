// M3-01：端到端链路（§11.4-必1）
class ppa_m3_01_test extends ppa_m3_base_test;

  `uvm_component_utils(ppa_m3_01_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    return m3_e2e_seq::type_id::create("m3_01_seq");
  endfunction

endclass
