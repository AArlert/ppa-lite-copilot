// M1 场景序列库：testplan M1-01~M1-06 对应序列，一场景一 body（沿用
// apb_seq_lib.sv 多序列共文件的既有约定）。期望值全部从 doc/spec.md 推导，
// 章节号随每条检查标注；地址常量取自 tb/uvm/env/ppa_reg_defs.sv（唯一定义点）。
// M1-03/M1-05/M1-06 需要驱动 M1 的 M3 结果只读输入，依赖 env 的 m3_stub_driver
// （ppa_env_pkg），故本文件置于 test 包内、在 apb_agent_pkg 与 ppa_env_pkg 之后编译。

// ---------------------------------------------------------------------------
// M1-01：APB 两段式读写时序 + CSR 默认值（§4.1 §5.2 §11.2-必1）
// 两段式 SETUP/ACCESS 时序与 PREADY 恒 1 由 tb/sva/apb_protocol_sva.sv 被动校验；
// 本序列聚焦复位默认值与写后读回生效。
// ---------------------------------------------------------------------------
class m1_csr_default_seq extends apb_base_seq;

  `uvm_object_utils(m1_csr_default_seq)

  function new(string name = "m1_csr_default_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] rdata;
    bit        slverr;

    // 复位默认值（spec §5.2 寄存器表"复位值"列；未列位域读回为 0）
    check_reg(ppa_reg_defs_pkg::ADDR_CTRL,           32'h0000_0000, "CTRL");
    check_reg(ppa_reg_defs_pkg::ADDR_CFG,             32'h0000_00F1, "CFG"); // [7:4]=1111,[0]=1
    check_reg(ppa_reg_defs_pkg::ADDR_STATUS,          32'h0000_0000, "STATUS");
    check_reg(ppa_reg_defs_pkg::ADDR_IRQ_EN,          32'h0000_0000, "IRQ_EN");
    check_reg(ppa_reg_defs_pkg::ADDR_IRQ_STA,         32'h0000_0000, "IRQ_STA");
    check_reg(ppa_reg_defs_pkg::ADDR_PKT_LEN_EXP,     32'h0000_0000, "PKT_LEN_EXP");
    check_reg(ppa_reg_defs_pkg::ADDR_RES_PKT_LEN,     32'h0000_0000, "RES_PKT_LEN");
    check_reg(ppa_reg_defs_pkg::ADDR_RES_PKT_TYPE,    32'h0000_0000, "RES_PKT_TYPE");
    check_reg(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_SUM, 32'h0000_0000, "RES_PAYLOAD_SUM");
    check_reg(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_XOR, 32'h0000_0000, "RES_PAYLOAD_XOR");
    check_reg(ppa_reg_defs_pkg::ADDR_ERR_FLAG,        32'h0000_0000, "ERR_FLAG");

    // 两段式写入生效 + W1P.start 读回恒 0（§4.1 §5.1）
    apb_write(ppa_reg_defs_pkg::ADDR_CTRL, 32'h0000_0003); // enable=1, start=1(W1P)
    apb_read(ppa_reg_defs_pkg::ADDR_CTRL, rdata, slverr);
    if (slverr)
      `uvm_error("M1-01", "写 CTRL 不应报 PSLVERR（§8.3 合法写）")
    else if (rdata !== 32'h0000_0001)
      `uvm_error("M1-01", $sformatf("CTRL 读回=0x%08h 期望 0x00000001（enable=1 生效，start 读回恒0，§5.1）", rdata))
    else
      `uvm_info("M1-01", "PASS: CTRL 两段式写入生效且 start 读回恒 0", UVM_LOW)
  endtask

  task check_reg(bit [11:0] addr, bit [31:0] exp, string name);
    bit [31:0] rdata;
    bit        slverr;
    apb_read(addr, rdata, slverr);
    if (slverr)
      `uvm_error("M1-01", $sformatf("读 %s(0x%03h) 报 PSLVERR，期望合法读（§8.3）", name, addr))
    else if (rdata !== exp)
      `uvm_error("M1-01", $sformatf("%s(0x%03h) 复位读回=0x%08h 期望=0x%08h（§5.2）", name, addr, rdata, exp))
    else
      `uvm_info("M1-01", $sformatf("PASS: %s 复位默认值=0x%08h 符合 §5.2", name, exp), UVM_LOW)
  endtask

endclass

// ---------------------------------------------------------------------------
// M1-02：PKT_MEM 写入地址映射（§6.1 §11.2-必2）
// wr_en/addr/data 映射契约由 tb/sva/apb_slave_if_sva.sv::a_pktmem_write_map 被动校验；
// 本序列负责产生覆盖 8 个 word 的写激励。
// ---------------------------------------------------------------------------
class m1_pktmem_write_seq extends apb_base_seq;

  `uvm_object_utils(m1_pktmem_write_seq)

  function new(string name = "m1_pktmem_write_seq");
    super.new(name);
  endfunction

  task body();
    bit [11:0] addr;
    bit [31:0] wdata;

    for (int i = 0; i < ppa_reg_defs_pkg::PKT_MEM_WORDS; i++) begin
      addr  = ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE + 12'(4 * i);
      wdata = 32'hA5A5_0000 + i[15:0]; // 每 word 可辨识 pattern
      apb_write(addr, wdata);
    end
    `uvm_info("M1-02", "PASS: 8 个 word 写满 PKT_MEM 窗口 0x040~0x05C（§6.1），地址映射由 SVA a_pktmem_write_map 校验", UVM_LOW)
  endtask

endclass

// ---------------------------------------------------------------------------
// M1-03：RES_* 只读通路（§5.2 §11.2-必3）
// ---------------------------------------------------------------------------
class m1_res_readback_seq extends apb_base_seq;

  `uvm_object_utils(m1_res_readback_seq)

  m3_stub_driver m3_drv; // 由 test 在 start() 前赋值

  function new(string name = "m1_res_readback_seq");
    super.new(name);
  endfunction

  task body();
    bit [5:0]  exp_pkt_len;
    bit [7:0]  exp_pkt_type, exp_sum, exp_xorv;
    bit [31:0] rdata;
    bit        slverr;

    if (m3_drv == null) `uvm_fatal("M1-03", "m3_drv 未设置，无法驱动 stub")

    exp_pkt_len  = 6'h2A;
    exp_pkt_type = 8'h04;
    exp_sum      = 8'hA5;
    exp_xorv     = 8'h3C;

    m3_drv.set_result(exp_pkt_len, exp_pkt_type, exp_sum, exp_xorv,
                       1'b1, 1'b0, 1'b0, 1'b0);

    apb_read(ppa_reg_defs_pkg::ADDR_RES_PKT_LEN, rdata, slverr);
    check(rdata, slverr, {26'b0, exp_pkt_len}, "RES_PKT_LEN");

    apb_read(ppa_reg_defs_pkg::ADDR_RES_PKT_TYPE, rdata, slverr);
    check(rdata, slverr, {24'b0, exp_pkt_type}, "RES_PKT_TYPE");

    apb_read(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_SUM, rdata, slverr);
    check(rdata, slverr, {24'b0, exp_sum}, "RES_PAYLOAD_SUM");

    apb_read(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_XOR, rdata, slverr);
    check(rdata, slverr, {24'b0, exp_xorv}, "RES_PAYLOAD_XOR");
  endtask

  task check(bit [31:0] rdata, bit slverr, bit [31:0] exp, string name);
    if (slverr)
      `uvm_error("M1-03", $sformatf("读 %s 报 PSLVERR，期望合法读（§8.3）", name))
    else if (rdata !== exp)
      `uvm_error("M1-03", $sformatf("%s 读回=0x%08h 期望=0x%08h（与 stub 驱动值一致，§2.3 §5.2）", name, rdata, exp))
    else
      `uvm_info("M1-03", $sformatf("PASS: %s 读回=0x%08h 与 stub 驱动值一致", name, exp), UVM_LOW)
  endtask

endclass

// ---------------------------------------------------------------------------
// M1-04：PSLVERR 统一响应（§8.3 §11.2-选4）
// ---------------------------------------------------------------------------
class m1_pslverr_seq extends apb_base_seq;

  `uvm_object_utils(m1_pslverr_seq)

  function new(string name = "m1_pslverr_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] rdata;
    bit        slverr;

    // 写只读寄存器（STATUS/RES_*/ERR_FLAG）：PSLVERR=1 且值不变（§5.1 §8.3）
    check_ro_write(ppa_reg_defs_pkg::ADDR_STATUS,          "STATUS");
    check_ro_write(ppa_reg_defs_pkg::ADDR_RES_PKT_LEN,     "RES_PKT_LEN");
    check_ro_write(ppa_reg_defs_pkg::ADDR_RES_PKT_TYPE,    "RES_PKT_TYPE");
    check_ro_write(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_SUM, "RES_PAYLOAD_SUM");
    check_ro_write(ppa_reg_defs_pkg::ADDR_RES_PAYLOAD_XOR, "RES_PAYLOAD_XOR");
    check_ro_write(ppa_reg_defs_pkg::ADDR_ERR_FLAG,        "ERR_FLAG");

    // CTRL 含 W1P start 位：写它是合法访问（PSLVERR=0），start 读回恒 0（不存储，§5.1）
    apb_write(ppa_reg_defs_pkg::ADDR_CTRL, 32'h0000_0002); // start=1，enable=0，故不会被接受
    apb_read(ppa_reg_defs_pkg::ADDR_CTRL, rdata, slverr);
    if (slverr)
      `uvm_error("M1-04", "写含 W1P 位的 CTRL 不应报 PSLVERR（§8.3）")
    else if (rdata[1] !== 1'b0)
      `uvm_error("M1-04", $sformatf("CTRL.start 读回=%0b 期望恒 0（W1P 不存储，§5.1）", rdata[1]))
    else
      `uvm_info("M1-04", "PASS: 写 CTRL(含 W1P start 位) 合法(PSLVERR=0)且 start 读回恒 0", UVM_LOW)

    // 访问保留区（0x02C~0x03F、0x05D~0x05F）与未定义地址（0x060+）：读写均 PSLVERR=1 且无副作用（§4.2 §8.3）
    check_reserved(12'h02C);
    check_reserved(12'h03F);
    check_reserved(12'h05D);
    check_reserved(12'h060);
    check_reserved(12'hFFF);
  endtask

  task check_ro_write(bit [11:0] addr, string name);
    bit [31:0] before_val, after_val;
    bit        rd_slverr, wr_slverr;
    apb_read(addr, before_val, rd_slverr);
    apb_write_chk(addr, 32'hFFFF_FFFF, wr_slverr);
    apb_read(addr, after_val, rd_slverr);
    if (!wr_slverr)
      `uvm_error("M1-04", $sformatf("写只读寄存器 %s 未报 PSLVERR（§5.1 §8.3）", name))
    else if (after_val !== before_val)
      `uvm_error("M1-04", $sformatf("写只读寄存器 %s 后值发生变化（写前=0x%08h 写后=0x%08h，§5.1 值不变）", name, before_val, after_val))
    else
      `uvm_info("M1-04", $sformatf("PASS: 写只读寄存器 %s 报 PSLVERR=1 且值不变", name), UVM_LOW)
  endtask

  task check_reserved(bit [11:0] addr);
    bit [31:0] rdata;
    bit        rd_slverr, wr_slverr;
    apb_read(addr, rdata, rd_slverr);
    apb_write_chk(addr, 32'hDEAD_BEEF, wr_slverr);
    if (!rd_slverr)
      `uvm_error("M1-04", $sformatf("读保留/未定义地址 0x%03h 未报 PSLVERR（§4.2 §8.3）", addr))
    else if (!wr_slverr)
      `uvm_error("M1-04", $sformatf("写保留/未定义地址 0x%03h 未报 PSLVERR（§4.2 §8.3）", addr))
    else
      `uvm_info("M1-04", $sformatf("PASS: 保留/未定义地址 0x%03h 读写均 PSLVERR=1", addr), UVM_LOW)
  endtask

endclass

// ---------------------------------------------------------------------------
// M1-05：IRQ 寄存器组（§5.2 §8.2 §11.2-选5）
// ---------------------------------------------------------------------------
class m1_irq_seq extends apb_base_seq;

  `uvm_object_utils(m1_irq_seq)

  m3_stub_driver m3_drv; // 由 test 在 start() 前赋值

  function new(string name = "m1_irq_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] rdata;
    bit        slverr;

    if (m3_drv == null) `uvm_fatal("M1-05", "m3_drv 未设置，无法驱动 stub")

    // IRQ_EN 读写（§5.2）
    apb_write(ppa_reg_defs_pkg::ADDR_IRQ_EN, 32'h0000_0003); // done_irq_en=1, err_irq_en=1
    apb_read(ppa_reg_defs_pkg::ADDR_IRQ_EN, rdata, slverr);
    if (slverr || rdata !== 32'h0000_0003)
      `uvm_error("M1-05", $sformatf("IRQ_EN 读回=0x%08h slverr=%0b 期望=0x3/0（§5.2）", rdata, slverr))
    else
      `uvm_info("M1-05", "PASS: IRQ_EN 读写正常", UVM_LOW)

    // done 事件（无错误）→ IRQ_STA.done_irq 同拍置位、irq_o=1（§8.2）
    m3_drv.pulse_done();
    apb_read(ppa_reg_defs_pkg::ADDR_IRQ_STA, rdata, slverr);
    if (slverr || rdata[0] !== 1'b1)
      `uvm_error("M1-05", $sformatf("done 中断后 IRQ_STA.done_irq 未置位（读回=0x%08h，§8.2）", rdata))
    else if (m3_drv.vif.drv_cb.irq !== 1'b1)
      `uvm_error("M1-05", "done 中断后 irq_o 未拉高（§8.2 组合输出）")
    else
      `uvm_info("M1-05", "PASS: done 中断同拍置位 IRQ_STA.done_irq 且 irq_o=1", UVM_LOW)

    // 软件写1清除：IRQ_STA 写 1 清 done_irq 位，随即 irq_o=0（§8.2 清除时序）
    apb_write(ppa_reg_defs_pkg::ADDR_IRQ_STA, 32'h0000_0001);
    apb_read(ppa_reg_defs_pkg::ADDR_IRQ_STA, rdata, slverr);
    if (rdata[0] !== 1'b0)
      `uvm_error("M1-05", $sformatf("写1清除后 IRQ_STA.done_irq 未清零（读回=0x%08h，§8.2）", rdata))
    else if (m3_drv.vif.drv_cb.irq !== 1'b0)
      `uvm_error("M1-05", "写1清除后 irq_o 未拉低（§8.2）")
    else
      `uvm_info("M1-05", "PASS: 写1清除 IRQ_STA.done_irq 且 irq_o 随即拉低", UVM_LOW)

    // err 事件：制造新的 done 上升沿并伴随错误标志，err_irq 应置位、irq_o=1（§8.2 §9.1）
    m3_drv.clear_done();
    m3_drv.set_result(6'd0, 8'd0, 8'd0, 8'd0, 1'b0, 1'b1 /*length_error*/, 1'b0, 1'b0);
    m3_drv.pulse_done();
    apb_read(ppa_reg_defs_pkg::ADDR_IRQ_STA, rdata, slverr);
    if (rdata[1] !== 1'b1)
      `uvm_error("M1-05", $sformatf("err 事件后 IRQ_STA.err_irq 未置位（读回=0x%08h，§8.2 §9.1）", rdata))
    else if (m3_drv.vif.drv_cb.irq !== 1'b1)
      `uvm_error("M1-05", "err 中断后 irq_o 未拉高（§8.2 irq_o=done_irq|err_irq）")
    else
      `uvm_info("M1-05", "PASS: err 中断同拍置位 IRQ_STA.err_irq 且 irq_o=1", UVM_LOW)

    apb_write(ppa_reg_defs_pkg::ADDR_IRQ_STA, 32'h0000_0002); // 清干净，收尾
  endtask

endclass

// ---------------------------------------------------------------------------
// M1-06：PKT_MEM APB 读回占位行为（§6.3(r7) §2.3 M2 表注(r7)）
// 已认可的对外行为（非缺陷）：本仓库架构下 M1 无 SRAM 读回通路，APB 读
// 0x040~0x05C 任意时刻 PSLVERR=0，PRDATA=32'h0。
// ---------------------------------------------------------------------------
class m1_pktmem_readback_seq extends apb_base_seq;

  `uvm_object_utils(m1_pktmem_readback_seq)

  m3_stub_driver m3_drv; // 用于驱动 busy_i=1，验证"任意时刻"含 busy 的情形

  function new(string name = "m1_pktmem_readback_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] rdata;
    bit        slverr;
    bit [11:0] addr;

    // 先写入非零数据，证明读回值与写入内容无关（占位值，§6.3(r7)）
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE, 32'hDEAD_BEEF);
    apb_write(ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE + 12'h04, 32'hCAFE_BABE);

    for (int i = 0; i < ppa_reg_defs_pkg::PKT_MEM_WORDS; i++) begin
      addr = ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE + 12'(4 * i);
      apb_read(addr, rdata, slverr);
      check(addr, rdata, slverr);
    end

    // busy=1 期间同样"任意时刻"（§6.3(r7) 明文含 busy，读不受 busy 保护）
    if (m3_drv != null) begin
      m3_drv.set_busy(1'b1);
      apb_read(ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE, rdata, slverr);
      check(ppa_reg_defs_pkg::ADDR_PKT_MEM_BASE, rdata, slverr);
      m3_drv.set_busy(1'b0);
    end
  endtask

  task check(bit [11:0] addr, bit [31:0] rdata, bit slverr);
    if (slverr)
      `uvm_error("M1-06", $sformatf("读 PKT_MEM 0x%03h 报 PSLVERR，期望 0（§6.3 r7）", addr))
    else if (rdata !== 32'h0)
      `uvm_error("M1-06", $sformatf("读 PKT_MEM 0x%03h=0x%08h 期望占位值 0（§6.3 r7）", addr, rdata))
    else
      `uvm_info("M1-06", $sformatf("PASS: PKT_MEM 0x%03h 读回占位值 0 PSLVERR=0", addr), UVM_LOW)
  endtask

endclass
