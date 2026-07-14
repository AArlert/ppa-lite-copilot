// M2-06：PKT_LEN_EXP 一致性（B-4）——exp≠0 且与 pkt_len 不符 → length_error=1；
// exp=0（未配置/复位默认）→ 跳过比对不报错（r4）；另补 exp=pkt_len 匹配的正向项。
// spec §5.2 §9.1 §10.3
class ppa_m2_06_test extends ppa_m2_base_test;

  `uvm_component_utils(ppa_m2_06_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_items(ppa_core_directed_seq s);
    ppa_core_seq_item mismatch, skip0, match;

    // exp=12 且 pkt_len=8（本身合法）→ length_error=1（不符）。pkt_len 合法故 sum/xor 仍比对
    mismatch = mk("B4-exp12-len8");
    mismatch.pkt_len = 8'd8; mismatch.pkt_type = 8'h02; mismatch.flags = 8'h00;
    mismatch.hdr_chk = 8'h0A; mismatch.exp_pkt_len = 6'd12;
    mismatch.payload = new[4]; mismatch.payload[0]=8'h01; mismatch.payload[1]=8'h02;
    mismatch.payload[2]=8'h03; mismatch.payload[3]=8'h04;
    s.items.push_back(mismatch);

    // exp=0（未配置）→ 跳过一致性检查，length_error=0（r4）
    skip0 = mk("B4-exp0-skip");
    skip0.pkt_len = 8'd8; skip0.pkt_type = 8'h02; skip0.flags = 8'h00;
    skip0.hdr_chk = 8'h0A; skip0.exp_pkt_len = 6'd0;
    skip0.payload = new[4]; skip0.payload[0]=8'h01; skip0.payload[1]=8'h02;
    skip0.payload[2]=8'h03; skip0.payload[3]=8'h04;
    s.items.push_back(skip0);

    // exp=8 且 pkt_len=8 → 一致，length_error=0（正向）
    match = mk("B4-exp8-match");
    match.pkt_len = 8'd8; match.pkt_type = 8'h02; match.flags = 8'h00;
    match.hdr_chk = 8'h0A; match.exp_pkt_len = 6'd8;
    match.payload = new[4]; match.payload[0]=8'h01; match.payload[1]=8'h02;
    match.payload[2]=8'h03; match.payload[3]=8'h04;
    s.items.push_back(match);
  endfunction

endclass
