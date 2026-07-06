// APB 序列库：基础读写序列 + 冒烟序列
class apb_base_seq extends uvm_sequence #(apb_seq_item);

  `uvm_object_utils(apb_base_seq)

  function new(string name = "apb_base_seq");
    super.new(name);
  endfunction

  // 单次写
  task apb_write(input bit [11:0] addr, input bit [31:0] data);
    apb_seq_item tr;
    tr = apb_seq_item::type_id::create("tr");
    start_item(tr);
    if (!tr.randomize() with { write == 1'b1; addr == local::addr; data == local::data; })
      `uvm_error("APB_SEQ", "randomize 失败")
    finish_item(tr);
  endtask

  // 单次读，返回读数据与 slverr
  task apb_read(input bit [11:0] addr, output bit [31:0] data, output bit slverr);
    apb_seq_item tr;
    tr = apb_seq_item::type_id::create("tr");
    start_item(tr);
    if (!tr.randomize() with { write == 1'b0; addr == local::addr; })
      `uvm_error("APB_SEQ", "randomize 失败")
    finish_item(tr);
    data   = tr.data;
    slverr = tr.slverr;
  endtask

endclass

// 冒烟序列：验证环境活性（driver 握手/monitor 采样/phase 流转），不做功能比对
class apb_smoke_seq extends apb_base_seq;

  `uvm_object_utils(apb_smoke_seq)

  function new(string name = "apb_smoke_seq");
    super.new(name);
  endfunction

  task body();
    bit [31:0] rdata;
    bit        slverr;
    // 向 PKT_MEM 窗口写 8 个 word（地址 0x040+4N，spec §6.1），再读一次 CSR 首地址
    for (int i = 0; i < 8; i++)
      apb_write(12'h040 + 12'(4 * i), $urandom());
    apb_read(12'h000, rdata, slverr);
    `uvm_info("SMOKE", $sformatf("冒烟完成: CTRL 读回 0x%08h slverr=%0b", rdata, slverr), UVM_LOW)
  endtask

endclass
