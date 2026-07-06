// 测试基类：建环境、打印拓扑；具体测试只需覆盖 main_seq
class ppa_base_test extends uvm_test;

  `uvm_component_utils(ppa_base_test)

  ppa_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = ppa_env::type_id::create("env", this);
  endfunction

  function void end_of_elaboration_phase(uvm_phase phase);
    uvm_top.print_topology();
  endfunction

  // 子类覆盖：返回本测试的主序列
  virtual function uvm_sequence #(apb_seq_item) main_seq();
    return null;
  endfunction

  task run_phase(uvm_phase phase);
    uvm_sequence #(apb_seq_item) seq = main_seq();
    if (seq == null) begin
      `uvm_info(get_type_name(), "无主序列，直接结束", UVM_LOW)
      return;
    end
    phase.raise_objection(this);
    seq.start(env.agt.sqr);
    phase.phase_done.set_drain_time(this, 100ns);
    phase.drop_objection(this);
  endtask

endclass
