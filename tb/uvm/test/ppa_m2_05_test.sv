// M2-05：hdr_chk 校验与旁路（E-5 algo_mode=1 错校验 chk_error=1 / E-6 algo_mode=0 旁路
// chk_error=0）。spec §9.1 §10.2
class ppa_m2_05_test extends ppa_m2_base_test;

  `uvm_component_utils(ppa_m2_05_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_items(ppa_core_directed_seq s);
    ppa_core_seq_item e5, e6;

    // E-5：hdr_chk=0xFF（正确应为 0x04^0x01^0x00=0x05），algo_mode=1 → chk_error=1
    e5 = mk("E-5-badchk");
    e5.pkt_len = 8'd4; e5.pkt_type = 8'h01; e5.flags = 8'h00; e5.hdr_chk = 8'hFF;
    e5.algo_mode = 1'b1;
    e5.payload = new[0];
    s.items.push_back(e5);

    // E-6：同 E-5 packet 但 algo_mode=0 → chk_error=0（校验旁路），format_ok=1
    e6 = mk("E-6-bypass");
    e6.pkt_len = 8'd4; e6.pkt_type = 8'h01; e6.flags = 8'h00; e6.hdr_chk = 8'hFF;
    e6.algo_mode = 1'b0;
    e6.payload = new[0];
    s.items.push_back(e6);
  endfunction

endclass
