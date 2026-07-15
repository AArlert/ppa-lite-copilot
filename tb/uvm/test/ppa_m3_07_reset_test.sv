// M4-02e：ppa_top 运行中复位（集成核 FSM 复位转移覆盖）
class ppa_m3_07_reset_test extends ppa_m3_base_test;

  `uvm_component_utils(ppa_m3_07_reset_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m4_reset_integ_seq seq = m4_reset_integ_seq::type_id::create("m3_07_seq");
    seq.top_vif = top_vif; // 顶层接口传入序列，用于驱动 force_rst_n
    return seq;
  endfunction

endclass
