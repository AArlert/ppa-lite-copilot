// packet_proc_core 接口/协议/时序契约断言：只引用模块端口信号（§2.3 M3 端口表），
// 禁止引用 RTL 内部信号（内部不变量归 DE，见 rtl/packet_proc_core.sv）。
// bind 到 rtl/packet_proc_core.sv 模块实例。归属：DV（tb/sva/README.md 约定）。
// 每条 property 均从 spec 章节推导，注明依据。
module packet_proc_core_sva (
    input logic        clk,
    input logic        rst_n,
    input logic        start_i,
    input logic        busy_o,
    input logic        done_o,
    input logic        mem_rd_en_o,
    input logic        format_ok_o,
    input logic        length_error_o,
    input logic        type_error_o,
    input logic        chk_error_o
);

  // disable iff 要求单一信号（避免 Lint-[SVA-CE]，同 apb_slave_if_sva 约定）
  logic rst;
  assign rst = !rst_n;

  // §7.2/§7.4/§10.3(M2-03)：start 被接受（非 busy 态，即 IDLE/DONE）后 1 拍 busy=1。
  // busy 期间（PROCESS）start 被忽略（§7.2 无 PROCESS→ 转移），故以 !busy_o 为守卫。
  a_busy_after_start: assert property (@(posedge clk) disable iff (rst)
    (start_i && !busy_o) |=> busy_o)
    else $error("packet_proc_core: start 被接受后 1 拍 busy 未置 1（§7.2/§7.4）");

  // §7.4：busy 与 done 互斥（PROCESS busy=1/done=0，DONE busy=0/done=1，IDLE 均 0）
  a_busy_done_excl: assert property (@(posedge clk) disable iff (rst)
    !(busy_o && done_o))
    else $error("packet_proc_core: busy_o 与 done_o 同时为 1（§7.4）");

  // §7.4：mem_rd_en_o 仅在 PROCESS（busy=1）态有效；IDLE/DONE 态不得读
  a_rden_only_in_process: assert property (@(posedge clk) disable iff (rst)
    mem_rd_en_o |-> busy_o)
    else $error("packet_proc_core: 非 PROCESS 态出现 mem_rd_en_o（§7.4）");

  // §7.3(r8)：读拍数钳位 [1,8]——busy 不得持续超过 8 拍（禁止越窗口/卡死，M2-02）。
  // busy 上升后须在 1..8 拍内落下（含 pkt_len 越界须钳到 8 拍以内的场景）。
  a_process_len_clamp: assert property (@(posedge clk) disable iff (rst)
    $rose(busy_o) |-> ##[1:8] !busy_o)
    else $error("packet_proc_core: PROCESS 持续超过 8 拍，未按 §7.3(r8) 钳位");

  // §7.2/§10.3(M2-03)：DONE 态 done 保持——done=1 且当拍无 start 时，下一拍仍 done=1
  a_done_hold: assert property (@(posedge clk) disable iff (rst)
    (done_o && !start_i) |=> done_o)
    else $error("packet_proc_core: DONE 态 done_o 未按 §7.2 保持");

  // §7.2/§10.3(M2-03)：再次 start 清零——done=1 时 start 被接受，下一拍进 PROCESS
  // （busy=1 且 done=0）
  a_restart_clears: assert property (@(posedge clk) disable iff (rst)
    (done_o && start_i) |=> (busy_o && !done_o))
    else $error("packet_proc_core: DONE 态再次 start 未清零/未进 PROCESS（§7.2）");

  // §5.2：format_ok = 三类错误均无（判定结果于 DONE 拍有效，故以 done_o 守卫）
  a_format_ok_def: assert property (@(posedge clk) disable iff (rst)
    done_o |-> (format_ok_o == !(length_error_o || type_error_o || chk_error_o)))
    else $error("packet_proc_core: format_ok 与错误标志不自洽（§5.2）");

endmodule

bind packet_proc_core packet_proc_core_sva u_packet_proc_core_sva (
    .clk            (clk),
    .rst_n          (rst_n),
    .start_i        (start_i),
    .busy_o         (busy_o),
    .done_o         (done_o),
    .mem_rd_en_o    (mem_rd_en_o),
    .format_ok_o    (format_ok_o),
    .length_error_o (length_error_o),
    .type_error_o   (type_error_o),
    .chk_error_o    (chk_error_o)
);
