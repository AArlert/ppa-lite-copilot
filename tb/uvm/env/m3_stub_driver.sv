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

endclass
