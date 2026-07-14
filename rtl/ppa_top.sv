// ppa_top (Top)：PPA-Lite 顶层集成模块
// 职责：apb_slave_if(M1) + packet_sram(M2) + packet_proc_core(M3) 三子模块纯连线，
//       统一分发 PCLK/PRESETn 到 M1/M2/M3；对外仅暴露 §2.3 Top 表 11 个引脚。
//       本模块为结构化网表，无任何寄存器/FSM/组合运算/译码逻辑（§2.2 第 158 行
//       「无额外状态逻辑」、§2.1 第 102 行「薄层连线」、§11.4 第 5 周「纯连线」）。
// spec 依据：doc/design-prompt/ppa_top.md 逐条列出的 §0#2/#7/#8、§2.1、§2.2、
//           §2.3(Top/M1/M2/M3 端口表)、§6.3、§8.1、§8.2、§11.4。
//
// 互连语义要点（均为通路，行为在子模块，本模块不加工）：
//   - M1↔M2 写端口、M3↔M2 读端口（同拍组合读，BUG-003/r6，本路径不插寄存/缓冲）。
//   - M1→M3 控制、M3→M1 结果/状态；busy 写保护通路（§6.3）、中断闭环通路（§8.2）。
//   - done_o 为 M3→M1 内部信号，不引出顶层引脚（r11/BUG-010 裁决，§8.1 经 APB 轮询观察）。
//   - PCLK/PRESETn 直连映射到子模块 clk/rst_n，均低有效复位，无同步器/门控/分频/极性变换。

