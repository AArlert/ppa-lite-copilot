// M4 覆盖率闭环集成序列库（经 ppa_top APB 端到端）：期望值全部从 spec 推导并标注章节，
// 地址常量取自 ppa_reg_defs_pkg（唯一定义点）。复用 m3_base_seq 的 wr_header/wr_word/
// do_start/poll_done/chk_eq。字节序同 m3_seq_lib（附录A 大端，BUG-009）。

// ---------------------------------------------------------------------------
// M4-02b：ppa_top 集成随机帧回归（多 seed）——补集成域 TOGGLE/COND/ASSERT
// 随机配置（algo_mode/type_mask/IRQ_EN/exp）+ 随机包端到端，参考模型逐字段比对；
// 另定向覆盖集成域断言前因（RO 写 PSLVERR、PKT_MEM 读占位、保留地址 PSLVERR、
// algo_mode=0 旁路、err 中断）。
// ---------------------------------------------------------------------------
class m4_rand_integ_seq extends m3_base_seq;

  `uvm_object_utils(m4_rand_integ_seq)

  int unsigned n_pkt = 20;

  function new(string name = "m4_rand_integ_seq");
    super.new(name);
  endfunction

  // spec 参考模型（§3.4 §9.1；与 M2 predict 同源自 spec，不照抄 RTL）
  function void ref_calc(
      input  bit [7:0] len, typ, flags, chk, input bit algo,
      input  bit [3:0] mask, input bit [5:0] exp, input bit [7:0] payload [],
      output bit len_err, type_err, chk_err, fmt_ok, valid_len,
      output bit [7:0] sum, xorv);
    bit valid_type;
    int idx, nb;
    bit [7:0] s = 8'h00, x = 8'h00;
    // §9.1 length_error：越界或 exp≠0 且不符（r4，零扩展 exp 后比较完整 8-bit）
    len_err = (len < 8'd4) || (len > 8'd32);
    if (exp != 6'd0 && (len != {2'b00, exp})) len_err = 1'b1;
    // §9.1 type_error：非合法 one-hot 或被 mask 屏蔽
    valid_type = (typ == 8'h01) || (typ == 8'h02) || (typ == 8'h04) || (typ == 8'h08);
    idx = (typ == 8'h01) ? 0 : (typ == 8'h02) ? 1 : (typ == 8'h04) ? 2 : 3;
    type_err = (!valid_type) || (!mask[idx]);
    // §9.1 chk_error：仅 algo_mode=1 时判定；hdr_chk != Byte0^Byte1^Byte2
    chk_err = algo && (chk != (len ^ typ ^ flags));
    fmt_ok  = (!len_err) && (!type_err) && (!chk_err);
    // §3.4/§7.3：合法包长时逐字节 sum/xor（有效字节 = len-4）；非法 UNSPECIFIED（r5）
    valid_len = (len >= 8'd4) && (len <= 8'd32);
    nb = valid_len ? (len - 8'd4) : 0;
    for (int i = 0; i < nb; i++) begin
      bit [7:0] pv = (i < payload.size()) ? payload[i] : 8'h00;
      s += pv; x ^= pv;
    end
    sum = s; xorv = x;
  endfunction

  // 把 payload 字节数组按大端打进 Word1..7 并写入 PKT_MEM（§6.1 附录A）
  task write_payload(input bit [7:0] payload []);
    for (int w = 1; w <= 7; w++) begin
      bit [31:0] wd = 32'h0;
      for (int p = 0; p < 4; p++) begin
        int b = (w - 1) * 4 + p; // payload byte 索引
        bit [7:0] bv = (b < payload.size()) ? payload[b] : 8'h00;
        wd[31 - 8*p -: 8] = bv;
      end
      wr_word(w, wd);
    end
  endtask

  // 跑一帧：写配置 → 写包 → start → 轮询 done → 逐字段比对 + IRQ 校验
  task run_one(input bit [7:0] len, typ, flags, chk, input bit algo,
               input bit [3:0] mask, input bit [5:0] exp,
               input bit irq_done_en, irq_err_en, input bit [7:0] payload [],
               input string tag);
    bit [31:0] status, err_flag_exp, irq_sta;
    bit        slverr;
    bit        len_err, type_err, chk_err, fmt_ok, valid_len, any_err;
    bit [7:0]  sum, xorv;

    ref_calc(len, typ, flags, chk, algo, mask, exp, payload,
             len_err, type_err, chk_err, fmt_ok, valid_len, sum, xorv);
    any_err = len_err | type_err | chk_err;

    // 配置（§5.2）：CFG.algo_mode=[0]/type_mask=[7:4]；IRQ_EN=[1:0]；PKT_LEN_EXP=[5:0]
    apb_write(ppa_reg_defs_pkg::ADDR_CFG,         {24'b0, mask, 3'b0, algo});
    apb_write(ppa_reg_defs_pkg::ADDR_IRQ_EN,      {30'b0, irq_err_en, irq_done_en});
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP, {26'b0, exp});

    // 写包头 + payload（§6.1）
    wr_header(len, typ, flags, chk);
    write_payload(payload);

    do_start();
    poll_done(status, tag);
    if (status[1] !== 1'b1)
      `uvm_error(tag, $sformatf("done 未置位（STATUS=0x%08h，§7.2）", status))

    // STATUS[3]=format_ok, [2]=any_error（§5.2）
    if (status[3] !== fmt_ok)
      `uvm_error(tag, $sformatf("STATUS.format_ok=%0b 期望 %0b（§5.2 §9，STATUS=0x%08h）", status[3], fmt_ok, status))
    if (status[2] !== any_err)
      `uvm_error(tag, $sformatf("STATUS.any_error=%0b 期望 %0b（§5.2 §9，STATUS=0x%08h）", status[2], any_err, status))

    // 结果寄存器（§3.4）：res_pkt_len 恒=Byte0[5:0]（r9）；res_pkt_type=Byte1
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PKT_LEN,  {26'b0, len[5:0]}, "RES_PKT_LEN",  tag, "§3.4 r9");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PKT_TYPE, {24'b0, typ},      "RES_PKT_TYPE", tag, "§3.4");
    // ERR_FLAG=[2]chk [1]type [0]length（§5.2 §9.1）
    err_flag_exp = {29'b0, chk_err, type_err, len_err};
    chk_eq(ppa_reg_defs_pkg::ADDR_ERR_FLAG, err_flag_exp, "ERR_FLAG", tag, "§9.1");
    // 合法包长才比对 sum/xor（非法 UNSPECIFIED，§7.3 r5）
    if (valid_len) begin
      chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_SUM, {24'b0, sum},  "RES_PAYLOAD_SUM", tag, "§3.4");
      chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_XOR, {24'b0, xorv}, "RES_PAYLOAD_XOR", tag, "§3.4");
    end

    // IRQ_STA（§8.2）：done 边沿后 done_irq=irq_done_en；err_irq=any_error&irq_err_en
    apb_read(ppa_reg_defs_pkg::ADDR_IRQ_STA, irq_sta, slverr);
    if (irq_sta[0] !== irq_done_en)
      `uvm_error(tag, $sformatf("IRQ_STA.done_irq=%0b 期望 %0b（§8.2）", irq_sta[0], irq_done_en))
    if (irq_sta[1] !== (any_err & irq_err_en))
      `uvm_error(tag, $sformatf("IRQ_STA.err_irq=%0b 期望 %0b（§8.2 §9.1）", irq_sta[1], any_err & irq_err_en))
    // RW1C 清除两位，避免残留影响下一帧观测（§8.2）
    apb_write(ppa_reg_defs_pkg::ADDR_IRQ_STA, 32'h0000_0003);
  endtask

  // 随机生成一帧参数并跑
  task run_random(int i);
    bit [7:0] len, typ, flags, chk;
    bit       algo;
    bit [3:0] mask;
    bit [5:0] exp;
    bit [7:0] payload [];
    int sel;
    payload = new[28];
    foreach (payload[k]) payload[k] = 8'($urandom);
    sel = $urandom_range(0, 9);
    if (sel < 6)       len = 8'($urandom_range(4, 32));
    else if (sel < 7)  len = 8'($urandom_range(0, 3));
    else if (sel < 8)  len = 8'($urandom_range(33, 63));
    else               len = 8'($urandom);
    typ   = 8'($urandom);
    flags = 8'($urandom);
    chk   = (($urandom & 1) != 0) ? (len ^ typ ^ flags) : 8'($urandom);
    algo  = 1'($urandom);
    mask  = 4'($urandom);
    exp   = ($urandom_range(0, 2) == 0) ? 6'($urandom) : 6'd0;
    run_one(len, typ, flags, chk, algo, mask, exp, 1'($urandom), 1'($urandom), payload,
            $sformatf("M4-02b-rand%0d", i));
  endtask

  // 地址位扫描：遍历一组地址令 APB PADDR 各位双向翻转（含高/未对齐未定义地址，
  // §4.2 §8.3 负向激励）。落在 CSR 区(≤0x02B)/PKT_MEM 区(0x040-0x05C)外者应 PSLVERR=1。
  task addr_sweep();
    bit [31:0] rdata;
    bit        slverr;
    bit [11:0] alist [] = '{12'hFFF, 12'h800, 12'h400, 12'h200, 12'h100, 12'h080,
                            12'h0AA, 12'h155, 12'h001, 12'h002, 12'h003, 12'h07C};
    foreach (alist[i]) begin
      bit [11:0] a = alist[i];
      bit in_csr = (a <= 12'h02B);
      bit in_mem = (a >= ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE) && (a <= ppa_reg_defs_pkg::ADDR_PKT_MEM_END);
      apb_read(a, rdata, slverr);
      if (!in_csr && !in_mem) begin
        if (slverr !== 1'b1)
          `uvm_error("M4-02b", $sformatf("访问未定义地址 0x%03h 未报 PSLVERR（§4.2 §8.3）", a))
      end else begin
        if (slverr !== 1'b0)
          `uvm_error("M4-02b", $sformatf("访问 CSR/PKT_MEM 区地址 0x%03h 误报 PSLVERR（§5.2 §6.3）", a))
      end
    end
  endtask

  task body();
    bit [31:0] rdata;
    bit        slverr;
    bit [7:0]  pl4 [];

    // 使能一次（enable 常驻；do_start 每帧仍会重写 enable=1）
    apb_write(ppa_reg_defs_pkg::ADDR_CTRL, 32'h0000_0001);

    // APB 地址位翻转扫描（覆盖 apb_top 接口 PADDR 全位翻转）
    addr_sweep();

    // ---- 定向覆盖集成域断言前因（一次性）----
    // 保留地址访问 → PSLVERR=1（§4.2 §8.3；a_reserved_addr_slverr@u_apb）
    apb_read(12'h030, rdata, slverr);
    if (slverr !== 1'b1)
      `uvm_error("M4-02b", "读保留地址 0x030 未报 PSLVERR（§4.2 §8.3）")
    // 写只读寄存器 STATUS → PSLVERR=1（§5.1 §8.3；a_pslverr_on_ro_write@u_apb）
    apb_write_chk(ppa_reg_defs_pkg::ADDR_STATUS, 32'hDEAD_BEEF, slverr);
    if (slverr !== 1'b1)
      `uvm_error("M4-02b", "写只读 STATUS 未报 PSLVERR（§5.1 §8.3）")
    // 读 PKT_MEM 窗口 → PSLVERR=0 且 PRDATA=0（§6.3 r7；a_pktmem_read_placeholder@u_apb）
    apb_read(ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE, rdata, slverr);
    if (slverr !== 1'b0 || rdata !== 32'h0)
      `uvm_error("M4-02b", $sformatf("读 PKT_MEM 占位行为不符（slverr=%0b data=0x%08h，§6.3 r7）", slverr, rdata))

    // ---- 定向覆盖：algo_mode=0 旁路（a_algo_mode0_no_chkerr@u_core），故意给错 hdr_chk----
    pl4 = new[4]; pl4[0]=8'h11; pl4[1]=8'h22; pl4[2]=8'h33; pl4[3]=8'h44;
    run_one(8'd8, 8'h01, 8'h00, 8'hFF /*错校验*/, 1'b0 /*algo=0 旁路*/, 4'b1111, 6'd0,
            1'b1, 1'b1, pl4, "M4-02b-algo0");

    // ---- 定向覆盖：错误包 + err_irq_en（a_irq_err_same_cycle@u_apb 集成 err 中断）----
    // pkt_type=0x03 非 one-hot → type_error；err_irq_en=1 → err 中断置位
    run_one(8'd8, 8'h03, 8'h00, 8'h00, 1'b0, 4'b1111, 6'd0,
            1'b0 /*done_en=0*/, 1'b1 /*err_en=1*/, pl4, "M4-02b-errirq");

    // ---- 随机帧主体 ----
    for (int i = 0; i < n_pkt; i++) run_random(i);
  endtask

endclass

// ---------------------------------------------------------------------------
// M4-02c：apb_slave_if 单元级 CSR/stub 随机（多 seed）——补 M1 单元域 TOGGLE/COND
// 随机读写 RW CSR（CFG.algo/type_mask、IRQ_EN 双位、CTRL.enable、PKT_LEN_EXP）令各
// RW 位双向翻转；经 m3_stub 驱动随机 result/error 令 res_*/error 输入翻转；定向覆盖
// 两个 COND 缺口：① done 边沿 + 有错 + err_irq_en=0（LINE187 "1 1 0"）；② enable=1 时
// 向非 CTRL 地址写且 PWDATA[1]=1（LINE151 "1 0 1 1 1"）。期望值/行为依据 §5.2 §8.2 §9.1。
// ---------------------------------------------------------------------------
class m4_rand_csr_seq extends apb_base_seq;

  `uvm_object_utils(m4_rand_csr_seq)

  m3_stub_driver m3_drv; // 由 test 在 start() 前赋值
  int unsigned   n_iter = 24;

  function new(string name = "m4_rand_csr_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] rdata;
    bit        slverr;

    if (m3_drv == null) `uvm_fatal("M4-02c", "m3_drv 未设置，无法驱动 stub")
    m3_drv.set_busy(1'b0);

    // ---- 随机 CSR 读写：令各 RW 字段双向翻转（§5.2）----
    for (int i = 0; i < n_iter; i++) begin
      bit       algo   = 1'($urandom);
      bit [3:0] mask   = 4'($urandom);
      bit       en     = 1'($urandom);
      bit       ie_d   = 1'($urandom);
      bit       ie_e   = 1'($urandom);
      bit [5:0] expv   = 6'($urandom);
      // CFG（algo_mode=[0], type_mask=[7:4]）
      apb_write(ppa_reg_defs_pkg::ADDR_CFG, {24'b0, mask, 3'b0, algo});
      apb_read (ppa_reg_defs_pkg::ADDR_CFG, rdata, slverr);
      // IRQ_EN（[1]=err,[0]=done）——双位随机 0/1 双向翻转
      apb_write(ppa_reg_defs_pkg::ADDR_IRQ_EN, {30'b0, ie_e, ie_d});
      apb_read (ppa_reg_defs_pkg::ADDR_IRQ_EN, rdata, slverr);
      // PKT_LEN_EXP（[5:0]）
      apb_write(ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP, {26'b0, expv});
      apb_read (ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP, rdata, slverr);
      // CTRL.enable 双向（[0]）
      apb_write(ppa_reg_defs_pkg::ADDR_CTRL, {31'b0, en});
    end

    // ---- COND LINE151 "1 0 1 1 1"：enable=1 时向非 CTRL 地址写、PWDATA[1]=1 ----
    apb_write(ppa_reg_defs_pkg::ADDR_CTRL, 32'h0000_0001);       // enable=1
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP, 32'h0000_0002); // 非 CTRL 写、bit1=1（§5.2）

    // ---- 随机 stub result/error：令 res_*/length/type/chk_error 输入翻转（§5.2 §9.1）----
    for (int i = 0; i < 8; i++) begin
      bit [5:0] rl  = 6'($urandom);
      bit [7:0] rt  = 8'($urandom);
      bit [7:0] rs  = 8'($urandom);
      bit [7:0] rx  = 8'($urandom);
      bit       le  = 1'($urandom);
      bit       te  = 1'($urandom);
      bit       ce  = 1'($urandom);
      bit       fo  = !(le | te | ce);
      m3_drv.set_result(rl, rt, rs, rx, fo, le, te, ce);
      // 读回 RES_*/ERR_FLAG，令 PRDATA 低位与译码信号翻转（§5.2）
      apb_read(ppa_reg_defs_pkg::ADDR_RES_PKT_LEN,     rdata, slverr);
      apb_read(ppa_reg_defs_pkg::ADDR_RES_PKT_TYPE,    rdata, slverr);
      apb_read(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_SUM, rdata, slverr);
      apb_read(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_XOR, rdata, slverr);
      apb_read(ppa_reg_defs_pkg::ADDR_ERR_FLAG,        rdata, slverr);
    end

    // ---- COND LINE187 "1 1 0"：done 边沿 + 有错 + err_irq_en=0（§8.2 §9.1）----
    apb_write(ppa_reg_defs_pkg::ADDR_IRQ_EN, 32'h0000_0000); // done/err irq 均关
    m3_drv.clear_done();
    m3_drv.set_result(6'd0, 8'd0, 8'd0, 8'd0, 1'b0, 1'b1 /*length_error*/, 1'b0, 1'b0);
    m3_drv.pulse_done(); // done 上升沿：any_error=1 但 irq_en_err=0 → 不置 err 中断
    apb_read(ppa_reg_defs_pkg::ADDR_IRQ_STA, rdata, slverr);
    if (rdata[1] !== 1'b0)
      `uvm_error("M4-02c", $sformatf("err_irq_en=0 时有错 done 边沿误置 err 中断（IRQ_STA=0x%08h，§8.2）", rdata))
    else
      `uvm_info("M4-02c", "PASS: err_irq_en=0 时有错 done 边沿不置 err 中断（§8.2 §9.1）", UVM_LOW)
    m3_drv.clear_done();
  endtask

endclass

// ---------------------------------------------------------------------------
// M4-02e：ppa_top 运行中复位（集成核 FSM 复位转移覆盖）
// 集成核进入 PROCESS/DONE 后经 ppa_top_if.force_rst_n 注入一次 PRESETn 复位，
// 覆盖 u_core FSM 转移 PROCESS→IDLE / DONE→IDLE（§7.1）；复位后 STATUS 清零，
// 再跑一帧确认恢复正常（§7.2）。APB 观测接口 presetn 不受影响（见 tb_top 注）。
// ---------------------------------------------------------------------------
class m4_reset_integ_seq extends m3_base_seq;

  `uvm_object_utils(m4_reset_integ_seq)

  function new(string name = "m4_reset_integ_seq");
    super.new(name);
  endfunction

  // 注入一次 PRESETn 复位（拉低 force_rst_n 保持 cycles 拍）
  task inject_rst(int cycles);
    if (top_vif == null) `uvm_fatal("M4-02e", "top_vif 未设置，无法注入复位")
    top_vif.force_rst_n = 1'b0;
    repeat (cycles) @(top_vif.mon_cb);
    top_vif.force_rst_n = 1'b1;
    repeat (2) @(top_vif.mon_cb);
  endtask

  // 写入 32B 长包（拉宽 busy 窗口便于在 PROCESS 态注入）
  task load_long_pkt();
    wr_header(8'd32, 8'h04, 8'h00, 8'd32 ^ 8'h04 ^ 8'h00);
    wr_word(1, 32'h0102_0304); wr_word(2, 32'h0506_0708);
    wr_word(3, 32'h090A_0B0C); wr_word(4, 32'h0D0E_0F10);
    wr_word(5, 32'h1112_1314); wr_word(6, 32'h1516_1718);
    wr_word(7, 32'h191A_1B1C);
  endtask

  task body();
    bit [31:0] status;
    bit        slverr;
    bit        saw_busy;
    int        guard;

    // ---- 1. PROCESS 态注入复位 ----
    apb_write(ppa_reg_defs_pkg::ADDR_CTRL, 32'h0000_0001); // enable
    load_long_pkt();
    do_start();
    // 紧密轮询直到观测 busy（STATUS[0]=1），随即注入复位
    saw_busy = 1'b0; guard = 0;
    forever begin
      apb_read(ppa_reg_defs_pkg::ADDR_STATUS, status, slverr);
      if (status[0] === 1'b1) begin saw_busy = 1'b1; break; end
      if (status[1] === 1'b1) break; // 已到 done（busy 窗口太窄），退出
      if (++guard > 200) break;
    end
    if (!saw_busy)
      `uvm_warning("M4-02e", "未捕获 busy 窗口即注入复位（busy 窗口过窄），仍执行复位注入")
    inject_rst(3);
    // 复位后 STATUS 应清零（IDLE：busy=0 done=0，§7.4）
    apb_read(ppa_reg_defs_pkg::ADDR_STATUS, status, slverr);
    if (status[1:0] !== 2'b00)
      `uvm_error("M4-02e", $sformatf("PROCESS 态复位后 STATUS[1:0]=%02b 期望 00（§7.4 IDLE）", status[1:0]))
    else
      `uvm_info("M4-02e", "PASS: PROCESS 态注入复位后集成核回 IDLE（STATUS 清零）", UVM_LOW)

    // ---- 2. DONE 态注入复位 ----
    apb_write(ppa_reg_defs_pkg::ADDR_CTRL, 32'h0000_0001);
    load_long_pkt();
    do_start();
    poll_done(status, "M4-02e");
    if (status[1] !== 1'b1)
      `uvm_error("M4-02e", "帧未完成即欲在 DONE 注入复位（§7.2）")
    inject_rst(3);
    apb_read(ppa_reg_defs_pkg::ADDR_STATUS, status, slverr);
    if (status[1:0] !== 2'b00)
      `uvm_error("M4-02e", $sformatf("DONE 态复位后 STATUS[1:0]=%02b 期望 00（§7.1 复位→IDLE）", status[1:0]))
    else
      `uvm_info("M4-02e", "PASS: DONE 态注入复位后集成核回 IDLE（STATUS 清零）", UVM_LOW)

    // ---- 3. 复位后正常处理确认恢复（N-2：len=8 type=0x02 → sum=0x0A xor=0x04）----
    apb_write(ppa_reg_defs_pkg::ADDR_CTRL, 32'h0000_0001);
    wr_header(8'd8, 8'h02, 8'h00, 8'd8 ^ 8'h02 ^ 8'h00);
    wr_word(1, 32'h0102_0304);
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP, 32'h0000_0008);
    do_start();
    poll_done(status, "M4-02e");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_SUM, 32'h0000_000A, "复位后 RES_PAYLOAD_SUM", "M4-02e", "§3.4");
    chk_eq(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_XOR, 32'h0000_0004, "复位后 RES_PAYLOAD_XOR", "M4-02e", "§3.4");
    chk_eq(ppa_reg_defs_pkg::ADDR_ERR_FLAG,        32'h0000_0000, "复位后 ERR_FLAG",        "M4-02e", "§9.1");
    `uvm_info("M4-02e", "PASS: 复位后集成通路正常处理，结果与规格一致", UVM_LOW)
  endtask

endclass
