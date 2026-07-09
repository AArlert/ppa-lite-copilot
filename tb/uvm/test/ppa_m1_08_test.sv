// M1-08：busy=1 期间写 PKT_MEM 被保护（不产生 we，写入不生效，§6.3）
class ppa_m1_08_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_08_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m1_busy_protect_seq seq = m1_busy_protect_seq::type_id::create("m1_08_seq");
    seq.m3_drv = env.m3_drv;
    return seq;
  endfunction

endclass
