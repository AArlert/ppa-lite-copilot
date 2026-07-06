// APB 主机 driver：两段式 SETUP→ACCESS 时序（spec §4.1）
class apb_driver extends uvm_driver #(apb_seq_item);

  `uvm_component_utils(apb_driver)

  virtual apb_if vif;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "apb_vif", vif))
      `uvm_fatal("APB_DRV", "未从 config_db 取到 apb_vif")
  endfunction

  task run_phase(uvm_phase phase);
    bus_idle();
    wait (vif.presetn === 1'b1);
    @(vif.drv_cb);
    forever begin
      seq_item_port.get_next_item(req);
      drive_one(req);
      seq_item_port.item_done();
    end
  endtask

  // 总线空闲态
  task bus_idle();
    vif.drv_cb.psel    <= 1'b0;
    vif.drv_cb.penable <= 1'b0;
    vif.drv_cb.pwrite  <= 1'b0;
    vif.drv_cb.paddr   <= '0;
    vif.drv_cb.pwdata  <= '0;
  endtask

  // 单次两段式传输；读数据与 slverr 回填进事务
  task drive_one(apb_seq_item tr);
    // SETUP：PSEL=1, PENABLE=0
    vif.drv_cb.psel    <= 1'b1;
    vif.drv_cb.penable <= 1'b0;
    vif.drv_cb.pwrite  <= tr.write;
    vif.drv_cb.paddr   <= tr.addr;
    vif.drv_cb.pwdata  <= tr.data;
    @(vif.drv_cb);
    // ACCESS：PENABLE=1，等待 PREADY（本设计固定 1，即单拍完成）
    vif.drv_cb.penable <= 1'b1;
    do @(vif.drv_cb); while (vif.drv_cb.pready !== 1'b1);
    if (!tr.write) tr.data = vif.drv_cb.prdata;
    tr.slverr = (vif.drv_cb.pslverr === 1'b1);
    bus_idle();
    `uvm_info("APB_DRV", tr.convert2string(), UVM_HIGH)
  endtask

endclass
