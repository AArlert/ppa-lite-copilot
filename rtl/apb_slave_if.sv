// apb_slave_if (M1)：APB 3.0 从机 + CSR 寄存器组 + 地址译码
// 职责：APB 两段式从机时序（PREADY 恒 1）；CTRL/CFG/STATUS/IRQ_EN/IRQ_STA/
//       PKT_LEN_EXP/RES_*/ERR_FLAG 寄存器组读写；PKT_MEM 窗口(0x040~0x05C)
//       写地址译码并转发给 M2；STATUS/RES_*/ERR_FLAG 对 M3 结果只读直透，
//       不做任何包语义判断；IRQ 生成与 RW1C 清除；PSLVERR 统一错误响应。
// spec 依据：doc/design-prompt/apb_slave_if.md 逐条列出的 §2.3(M1 端口表)/
//           §4.1/§4.2/§5.1/§5.2/§6.1/§6.3/§8.1/§8.2/§8.3/§9.1/§11.2。
//
// 已知遗留问题（BUG-004，OPEN，待 rev/arch 裁决）：
//   §6.3"APB 读 PKT_MEM 任意时刻返回当前 SRAM 内容"与 §2.3 M1 端口表（M1 对
//   PKT_MEM 只有写通路、无读回数据输入）结构性冲突。本模块对 PKT_MEM 地址范围
//   的读访问采用 PSLVERR=0（合法访问）+ PRDATA 固定输出 0（无数据源可用，仅避免
//   X 态，非真实 SRAM 内容）的临时处理，不作为对外行为承诺，见 doc/bugs.md。

module apb_slave_if
  import ppa_reg_defs_pkg::*;
