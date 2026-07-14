// M3-02：连续两帧（§10.1 N-4 §11.4-必2）
class ppa_m3_02_test extends ppa_m3_base_test;

  `uvm_component_utils(ppa_m3_02_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    return m3_two_frame_seq::type_id::create("m3_02_seq");
  endfunction

endclass
