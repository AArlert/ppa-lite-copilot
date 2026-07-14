// M3-04：busy 写保护（§6.3 §10.3 B-2 §11.4-选4）
class ppa_m3_04_test extends ppa_m3_base_test;

  `uvm_component_utils(ppa_m3_04_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    return m3_busy_wprotect_seq::type_id::create("m3_04_seq");
  endfunction

endclass
