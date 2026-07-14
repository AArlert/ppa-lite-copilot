// M3 集成基础测试：在真实 ppa_top DUT 上建端到端验证环境。
// 复用 ppa_env（apb_agent + 被动 scoreboard/cov + m3_stub_driver），但 env 实例名
// 取 "m3_env"，使 tb_top 的 config_db 将 apb agent 绑定到 ppa_top 的 APB 接口
// （apb_top），与 M1 单元通路（env 实例 "env" → apb 接口）物理隔离、互不冲突。
// 子类覆盖 main_seq() 返回本场景主序列；需观测 irq_o 的场景经 top_vif 取顶层接口。
class ppa_m3_base_test extends uvm_test;

  `uvm_component_utils(ppa_m3_base_test)

  ppa_env            env;
  virtual ppa_top_if top_vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    // 实例名 "m3_env"：与 tb_top 中 "uvm_test_top.m3_env.*"→apb_top 的 config 对齐
    env = ppa_env::type_id::create("m3_env", this);
    if (!uvm_config_db#(virtual ppa_top_if)::get(this, "", "ppa_top_vif", top_vif))
      `uvm_fatal("M3_BASE", "未从 config_db 取到 ppa_top_vif（顶层 irq 观测接口）")
  endfunction

  function void end_of_elaboration_phase(uvm_phase phase);
    uvm_top.print_topology();
  endfunction

  // 子类覆盖：返回本测试主序列
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
