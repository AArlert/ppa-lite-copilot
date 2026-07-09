// M1-05：IRQ 寄存器组（§5.2 §8.2 §11.2-选5）
class ppa_m1_05_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_05_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m1_irq_seq seq = m1_irq_seq::type_id::create("m1_05_seq");
    seq.m3_drv = env.m3_drv;
    return seq;
  endfunction

endclass