(
    // ---- APB 3.0 从机接口（§2.3 M1 端口表）----
    input  logic        PCLK,
    input  logic        PRESETn,
    input  logic        PSEL,
    input  logic        PENABLE,
    input  logic        PWRITE,
    input  logic [11:0]  PADDR,
    input  logic [31:0]  PWDATA,
    output logic [31:0]  PRDATA,
    output logic         PREADY,
    output logic         PSLVERR,

    // ---- 字段广播输出（送 M3，§5.2 §2.3）----
    output logic         enable_o,
    output logic         start_o,
    output logic         algo_mode_o,
    output logic [3:0]   type_mask_o,
    output logic [5:0]   exp_pkt_len_o,
    output logic         done_irq_en_o,
    output logic         err_irq_en_o,

    // ---- PKT_MEM 写通路（送 M2，§6.1）----
    output logic         pkt_mem_we_o,
    output logic [2:0]   pkt_mem_addr_o,
    output logic [31:0]  pkt_mem_wdata_o,

    // ---- M3 结果只读输入（透传到 RES_*/STATUS/ERR_FLAG，§8.1 §9.1）----
    input  logic         busy_i,
    input  logic         done_i,
    input  logic         format_ok_i,
    input  logic         length_error_i,
    input  logic         type_error_i,
    input  logic         chk_error_i,
    input  logic [5:0]   res_pkt_len_i,
    input  logic [7:0]   res_pkt_type_i,
    input  logic [7:0]   res_payload_sum_i,
    input  logic [7:0]   res_payload_xor_i,

    // ---- 中断输出 ----
    output logic         irq_o
);

  // ------------------------------------------------------------------
  // APB 两段式时序（§4.1）：PREADY 恒 1，无等待态
  // ------------------------------------------------------------------
  assign PREADY = 1'b1;

  // ACCESS 阶段：PSEL=1 且 PENABLE=1；PREADY 恒 1，此阶段仅持续 1 个时钟周期
  logic access;
  logic write_access;
  logic read_access;
  assign access       = PSEL && PENABLE;
  assign write_access = access && PWRITE;
  assign read_access  = access && !PWRITE;

  // ------------------------------------------------------------------
  // 地址译码（§4.2 §5.2 §6.1）
  // ------------------------------------------------------------------
  logic is_ctrl, is_cfg, is_status, is_irq_en, is_irq_sta, is_pkt_len_exp;
  logic is_res_pkt_len, is_res_pkt_type, is_res_payload_sum, is_res_payload_xor;
  logic is_err_flag;
  logic is_csr_defined;   // 命中已定义的 11 个 CSR 之一
  logic is_ro_reg;        // 命中只读寄存器（STATUS/RES_*/ERR_FLAG）
  logic is_csr_range;     // 落在 CSR 区地址范围 0x000~0x02B（§4.2）
  logic is_pkt_mem_range; // 落在 PKT_MEM 窗口 0x040~0x05C（§6.1）

  assign is_ctrl            = (PADDR == ADDR_CTRL);
  assign is_cfg              = (PADDR == ADDR_CFG);
  assign is_status           = (PADDR == ADDR_STATUS);
  assign is_irq_en           = (PADDR == ADDR_IRQ_EN);
  assign is_irq_sta          = (PADDR == ADDR_IRQ_STA);
  assign is_pkt_len_exp      = (PADDR == ADDR_PKT_LEN_EXP);
  assign is_res_pkt_len      = (PADDR == ADDR_RES_PKT_LEN);
  assign is_res_pkt_type     = (PADDR == ADDR_RES_PKT_TYPE);
  assign is_res_payload_sum  = (PADDR == ADDR_RES_PAYLOAD_SUM);
  assign is_res_payload_xor  = (PADDR == ADDR_RES_PAYLOAD_XOR);
  assign is_err_flag         = (PADDR == ADDR_ERR_FLAG);

  assign is_csr_defined = is_ctrl | is_cfg | is_status | is_irq_en | is_irq_sta |
                           is_pkt_len_exp | is_res_pkt_len | is_res_pkt_type |
                           is_res_payload_sum | is_res_payload_xor | is_err_flag;
  assign is_ro_reg = is_status | is_res_pkt_len | is_res_pkt_type |
                      is_res_payload_sum | is_res_payload_xor | is_err_flag;

  assign is_csr_range     = (PADDR <= 12'h02B);
  assign is_pkt_mem_range = (PADDR >= ADDR_PKT_MEM_BASE) && (PADDR <= ADDR_PKT_MEM_END);
  // 0x02C~0x03F、0x05D~0x05F、0x060 及以上均落入"既非 CSR 区也非 PKT_MEM 区"，
  // 统一按保留/未定义处理（§4.2 §8.3），不再单独区分子区间。

  // ------------------------------------------------------------------
  // CSR 寄存器存储（RW 字段，§5.2）；复位值见 §5.2 表
  // ------------------------------------------------------------------
  logic       ctrl_enable;    // CTRL.enable（RW，复位 0）
  logic       cfg_algo_mode;  // CFG.algo_mode（RW，复位 1）
  logic [3:0] cfg_type_mask;  // CFG.type_mask（RW，复位 4'b1111）
  logic       irq_en_done;    // IRQ_EN.done_irq_en（RW，复位 0）
  logic       irq_en_err;     // IRQ_EN.err_irq_en（RW，复位 0）
  logic [5:0] pkt_len_exp;    // PKT_LEN_EXP.exp_pkt_len（RW，复位 0）

  always_ff @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      ctrl_enable   <= 1'b0;
      cfg_algo_mode <= 1'b1;
      cfg_type_mask <= 4'b1111;
      irq_en_done   <= 1'b0;
      irq_en_err    <= 1'b0;
      pkt_len_exp   <= 6'b0;
    end else if (write_access) begin
      if (is_ctrl) ctrl_enable <= PWDATA[0];
      if (is_cfg) begin
        cfg_algo_mode <= PWDATA[0];
        cfg_type_mask <= PWDATA[7:4];
      end
      if (is_irq_en) begin
        irq_en_done <= PWDATA[0];
        irq_en_err  <= PWDATA[1];
      end
      if (is_pkt_len_exp) pkt_len_exp <= PWDATA[5:0];
    end
  end

  // ------------------------------------------------------------------
  // STATUS/RES_*/ERR_FLAG：M3 结果只读直透，不锁存不判定（§8.1 §9.1，
  // design-prompt"边界与约束"一节明示）
  // ------------------------------------------------------------------
  logic any_error_w;
  assign any_error_w = length_error_i | type_error_i | chk_error_i; // STATUS[2]（§5.2）

  // ------------------------------------------------------------------
  // CTRL.start（W1P）：仅在 enable=1 && busy=0 时被接受，产生单拍脉冲（§5.2）
  // 使用当前（写前）ctrl_enable 值判定，与附录 A 示例"先写 enable 再写 start"
  // 的两步序列一致
  // ------------------------------------------------------------------
  assign start_o = write_access && is_ctrl && PWDATA[1] && ctrl_enable && !busy_i;

  // ------------------------------------------------------------------
  // IRQ_STA（RW1C）与中断生成（§8.2）：
  //   done_i 上升沿 且 对应 irq_en=1 时"同拍立即置位"；软件写1下一拍清零。
  //   为实现"同拍置位"（而非延迟 1 拍），置位判定使用当前拍 done_i 与上一拍
  //   done_i_prev 的组合比较（done_rise 为组合信号，在 done_i 首次为 1 的
  //   同一拍即为真），IRQ_STA 位的对外可见值 = 组合脉冲项 或 已锁存的
  //   held 寄存器，二者相或，从而在触发的同一拍即可见、且能被后续软件读取/
  //   清零持久保持。
  // ------------------------------------------------------------------
  logic done_i_prev;
  logic done_rise;

  always_ff @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) done_i_prev <= 1'b0;
    else          done_i_prev <= done_i;
  end
  assign done_rise = done_i & ~done_i_prev;

  logic irq_sta_done_held, irq_sta_err_held;
  logic irq_sta_done, irq_sta_err;

  always_ff @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      irq_sta_done_held <= 1'b0;
    end else if (done_rise && irq_en_done) begin
      irq_sta_done_held <= 1'b1;
    end else if (write_access && is_irq_sta && PWDATA[0]) begin
      irq_sta_done_held <= 1'b0;
    end
  end

  always_ff @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn) begin
      irq_sta_err_held <= 1'b0;
    end else if (done_rise && any_error_w && irq_en_err) begin
      irq_sta_err_held <= 1'b1;
    end else if (write_access && is_irq_sta && PWDATA[1]) begin
      irq_sta_err_held <= 1'b0;
    end
  end

  assign irq_sta_done = (done_rise && irq_en_done) | irq_sta_done_held;
  assign irq_sta_err  = (done_rise && any_error_w && irq_en_err) | irq_sta_err_held;
  assign irq_o        = irq_sta_done | irq_sta_err;

  // ------------------------------------------------------------------
  // 字段广播输出（§5.2 §2.3）：反映对应 RW 字段当前值
  // ------------------------------------------------------------------
  assign enable_o       = ctrl_enable;
  assign algo_mode_o    = cfg_algo_mode;
  assign type_mask_o    = cfg_type_mask;
  assign exp_pkt_len_o  = pkt_len_exp;
  assign done_irq_en_o  = irq_en_done;
  assign err_irq_en_o   = irq_en_err;

  // ------------------------------------------------------------------
  // PKT_MEM 写通路（§6.1 §6.3 §8.3）：busy=1 期间写保护，仅本模块把关
  // ------------------------------------------------------------------
  logic [11:0] pkt_mem_offset;
  assign pkt_mem_offset  = PADDR - ADDR_PKT_MEM_BASE;
  assign pkt_mem_we_o    = write_access && is_pkt_mem_range && !busy_i;
  assign pkt_mem_addr_o  = pkt_mem_offset[4:2]; // (PADDR-0x040)>>2 = Word N（§6.1）
  assign pkt_mem_wdata_o = PWDATA;

  // ------------------------------------------------------------------
  // PSLVERR 统一响应（§8.3）：仅在 ACCESS 阶段随访问给出
  // ------------------------------------------------------------------
  always_comb begin
    PSLVERR = 1'b0;
    if (access) begin
      if (!is_csr_range && !is_pkt_mem_range) begin
        // 保留区(0x02C~0x03F/0x05D~0x05F)或未定义地址(0x060+)：无副作用（§4.2 §8.3）
        PSLVERR = 1'b1;
      end else if (is_pkt_mem_range) begin
        // PKT_MEM：写受 busy 保护（§6.3）；读不受 busy 保护，恒合法（BUG-004 备注）
        PSLVERR = write_access && busy_i;
      end else begin
        // CSR 区：写只读寄存器报错；未命中已定义偏移的地址按"未列位域"处理，
        // 读写均无副作用、PSLVERR=0（§5.2 尾注的寄存器粒度推广）
        PSLVERR = write_access && is_ro_reg;
      end
    end
  end

  // ------------------------------------------------------------------
  // PRDATA：组合读，地址落在 ACCESS 阶段即可采样（§4.1 允许组合或寄存器输出）
  // ------------------------------------------------------------------
  always_comb begin
    unique case (1'b1)
      is_ctrl:             PRDATA = {30'b0, 1'b0, ctrl_enable}; // start 读回恒 0（W1P 不存储）
      is_cfg:               PRDATA = {24'b0, cfg_type_mask, 3'b0, cfg_algo_mode};
      is_status:            PRDATA = {28'b0, format_ok_i, any_error_w, done_i, busy_i};
      is_irq_en:            PRDATA = {30'b0, irq_en_err, irq_en_done};
      is_irq_sta:           PRDATA = {30'b0, irq_sta_err, irq_sta_done};
      is_pkt_len_exp:       PRDATA = {26'b0, pkt_len_exp};
      is_res_pkt_len:       PRDATA = {26'b0, res_pkt_len_i};
      is_res_pkt_type:      PRDATA = {24'b0, res_pkt_type_i};
      is_res_payload_sum:   PRDATA = {24'b0, res_payload_sum_i};
      is_res_payload_xor:   PRDATA = {24'b0, res_payload_xor_i};
      is_err_flag:          PRDATA = {29'b0, chk_error_i, type_error_i, length_error_i};
      is_pkt_mem_range:     PRDATA = 32'd0; // BUG-004：M1 无 SRAM 读回数据源，见 doc/bugs.md
      default:              PRDATA = 32'd0; // 保留/未定义地址、未命中的 CSR 偏移（§5.2 尾注）
    endcase
  end

  // ------------------------------------------------------------------
  // 内部不变量断言（DE 撰写，design-prompt"内部断言建议"一节）
  // ------------------------------------------------------------------
`ifndef SYNTHESIS
  // disable iff 要求引用单一信号而非复合表达式（VCS lint Lint-[SVA-CE] "Complex
  // expression found"），故用一个连续赋值的高有效复位信号供各断言复用（同 packet_sram.sv 约定）。
  logic rst;
  assign rst = !PRESETn;

  // PREADY 恒为 1（§4.1）
  a_pready_always1: assert property (@(posedge PCLK) disable iff (rst)
    PREADY == 1'b1)
    else $error("apb_slave_if: PREADY 非恒 1");

  // pkt_mem_we_o 有效 => 处于 ACCESS 写、地址在 PKT_MEM 窗口、且 busy_i=0（§6.3 §8.3）
  a_we_valid_cond: assert property (@(posedge PCLK) disable iff (rst)
    pkt_mem_we_o |-> (write_access && is_pkt_mem_range && !busy_i))
    else $error("apb_slave_if: pkt_mem_we_o 置起条件不满足");

  // busy_i=1 时 PKT_MEM 写不得产生 we 脉冲（§6.3）
  a_no_we_when_busy: assert property (@(posedge PCLK) disable iff (rst)
    busy_i |-> !pkt_mem_we_o)
    else $error("apb_slave_if: busy=1 期间出现 pkt_mem_we_o");

  // start_o 蕴含 enable=1 && busy=0（§5.2）
  a_start_implies_enable_idle: assert property (@(posedge PCLK) disable iff (rst)
    start_o |-> (ctrl_enable && !busy_i))
    else $error("apb_slave_if: start_o 置起时 enable/busy 条件不满足");

  // start_o 至多单拍脉冲（依赖 APB 协议合规：ACCESS 阶段仅持续 1 拍，
  // 新事务须先经 SETUP 阶段，PSEL&&PENABLE 不会连续 2 拍为同一事务保持；
  // 本断言为设计自检，非协议契约本身）
  a_start_single_pulse: assert property (@(posedge PCLK) disable iff (rst)
    start_o |=> !start_o)
    else $error("apb_slave_if: start_o 连续多拍有效");

  // 地址译码互斥：同一 ACCESS 拍 CSR 命中与 PKT_MEM 命中不同时有效（结构性恒成立）
  a_addr_decode_mutex: assert property (@(posedge PCLK) disable iff (rst)
    !(is_csr_defined && is_pkt_mem_range))
    else $error("apb_slave_if: CSR 与 PKT_MEM 地址译码同时命中");

  // PSLVERR=1 时不得产生 PKT_MEM 写副作用（§8.3）
  a_pslverr_no_we_sideeffect: assert property (@(posedge PCLK) disable iff (rst)
    PSLVERR |-> !pkt_mem_we_o)
    else $error("apb_slave_if: PSLVERR=1 但仍产生 pkt_mem_we_o");

  // 写只读寄存器必然报 PSLVERR=1（§5.1 §8.3，与"寄存器值不变"配合：RO 寄存器
  // 在本模块内本无存储，故"值不变"天然成立）
  a_pslverr_on_ro_write: assert property (@(posedge PCLK) disable iff (rst)
    (write_access && is_ro_reg) |-> PSLVERR)
    else $error("apb_slave_if: 写只读寄存器未报 PSLVERR");
`endif

endmodule
