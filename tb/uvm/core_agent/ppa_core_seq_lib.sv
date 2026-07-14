// packet_proc_core 单元级定向序列：test 预先填充 items 队列，body 逐条发到 driver。
class ppa_core_directed_seq extends uvm_sequence #(ppa_core_seq_item);

  `uvm_object_utils(ppa_core_directed_seq)

  ppa_core_seq_item items[$];

  function new(string name = "ppa_core_directed_seq");
    super.new(name);
  endfunction

  task body();
    foreach (items[i]) begin
      ppa_core_seq_item it = items[i];
      start_item(it);
      finish_item(it);
    end
  endtask

endclass
