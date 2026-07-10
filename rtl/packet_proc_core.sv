// packet_proc_core (M3)：3 态 FSM 包处理核
// 职责：接收 M1 已完成 enable/busy 门控后的 start_i 脉冲；驱动 M2 读端口逐 word
//       读取 SRAM；第 0 拍解析包头（pkt_len/pkt_type/flags/hdr_chk）并行判定
//       length_error/type_error/chk_error 三类错误；第 1..N-1 拍累加 payload
//       sum/XOR；PROCESS→DONE 一次性写入结果与错误标志；busy_o/done_o 与状态
//       严格对应。不做 CSR 存储、APB 协议、SRAM 存储/写通路、中断生成（均为
//       M1/M2 职责）。
// spec 依据：doc/design-prompt/packet_proc_core.md 逐条列出的 §2.3(M3 端口表)/
//           §3.1-3.4/§5.2/§6.1-6.3/§7.1-7.4/§8.1/§9.1-9.3/§10.1-10.3/§11.3。
//
// 时序契约要点：
//   - M2 为同拍组合读（BUG-003/r6）：mem_rd_addr_o 当拍驱动，mem_rd_data_i 当拍
//     即为该地址内容，无读延迟对齐拍；第 0 拍（word_cnt=0）据此同拍完成头部
//     解析与三类错误的组合判定。
//   - 非法 pkt_len 时读拍数钳位为 min(max(ceil(pkt_len/4),1),8)（BUG-P1/r8 补
//     下界）：pkt_len=0 帧仅第 0 拍即进 DONE；pkt_len 越界大包钳到 8 拍以内，
//     禁止越过 8-word 窗口、禁止卡死。
//   - 非法 pkt_len 时 res_payload_sum_o/res_payload_xor_o 为 UNSPECIFIED（本模块
//     仍按通用累加公式计算某个确定值，不刻意置位，验证侧不比对，BUG-002/r5）。
//   - res_pkt_len_o 恒 = Byte0[5:0]（BUG-P2/r9），不并入 UNSPECIFIED 集合。
//   - exp_pkt_len_i=0 为未配置哨兵，跳过一致性比对（BUG-001/r4）；比对须零扩展
//     exp_pkt_len_i 到 8 位后与完整 8-bit pkt_len 比较，不得先截断 pkt_len。

module packet_proc_core
  import ppa_reg_defs_pkg::*;
