// APB 3.0 接口（spec §2.3/§4.1：PADDR 12bit，PREADY 由从机输出、本设计固定 1）
interface apb_if #(
  parameter int ADDR_W = 12,
  parameter int DATA_W = 32
) (
  input logic pclk,
  input logic presetn
);

  logic              psel;
  logic              penable;
  logic              pwrite;
  logic [ADDR_W-1:0] paddr;
  logic [DATA_W-1:0] pwdata;
  logic [DATA_W-1:0] prdata;
  logic              pready;
  logic              pslverr;

  // driver 时钟块：主机方向输出，从机方向输入
  clocking drv_cb @(posedge pclk);
    output psel, penable, pwrite, paddr, pwdata;
    input  prdata, pready, pslverr;
  endclocking

  // monitor 时钟块：全部采样
  clocking mon_cb @(posedge pclk);
    input psel, penable, pwrite, paddr, pwdata, prdata, pready, pslverr;
  endclocking

endinterface
