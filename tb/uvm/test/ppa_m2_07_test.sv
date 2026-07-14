// M2-07：配置帧内稳定契约（§5.2 §7.2 §7.3 r10）——三项配置（algo_mode/type_mask/
// exp_pkt_len）在 start 前置好、整个 busy 期间不改写（driver 恒稳定驱动），判定结果须
// 符合帧起始配置预期。核对：配置活值确实参与第 0 拍判定（r10 组合取活值）。
//
// 范围说明：负向观测"busy 期间写 CFG/PKT_LEN_EXP 不报 PSLVERR"（§6.3 对照）属含 APB
// 通路的集成层（apb_slave_if）：CFG/PKT_LEN_EXP 为 RW 且不在 §6.3 busy 写保护之列，
// 与 PKT_MEM（M1-08/M3-04）不同等约束。packet_proc_core 单元级无 APB/PSLVERR 端口，
// 该负向观测在 M3 集成 test 覆盖；本单元 test 验证 r10 正向契约（稳定配置→帧判定符合）。
class ppa_m2_07_test extends ppa_m2_base_test;

  `uvm_component_utils(ppa_m2_07_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_items(ppa_core_directed_seq s);
    ppa_core_seq_item pass_cfg, block_cfg;

    // 配置全部参与且放行：type_mask=0010 仅允许 type=0x02，exp=8 与 len=8 一致，
    // algo_mode=1 且 hdr_chk 正确 → 三项判定均通过，format_ok=1
    pass_cfg = mk("CFG-stable-pass");
    pass_cfg.pkt_len = 8'd8; pass_cfg.pkt_type = 8'h02; pass_cfg.flags = 8'h00;
    pass_cfg.hdr_chk = 8'h0A;
    pass_cfg.algo_mode = 1'b1; pass_cfg.type_mask = 4'b0010; pass_cfg.exp_pkt_len = 6'd8;
    pass_cfg.payload = new[4]; pass_cfg.payload[0]=8'h01; pass_cfg.payload[1]=8'h02;
    pass_cfg.payload[2]=8'h03; pass_cfg.payload[3]=8'h04;
    pass_cfg.post_done_idle = 4;
    s.items.push_back(pass_cfg);

    // 同 type_mask=0010 但 pkt_type=0x01（bit0 被屏蔽）→ type_error=1，
    // 证明 type_mask 活值确实参与判定（r10 组合取活值）
    block_cfg = mk("CFG-stable-block");
    block_cfg.pkt_len = 8'd8; block_cfg.pkt_type = 8'h01; block_cfg.flags = 8'h00;
    block_cfg.hdr_chk = 8'h09; // 0x08^0x01^0x00=0x09
    block_cfg.algo_mode = 1'b1; block_cfg.type_mask = 4'b0010; block_cfg.exp_pkt_len = 6'd8;
    block_cfg.payload = new[4]; block_cfg.payload[0]=8'h0A; block_cfg.payload[1]=8'h0B;
    block_cfg.payload[2]=8'h0C; block_cfg.payload[3]=8'h0D;
    s.items.push_back(block_cfg);
  endfunction

endclass
