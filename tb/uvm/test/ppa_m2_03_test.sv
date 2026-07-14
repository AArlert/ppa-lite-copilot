// M2-03：busy/done 时序（B-1）——start 后 1 拍 busy=1（SVA a_busy_after_start）；
// DONE 态 done 保持（post_done_idle 停留期间 SVA a_done_hold 监视）；再次 start 清零
// （第二帧覆盖，SVA a_restart_clears）。spec §7.4 §8.1 §10.3
class ppa_m2_03_test extends ppa_m2_base_test;

  `uvm_component_utils(ppa_m2_03_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_items(ppa_core_directed_seq s);
    ppa_core_seq_item f1, f2;

    // 第一帧：合法包，处理完成后在 DONE 态停留若干拍观测 done 保持
    f1 = mk("B1-frame1");
    f1.pkt_len = 8'd4; f1.pkt_type = 8'h01; f1.flags = 8'h00; f1.hdr_chk = 8'h05;
    f1.payload = new[0];
    f1.post_done_idle = 6; // DONE 态停留 6 拍：a_done_hold 被动验证 done 保持
    s.items.push_back(f1);

    // 第二帧：done 未清除时再次 start —— 结果被新帧覆盖（len=8/type=0x02）
    f2 = mk("B1-frame2");
    f2.pkt_len = 8'd8; f2.pkt_type = 8'h02; f2.flags = 8'h00; f2.hdr_chk = 8'h0A;
    f2.payload = new[4]; f2.payload[0]=8'h01; f2.payload[1]=8'h02;
    f2.payload[2]=8'h03; f2.payload[3]=8'h04;
    s.items.push_back(f2);
  endfunction

endclass
