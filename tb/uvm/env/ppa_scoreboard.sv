// scoreboard：接收 APB monitor 事务，做读/写事务计数与 UVM_HIGH 级流水打印
//
// 已选架构（有意的规模取舍，不是待办事项）：本项目的期望值比对**不集中在本组件**，
// 而是落在自检序列与 agent 内建参考模型里。实际落点：
//   · CSR/寄存器行为（复位值、RO/W1P、PSLVERR）：tb/uvm/test/m1_seq_lib.sv，31 处
//     `uvm_error` 比对点，每条注明 spec 章节号；
//   · 集成通路读回比对：tb/uvm/test/m3_seq_lib.sv 的 chk_eq()（定义于该文件，14 处
//     调用）与 tb/uvm/test/m4_seq_lib.sv（8 处调用）；
//   · 核输出比对：tb/uvm/core_agent/ppa_core_driver.sv::check_outputs()（chk/chkv
//     共 8 个调用点），期望值由 tb/uvm/core_agent/ppa_core_seq_item.sv::predict()
//     按 spec §3.4/§9.1 逐条推导；
//   · 协议/时序契约：tb/sva/ 下三个文件的 17 条断言（bind 挂接）。
// （上列处数为 0.5.1 登记时刻的计数，会随 TB 演进漂移；落点路径才是本注释的承重部分，
//  现算值见 `python3 scripts/report.py --summary`。）
// 代价（如实记录）：检查逻辑分散在序列与 driver 中，没有单一的"期望 vs 实得"汇聚点，
// 跨场景复用靠各自实现，规模扩大后维护性差；本组件因此只剩事务计数，report_phase
// 打印的读/写数**不构成任何通过判据**。
// 后续演进项：把上述比对收敛为集中式记分板（本组件订阅 monitor + 独立参考模型）。若走这一步，
// 独立参考模型应从 core-agent 的 ppa_core_seq_item.sv::predict() 抽出——**目前全工程只有
// predict() 这一份参考模型**（原 env 内另有一份 golden 计算的独立参考模型，零调用死代码，
// 与 predict() 构成双份实现的静默漂移风险，已按 BUG-016 删除）。
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
    // 此处不做期望值比对：CSR 镜像/结果比对的实际落点见文件头"已选架构"一节
  endfunction

  function void report_phase(uvm_phase phase);
    `uvm_info("SB", $sformatf("APB 事务统计: 写=%0d 读=%0d", n_writes, n_reads), UVM_LOW)
  endfunction

endclass
