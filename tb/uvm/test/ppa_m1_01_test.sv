// M1-01：APB 两段式读写时序 + CSR 默认值（§4.1 §5.2 §11.2-必1）
class ppa_m1_01_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_01_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    return m1_csr_default_seq::type_id::create("m1_01_seq");
  endfunction

endclass
