// M1-07：CTRL 先 enable 后 START 两步序列，START 单拍脉冲行为（§5.1 §5.2 附录A）
class ppa_m1_07_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_07_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m1_start_pulse_seq seq = m1_start_pulse_seq::type_id::create("m1_07_seq");
    seq.m3_drv = env.m3_drv;
    return seq;
  endfunction

endclass
