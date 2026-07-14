// M3 集成场景序列库：testplan M3-01~M3-05 对应序列（沿用 apb_seq_lib.sv/m1_seq_lib.sv
// 多序列共文件的既有约定）。期望值全部从 doc/spec.md 推导，章节号随每条检查标注；
// 地址常量取自 tb/uvm/env/ppa_reg_defs.sv（唯一定义点）。经 ppa_top 的 APB 端口驱动，
// 端到端观测（写包→配置→start→轮询 done→读 RES_*）。
//
// 包字节序（附录A/§3.1/§6.1）：一个 32-bit word 大端排布——Word0 = {Byte0,Byte1,
//   Byte2,Byte3} = {pkt_len,pkt_type,flags,hdr_chk} 落在 [31:24][23:16][15:8][7:0]
//   （附录A 示例 32'h08_01_00_09：pkt_len=8@[31:24]、hdr_chk=0x09@[7:0]，BUG-009 端序裁决）。
// hdr_chk = Byte0 ^ Byte1 ^ Byte2（§3.1 §9.1）。

// ---------------------------------------------------------------------------
// M3 序列基类：封装写包/配置/start/轮询 done/比对等公共任务
// ---------------------------------------------------------------------------
class m3_base_seq extends apb_base_seq;

  `uvm_object_utils(m3_base_seq)

  virtual ppa_top_if top_vif; // 需观测 irq_o 的场景（M3-05）由 test 赋值

  function new(string name = "m3_base_seq");
    super.new(name);
  endfunction

  // 组头部 word（大端，附录A）
  function bit [31:0] hdr_word(bit [7:0] pkt_len, bit [7:0] pkt_type,
                                bit [7:0] flags, bit [7:0] hdr_chk);
    return {pkt_len, pkt_type, flags, hdr_chk};
  endfunction

  // hdr_chk = Byte0 ^ Byte1 ^ Byte2（§3.1 §9.1）
  function bit [7:0] calc_chk(bit [7:0] pkt_len, bit [7:0] pkt_type, bit [7:0] flags);
    return pkt_len ^ pkt_type ^ flags;
  endfunction

  // 写头部到 Word0（0x040，§6.1）
  task wr_header(bit [7:0] pkt_len, bit [7:0] pkt_type, bit [7:0] flags, bit [7:0] hdr_chk);
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE, hdr_word(pkt_len, pkt_type, flags, hdr_chk));
  endtask

  // 写第 idx 个 word（0x040+4*idx，§6.1）
  task wr_word(int idx, bit [31:0] data);
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE + 12'(4 * idx), data);
  endtask

  // 使能并触发处理（附录A 步骤4/5：先写 enable=1，再写 start=1，W1P）
  task do_start();
    apb_write(ppa_reg_defs_pkg::ADDR_CTRL, 32'h0000_0001); // enable=1（§5.2）
    apb_write(ppa_reg_defs_pkg::ADDR_CTRL, 32'h0000_0003); // start（W1P，§5.1 §5.2）
  endtask

  // 轮询 STATUS 直到 done（[1]=1）；guard 防 FSM 卡死（§7.2），超限报错而非挂死
  task poll_done(output bit [31:0] status, input string tag);
    bit slverr;
    int guard = 0;
    forever begin
      apb_read(ppa_reg_defs_pkg::ADDR_STATUS, status, slverr);
      if (slverr)
        `uvm_error(tag, "读 STATUS 报 PSLVERR，期望合法只读（§5.2 RO §8.3）")
      if (status[1] === 1'b1) break;       // done=1（§5.2 STATUS[1]）
      guard++;
      if (guard > 200) begin
        `uvm_error(tag, "轮询 done 超时（>200 次）：疑似 FSM 未进 DONE / 卡死（§7.2）")
        break;
      end
    end
  endtask

  // 读寄存器并比对
  task chk_eq(bit [11:0] addr, bit [31:0] exp, string field, string tag, string sref);
    bit [31:0] got;
    bit        slverr;
    apb_read(addr, got, slverr);
    if (slverr)
      `uvm_error(tag, $sformatf("读 %s(0x%03h) 报 PSLVERR，期望合法只读（§8.3）", field, addr))
    else if (got !== exp)
      `uvm_error(tag, $sformatf("%s(0x%03h) 读回=0x%08h 期望=0x%08h（%s）", field, addr, got, exp, sref))
    else
      `uvm_info(tag, $sformatf("PASS: %s=0x%08h 与期望一致（%s）", field, exp, sref), UVM_LOW)
  endtask

endclass

// ---------------------------------------------------------------------------
// M3-01：端到端链路（§11.4-必1；激励取 §10.1 N-2）
// 写合法 8B 包 → 配置 → start → 轮询 done → 读 RES_*/ERR_FLAG 与写入/规格一致
// ---------------------------------------------------------------------------
class m3_e2e_seq extends m3_base_seq;

  `uvm_object_utils(m3_e2e_seq)

  function new(string name = "m3_e2e_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] status;
    bit [7:0]  len, typ, flags, chk;

    // N-2：pkt_len=8, pkt_type=0x02, flags=0；payload=0x01020304
    // → sum=0x01+0x02+0x03+0x04=0x0A；xor=0x01^0x02^0x03^0x04=0x04（§3.4 §10.1 N-2）
    len = 8'd8; typ = 8'h02; flags = 8'h00;
    chk = calc_chk(len, typ, flags); // 0x08^0x02^0x00 = 0x0A

    wr_header(len, typ, flags, chk);          // Word0（§6.1）
    wr_word(1, 32'h0102_0304);                // Word1 payload（Byte4-7）
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP, 32'h0000_0008); // exp=8 一致性检查（§5.2 附录A）
    do_start();
    poll_done(status, "M3-01");

    if (status[1] !== 1'b1)
      `uvm_error("M3-01", "轮询结束 STATUS.done 未置位（§5.2 §11.4-必1）")
    // format_ok（STATUS[3]）：长度/类型/头校验均通过（§5.2 §9）
    if (status[3] !== 1'b1)
      `uvm_error("M3-01", $sformatf("STATUS.format_ok 未置位（STATUS=0x%08h，§5.2 §9）", status))
    else
      `uvm_info("M3-01", "PASS: done=1 且 format_ok=1", UVM_LOW)

    // 结果寄存器与写入/规格一致（§3.4 §5.2 §11.4-必1）
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PKT_LEN,     32'h0000_0008, "RES_PKT_LEN",     "M3-01", "§3.4 =Byte0[5:0]=8");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PKT_TYPE,    32'h0000_0002, "RES_PKT_TYPE",    "M3-01", "§3.4 =Byte1=0x02");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_SUM, 32'h0000_000A, "RES_PAYLOAD_SUM", "M3-01", "§3.4 payload 累加=0x0A");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_XOR, 32'h0000_0004, "RES_PAYLOAD_XOR", "M3-01", "§3.4 payload XOR=0x04");
    chk_eq(ppa_reg_defs_pkg::ADDR_ERR_FLAG,        32'h0000_0000, "ERR_FLAG",        "M3-01", "§9.1 合法包无错误");
  endtask

endclass

// ---------------------------------------------------------------------------
// M3-02：连续两帧（§10.1 N-4 §11.4-必2）
// 两帧结果独立正确；帧间 done 有清零过程（§5.2 STATUS.done 下次合法 start 接受时清 0，§7.2）
// 帧2 用 32B 长包，使 busy 窗口够宽，start 后首次 STATUS 读能确定落在 done 已清零窗口
// ---------------------------------------------------------------------------
class m3_two_frame_seq extends m3_base_seq;

  `uvm_object_utils(m3_two_frame_seq)

  function new(string name = "m3_two_frame_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] status, st_after_start;
    bit        slverr;

    // ---- 帧1：8B 包（同 N-2）----
    wr_header(8'd8, 8'h02, 8'h00, calc_chk(8'd8, 8'h02, 8'h00)); // chk=0x0A
    wr_word(1, 32'h0102_0304);
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP, 32'h0000_0008);
    do_start();
    poll_done(status, "M3-02");
    if (status[1] !== 1'b1)
      `uvm_error("M3-02", "帧1 done 未置位（§11.4-必2）")
    else
      `uvm_info("M3-02", "PASS: 帧1 完成 done=1", UVM_LOW)
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PKT_LEN,     32'h0000_0008, "帧1 RES_PKT_LEN",     "M3-02", "§3.4=8");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PKT_TYPE,    32'h0000_0002, "帧1 RES_PKT_TYPE",    "M3-02", "§3.4=0x02");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_SUM, 32'h0000_000A, "帧1 RES_PAYLOAD_SUM", "M3-02", "§3.4=0x0A");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_XOR, 32'h0000_0004, "帧1 RES_PAYLOAD_XOR", "M3-02", "§3.4=0x04");

    // ---- 帧2：32B 长包，pkt_type=0x04 ----
    // payload = Byte4..Byte31 = 0x01..0x1C（十进制 1..28），7 个 word：
    //   sum = Σ(1..28)=406 → 8-bit 截断 0x96；xor = XOR(1..28)=28=0x1C（§3.4）
    wr_header(8'd32, 8'h04, 8'h00, calc_chk(8'd32, 8'h04, 8'h00)); // chk=0x20^0x04=0x24
    wr_word(1, 32'h0102_0304);
    wr_word(2, 32'h0506_0708);
    wr_word(3, 32'h090A_0B0C);
    wr_word(4, 32'h0D0E_0F10);
    wr_word(5, 32'h1112_1314);
    wr_word(6, 32'h1516_1718);
    wr_word(7, 32'h191A_1B1C);
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP, 32'h0000_0020); // exp=32
    do_start();

    // 帧间 done 清零观测：start 被接受后 done 应先清 0（§5.2 §7.2），随后新帧再置 1
    apb_read(ppa_reg_defs_pkg::ADDR_STATUS, st_after_start, slverr);
    if (st_after_start[1] !== 1'b0)
      `uvm_error("M3-02", $sformatf("帧2 start 接受后 done 未清零（STATUS=0x%08h，§5.2 §7.2 §11.4-必2）", st_after_start))
    else
      `uvm_info("M3-02", "PASS: 帧间 done 有清零过程（start 后 done=0）", UVM_LOW)

    poll_done(status, "M3-02");
    if (status[1] !== 1'b1)
      `uvm_error("M3-02", "帧2 done 未置位（§11.4-必2）")
    // 帧2 结果独立正确（不受帧1 影响，§7.2 IDLE/DONE→PROCESS 清除上一帧结果）
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PKT_LEN,     32'h0000_0020, "帧2 RES_PKT_LEN",     "M3-02", "§3.4=32");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PKT_TYPE,    32'h0000_0004, "帧2 RES_PKT_TYPE",    "M3-02", "§3.4=0x04");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_SUM, 32'h0000_0096, "帧2 RES_PAYLOAD_SUM", "M3-02", "§3.4 Σ(1..28)&0xFF=0x96");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_XOR, 32'h0000_001C, "帧2 RES_PAYLOAD_XOR", "M3-02", "§3.4 XOR(1..28)=0x1C");
    chk_eq(ppa_reg_defs_pkg::ADDR_ERR_FLAG,        32'h0000_0000, "帧2 ERR_FLAG",        "M3-02", "§9.1 合法包无错误");
  endtask

endclass

// ---------------------------------------------------------------------------
// M3-03：STATUS 总线通路（§11.4-必3）
// busy 期间 STATUS[1:0]=2'b01；done 期间 STATUS[1:0]=2'b10；二者互斥（§5.2 §7.4）
// 用 32B 长包拉宽 busy 窗口，紧密轮询捕获 busy 样本
// ---------------------------------------------------------------------------
class m3_status_bus_seq extends m3_base_seq;

  `uvm_object_utils(m3_status_bus_seq)

  function new(string name = "m3_status_bus_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] st;
    bit        slverr;
    bit        saw_busy = 1'b0;
    int        guard = 0;

    // 32B 长包（同 M3-02 帧2）
    wr_header(8'd32, 8'h04, 8'h00, calc_chk(8'd32, 8'h04, 8'h00));
    wr_word(1, 32'h0102_0304); wr_word(2, 32'h0506_0708);
    wr_word(3, 32'h090A_0B0C); wr_word(4, 32'h0D0E_0F10);
    wr_word(5, 32'h1112_1314); wr_word(6, 32'h1516_1718);
    wr_word(7, 32'h191A_1B1C);
    do_start();

    // 紧密轮询 STATUS，逐样本核对 busy/done 位映射与互斥（§5.2 §7.4 §11.4-必3）
    forever begin
      apb_read(ppa_reg_defs_pkg::ADDR_STATUS, st, slverr);
      if (slverr)
        `uvm_error("M3-03", "读 STATUS 报 PSLVERR（§5.2 RO）")
      // 互斥：busy 与 done 不得同时为 1（§7.4 IDLE/PROCESS/DONE 三态输出互斥）
      if (st[0] === 1'b1 && st[1] === 1'b1)
        `uvm_error("M3-03", $sformatf("STATUS[1:0]=2'b11 非法：busy 与 done 同置（STATUS=0x%08h，§7.4）", st))
      if (st[1:0] === 2'b01) saw_busy = 1'b1; // busy 期间 = 01（§11.4-必3）
      if (st[1] === 1'b1) break;              // 进入 done
      guard++;
      if (guard > 200) begin
        `uvm_error("M3-03", "轮询 done 超时（§7.2 疑似卡死）")
        break;
      end
    end

    if (!saw_busy)
      `uvm_error("M3-03", "未捕获到 busy 期间 STATUS[1:0]=2'b01（§11.4-必3；如 busy 窗口过窄需加长包）")
    else
      `uvm_info("M3-03", "PASS: busy 期间观测到 STATUS[1:0]=2'b01", UVM_LOW)

    // done 期间 STATUS[1:0]=2'b10（§11.4-必3）
    if (st[1:0] !== 2'b10)
      `uvm_error("M3-03", $sformatf("done 期间 STATUS[1:0]=2'b%02b 期望 2'b10（§11.4-必3）", st[1:0]))
    else
      `uvm_info("M3-03", "PASS: done 期间 STATUS[1:0]=2'b10", UVM_LOW)
  endtask

endclass

// ---------------------------------------------------------------------------
// M3-04：busy 写保护（§6.3 §10.3 B-2 §11.4-选4）
// busy=1 期间写 PKT_MEM → PSLVERR=1；SRAM 内容不变（后者由绑定到 ppa_top.u_apb 的
// apb_slave_if_sva::a_pktmem_busy_protect 被动核实 we 被抑制）
// 用 32B 长包拉宽 busy 窗口，start 后立即发起非法写
// ---------------------------------------------------------------------------
class m3_busy_wprotect_seq extends m3_base_seq;

  `uvm_object_utils(m3_busy_wprotect_seq)

  function new(string name = "m3_busy_wprotect_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] status;
    bit        slverr;

    // 32B 长包
    wr_header(8'd32, 8'h04, 8'h00, calc_chk(8'd32, 8'h04, 8'h00));
    wr_word(1, 32'h0102_0304); wr_word(2, 32'h0506_0708);
    wr_word(3, 32'h090A_0B0C); wr_word(4, 32'h0D0E_0F10);
    wr_word(5, 32'h1112_1314); wr_word(6, 32'h1516_1718);
    wr_word(7, 32'h191A_1B1C);
    do_start();

    // busy=1 期间写 PKT_MEM（附录B.4）：应 PSLVERR=1（§6.3 表行2 §8.3）
    apb_write_chk(ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE + 12'h04, 32'hDEAD_BEEF, slverr);
    if (slverr !== 1'b1)
      `uvm_error("M3-04", "busy=1 期间写 PKT_MEM 未报 PSLVERR（§6.3 §10.3 B-2）；如 busy 窗口过窄需加长包")
    else
      `uvm_info("M3-04", "PASS: busy=1 期间写 PKT_MEM 报 PSLVERR=1（SRAM 不变由绑定 SVA a_pktmem_busy_protect 核实）", UVM_LOW)

    poll_done(status, "M3-04"); // 收尾等处理完成
    if (status[1] !== 1'b1)
      `uvm_error("M3-04", "处理未完成 done 未置位（§7.2）")
  endtask

endclass

// ---------------------------------------------------------------------------
// M3-05：中断路径闭环（§8.2 §10.3 B-3 §11.4-选5）
// done_irq_en=1 → done 上升沿置 IRQ_STA.done_irq、irq_o=1 → 写1清 → irq_o=0
// ---------------------------------------------------------------------------
class m3_irq_seq extends m3_base_seq;

  `uvm_object_utils(m3_irq_seq)

  function new(string name = "m3_irq_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] status, rdata;
    bit        slverr;

    if (top_vif == null)
      `uvm_fatal("M3-05", "top_vif 未设置，无法观测 irq_o")

    // 使能完成中断（§5.2 §8.2）——须在 start 前配置好
    apb_write(ppa_reg_defs_pkg::ADDR_IRQ_EN, 32'h0000_0001); // done_irq_en=1

    // 合法 8B 包（中断仅依赖 done 上升沿，包内容取合法即可）
    wr_header(8'd8, 8'h02, 8'h00, calc_chk(8'd8, 8'h02, 8'h00));
    wr_word(1, 32'h0102_0304);
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP, 32'h0000_0008);
    do_start();
    poll_done(status, "M3-05");

    // done 上升沿 → IRQ_STA.done_irq=1（§8.2）
    apb_read(ppa_reg_defs_pkg::ADDR_IRQ_STA, rdata, slverr);
    if (slverr || rdata[0] !== 1'b1)
      `uvm_error("M3-05", $sformatf("done 后 IRQ_STA.done_irq 未置位（读回=0x%08h，§8.2）", rdata))
    else
      `uvm_info("M3-05", "PASS: done 中断置位 IRQ_STA.done_irq", UVM_LOW)

    // irq_o=1（§8.2 irq_o=done_irq|err_irq，组合输出）
    @(top_vif.mon_cb);
    if (top_vif.mon_cb.irq_o !== 1'b1)
      `uvm_error("M3-05", "done 中断后 irq_o 未拉高（§8.2 组合输出）")
    else
      `uvm_info("M3-05", "PASS: irq_o=1", UVM_LOW)

    // 软件写1清除 IRQ_STA.done_irq（§8.2 RW1C）
    apb_write(ppa_reg_defs_pkg::ADDR_IRQ_STA, 32'h0000_0001);
    apb_read(ppa_reg_defs_pkg::ADDR_IRQ_STA, rdata, slverr);
    if (rdata[0] !== 1'b0)
      `uvm_error("M3-05", $sformatf("写1清除后 IRQ_STA.done_irq 未清零（读回=0x%08h，§8.2）", rdata))
    else
      `uvm_info("M3-05", "PASS: 写1清除 IRQ_STA.done_irq", UVM_LOW)

    // irq_o 随即拉低（§8.2）
    @(top_vif.mon_cb);
    if (top_vif.mon_cb.irq_o !== 1'b0)
      `uvm_error("M3-05", "写1清除后 irq_o 未拉低（§8.2）")
    else
      `uvm_info("M3-05", "PASS: irq_o=0（中断路径闭环）", UVM_LOW)
  endtask

endclass
