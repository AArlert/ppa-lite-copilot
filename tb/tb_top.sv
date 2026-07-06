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
  // M1 接入 apb_slave_if/ppa_top 时：定义 +define+HAS_DUT、在 flist/rtl.f 启用 RTL、
  // 删除下方从机占位并例化 DUT。
`ifndef HAS_DUT
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
    run_test();
  end

endmodule
