// APB 单次传输事务
class apb_seq_item extends uvm_sequence_item;

  rand bit        write;    // 1=写 0=读
  rand bit [11:0] addr;
  rand bit [31:0] data;     // 写数据；读事务完成后由 driver 回填读数据
  bit             slverr;   // 从机错误响应（driver/monitor 回填）

  `uvm_object_utils_begin(apb_seq_item)
    `uvm_field_int(write,  UVM_ALL_ON)
    `uvm_field_int(addr,   UVM_ALL_ON)
    `uvm_field_int(data,   UVM_ALL_ON)
    `uvm_field_int(slverr, UVM_ALL_ON)
  `uvm_object_utils_end

  function new(string name = "apb_seq_item");
    super.new(name);
  endfunction

  function string convert2string();
    return $sformatf("%s addr=0x%03h data=0x%08h slverr=%0b",
                     write ? "WR" : "RD", addr, data, slverr);
  endfunction

endclass
