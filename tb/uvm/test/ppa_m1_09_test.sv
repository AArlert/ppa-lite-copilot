// M1-09：packet_sram 读口行为——APB 写入已知数据后经 m3_stub 驱动 rd_en/rd_addr
// 校验 rd_data 同拍组合读（§2.3 M2 表注 r6）
class ppa_m1_09_test extends ppa_base_test;

  `uvm_component_utils(ppa_m1_09_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function uvm_sequence #(apb_seq_item) main_seq();
    m1_sram_read_seq seq = m1_sram_read_seq::type_id::create("m1_09_seq");
    seq.m3_drv = env.m3_drv;
    return seq;
  endfunction

endclass
