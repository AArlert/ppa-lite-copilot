// M1-03：RES_* 只读通路（stub 驱动 res_* 输入）（§5.2 §11.2-必3）
class ppa_m1_03_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_03_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m1_res_readback_seq seq = m1_res_readback_seq::type_id::create("m1_03_seq");
    seq.m3_drv = env.m3_drv;
    return seq;
  endfunction

endclass
