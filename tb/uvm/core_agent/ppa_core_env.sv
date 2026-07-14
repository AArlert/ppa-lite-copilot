// packet_proc_core 单元级环境：仅含 core agent（自检 driver 内建 spec 参考模型比对）
class ppa_core_env extends uvm_env;

  `uvm_component_utils(ppa_core_env)

  ppa_core_agent agt;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    agt = ppa_core_agent::type_id::create("agt", this);
  endfunction

endclass
