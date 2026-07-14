// M2-02：长度越界检测（E-1 len=3 / E-2 len=33）——length_error=1（第 0 拍判定）、
// format_ok=0、不卡死；sum/xor 不比对（UNSPECIFIED，§7.3 r5）；读拍钳位 [1,8]（r8）；
// 补 pkt_len=0（读拍下界）与 pkt_len>63（res_pkt_len=Byte0[5:0]，r9）激励。
// spec §7.3 §9.1 §10.2
class ppa_m2_02_test extends ppa_m2_base_test;

  `uvm_component_utils(ppa_m2_02_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_items(ppa_core_directed_seq s);
    ppa_core_seq_item e1, e2, z0, big;

    // E-1 包长下溢 len=3：hdr_chk=0x03^0x01^0x00=0x02（隔离 chk/type，仅 length_error）
    e1 = mk("E-1-len3");
    e1.pkt_len = 8'd3; e1.pkt_type = 8'h01; e1.flags = 8'h00; e1.hdr_chk = 8'h02;
    e1.payload = new[0];
    s.items.push_back(e1);

    // E-2 包长上溢 len=33：ceil(33/4)=9 须钳到 8 拍（r8），不越 8-word 窗口/不卡死
    // hdr_chk=0x21^0x01^0x00=0x20
    e2 = mk("E-2-len33");
    e2.pkt_len = 8'd33; e2.pkt_type = 8'h01; e2.flags = 8'h00; e2.hdr_chk = 8'h20;
    e2.payload = new[28];
    foreach (e2.payload[i]) e2.payload[i] = i;
    s.items.push_back(e2);

    // 补：pkt_len=0（读拍下界，PROCESS 仅第 0 拍即进 DONE，r8）
    // res_pkt_len=0；length_error=1；hdr_chk=0x00^0x01^0x00=0x01
    z0 = mk("E-len0");
    z0.pkt_len = 8'd0; z0.pkt_type = 8'h01; z0.flags = 8'h00; z0.hdr_chk = 8'h01;
    z0.payload = new[0];
    s.items.push_back(z0);

    // 补：pkt_len>63（=100）res_pkt_len=Byte0[5:0]=100[5:0]=36（r9 截断）；length_error=1
    // hdr_chk=0x64^0x01^0x00=0x65；ceil(100/4)=25 须钳到 8 拍
    big = mk("E-len100");
    big.pkt_len = 8'd100; big.pkt_type = 8'h01; big.flags = 8'h00; big.hdr_chk = 8'h65;
    big.payload = new[28];
    foreach (big.payload[i]) big.payload[i] = i;
    s.items.push_back(big);
  endfunction

endclass
