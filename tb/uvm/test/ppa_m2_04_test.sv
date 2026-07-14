// M2-04：类型合法性 + type_mask（E-3 非 one-hot / E-4 mask 屏蔽）——type_error=1。
// spec §9.1 §10.2
class ppa_m2_04_test extends ppa_m2_base_test;

  `uvm_component_utils(ppa_m2_04_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_items(ppa_core_directed_seq s);
    ppa_core_seq_item e3, e4;

    // E-3 非法 pkt_type=0x03（非 one-hot）：type_error=1。len=4 合法、hdr_chk=0x04^0x03^0x00=0x07
    e3 = mk("E-3-type03");
    e3.pkt_len = 8'd4; e3.pkt_type = 8'h03; e3.flags = 8'h00; e3.hdr_chk = 8'h07;
    e3.payload = new[0];
    s.items.push_back(e3);

    // E-4 type_mask=4'b1110 屏蔽 pkt_type=0x01（bit0=0）：type_error=1。hdr_chk=0x04^0x01^0x00=0x05
    e4 = mk("E-4-mask");
    e4.pkt_len = 8'd4; e4.pkt_type = 8'h01; e4.flags = 8'h00; e4.hdr_chk = 8'h05;
    e4.type_mask = 4'b1110;
    e4.payload = new[0];
    s.items.push_back(e4);
  endfunction

endclass
