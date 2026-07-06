// scoreboard：接收 APB monitor 事务，与参考模型/寄存器镜像比对
// 骨架阶段只做事务记录；M1 起由 DV 补齐 CSR 镜像比对（期望值逐条注明 spec 章节）
class ppa_scoreboard extends uvm_scoreboard;

  `uvm_component_utils(ppa_scoreboard)

  uvm_analysis_imp #(apb_seq_item, ppa_scoreboard) apb_imp;

  int unsigned n_writes;
  int unsigned n_reads;

  function new(string name, uvm_component parent);
    super.new(name, parent);
    apb_imp = new("apb_imp", this);
  endfunction

  function void write(apb_seq_item tr);
    if (tr.write) n_writes++;
    else          n_reads++;
    `uvm_info("SB", tr.convert2string(), UVM_HIGH)
    // TODO(M1, DV): CSR 镜像 + 默认值比对（spec §5.2）、PSLVERR 期望（spec §8.3）
    // TODO(M3, DV): 结果寄存器与 ppa_ref_model::golden_calc 比对（spec §3.4/§9）
  endfunction

  function void report_phase(uvm_phase phase);
    `uvm_info("SB", $sformatf("APB 事务统计: 写=%0d 读=%0d", n_writes, n_reads), UVM_LOW)
  endfunction

endclass
