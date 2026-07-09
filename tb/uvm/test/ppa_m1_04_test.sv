// M1-04：PSLVERR 统一响应（§8.3 §11.2-选4）
class ppa_m1_04_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_04_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    return m1_pslverr_seq::type_id::create("m1_04_seq");
  endfunction

endclass