module ppa_top (
    // ---- 对外端口：§2.3 Top ppa_top 端口表（第 241–253 行，唯一权威，11 信号）----
    input  logic        PCLK,     // APB 时钟
    input  logic        PRESETn,  // APB 复位（低有效）
    input  logic        PSEL,     // APB 从设备选择
    input  logic        PENABLE,  // APB 使能信号
    input  logic        PWRITE,   // APB 写使能
    input  logic [11:0] PADDR,    // APB 地址
    input  logic [31:0] PWDATA,   // APB 写数据
    output logic [31:0] PRDATA,   // APB 读数据
    output logic        PREADY,   // APB 就绪（固定 1，M1 产生）
    output logic        PSLVERR,  // APB 错误响应（M1 产生）
    output logic        irq_o     // 中断输出（来自 M1，覆盖 done/err 事件通知）
);

  // ------------------------------------------------------------------
  // 内部互连线（信号名/位宽以 §2.3 各子模块表为准）
  // ------------------------------------------------------------------
  // M1 → M2 写端口（§2.3 M1 pkt_mem_*_o / M2 wr_*）
  logic        pkt_mem_we;      // M1.pkt_mem_we_o   → M2.wr_en
  logic [2:0]  pkt_mem_addr;    // M1.pkt_mem_addr_o → M2.wr_addr
  logic [31:0] pkt_mem_wdata;   // M1.pkt_mem_wdata_o→ M2.wr_data

  // M3 → M2 读端口（§2.3 M3 mem_rd_*_o / M2 rd_*；同拍组合读，不插寄存 r6）
  logic        mem_rd_en;       // M3.mem_rd_en_o    → M2.rd_en
  logic [2:0]  mem_rd_addr;     // M3.mem_rd_addr_o  → M2.rd_addr
  logic [31:0] mem_rd_data;     // M2.rd_data        → M3.mem_rd_data_i

  // M1 → M3 控制（§2.3 M3 输入「来自 M1」）
  logic        start;           // M1.start_o        → M3.start_i
  logic        algo_mode;       // M1.algo_mode_o    → M3.algo_mode_i
  logic [3:0]  type_mask;       // M1.type_mask_o    → M3.type_mask_i
  logic [5:0]  exp_pkt_len;     // M1.exp_pkt_len_o  → M3.exp_pkt_len_i

  // M3 → M1 结果/状态（§2.3 M1 输入「M3 …」）
  logic        busy;            // M3.busy_o         → M1.busy_i（含 §6.3 写保护通路）
  logic        done;            // M3.done_o         → M1.done_i（§8.2 中断闭环通路）
  logic        format_ok;       // M3.format_ok_o    → M1.format_ok_i
  logic        length_error;    // M3.length_error_o → M1.length_error_i
  logic        type_error;      // M3.type_error_o   → M1.type_error_i
  logic        chk_error;       // M3.chk_error_o    → M1.chk_error_i
  logic [5:0]  res_pkt_len;     // M3.res_pkt_len_o  → M1.res_pkt_len_i（6-bit 直连 r9）
  logic [7:0]  res_pkt_type;    // M3.res_pkt_type_o → M1.res_pkt_type_i
  logic [7:0]  res_payload_sum; // M3.res_payload_sum_o → M1.res_payload_sum_i
  logic [7:0]  res_payload_xor; // M3.res_payload_xor_o → M1.res_payload_xor_i

  // ------------------------------------------------------------------
  // M1：apb_slave_if —— APB 从机 + CSR + PKT_MEM 写译码 + 中断（§2.3 M1 表）
  //   顶层 APB 引脚直透；enable_o/done_irq_en_o/err_irq_en_o 为字段观测抽头，
  //   §2.3 Top 表无对应引脚、无子模块消费，按 design-prompt 允许悬空。
  // ------------------------------------------------------------------
  apb_slave_if u_apb (
      // APB 3.0 从机接口（顶层引脚直透）
      .PCLK           (PCLK),
      .PRESETn        (PRESETn),
      .PSEL           (PSEL),
      .PENABLE        (PENABLE),
      .PWRITE         (PWRITE),
      .PADDR          (PADDR),
      .PWDATA         (PWDATA),
      .PRDATA         (PRDATA),
      .PREADY         (PREADY),
      .PSLVERR        (PSLVERR),
      // 字段广播输出 → M3 控制
      .enable_o       (/* 未连接：CTRL.enable 观测抽头，§2.3 Top 无引脚 */),
      .start_o        (start),
      .algo_mode_o    (algo_mode),
      .type_mask_o    (type_mask),
      .exp_pkt_len_o  (exp_pkt_len),
      .done_irq_en_o  (/* 未连接：IRQ_EN.done_irq_en 观测抽头，§2.3 Top 无引脚 */),
      .err_irq_en_o   (/* 未连接：IRQ_EN.err_irq_en 观测抽头，§2.3 Top 无引脚 */),
      // PKT_MEM 写通路 → M2
      .pkt_mem_we_o   (pkt_mem_we),
      .pkt_mem_addr_o (pkt_mem_addr),
      .pkt_mem_wdata_o(pkt_mem_wdata),
      // M3 结果/状态只读输入
      .busy_i         (busy),
      .done_i         (done),
      .format_ok_i    (format_ok),
      .length_error_i (length_error),
      .type_error_i   (type_error),
      .chk_error_i    (chk_error),
      .res_pkt_len_i  (res_pkt_len),
      .res_pkt_type_i (res_pkt_type),
      .res_payload_sum_i(res_payload_sum),
      .res_payload_xor_i(res_payload_xor),
      // 中断输出 → 顶层引脚
      .irq_o          (irq_o)
  );

  // ------------------------------------------------------------------
  // M2：packet_sram —— 8×32-bit SRAM（写端口来自 M1，读端口供 M3；§2.3 M2 表）
  //   clk/rst_n 由 PCLK/PRESETn 直连映射（§2.1 第 118 行、§2.3 M2 表 clk/rst_n 说明）。
  // ------------------------------------------------------------------
  packet_sram u_sram (
      .clk     (PCLK),
      .rst_n   (PRESETn),
      // 写端口（来自 M1）
      .wr_en   (pkt_mem_we),
      .wr_addr (pkt_mem_addr),
      .wr_data (pkt_mem_wdata),
      // 读端口（供 M3；同拍组合读 r6）
      .rd_en   (mem_rd_en),
      .rd_addr (mem_rd_addr),
      .rd_data (mem_rd_data)
  );

  // ------------------------------------------------------------------
  // M3：packet_proc_core —— 3 态 FSM 包处理核（§2.3 M3 表）
  //   clk/rst_n 由 PCLK/PRESETn 直连映射（§2.1 第 118 行、§2.3 M3 表 clk/rst_n 说明）。
  // ------------------------------------------------------------------
  packet_proc_core u_core (
      .clk           (PCLK),
      .rst_n         (PRESETn),
      // 控制输入（来自 M1）
      .start_i       (start),
      .algo_mode_i   (algo_mode),
      .type_mask_i   (type_mask),
      .exp_pkt_len_i (exp_pkt_len),
      // SRAM 读端口（供/来自 M2）
      .mem_rd_en_o   (mem_rd_en),
      .mem_rd_addr_o (mem_rd_addr),
      .mem_rd_data_i (mem_rd_data),
      // 状态输出 → M1
      .busy_o        (busy),
      .done_o        (done),
      // 结果输出 → M1
      .res_pkt_len_o     (res_pkt_len),
      .res_pkt_type_o    (res_pkt_type),
      .res_payload_sum_o (res_payload_sum),
      .res_payload_xor_o (res_payload_xor),
      // 错误/格式标志 → M1
      .format_ok_o    (format_ok),
      .length_error_o (length_error),
      .type_error_o   (type_error),
      .chk_error_o    (chk_error)
  );

  // ------------------------------------------------------------------
  // 内部不变量断言（DE 撰写，§0 适配 #7；design-prompt「内部断言建议」一节）
  // 纯连线无状态模块，断言聚焦连通性与信号确定性：
  //   (1) 复位释放后关键互连线无 X —— 早期发现悬空/错接；
  //   (2) 子模块 clk/rst_n 与顶层同源直连 —— 捕获意外插入的门控/分频/极性变换。
  // ------------------------------------------------------------------
