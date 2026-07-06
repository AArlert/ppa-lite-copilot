// 寄存器地址/常量唯一定义点（spec §4.2/§5.2/§6.1）——禁止在别处硬编码地址
package ppa_reg_defs_pkg;

  localparam int ADDR_W = 12;
  localparam int DATA_W = 32;

  // CSR 区（spec §5.2）
  localparam logic [ADDR_W-1:0] ADDR_CTRL            = 'h000;
  localparam logic [ADDR_W-1:0] ADDR_CFG             = 'h004;
  localparam logic [ADDR_W-1:0] ADDR_STATUS          = 'h008;
  localparam logic [ADDR_W-1:0] ADDR_IRQ_EN          = 'h00C;
  localparam logic [ADDR_W-1:0] ADDR_IRQ_STA         = 'h010;
  localparam logic [ADDR_W-1:0] ADDR_PKT_LEN_EXP     = 'h014;
  localparam logic [ADDR_W-1:0] ADDR_RES_PKT_LEN     = 'h018;
  localparam logic [ADDR_W-1:0] ADDR_RES_PKT_TYPE    = 'h01C;
  localparam logic [ADDR_W-1:0] ADDR_RES_PAYLOAD_SUM = 'h020;
  localparam logic [ADDR_W-1:0] ADDR_RES_PAYLOAD_XOR = 'h024;
  localparam logic [ADDR_W-1:0] ADDR_ERR_FLAG        = 'h028;

  // PKT_MEM 窗口（spec §6.1）：0x040 + 4×N，N=0..7
  localparam logic [ADDR_W-1:0] ADDR_PKT_MEM_BASE    = 'h040;
  localparam logic [ADDR_W-1:0] ADDR_PKT_MEM_END     = 'h05C;
  localparam int                PKT_MEM_WORDS        = 8;

  // 包格式常量（spec §3）
  localparam int PKT_LEN_MIN = 4;
  localparam int PKT_LEN_MAX = 32;

endpackage
