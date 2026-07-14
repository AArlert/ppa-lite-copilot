// M3-03：STATUS 总线通路（§11.4-必3）
class ppa_m3_03_test extends ppa_m3_base_test;

  `uvm_component_utils(ppa_m3_03_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    return m3_status_bus_seq::type_id::create("m3_03_seq");
  endfunction

endclass