`ifndef SYNTHESIS
  // disable iff 要求引用单一信号而非复合表达式（VCS lint Lint-[SVA-CE]），
  // 沿用 apb_slave_if.sv / packet_sram.sv / packet_proc_core.sv 约定。
  logic rst;
  assign rst = !PRESETn;

  // (1) 关键互连线复位后无 X（悬空/错接自检）
  a_no_x_pkt_mem_we: assert property (@(posedge PCLK) disable iff (rst)
    !$isunknown(pkt_mem_we))
    else $error("ppa_top: pkt_mem_we 复位后为 X 态");

  a_no_x_mem_rd_en: assert property (@(posedge PCLK) disable iff (rst)
    !$isunknown(mem_rd_en))
    else $error("ppa_top: mem_rd_en 复位后为 X 态");

  a_no_x_busy: assert property (@(posedge PCLK) disable iff (rst)
    !$isunknown(busy))
    else $error("ppa_top: busy 复位后为 X 态");

  a_no_x_done: assert property (@(posedge PCLK) disable iff (rst)
    !$isunknown(done))
    else $error("ppa_top: done 复位后为 X 态");

  a_no_x_start: assert property (@(posedge PCLK) disable iff (rst)
    !$isunknown(start))
    else $error("ppa_top: start 复位后为 X 态");

  // 读通路组合直连自检：M2.rd_data 与 M3.mem_rd_data_i 为同一网（无中间逻辑，r6）
  a_rd_data_direct: assert property (@(posedge PCLK) disable iff (rst)
    u_sram.rd_data === u_core.mem_rd_data_i)
    else $error("ppa_top: M2.rd_data 与 M3.mem_rd_data_i 非同源直连");

  // (2) 子模块时钟/复位与顶层同源（捕获意外门控/分频/极性变换）
  a_sram_clk_conn: assert property (@(posedge PCLK)
    u_sram.clk === PCLK)
    else $error("ppa_top: M2.clk 与 PCLK 非同源直连");

  a_core_clk_conn: assert property (@(posedge PCLK)
    u_core.clk === PCLK)
    else $error("ppa_top: M3.clk 与 PCLK 非同源直连");

  a_sram_rst_conn: assert property (@(posedge PCLK)
    u_sram.rst_n === PRESETn)
    else $error("ppa_top: M2.rst_n 与 PRESETn 非同源直连（疑似极性变换）");

  a_core_rst_conn: assert property (@(posedge PCLK)
    u_core.rst_n === PRESETn)
    else $error("ppa_top: M3.rst_n 与 PRESETn 非同源直连（疑似极性变换）");
`endif

endmodule
