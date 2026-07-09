// M1-06：PKT_MEM APB 读回占位行为（§6.3(r7) §2.3 M2 表注(r7)）
class ppa_m1_06_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_06_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m1_pktmem_readback_seq seq = m1_pktmem_readback_seq::type_id::create("m1_06_seq");
    seq.m3_drv = env.m3_drv;
    return seq;
  endfunction

endclass
