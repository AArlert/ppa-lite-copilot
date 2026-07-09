// 顶层验证环境：APB agent + scoreboard + 功能覆盖
class ppa_env extends uvm_env;

  `uvm_component_utils(ppa_env)

  apb_agent      agt;
  ppa_scoreboard sb;
  ppa_cov        cov;
  m3_stub_driver m3_drv; // M3 尚未交付，桩驱动供 M1-03/M1-05/M1-06 场景使用

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    agt    = apb_agent::type_id::create("agt", this);
    sb     = ppa_scoreboard::type_id::create("sb", this);
    cov    = ppa_cov::type_id::create("cov", this);
    m3_drv = m3_stub_driver::type_id::create("m3_drv", this);
  endfunction

  function void connect_phase(uvm_phase phase);
    agt.mon.ap.connect(sb.apb_imp);
    agt.mon.ap.connect(cov.analysis_export);
  endfunction

endclass