(
    input  logic       clk,           // 时钟（来自 ppa_top.PCLK）
    input  logic       rst_n,         // 复位（低有效，来自 ppa_top.PRESETn 映射）

    input  logic       start_i,       // 触发脉冲（来自 M1.start_o，已完成 enable/busy 门控）
    input  logic       algo_mode_i,   // 算法模式（1=校验 hdr_chk，0=旁路）
    input  logic [3:0] type_mask_i,   // 类型掩码，bit[n]=1 允许 pkt_type=(1<<n)
    input  logic [5:0] exp_pkt_len_i, // 期望包长，=0 为未配置哨兵（r4）

    output logic       mem_rd_en_o,   // SRAM 读使能
    output logic [2:0] mem_rd_addr_o, // SRAM 读地址（字计数器驱动）
    input  logic [31:0] mem_rd_data_i,// SRAM 读数据（同拍组合读，r6）

    output logic       busy_o,        // 正在处理（=PROCESS 态）
    output logic       done_o,        // 处理完成（电平，DONE 态保持）

    output logic [5:0] res_pkt_len_o,     // 解析包长，恒=Byte0[5:0]（r9）
    output logic [7:0] res_pkt_type_o,    // 解析包类型（=Byte1）
    output logic [7:0] res_payload_sum_o, // payload 字节和（8-bit 截断）
    output logic [7:0] res_payload_xor_o, // payload 全字节 XOR

    output logic       format_ok_o,    // 格式合法：长度/类型/校验均通过
    output logic       length_error_o, // 长度越界或与 exp_pkt_len 不符
    output logic       type_error_o,   // 类型非法或被 type_mask 屏蔽
    output logic       chk_error_o     // 头校验失败（仅 algo_mode=1 时判定）
);

  // ------------------------------------------------------------------
  // FSM 状态编码（§7.1）
  // ------------------------------------------------------------------
  typedef enum logic [1:0] {
    ST_IDLE    = 2'b00,
    ST_PROCESS = 2'b01,
    ST_DONE    = 2'b10
  } state_e;

  state_e state_q, state_d;
  logic [2:0] word_cnt_q, word_cnt_d; // 字计数器，驱动 mem_rd_addr_o（0-7）

  // 头部字段锁存（第 0 拍读 word0 时锁存，供后续拍复用；§7.3）
  logic [7:0] pkt_len_q, pkt_type_q, flags_q, hdr_chk_q;

  // payload 累加寄存器（§3.4 §7.3）
  logic [7:0] sum_acc_q, xor_acc_q;

  // ------------------------------------------------------------------
  // 头部字段"有效值"（第 0 拍取当拍组合读数据，其余拍取已锁存值，r6）
  // ------------------------------------------------------------------
  logic [7:0] pkt_len_eff, pkt_type_eff, flags_eff, hdr_chk_eff;
  assign pkt_len_eff  = (word_cnt_q == 3'd0) ? mem_rd_data_i[7:0]   : pkt_len_q;
  assign pkt_type_eff = (word_cnt_q == 3'd0) ? mem_rd_data_i[15:8]  : pkt_type_q;
  assign flags_eff    = (word_cnt_q == 3'd0) ? mem_rd_data_i[23:16] : flags_q;
  assign hdr_chk_eff  = (word_cnt_q == 3'd0) ? mem_rd_data_i[31:24] : hdr_chk_q;

  // ------------------------------------------------------------------
  // 读拍数钳位与最后一拍编号（BUG-P1/r8）：
  //   read_words = min(max(ceil(pkt_len/4), 1), 8)；last_word_cnt = read_words-1
  // ------------------------------------------------------------------
  logic [8:0] ceil_raw; // ceil(pkt_len/4) = (pkt_len+3)>>2，pkt_len 8-bit 需 9-bit 中间量
  assign ceil_raw = ({1'b0, pkt_len_eff} + 9'd3) >> 2;

  logic [3:0] read_words_clamped; // 钳位到 [1,8]
  always_comb begin
    if (ceil_raw == 9'd0)      read_words_clamped = 4'd1;
    else if (ceil_raw > 9'd8)  read_words_clamped = 4'd8;
    else                       read_words_clamped = ceil_raw[3:0];
  end

  logic [3:0] last_word_cnt_ext; // read_words_clamped∈[1,8]，减1后范围[0,7]，4-bit 无需担心下溢
  assign last_word_cnt_ext = read_words_clamped - 4'd1;
  logic [2:0] last_word_cnt;
  assign last_word_cnt = last_word_cnt_ext[2:0]; // 范围 [0,7]

  // ------------------------------------------------------------------
  // 三类错误组合判定（§9.1 §9.2）——基于 pkt_len_eff/pkt_type_eff/hdr_chk_eff/
  // flags_eff，全程可用（第 0 拍即为最终值，其余拍沿用锁存值）
  // ------------------------------------------------------------------
  logic [7:0] exp_pkt_len_ext; // exp_pkt_len_i 零扩展到 8-bit，禁止先截断 pkt_len（r4）
  assign exp_pkt_len_ext = {2'b00, exp_pkt_len_i};

  logic length_error_w;
  assign length_error_w = (pkt_len_eff < 8'(PKT_LEN_MIN)) ||
                           (pkt_len_eff > 8'(PKT_LEN_MAX)) ||
                           ((exp_pkt_len_i != 6'd0) && (exp_pkt_len_ext != pkt_len_eff));

  logic type_valid_w;
  assign type_valid_w = (pkt_type_eff == 8'h01 && type_mask_i[0]) ||
                         (pkt_type_eff == 8'h02 && type_mask_i[1]) ||
                         (pkt_type_eff == 8'h04 && type_mask_i[2]) ||
                         (pkt_type_eff == 8'h08 && type_mask_i[3]);
  logic type_error_w;
  assign type_error_w = !type_valid_w;

  logic chk_error_w;
  assign chk_error_w = algo_mode_i &&
                        (hdr_chk_eff != (pkt_len_eff ^ pkt_type_eff ^ flags_eff));

  logic format_ok_w;
  assign format_ok_w = !(length_error_w || type_error_w || chk_error_w);

  // ------------------------------------------------------------------
  // payload 逐字节 sum/XOR 累加（§3.4 §6.2 §7.3）：word_cnt_q=0 为头部拍，
  // 不参与累加；word_cnt_q>=1 时按当拍 word 的 4 字节、以 pkt_len_eff 界定
  // 有效范围（越界字节不计入，用于最后一个不满 word 的情形）
  // ------------------------------------------------------------------
  logic [7:0] word_byte_base; // = word_cnt_q * 4，最大 7*4=28
  assign word_byte_base = ({5'b0, word_cnt_q} << 2);

  logic valid_b0, valid_b1, valid_b2, valid_b3;
  assign valid_b0 = (word_byte_base + 8'd0) < pkt_len_eff;
  assign valid_b1 = (word_byte_base + 8'd1) < pkt_len_eff;
  assign valid_b2 = (word_byte_base + 8'd2) < pkt_len_eff;
  assign valid_b3 = (word_byte_base + 8'd3) < pkt_len_eff;

  logic [7:0] byte0_cur, byte1_cur, byte2_cur, byte3_cur;
  assign byte0_cur = mem_rd_data_i[7:0];
  assign byte1_cur = mem_rd_data_i[15:8];
  assign byte2_cur = mem_rd_data_i[23:16];
  assign byte3_cur = mem_rd_data_i[31:24];

  logic [7:0] sum_next, xor_next;
  assign sum_next = (word_cnt_q == 3'd0) ? sum_acc_q :
                     sum_acc_q + (valid_b0 ? byte0_cur : 8'd0)
                               + (valid_b1 ? byte1_cur : 8'd0)
                               + (valid_b2 ? byte2_cur : 8'd0)
                               + (valid_b3 ? byte3_cur : 8'd0);
  assign xor_next = (word_cnt_q == 3'd0) ? xor_acc_q :
                     xor_acc_q ^ (valid_b0 ? byte0_cur : 8'd0)
                               ^ (valid_b1 ? byte1_cur : 8'd0)
                               ^ (valid_b2 ? byte2_cur : 8'd0)
                               ^ (valid_b3 ? byte3_cur : 8'd0);

  // ------------------------------------------------------------------
  // 次态组合逻辑（§7.2 状态转移表）
  // ------------------------------------------------------------------
  always_comb begin
    state_d    = state_q;
    word_cnt_d = word_cnt_q;
    unique case (state_q)
      ST_IDLE: begin
        if (start_i) begin
          state_d    = ST_PROCESS;
          word_cnt_d = 3'd0;
        end
      end
      ST_PROCESS: begin
        if (word_cnt_q == last_word_cnt) begin
          state_d = ST_DONE; // 停止读取，进入 DONE（§7.2 §7.3）
        end else begin
          state_d    = ST_PROCESS;
          word_cnt_d = word_cnt_q + 3'd1;
        end
      end
      ST_DONE: begin
        if (start_i) begin
          state_d    = ST_PROCESS;
          word_cnt_d = 3'd0;
        end
      end
      default: begin
        state_d    = ST_IDLE; // 非法编码安全回退（不变量断言会捕获此情形）
        word_cnt_d = 3'd0;
      end
    endcase
  end

  // ------------------------------------------------------------------
  // 状态/结果寄存器更新
  // ------------------------------------------------------------------
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state_q    <= ST_IDLE;
      word_cnt_q <= 3'd0;
      pkt_len_q  <= 8'd0;
      pkt_type_q <= 8'd0;
      flags_q    <= 8'd0;
      hdr_chk_q  <= 8'd0;
      sum_acc_q  <= 8'd0;
      xor_acc_q  <= 8'd0;

      res_pkt_len_o     <= 6'd0;
      res_pkt_type_o    <= 8'd0;
      res_payload_sum_o <= 8'd0;
      res_payload_xor_o <= 8'd0;
      format_ok_o       <= 1'b0;
      length_error_o    <= 1'b0;
      type_error_o      <= 1'b0;
      chk_error_o       <= 1'b0;
    end else begin
      state_q    <= state_d;
      word_cnt_q <= word_cnt_d;

      // 第 0 拍锁存头部字段，供后续拍复用（§7.3）
      if (state_q == ST_PROCESS && word_cnt_q == 3'd0) begin
        pkt_len_q  <= mem_rd_data_i[7:0];
        pkt_type_q <= mem_rd_data_i[15:8];
        flags_q    <= mem_rd_data_i[23:16]; // 保留字段，提取但不校验（§3.1，明确不做）
        hdr_chk_q  <= mem_rd_data_i[31:24];
      end

      // payload 逐拍累加（word_cnt_q=0 时 sum_next/xor_next 等于原值，天然 no-op）
      if (state_q == ST_PROCESS) begin
        sum_acc_q <= sum_next;
        xor_acc_q <= xor_next;
      end

      // IDLE/DONE -> PROCESS：清除上一帧结果/错误标志/累加器（§7.2 §9.3）
      if ((state_q == ST_IDLE || state_q == ST_DONE) && start_i) begin
        sum_acc_q          <= 8'd0;
        xor_acc_q          <= 8'd0;
        res_pkt_len_o       <= 6'd0;
        res_pkt_type_o      <= 8'd0;
        res_payload_sum_o   <= 8'd0;
        res_payload_xor_o   <= 8'd0;
        format_ok_o         <= 1'b0;
        length_error_o      <= 1'b0;
        type_error_o        <= 1'b0;
        chk_error_o         <= 1'b0;
      end

      // PROCESS -> DONE：一次性写入结果与错误标志（§7.2 §9.2）
      if (state_q == ST_PROCESS && word_cnt_q == last_word_cnt) begin
        res_pkt_len_o       <= pkt_len_eff[5:0];  // 恒=Byte0[5:0]（r9）
        res_pkt_type_o      <= pkt_type_eff;
        res_payload_sum_o   <= sum_next;          // 含本拍（末拍）贡献
        res_payload_xor_o   <= xor_next;
        format_ok_o         <= format_ok_w;
        length_error_o      <= length_error_w;
        type_error_o        <= type_error_w;
        chk_error_o         <= chk_error_w;
      end
    end
  end

  // ------------------------------------------------------------------
  // 输出组合逻辑：busy_o/done_o/mem_rd_en_o/mem_rd_addr_o 与状态严格对应（§7.4）
  // ------------------------------------------------------------------
  assign busy_o        = (state_q == ST_PROCESS);
  assign done_o         = (state_q == ST_DONE);
  assign mem_rd_en_o    = (state_q == ST_PROCESS);
  assign mem_rd_addr_o  = word_cnt_q;

  // ------------------------------------------------------------------
  // 内部不变量断言（DE 撰写，design-prompt"内部断言建议"一节）
  // ------------------------------------------------------------------
`ifndef SYNTHESIS
  // disable iff 要求引用单一信号而非复合表达式（VCS lint Lint-[SVA-CE]），
  // 沿用 apb_slave_if.sv / packet_sram.sv 约定。
  logic rst;
  assign rst = !rst_n;

  // FSM 状态恒在合法编码内，无非法态（typedef 仅定义 3 个值，2'b11 非法）
  a_state_legal: assert property (@(posedge clk) disable iff (rst)
    state_q inside {ST_IDLE, ST_PROCESS, ST_DONE})
    else $error("packet_proc_core: FSM 出现非法状态编码");

  // busy_o 与 done_o 永不同时为 1
  a_busy_done_mutex: assert property (@(posedge clk) disable iff (rst)
    !(busy_o && done_o))
    else $error("packet_proc_core: busy_o 与 done_o 同时为 1");

  // mem_rd_en_o=1 仅出现在 PROCESS（busy_o=1）拍
  a_rden_only_process: assert property (@(posedge clk) disable iff (rst)
    mem_rd_en_o |-> busy_o)
    else $error("packet_proc_core: mem_rd_en_o 在非 PROCESS 态置起");

  // PROCESS 态字计数器不越过钳位后的最后一拍编号（读拍钳位，§7.3 r8）
  a_word_cnt_bound: assert property (@(posedge clk) disable iff (rst)
    (state_q == ST_PROCESS) |-> (word_cnt_q <= last_word_cnt))
    else $error("packet_proc_core: word_cnt_q 越过钳位后的最后一拍编号");

  // PROCESS 未到末拍时，字计数器每拍恰好 +1（mem_rd_addr_o 自 0 逐拍递增、不回绕）
  a_word_cnt_incr: assert property (@(posedge clk) disable iff (rst)
    (state_q == ST_PROCESS && word_cnt_q != last_word_cnt) |->
    (word_cnt_d == word_cnt_q + 3'd1))
    else $error("packet_proc_core: PROCESS 态字计数器未按 +1 递增");

  // PROCESS 态次态不会跳变为 IDLE（start_i 在 PROCESS 期间不改变状态，§7.2）
  a_process_ignores_start: assert property (@(posedge clk) disable iff (rst)
    (state_q == ST_PROCESS) |-> (state_d inside {ST_PROCESS, ST_DONE}))
    else $error("packet_proc_core: PROCESS 态被 start_i 提前打断为 IDLE");

  // PROCESS 期间错误标志/format_ok/res_* 输出保持清零态，仅 PROCESS->DONE 一次性更新
  a_process_outputs_clear: assert property (@(posedge clk) disable iff (rst)
    (state_q == ST_PROCESS) |->
    (!length_error_o && !type_error_o && !chk_error_o && !format_ok_o &&
     res_pkt_len_o == 6'd0 && res_pkt_type_o == 8'd0 &&
     res_payload_sum_o == 8'd0 && res_payload_xor_o == 8'd0))
    else $error("packet_proc_core: PROCESS 期间错误标志/format_ok/res_* 未保持清零");

  // algo_mode_i=0 时 chk_error 判定恒为 0（§9.2）
  a_algo_mode0_no_chkerr: assert property (@(posedge clk) disable iff (rst)
    !algo_mode_i |-> !chk_error_w)
    else $error("packet_proc_core: algo_mode_i=0 时 chk_error_w 非 0");

  // format_ok_o 与三类错误输出互斥一致（DONE 态，§9.2）
  a_format_ok_consistency: assert property (@(posedge clk) disable iff (rst)
    (state_q == ST_DONE) |->
    (format_ok_o == !(length_error_o || type_error_o || chk_error_o)))
    else $error("packet_proc_core: DONE 态 format_ok_o 与错误标志不一致");
`endif

endmodule
