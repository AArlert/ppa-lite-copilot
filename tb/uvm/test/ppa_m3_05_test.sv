// M3-05：中断路径闭环（§8.2 §10.3 B-3 §11.4-选5）
class ppa_m3_05_test extends ppa_m3_base_test;

  `uvm_component_utils(ppa_m3_05_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m3_irq_seq seq = m3_irq_seq::type_id::create("m3_05_seq");
    seq.top_vif = top_vif; // 顶层 irq 观测接口传入序列
    return seq;
  endfunction

endclass
