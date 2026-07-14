// M2 基础测试：建 packet_proc_core 单元级环境（core agent）；子类覆盖 build_items()
// 往 seq.items 填充定向激励。driver 内建 spec 参考模型自检，比对失败即 UVM_ERROR。
class ppa_m2_base_test extends uvm_test;

  `uvm_component_utils(ppa_m2_base_test)

  ppa_core_env            env;
  ppa_core_directed_seq   seq;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = ppa_core_env::type_id::create("env", this);
  endfunction

  function void end_of_elaboration_phase(uvm_phase phase);
    uvm_top.print_topology();
  endfunction

  // 便捷构造：合法/异常包 item
  function ppa_core_seq_item mk(string label);
    ppa_core_seq_item it = ppa_core_seq_item::type_id::create(label);
    it.label = label;
    return it;
  endfunction

  // 子类覆盖：填充 seq.items
  virtual function void build_items(ppa_core_directed_seq s);
  endfunction

  task run_phase(uvm_phase phase);
    seq = ppa_core_directed_seq::type_id::create("seq");
    build_items(seq);
    if (seq.items.size() == 0) begin
      `uvm_info(get_type_name(), "无激励项，直接结束", UVM_LOW)
      return;
    end
    phase.raise_objection(this);
    seq.start(env.agt.sqr);
    phase.phase_done.set_drain_time(this, 100ns);
    phase.drop_objection(this);
  endtask

endclass
