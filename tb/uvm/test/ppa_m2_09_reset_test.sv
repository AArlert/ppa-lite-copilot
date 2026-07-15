// M4-02d：packet_proc_core 运行中复位（FSM 复位转移覆盖 + 鲁棒性）
// 在 PROCESS 态与 DONE 态各注入一次异步复位（driver 拉低 force_rst_n），核对 FSM
// 干净回到 IDLE（覆盖 FSM 转移 PROCESS→IDLE / DONE→IDLE，spec §7.1 [*]→IDLE），复位后
// 输出清零（§7.4 §9.3）；随后一帧正常处理确认复位后恢复正常（§7.2）。
class ppa_m2_09_reset_test extends ppa_m2_base_test;

  `uvm_component_utils(ppa_m2_09_reset_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function bit [7:0] good_chk(bit [7:0] len, bit [7:0] typ, bit [7:0] flg);
    return len ^ typ ^ flg;
  endfunction

  virtual function void build_items(ppa_core_directed_seq s);
    ppa_core_seq_item r_proc, r_done, normal;

    // ---- 1. PROCESS 态注入复位（长帧拉宽 busy 窗口）----
    r_proc = mk("rst_in_process");
    r_proc.pkt_len    = 8'd32;
    r_proc.pkt_type   = 8'h04;
    r_proc.flags      = 8'h00;
    r_proc.hdr_chk    = good_chk(8'd32, 8'h04, 8'h00);
    r_proc.payload    = new[28];
    foreach (r_proc.payload[i]) r_proc.payload[i] = 8'(i + 1);
    r_proc.inject_rst = 1'b1;
    r_proc.rst_phase  = 0; // PROCESS 态注入
    s.items.push_back(r_proc);

    // ---- 2. DONE 态注入复位（短帧，先跑到 done 再注入）----
    r_done = mk("rst_in_done");
    r_done.pkt_len    = 8'd8;
    r_done.pkt_type   = 8'h02;
    r_done.flags      = 8'h00;
    r_done.hdr_chk    = good_chk(8'd8, 8'h02, 8'h00);
    r_done.payload    = new[28];
    foreach (r_done.payload[i]) r_done.payload[i] = 8'(i + 1);
    r_done.inject_rst = 1'b1;
    r_done.rst_phase  = 1; // DONE 态注入
    s.items.push_back(r_done);

    // ---- 3. 复位后正常处理（确认恢复；参考模型逐字段比对）----
    // N-2 样式：len=8 type=0x02 payload=0x01020304 → sum=0x0A xor=0x04（§3.4）
    normal = mk("post_rst_normal");
    normal.pkt_len  = 8'd8;
    normal.pkt_type = 8'h02;
    normal.flags    = 8'h00;
    normal.hdr_chk  = good_chk(8'd8, 8'h02, 8'h00);
    normal.payload  = new[4];
    normal.payload[0] = 8'h01; normal.payload[1] = 8'h02;
    normal.payload[2] = 8'h03; normal.payload[3] = 8'h04;
    s.items.push_back(normal);
  endfunction

endclass
