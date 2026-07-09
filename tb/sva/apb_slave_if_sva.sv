// apb_slave_if 接口级契约：只引用模块端口信号（§2.3 M1 端口表），禁止引用 RTL
// 内部信号（RTL 内部不变量断言归 DE，见 rtl/apb_slave_if.sv）。bind 到
// rtl/apb_slave_if.sv 模块实例。归属：DV（tb/sva/README.md 约定）。
module apb_slave_if_sva
  import ppa_reg_defs_pkg::*;
(
    input logic        PCLK,
    input logic        PRESETn,
    input logic        PSEL,
    input logic        PENABLE,
    input logic        PWRITE,
    input logic [11:0] PADDR,
    input logic [31:0] PWDATA,
    input logic [31:0] PRDATA,
    input logic         PSLVERR,
    input logic         busy_i,
    input logic         done_i,
    input logic         length_error_i,
    input logic         type_error_i,
    input logic         chk_error_i,
    input logic         done_irq_en_o,
    input logic         err_irq_en_o,
    input logic         pkt_mem_we_o,
    input logic [2:0]   pkt_mem_addr_o,
    input logic [31:0]  pkt_mem_wdata_o,
    input logic         irq_o
);

  // disable iff 要求引用单一信号而非复合表达式（避免 Lint-[SVA-CE]，同 rtl/ 侧约定）
  logic rst;
  assign rst = !PRESETn;

  logic access, write_access, read_access;
  assign access       = PSEL && PENABLE;
  assign write_access = access && PWRITE;
  assign read_access  = access && !PWRITE;

  // 地址区间判定仅依据 spec §4.2/§6.1 地址映射公式与 ppa_reg_defs_pkg 常量，
  // 不引用 RTL 内部译码信号（属重新推导，非照抄实现）
  logic pkt_mem_range, csr_range;
  assign csr_range     = (PADDR <= 12'h02B);
  assign pkt_mem_range = (PADDR >= ADDR_PKT_MEM_BASE) && (PADDR <= ADDR_PKT_MEM_END);

  // §6.1 地址公式：APB 地址 0x040+4N 对应 Word N（用位选取代右移，避免位宽截断告警）
  logic [11:0] pkt_mem_offset;
  logic [2:0]  pkt_mem_word;
  assign pkt_mem_offset = PADDR - ADDR_PKT_MEM_BASE;
  assign pkt_mem_word   = pkt_mem_offset[4:2];

  // §6.1 §6.2：合法写（busy=0）落在 PKT_MEM 窗口 → we/addr/data 映射正确
  a_pktmem_write_map: assert property (@(posedge PCLK) disable iff (rst)
    (write_access && pkt_mem_range && !busy_i) |->
      (pkt_mem_we_o && pkt_mem_addr_o == pkt_mem_word && pkt_mem_wdata_o == PWDATA))
    else $error("apb_slave_if: PKT_MEM 写地址映射不符（§6.1 §6.2）");

  // §6.3 §8.3：busy=1 期间写 PKT_MEM 必须报 PSLVERR=1 且不得产生 we
  a_pktmem_busy_protect: assert property (@(posedge PCLK) disable iff (rst)
    (write_access && pkt_mem_range && busy_i) |-> (PSLVERR && !pkt_mem_we_o))
    else $error("apb_slave_if: busy=1 期间写 PKT_MEM 未按 §6.3 报 PSLVERR/禁写");

  // §6.3(r7)：APB 读 PKT_MEM 任意时刻 PSLVERR=0 且 PRDATA=占位值 32'h0
  // （已认可的对外行为：本仓库架构下 M1 无 SRAM 读回通路，非缺陷）
  a_pktmem_read_placeholder: assert property (@(posedge PCLK) disable iff (rst)
    (read_access && pkt_mem_range) |-> (!PSLVERR && PRDATA == 32'h0))
    else $error("apb_slave_if: APB 读 PKT_MEM 未按 §6.3(r7) 返回占位值");

  // §4.2 §8.3：访问保留/未定义地址（既非 CSR 区也非 PKT_MEM 区）恒 PSLVERR=1
  a_reserved_addr_slverr: assert property (@(posedge PCLK) disable iff (rst)
    (access && !csr_range && !pkt_mem_range) |-> PSLVERR)
    else $error("apb_slave_if: 访问保留/未定义地址未报 PSLVERR（§4.2 §8.3）");

  // §8.2：done_i 上升沿且 done_irq_en=1 → 同拍 irq_o 置 1（组合输出，无延迟）
  a_irq_done_same_cycle: assert property (@(posedge PCLK) disable iff (rst)
    ($rose(done_i) && done_irq_en_o) |-> irq_o)
    else $error("apb_slave_if: done 中断未同拍置位 irq_o（§8.2）");

  // §8.2 §9.1：done_i 上升沿且存在错误且 err_irq_en=1 → 同拍 irq_o 置 1
  a_irq_err_same_cycle: assert property (@(posedge PCLK) disable iff (rst)
    ($rose(done_i) && err_irq_en_o && (length_error_i || type_error_i || chk_error_i)) |-> irq_o)
    else $error("apb_slave_if: err 中断未同拍置位 irq_o（§8.2 §9.1）");

endmodule

bind apb_slave_if apb_slave_if_sva u_apb_slave_if_sva (
    .PCLK            (PCLK),
    .PRESETn         (PRESETn),
    .PSEL            (PSEL),
    .PENABLE         (PENABLE),
    .PWRITE          (PWRITE),
    .PADDR           (PADDR),
    .PWDATA          (PWDATA),
    .PRDATA          (PRDATA),
    .PSLVERR         (PSLVERR),
    .busy_i          (busy_i),
    .done_i          (done_i),
    .length_error_i  (length_error_i),
    .type_error_i    (type_error_i),
    .chk_error_i     (chk_error_i),
    .done_irq_en_o   (done_irq_en_o),
    .err_irq_en_o    (err_irq_en_o),
    .pkt_mem_we_o    (pkt_mem_we_o),
    .pkt_mem_addr_o  (pkt_mem_addr_o),
    .pkt_mem_wdata_o (pkt_mem_wdata_o),
    .irq_o           (irq_o)
);
