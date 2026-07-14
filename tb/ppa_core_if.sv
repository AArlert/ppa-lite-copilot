// packet_proc_core（M3）单元级验证接口 + 行为 SRAM 模型（M2 独立 TB）。
// 只承载 spec §2.3(M3 端口表) 列出的模块端口；行为 SRAM 按 §6.1 窗口（8 word）
// 建模，读端口为同拍组合读（BUG-003/r6：rd_en=1 当拍 rd_data=mem[rd_addr] 有效、
// 无寄存延迟）。字节装 word 采用附录 A 大端约定：Word 的 [31:24]=Byte0 … [7:0]=Byte3
// （见 spec 附录 A：`APB_WRITE(0x040, 32'h08_01_00_09)` → pkt_len=0x08 位于 MSB）。
// 仅供 TB 使用，不代表 RTL 内部实现契约。
interface ppa_core_if (input logic clk, input logic rst_n);

  // ---- 驱动到 DUT（激励） ----
  logic        start_i       = 1'b0;
  logic        algo_mode_i   = 1'b1;   // 复位默认 1（§5.2 CFG.algo_mode）
  logic [3:0]  type_mask_i   = 4'b1111;// 复位默认 1111（§5.2 CFG.type_mask）
  logic [5:0]  exp_pkt_len_i = 6'd0;   // 复位默认 0=未配置（§5.2 PKT_LEN_EXP，r4）

  // ---- 来自 DUT（观测） ----
  logic        mem_rd_en_o;
  logic [2:0]  mem_rd_addr_o;
  logic        busy_o;
  logic        done_o;
  logic [5:0]  res_pkt_len_o;
  logic [7:0]  res_pkt_type_o;
  logic [7:0]  res_payload_sum_o;
  logic [7:0]  res_payload_xor_o;
  logic        format_ok_o;
  logic        length_error_o;
  logic        type_error_o;
  logic        chk_error_o;

  // ---- 行为 SRAM（§6.1：8 word 窗口）----
  // mem 由 driver 在帧起始前装载；组合读回给 DUT 的 mem_rd_data_i（r6 同拍组合读）
  logic [31:0] mem [0:7];
  logic [31:0] mem_rd_data_i;
  // rd_addr 为 3-bit，天然落在 [0,7] 窗口内（§6.1，禁止越窗口由 DUT 侧钳位保证）
  assign mem_rd_data_i = mem[mem_rd_addr_o];

  // ---- 驱动/采样时钟块 ----
  clocking drv_cb @(posedge clk);
    output start_i, algo_mode_i, type_mask_i, exp_pkt_len_i;
    input  mem_rd_en_o, mem_rd_addr_o, busy_o, done_o,
           res_pkt_len_o, res_pkt_type_o, res_payload_sum_o, res_payload_xor_o,
           format_ok_o, length_error_o, type_error_o, chk_error_o;
  endclocking

endinterface
