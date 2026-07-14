// TB 顶层：时钟/复位、接口实例、DUT 接入点、run_test 入口
`timescale 1ns/1ps

module tb_top;

  import uvm_pkg::*;
  import ppa_test_pkg::*;

  logic pclk;
  logic presetn;

  // 100MHz 时钟 + 低有效复位
  initial begin
    pclk = 1'b0;
    forever #5 pclk = ~pclk;
  end

  initial begin
    presetn = 1'b0;
    repeat (5) @(posedge pclk);
    presetn = 1'b1;
  end

  apb_if #(.ADDR_W(12), .DATA_W(32)) apb (.pclk(pclk), .presetn(presetn));

  // ---- DUT 接入点 ----
  // M1（apb_slave_if + packet_sram）已交付，HAS_DUT 由 sim/flist/rtl.f 定义。
  // M2 的 rd_en/rd_addr/rd_data 接至 m3_stub_if（M3 尚未交付，由 stub 代行 M3
  // 角色驱动/观测该读口，§2.3 M2 表注 r7：读端口仅供 M3），供 M1-08/M1-09 场景
  // 经 m3_stub_driver 驱动 rd_en/rd_addr、观测 rd_data。
`ifdef HAS_DUT
  logic        start_w;
  logic        pkt_mem_we_w;
  logic [2:0]  pkt_mem_addr_w;
  logic [31:0] pkt_mem_wdata_w;
  logic        irq_w;

  // M3 尚未交付：用受控 stub 接口驱动 apb_slave_if 的 M3 结果只读输入
  // （§2.3 M1 端口表 busy_i/done_i/.../res_payload_xor_i），供 UVM 环境
  // （tb/uvm/env/m3_stub_driver.sv）驱动，M1-03/M1-05/M1-06 场景使用。
  m3_stub_if m3_stub (.pclk(pclk));
  assign m3_stub.irq         = irq_w;
  assign m3_stub.start_pulse = start_w;

  apb_slave_if u_apb_slave_if (
      .PCLK    (pclk),
      .PRESETn (presetn),
      .PSEL    (apb.psel),
      .PENABLE (apb.penable),
      .PWRITE  (apb.pwrite),
      .PADDR   (apb.paddr),
      .PWDATA  (apb.pwdata),
      .PRDATA  (apb.prdata),
      .PREADY  (apb.pready),
      .PSLVERR (apb.pslverr),

      .enable_o      (),
      .start_o       (start_w),
      .algo_mode_o   (),
      .type_mask_o   (),
      .exp_pkt_len_o (),
      .done_irq_en_o (),
      .err_irq_en_o  (),

      .pkt_mem_we_o    (pkt_mem_we_w),
      .pkt_mem_addr_o  (pkt_mem_addr_w),
      .pkt_mem_wdata_o (pkt_mem_wdata_w),

      .busy_i            (m3_stub.busy),
      .done_i            (m3_stub.done),
      .format_ok_i       (m3_stub.format_ok),
      .length_error_i    (m3_stub.length_error),
      .type_error_i      (m3_stub.type_error),
      .chk_error_i       (m3_stub.chk_error),
      .res_pkt_len_i     (m3_stub.res_pkt_len),
      .res_pkt_type_i    (m3_stub.res_pkt_type),
      .res_payload_sum_i (m3_stub.res_payload_sum),
      .res_payload_xor_i (m3_stub.res_payload_xor),

      .irq_o (irq_w)
  );

  packet_sram u_packet_sram (
      .clk     (pclk),
      .rst_n   (presetn),
      .wr_en   (pkt_mem_we_w),
      .wr_addr (pkt_mem_addr_w),
      .wr_data (pkt_mem_wdata_w),
      .rd_en   (m3_stub.rd_en),
      .rd_addr (m3_stub.rd_addr),
      .rd_data (m3_stub.rd_data)
  );

  // ---- M2 packet_proc_core 单元级 TB（独立通路 + 行为 SRAM 模型）----
  // 与上面 M1（apb_slave_if + packet_sram）通路并存但互不相连：core 直接由
  // ppa_core_if 驱动 start/algo_mode/type_mask/exp_pkt_len，并通过接口内建的行为
  // SRAM（组合读，r6）响应 mem_rd_en_o/mem_rd_addr_o。M2-01~M2-07 场景专用。
  ppa_core_if u_core_if (.clk(pclk), .rst_n(presetn));

  packet_proc_core u_packet_proc_core (
      .clk               (u_core_if.clk),
      .rst_n             (u_core_if.rst_n),
      .start_i           (u_core_if.start_i),
      .algo_mode_i       (u_core_if.algo_mode_i),
      .type_mask_i       (u_core_if.type_mask_i),
      .exp_pkt_len_i     (u_core_if.exp_pkt_len_i),
      .mem_rd_en_o       (u_core_if.mem_rd_en_o),
      .mem_rd_addr_o     (u_core_if.mem_rd_addr_o),
      .mem_rd_data_i     (u_core_if.mem_rd_data_i),
      .busy_o            (u_core_if.busy_o),
      .done_o            (u_core_if.done_o),
      .res_pkt_len_o     (u_core_if.res_pkt_len_o),
      .res_pkt_type_o    (u_core_if.res_pkt_type_o),
      .res_payload_sum_o (u_core_if.res_payload_sum_o),
      .res_payload_xor_o (u_core_if.res_payload_xor_o),
      .format_ok_o       (u_core_if.format_ok_o),
      .length_error_o    (u_core_if.length_error_o),
      .type_error_o      (u_core_if.type_error_o),
      .chk_error_o       (u_core_if.chk_error_o)
  );
`else
  // 从机占位：无 DUT 时保证 driver 握手可完成（PREADY 恒 1，读返回 0）
  assign apb.prdata  = '0;
  assign apb.pready  = 1'b1;
  assign apb.pslverr = 1'b0;
`endif

`ifdef DUMP_FSDB
  initial begin
    $fsdbDumpfile("out/wave.fsdb");
    $fsdbDumpvars(0, tb_top);
  end
`endif

  initial begin
    uvm_config_db#(virtual apb_if)::set(null, "*", "apb_vif", apb);
`ifdef HAS_DUT
    uvm_config_db#(virtual m3_stub_if)::set(null, "*", "m3_stub_vif", m3_stub);
    uvm_config_db#(virtual ppa_core_if)::set(null, "*", "ppa_core_vif", u_core_if);
`endif
    run_test();
  end

endmodule
