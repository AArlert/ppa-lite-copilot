// M3 桩接口：M3（packet_proc_core）本轮尚未交付，本接口为驱动 apb_slave_if
// 的"M3 结果只读输入"（busy_i/done_i/format_ok_i/length_error_i/type_error_i/
// chk_error_i/res_pkt_len_i/res_pkt_type_i/res_payload_sum_i/res_payload_xor_i，
// spec §2.3 M1 端口表）提供受控激励，供 M1-03（RES_* 只读通路）/M1-05（IRQ）
// /M1-06（busy 期间读 PKT_MEM）场景使用；irq 字段旁路采样 apb_slave_if.irq_o
// 输出（同一张 §2.3 端口表），供 M1-05 中断路径观测。
// 仅供 TB 使用，不代表 M3 的设计契约（M3 由后续 Lab2 独立交付）。
interface m3_stub_if (input logic pclk);

  // 各字段默认值 0：spec §5.2 寄存器表 STATUS/RES_*/ERR_FLAG 复位值均为 0，
  // 本 stub 上电默认态与之一致
  logic       busy         = 1'b0;
  logic       done         = 1'b0;
  logic       format_ok    = 1'b0;
  logic       length_error = 1'b0;
  logic       type_error   = 1'b0;
  logic       chk_error    = 1'b0;
  logic [5:0] res_pkt_len     = 6'd0;
  logic [7:0] res_pkt_type    = 8'd0;
  logic [7:0] res_payload_sum = 8'd0;
  logic [7:0] res_payload_xor = 8'd0;

  // DUT irq_o 观测（tb_top 内 assign 连接），只读，不经本接口驱动
  logic irq;

  // 驱动时钟块：本 stub 作为"主机"角色驱动 M1 的结果输入；irq 作为输入采样观测
  clocking drv_cb @(posedge pclk);
    output busy, done, format_ok, length_error, type_error, chk_error,
           res_pkt_len, res_pkt_type, res_payload_sum, res_payload_xor;
    input  irq;
  endclocking

endinterface
