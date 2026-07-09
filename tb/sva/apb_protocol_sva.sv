// APB 3.0 通用两段式协议契约（spec §4.1）：SETUP→ACCESS 时序、PREADY 恒 1、
// 地址/数据在 SETUP→ACCESS 期间保持稳定。bind 到 tb/apb_if.sv（总线级信号，
// 与具体从机实现无关），只引用接口端口信号，不引用任何 RTL 内部信号。
// 归属：DV（tb/sva/README.md 约定）。
module apb_protocol_sva (
    input logic        pclk,
    input logic        presetn,
    input logic        psel,
    input logic        penable,
    input logic        pwrite,
    input logic [11:0] paddr,
    input logic [31:0] pwdata,
    input logic         pready
);

  // disable iff 要求引用单一信号而非复合表达式（避免 Lint-[SVA-CE]，同 rtl/ 侧约定）
  logic rst;
  assign rst = !presetn;

  // §4.1："PREADY 固定为 1，不引入等待状态"
  a_pready_always1: assert property (@(posedge pclk) disable iff (rst)
    pready == 1'b1)
    else $error("apb_if: PREADY 非恒 1（§4.1）");

  // §4.1：ACCESS（PSEL=1,PENABLE=1）阶段必须由同一事务的 SETUP（PSEL=1,PENABLE=0）
  // 阶段紧邻先行
  a_access_preceded_by_setup: assert property (@(posedge pclk) disable iff (rst)
    (psel && penable) |-> ($past(psel) && !$past(penable)))
    else $error("apb_if: ACCESS 阶段之前未见 SETUP 阶段（§4.1 两段式）");

  // §4.1：PREADY 恒 1、无等待态——SETUP 阶段下一拍必须进入 ACCESS
  a_setup_then_access: assert property (@(posedge pclk) disable iff (rst)
    (psel && !penable) |=> (psel && penable))
    else $error("apb_if: SETUP 阶段后未在下一拍进入 ACCESS（§4.1）");

  // §4.1："在 ACCESS 阶段上升沿采样地址/数据"——地址/写数据/方向须在
  // SETUP→ACCESS 期间保持稳定，不得在两阶段间变化
  a_addr_stable_setup_to_access: assert property (@(posedge pclk) disable iff (rst)
    (psel && !penable) |=> (paddr == $past(paddr) && pwrite == $past(pwrite) &&
                             (!$past(pwrite) || pwdata == $past(pwdata))))
    else $error("apb_if: SETUP→ACCESS 期间地址/数据发生变化（§4.1）");

endmodule

// VCS 不支持将普通 module 直接 bind 进 interface 实例（Illegal instantiation of
// module in interface），故改为 bind 到例化了 apb 接口的 tb_top，端口经层次引用
// 接到 apb 接口实例的信号（apb.psel 等）——仍是总线级信号，非 RTL 内部信号。
bind tb_top apb_protocol_sva u_apb_protocol_sva (
    .pclk    (pclk),
    .presetn (presetn),
    .psel    (apb.psel),
    .penable (apb.penable),
    .pwrite  (apb.pwrite),
    .paddr   (apb.paddr),
    .pwdata  (apb.pwdata),
    .pready  (apb.pready)
);
