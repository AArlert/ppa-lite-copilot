// packet_proc_core 单元级 driver + 自检：装载行为 SRAM、置帧级配置、发 start 单拍脉冲、
// 等 done、按 spec 参考模型（seq_item.predict）逐字段比对 DUT 输出。
// 配置在 start 前置好并整个 busy 期间保持不变（§5.2 r10 软件契约）。
class ppa_core_driver extends uvm_driver #(ppa_core_seq_item);

  `uvm_component_utils(ppa_core_driver)

  virtual ppa_core_if vif;

  // 超时上限：合法/非法帧读拍数钳位 [1,8]（§7.3 r8），留足余量判"卡死"
  localparam int DONE_TIMEOUT = 64;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual ppa_core_if)::get(this, "", "ppa_core_vif", vif))
      `uvm_fatal("M2_DRV", "未从 config_db 取到 ppa_core_vif")
  endfunction

  task run_phase(uvm_phase phase);
    // 复位期默认激励
    vif.drv_cb.start_i       <= 1'b0;
    vif.drv_cb.algo_mode_i   <= 1'b1;
    vif.drv_cb.type_mask_i   <= 4'b1111;
    vif.drv_cb.exp_pkt_len_i <= 6'd0;
    wait (vif.rst_n === 1'b1);
    @(vif.drv_cb);
    forever begin
      seq_item_port.get_next_item(req);
      drive_item(req);
      seq_item_port.item_done();
    end
  endtask

  task drive_item(ppa_core_seq_item tr);
    tr.predict();
    // 帧起始前装载行为 SRAM（§6.1 8 word）
    for (int w = 0; w < 8; w++) vif.mem[w] = tr.get_word(w);
    // 帧级配置在 start 前置好并保持（§5.2 r10 契约）
    vif.drv_cb.algo_mode_i   <= tr.algo_mode;
    vif.drv_cb.type_mask_i   <= tr.type_mask;
    vif.drv_cb.exp_pkt_len_i <= tr.exp_pkt_len;
    vif.drv_cb.start_i       <= 1'b0;
    @(vif.drv_cb);
    // start 脉冲（§5.2 W1P，缺省 start_hold=1 为单拍）；start_hold>1 时 start 保持高延伸
    // 到 PROCESS 期间，覆盖"PROCESS 忽略 start"的条件分支（M4-02a）——PROCESS 期间置起
    // start 不改变状态（§7.2），正确性由内部断言 a_process_ignores_start 被动保证。
    vif.drv_cb.start_i <= 1'b1;
    repeat (tr.start_hold) @(vif.drv_cb);
    vif.drv_cb.start_i <= 1'b0;

    if (tr.inject_rst) begin
      inject_reset(tr); // M4-02d：运行中注入异步复位并核对回 IDLE
      return;
    end

    // 等待 done（§7.2 PROCESS→DONE；带超时防卡死，§7.3 E-1/E-2 不卡死）
    wait_and_check(tr);
    // DONE 态停留（M2-03：done 保持有效，由 SVA a_done_hold 被动监视）
    repeat (tr.post_done_idle) @(vif.drv_cb);
  endtask

  // M4-02d：在 PROCESS 或 DONE 态注入一次异步复位（拉低 force_rst_n），核对 FSM
  // 干净回到 IDLE（§7.1 [*]→IDLE / §7.4 IDLE 态输出）。覆盖 FSM 复位转移
  // PROCESS→IDLE / DONE→IDLE。期望值均从 spec 推导：复位后 busy_o/done_o=0、
  // res_*/错误标志清零（§7.4 §9.3 复位值）。
  task inject_reset(ppa_core_seq_item tr);
    int to = DONE_TIMEOUT;
    string ph = (tr.rst_phase == 0) ? "PROCESS" : "DONE";
    // 等到目标态
    if (tr.rst_phase == 0) begin
      // 等 busy_o（PROCESS 态，§7.4）
      do @(vif.drv_cb); while ((vif.drv_cb.busy_o !== 1'b1) && (--to > 0));
      if (vif.drv_cb.busy_o !== 1'b1)
        `uvm_error("M2_RST", $sformatf("%s：注入复位前未见 busy_o=1（§7.4）", tr.label))
    end else begin
      // 等 done_o（DONE 态，§7.4）
      do @(vif.drv_cb); while ((vif.drv_cb.done_o !== 1'b1) && (--to > 0));
      if (vif.drv_cb.done_o !== 1'b1)
        `uvm_error("M2_RST", $sformatf("%s：注入复位前未见 done_o=1（§7.4）", tr.label))
    end

    // 注入异步复位：拉低 force_rst_n 保持 2 拍（触发 FSM 复位转移回 IDLE）
    vif.force_rst_n = 1'b0;
    repeat (2) @(vif.drv_cb);
    vif.force_rst_n = 1'b1;
    @(vif.drv_cb);

    // 复位后应处于 IDLE：busy_o=0、done_o=0、res_*/错误标志清零（§7.1 §7.4 §9.3）
    if (vif.drv_cb.busy_o !== 1'b0)
      `uvm_error("M2_RST", $sformatf("%s（%s 注入复位）：复位后 busy_o 未清零（§7.4 IDLE）", tr.label, ph))
    if (vif.drv_cb.done_o !== 1'b0)
      `uvm_error("M2_RST", $sformatf("%s（%s 注入复位）：复位后 done_o 未清零（§7.1 复位→IDLE）", tr.label, ph))
    if (vif.drv_cb.length_error_o !== 1'b0 || vif.drv_cb.type_error_o !== 1'b0 ||
        vif.drv_cb.chk_error_o !== 1'b0 || vif.drv_cb.format_ok_o !== 1'b0 ||
        vif.drv_cb.res_pkt_len_o !== 6'd0 || vif.drv_cb.res_pkt_type_o !== 8'd0 ||
        vif.drv_cb.res_payload_sum_o !== 8'd0 || vif.drv_cb.res_payload_xor_o !== 8'd0)
      `uvm_error("M2_RST", $sformatf("%s（%s 注入复位）：复位后结果/错误寄存器未清零（§9.3）", tr.label, ph))
    else
      `uvm_info("M2_RST", $sformatf("PASS: %s 态注入复位后 FSM 干净回 IDLE、输出清零", ph), UVM_LOW)
  endtask

  task wait_and_check(ppa_core_seq_item tr);
    int to = DONE_TIMEOUT;
    bit busy_seen = 1'b0;
    do begin
      @(vif.drv_cb);
      if (vif.drv_cb.busy_o) busy_seen = 1'b1;
      to--;
    end while ((vif.drv_cb.done_o !== 1'b1) && (to > 0));

    if (vif.drv_cb.done_o !== 1'b1) begin
      `uvm_error("M2_DRV", $sformatf("%s 超时未见 done_o（疑似卡死，§7.2/§7.3）",
                                     tr.convert2string()))
      return;
    end
    if (!busy_seen)
      `uvm_error("M2_DRV", $sformatf("%s 处理期间未观测到 busy_o=1（§7.4 PROCESS busy=1）",
                                     tr.convert2string()))
    check_outputs(tr);
  endtask

  // done 拍采样输出并按 spec 参考模型比对
  task check_outputs(ppa_core_seq_item tr);
    string ctx = tr.convert2string();
    // §5.2/§9.1 错误标志
    chk("length_error", vif.drv_cb.length_error_o, tr.e_length_error, ctx);
    chk("type_error",   vif.drv_cb.type_error_o,   tr.e_type_error,   ctx);
    chk("chk_error",    vif.drv_cb.chk_error_o,    tr.e_chk_error,    ctx);
    chk("format_ok",    vif.drv_cb.format_ok_o,    tr.e_format_ok,    ctx);
    // §3.4 结果字段
    chkv("res_pkt_len",  vif.drv_cb.res_pkt_len_o,  tr.e_res_pkt_len,  ctx);
    chkv("res_pkt_type", vif.drv_cb.res_pkt_type_o, tr.e_res_pkt_type, ctx);
    // §3.4/§7.3：仅合法包长比对 sum/xor（非法包长 UNSPECIFIED，r5）
    if (tr.check_sum_xor) begin
      chkv("res_payload_sum", vif.drv_cb.res_payload_sum_o, tr.e_sum, ctx);
      chkv("res_payload_xor", vif.drv_cb.res_payload_xor_o, tr.e_xor, ctx);
    end else begin
      `uvm_info("M2_DRV", $sformatf("%s sum/xor 非法包长 UNSPECIFIED，不比对（§7.3 r5）", ctx), UVM_MEDIUM)
    end
  endtask

  function void chk(string nm, bit act, bit exp, string ctx);
    if (act !== exp)
      `uvm_error("M2_CHK", $sformatf("%s %s 不符：期望 %0b 实得 %0b", ctx, nm, exp, act))
    else
      `uvm_info("M2_CHK", $sformatf("%s %s=%0b MATCH", ctx, nm, act), UVM_HIGH)
  endfunction

  function void chkv(string nm, bit [7:0] act, bit [7:0] exp, string ctx);
    if (act !== exp)
      `uvm_error("M2_CHK", $sformatf("%s %s 不符：期望 0x%02h 实得 0x%02h", ctx, nm, exp, act))
    else
      `uvm_info("M2_CHK", $sformatf("%s %s=0x%02h MATCH", ctx, nm, act), UVM_HIGH)
  endfunction

endclass
