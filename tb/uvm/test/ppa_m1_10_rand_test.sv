// M4-02c：apb_slave_if 单元级 CSR/stub 随机回归（多 seed 覆盖率闭环）
class ppa_m1_10_rand_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_10_rand_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m4_rand_csr_seq seq = m4_rand_csr_seq::type_id::create("m1_10_seq");
    seq.m3_drv = env.m3_drv;
    return seq;
  endfunction

endclass
