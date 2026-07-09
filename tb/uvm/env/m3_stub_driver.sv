// M3 桩驱动组件：把 m3_stub_if 的受控激励封装成任务接口，供 M1-03/M1-05/M1-06
// 场景序列驱动 apb_slave_if 的 M3 结果只读输入（spec §2.3 M1 端口表）。
// 未接 DUT（HAS_DUT 未定义）时 config_db 取不到虚接口属预期，本组件任务直接
// 空转返回，不影响不依赖 M3 stub 的测试（如 ppa_smoke_test）正常运行。
class m3_stub_driver extends uvm_component;

  `uvm_component_utils(m3_stub_driver)

  virtual m3_stub_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual m3_stub_if)::get(this, "", "m3_stub_vif", vif))
      `uvm_info("M3_STUB", "未取到 m3_stub_vif（未接 DUT 时属预期，本组件本次不启用）", UVM_LOW)
  endfunction

  // 设置结果字段（不产生 done 边沿），供 M1-03 RES_* 只读通路场景使用（spec §2.3 §5.2）
  task set_result(bit [5:0] pkt_len, bit [7:0] pkt_type,
                   bit [7:0] sum, bit [7:0] xorv,
                   bit format_ok, bit len_err, bit type_err, bit chk_err);
    if (vif == null) return;
    @(vif.drv_cb);
    vif.drv_cb.res_pkt_len     <= pkt_len;
    vif.drv_cb.res_pkt_type    <= pkt_type;
    vif.drv_cb.res_payload_sum <= sum;
    vif.drv_cb.res_payload_xor <= xorv;
    vif.drv_cb.format_ok       <= format_ok;
    vif.drv_cb.length_error    <= len_err;
    vif.drv_cb.type_error      <= type_err;
    vif.drv_cb.chk_error       <= chk_err;
    @(vif.drv_cb); // 等待驱动生效，供后续 APB 读事务采样到新值
  endtask

  // 驱动 busy_i（spec §6.3：busy=1 期间 APB 写 PKT_MEM 受保护；busy 不影响读）
  task set_busy(bit b);
    if (vif == null) return;
    @(vif.drv_cb);
    vif.drv_cb.busy <= b;
    @(vif.drv_cb);
  endtask

  // 产生 done_i 上升沿并保持高电平（spec §8.2："done_i 上升沿"驱动中断置位判定）。
  // 若调用前 done 已为 1，需先 clear_done() 制造新的上升沿。
  task pulse_done();
    if (vif == null) return;
    @(vif.drv_cb);
    vif.drv_cb.done <= 1'b1;
    @(vif.drv_cb);
  endtask

  task clear_done();
    if (vif == null) return;
    @(vif.drv_cb);
    vif.drv_cb.done <= 1'b0;
    @(vif.drv_cb);
  endtask

  // 驱动 packet_sram（M2）读端口 rd_en/rd_addr 并回读 rd_data（spec §2.3 M2 表注 r6：
  // 组合读，rd_en=1 当拍 rd_data=mem[rd_addr] 同拍有效，无寄存延迟）。经 clocking block
  // 驱动存在输出时延，故用"驱动→等一拍使物理信号与组合读结果稳定→采样→撤销 rd_en"
  // 节奏；采样后立即撤销 rd_en，顺带驱动 rd_en=0 分支，供 M1-08/M1-09 场景使用。
  task read_sram(bit [2:0] addr, output bit [31:0] data);
    if (vif == null) begin
      data = 32'hxxxx_xxxx;
      return;
    end
    @(vif.drv_cb);
    vif.drv_cb.rd_en   <= 1'b1;
    vif.drv_cb.rd_addr <= addr;
    @(vif.drv_cb);
    data = vif.drv_cb.rd_data;
    vif.drv_cb.rd_en   <= 1'b0;
    @(vif.drv_cb);
  endtask

  // 在后续固定 cycles 个时钟周期内观测 start_o（经 m3_stub.start_pulse 旁路采样）
  // 是否出现脉冲及出现次数，供 M1-07 与目标 APB 写事务并发（fork）运行，避免序列
  // 在写事务返回后才采样、错过组合输出仅持续 1 拍的 ACCESS 窗口（spec §5.2 CTRL.start）。
  task watch_start_pulse(output int pulse_cnt, input int cycles = 4);
    pulse_cnt = 0;
    if (vif == null) return;
    repeat (cycles) begin
      @(vif.drv_cb);
      if (vif.drv_cb.start_pulse) pulse_cnt++;
    end
  endtask

endclass
