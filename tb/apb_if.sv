// APB 3.0 接口（spec §2.3/§4.1：PADDR 12bit，PREADY 由从机输出、本设计固定 1）
interface apb_if #(
  parameter int ADDR_W = 12,
  parameter int DATA_W = 32
) (
  input logic pclk,
  input logic presetn
);

  // 主机方向信号给出空闲初值：M2 单元级 TB 不实例化 APB agent 时，本接口所连的
  // apb_slave_if/packet_sram 输入不再悬空为 X（否则触发其 X 检查断言）；M1 场景由
  // apb_driver 正常驱动、初值被覆盖，无影响。
  logic              psel    = 1'b0;
  logic              penable = 1'b0;
  logic              pwrite  = 1'b0;
  logic [ADDR_W-1:0] paddr   = '0;
  logic [DATA_W-1:0] pwdata  = '0;
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
