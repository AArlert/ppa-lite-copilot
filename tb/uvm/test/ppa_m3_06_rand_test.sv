// M4-02b：ppa_top 集成随机帧回归（多 seed 覆盖率闭环）
class ppa_m3_06_rand_test extends ppa_m3_base_test;

  `uvm_component_utils(ppa_m3_06_rand_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m4_rand_integ_seq seq = m4_rand_integ_seq::type_id::create("m3_06_seq");
    return seq;
  endfunction

endclass
