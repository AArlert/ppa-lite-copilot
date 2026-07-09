// M3 桩接口：M3（packet_proc_core）本轮尚未交付，本接口为驱动 apb_slave_if
// 的"M3 结果只读输入"（busy_i/done_i/format_ok_i/length_error_i/type_error_i/
// chk_error_i/res_pkt_len_i/res_pkt_type_i/res_payload_sum_i/res_payload_xor_i，
// spec §2.3 M1 端口表）提供受控激励，供 M1-03（RES_* 只读通路）/M1-05（IRQ）
// /M1-06（busy 期间读 PKT_MEM）场景使用；irq 字段旁路采样 apb_slave_if.irq_o
// 输出（同一张 §2.3 端口表），供 M1-05 中断路径观测；start_pulse 字段旁路采样
// apb_slave_if.start_o 输出（§2.3 M1 端口表"触发脉冲…送 M3"），供 M1-07 观测
// CTRL.START 单拍脉冲行为。rd_en/rd_addr/rd_data 字段驱动/观测 packet_sram（M2）
// 的读端口（§2.3 M2 表："rd_en/rd_addr 来自 M3"），本 stub 代行 M3 角色驱动，
// 供 M1-08（busy 写保护后经 SRAM 读口核实内容不变）/M1-09（SRAM 组合读行为）
// 场景使用。
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

  // packet_sram（M2）读端口驱动侧：默认 rd_en=0（不读），spec §2.3 M2 表
  logic       rd_en   = 1'b0;
  logic [2:0] rd_addr = 3'd0;
  // packet_sram（M2）读数据观测（tb_top 内直连 packet_sram.rd_data），只读
  logic [31:0] rd_data;

  // DUT irq_o 观测（tb_top 内 assign 连接），只读，不经本接口驱动
  logic irq;
  // DUT start_o 观测（tb_top 内 assign 连接），只读，不经本接口驱动
  logic start_pulse;

  // 驱动时钟块：本 stub 作为"主机"角色驱动 M1 的结果输入 + M2 的读端口；
  // irq/start_pulse/rd_data 作为输入采样观测
  clocking drv_cb @(posedge pclk);
    output busy, done, format_ok, length_error, type_error, chk_error,
           res_pkt_len, res_pkt_type, res_payload_sum, res_payload_xor,
           rd_en, rd_addr;
    input  irq, start_pulse, rd_data;
  endclocking

endinterface
