// M2-01：合法包完整处理（N-1/N-2/N-3）——done 拉高、res_pkt_len/type/sum/xor 正确、
// FSM IDLE→PROCESS→DONE（§7 §10.1）。hdr_chk 均取 Byte0^Byte1^Byte2 以保证 chk_error=0。
class ppa_m2_01_test extends ppa_m2_base_test;

  `uvm_component_utils(ppa_m2_01_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_items(ppa_core_directed_seq s);
    ppa_core_seq_item n1, n2, n3;

    // N-1 最小合法包（纯头部）：len=4 type=0x01 hdr_chk=0x04^0x01^0x00=0x05
    n1 = mk("N-1");
    n1.pkt_len = 8'd4; n1.pkt_type = 8'h01; n1.flags = 8'h00; n1.hdr_chk = 8'h05;
    n1.payload = new[0];
    s.items.push_back(n1);

    // N-2 8 字节合法包：len=8 type=0x02 hdr_chk=0x08^0x02^0x00=0x0A payload={01,02,03,04}
    n2 = mk("N-2");
    n2.pkt_len = 8'd8; n2.pkt_type = 8'h02; n2.flags = 8'h00; n2.hdr_chk = 8'h0A;
    n2.payload = new[4]; n2.payload[0]=8'h01; n2.payload[1]=8'h02;
    n2.payload[2]=8'h03; n2.payload[3]=8'h04;
    s.items.push_back(n2);

    // N-3 最大合法包（32 bytes，28B payload）：len=32 type=0x04 hdr_chk=0x20^0x04^0x00=0x24
    n3 = mk("N-3");
    n3.pkt_len = 8'd32; n3.pkt_type = 8'h04; n3.flags = 8'h00; n3.hdr_chk = 8'h24;
    n3.payload = new[28];
    foreach (n3.payload[i]) n3.payload[i] = i + 1; // 任意图案，sum/xor 由参考模型算
    s.items.push_back(n3);
  endfunction

endclass
