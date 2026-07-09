// M1-02：PKT_MEM 写入地址映射（§6.1 §11.2-必2）
class ppa_m1_02_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_02_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    return m1_pktmem_write_seq::type_id::create("m1_02_seq");
  endfunction

endclass
