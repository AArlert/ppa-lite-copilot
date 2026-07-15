// packet_proc_core 单元级事务：承载一帧激励（包字节 + 帧级配置）与 spec 推导的
// 期望值。参考模型 predict() 的每条期望均标注 spec 依据，禁止照抄 RTL 实现。
class ppa_core_seq_item extends uvm_sequence_item;

  // ---- 激励：包头四字节（§3.1）----
  bit [7:0] pkt_len  = 8'd4;
  bit [7:0] pkt_type = 8'h01;
  bit [7:0] flags    = 8'h00;
  bit [7:0] hdr_chk  = 8'h05;
  // ---- 激励：payload 字节（§3.1 Byte4..，长度 = pkt_len-4）----
  bit [7:0] payload [];

  // ---- 帧级配置（§5.2；start 前置好、busy 期间保持稳定，r10 契约）----
  bit       algo_mode   = 1'b1;
  bit [3:0] type_mask   = 4'b1111;
  bit [5:0] exp_pkt_len = 6'd0;

  // ---- 时序控制 ----
  int unsigned post_done_idle = 0;   // 处理完成后在 DONE 态停留拍数（M2-03 done 保持观测）
  int unsigned start_hold      = 1;   // start_i 保持拍数（缺省 1=单拍脉冲；>1 使 start 在
                                       // PROCESS 期间仍为高，覆盖 §7.2 PROCESS 忽略 start 的
                                       // 条件组合，M4-02a；PROCESS 忽略 start 的正确性由
                                       // 内部断言 a_process_ignores_start 被动保证）
  // ---- 运行中复位注入（M4-02d：FSM PROCESS→IDLE / DONE→IDLE 复位转移覆盖）----
  bit          inject_rst = 1'b0;    // 1=本 item 为复位注入帧（非普通比对帧）
  int unsigned rst_phase  = 0;        // 0=PROCESS 态注入复位；1=DONE 态注入复位
  string       label = "";

  // ---- 期望（predict 计算）----
  bit [5:0] e_res_pkt_len;
  bit [7:0] e_res_pkt_type;
  bit [7:0] e_sum;
  bit [7:0] e_xor;
  bit       e_length_error;
  bit       e_type_error;
  bit       e_chk_error;
  bit       e_format_ok;
  bit       check_sum_xor;   // 仅合法包长时比对 sum/xor（§7.3 r5：非法包长 UNSPECIFIED）

  `uvm_object_utils(ppa_core_seq_item)

  function new(string name = "ppa_core_seq_item");
    super.new(name);
  endfunction

  // 按附录 A 大端约定组装第 w 个 32-bit word：[31:24]=Byte(4w) … [7:0]=Byte(4w+3)
  function bit [31:0] get_word(int w);
    bit [31:0] wd = 32'h0;
    for (int p = 0; p < 4; p++) begin
      int b = w * 4 + p;
      bit [7:0] bv;
      case (b)
        0: bv = pkt_len;
        1: bv = pkt_type;
        2: bv = flags;
        3: bv = hdr_chk;
        default: bv = ((b - 4) < payload.size()) ? payload[b - 4] : 8'h00;
      endcase
      wd[31 - 8*p -: 8] = bv;
    end
    return wd;
  endfunction

  // spec 推导的参考模型：每条期望标注章节，禁止照抄 RTL
  function void predict();
    bit valid_type;
    int idx;
    int nb;
    bit [7:0] s = 8'h00;
    bit [7:0] x = 8'h00;

    // §3.4/r9：res_pkt_len 恒 = Byte0[5:0]
    e_res_pkt_len  = pkt_len[5:0];
    // §3.4：res_pkt_type = Byte1
    e_res_pkt_type = pkt_type;

    // §9.1：length_error = pkt_len<4 || pkt_len>32 ；或 exp_pkt_len!=0 且不符（r4）
    e_length_error = (pkt_len < 8'd4) || (pkt_len > 8'd32);
    if (exp_pkt_len != 6'd0)
      if (pkt_len != {2'b00, exp_pkt_len}) e_length_error = 1'b1;

    // §9.1：type_error = 非有效 one-hot(01/02/04/08) 或对应 bit 被 type_mask 屏蔽
    valid_type = (pkt_type == 8'h01) || (pkt_type == 8'h02) ||
                 (pkt_type == 8'h04) || (pkt_type == 8'h08);
    idx = (pkt_type == 8'h01) ? 0 : (pkt_type == 8'h02) ? 1 :
          (pkt_type == 8'h04) ? 2 : 3;
    e_type_error = (!valid_type) || (!type_mask[idx]);

    // §9.1：chk_error 仅 algo_mode=1 时有效；hdr_chk != Byte0^Byte1^Byte2
    e_chk_error = algo_mode && (hdr_chk != (pkt_len ^ pkt_type ^ flags));

    // §5.2 format_ok：长度/类型/头校验均通过
    e_format_ok = (!e_length_error) && (!e_type_error) && (!e_chk_error);

    // §3.4/§7.3：合法包长时 payload 各字节累加/XOR（有效字节数 = pkt_len-4，§6.2）；
    // 非法包长 UNSPECIFIED，不比对（§7.3 r5）
    check_sum_xor = (pkt_len >= 8'd4) && (pkt_len <= 8'd32);
    nb = check_sum_xor ? (pkt_len - 8'd4) : 0;
    for (int i = 0; i < nb; i++) begin
      bit [7:0] pv = (i < payload.size()) ? payload[i] : 8'h00;
      s += pv;
      x ^= pv;
    end
    e_sum = s;
    e_xor = x;
  endfunction

  function string convert2string();
    return $sformatf("[%s] len=%0d type=0x%02h flags=0x%02h chk=0x%02h algo=%0b mask=%04b exp=%0d",
                     label, pkt_len, pkt_type, flags, hdr_chk, algo_mode, type_mask, exp_pkt_len);
  endfunction

endclass
