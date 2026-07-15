// M4-02a：packet_proc_core 随机帧回归（多 seed 覆盖率闭环）
// 目的：用随机 pkt_len/pkt_type/flags/hdr_chk/payload/algo_mode/type_mask/exp 帧覆盖
//   packet_proc_core 的数据通路 TOGGLE 与判定 COND 缺口——参考模型 predict() 逐字段
//   比对，期望值全部从 spec 推导（§3.4 §9.1 §7.3），不照抄 RTL。多 seed 回归（见
//   sim/regress/regress.list）扩大随机空间。定向补齐若干 COND 组合（pkt_type=0x08
//   收/屏蔽、0x02/0x04 屏蔽、algo_mode=0、PROCESS 期 start 保持）。
class ppa_m2_08_rand_test extends ppa_m2_base_test;

  `uvm_component_utils(ppa_m2_08_rand_test)

  int unsigned n_rand = 60; // 每次运行随机帧数（多 seed 叠加扩大覆盖）

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // 构造一帧 item：装 28 字节随机 payload（多余字节落窗口内不被读，仅用于加大数据翻转）
  function ppa_core_seq_item mk_frame(
      string    label,
      bit [7:0] pkt_len, bit [7:0] pkt_type, bit [7:0] flags, bit [7:0] hdr_chk,
      bit algo_mode, bit [3:0] type_mask, bit [5:0] exp_pkt_len,
      int unsigned start_hold = 1);
    ppa_core_seq_item it = mk(label);
    it.pkt_len     = pkt_len;
    it.pkt_type    = pkt_type;
    it.flags       = flags;
    it.hdr_chk     = hdr_chk;
    it.algo_mode   = algo_mode;
    it.type_mask   = type_mask;
    it.exp_pkt_len = exp_pkt_len;
    it.start_hold  = start_hold;
    it.payload     = new[28];
    foreach (it.payload[i]) it.payload[i] = 8'($urandom);
    return it;
  endfunction

  // 正确头校验值（§3.1 §9.1）：Byte0 ^ Byte1 ^ Byte2
  function bit [7:0] good_chk(bit [7:0] len, bit [7:0] typ, bit [7:0] flg);
    return len ^ typ ^ flg;
  endfunction

  virtual function void build_items(ppa_core_directed_seq s);
    bit [7:0] len, typ, flags, chk;
    bit       algo;
    bit [3:0] mask;
    bit [5:0] expv;

    // ---- 定向补齐 COND 缺口（§9.1 类型判定四路 one-hot × type_mask）----
    // pkt_type=0x08 且 mask[3]=1 → 合法接受（LINE113 主项 0001 / 子项 0x08 "1 1"）
    s.items.push_back(mk_frame("t08_accept", 8'd8, 8'h08, 8'h00, good_chk(8'd8,8'h08,8'h00),
                               1'b1, 4'b1000, 6'd0));
    // pkt_type=0x08 且 mask[3]=0 → 屏蔽（子项 0x08 "1 0"）
    s.items.push_back(mk_frame("t08_masked", 8'd8, 8'h08, 8'h00, good_chk(8'd8,8'h08,8'h00),
                               1'b1, 4'b0111, 6'd0));
    // pkt_type=0x02 且 mask[1]=0 → 屏蔽（子项 0x02 "1 0"）
    s.items.push_back(mk_frame("t02_masked", 8'd8, 8'h02, 8'h00, good_chk(8'd8,8'h02,8'h00),
                               1'b1, 4'b1101, 6'd0));
    // pkt_type=0x04 且 mask[2]=0 → 屏蔽（子项 0x04 "1 0"）
    s.items.push_back(mk_frame("t04_masked", 8'd8, 8'h04, 8'h00, good_chk(8'd8,8'h04,8'h00),
                               1'b1, 4'b1011, 6'd0));
    // algo_mode=0 旁路校验：即使 hdr_chk 错也不产生 chk_error（§9.1；a_algo_mode0_no_chkerr）
    s.items.push_back(mk_frame("algo0_bypass", 8'd8, 8'h01, 8'hAA, 8'hFF,
                               1'b0, 4'b1111, 6'd0));
    // PROCESS 期间 start 保持高：长帧 + start_hold=3，覆盖 §7.2 "PROCESS 忽略 start" 条件分支
    s.items.push_back(mk_frame("start_hold", 8'd32, 8'h04, 8'h00, good_chk(8'd32,8'h04,8'h00),
                               1'b1, 4'b1111, 6'd0, /*start_hold*/3));

    // ---- 随机帧：数据通路 TOGGLE + 判定 COND 广谱覆盖 ----
    for (int i = 0; i < n_rand; i++) begin
      int sel = $urandom_range(0, 9);
      // pkt_len 分布：偏重合法 [4,32]，掺入非法小包、非法大包与高位（翻转 pkt_len[7:6]）
      if (sel < 6)       len = 8'($urandom_range(4, 32));    // 合法
      else if (sel < 7)  len = 8'($urandom_range(0, 3));     // 非法小
      else if (sel < 8)  len = 8'($urandom_range(33, 63));   // 非法大（≤6-bit）
      else               len = 8'($urandom);                 // 全 8-bit（翻转高位）
      typ  = 8'($urandom);                   // 全 8-bit（合法 one-hot 与非法/高位）
      flags= 8'($urandom);                   // 全 8-bit（翻转 flags_q）
      // 头校验：一半给正确值（algo_mode=1 时 format_ok 可成立），一半随机（触发 chk_error）
      chk  = (($urandom & 1) != 0) ? good_chk(len, typ, flags) : 8'($urandom);
      algo = 1'($urandom);
      mask = 4'($urandom);
      // exp_pkt_len：多为 0（跳过比对），少量给值（含与 len 一致/不一致，翻转 exp 位）
      expv = ($urandom_range(0, 2) == 0) ? 6'($urandom) : 6'd0;
      s.items.push_back(mk_frame($sformatf("rand%0d", i), len, typ, flags, chk, algo, mask, expv));
    end
  endfunction

endclass
