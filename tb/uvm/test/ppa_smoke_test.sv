// 冒烟测试：跑 apb_smoke_seq，验证环境活性（编译、phase 流转、driver 握手、monitor 采样）
class ppa_smoke_test extends ppa_base_test;

  `uvm_component_utils(ppa_smoke_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    return apb_smoke_seq::type_id::create("smoke_seq");
  endfunction

endclass
