// APB monitor：在 ACCESS 完成拍（PSEL&PENABLE&PREADY）采样，广播给 scoreboard/coverage
class apb_monitor extends uvm_monitor;

  `uvm_component_utils(apb_monitor)

  virtual apb_if vif;
  uvm_analysis_port #(apb_seq_item) ap;

  function new(string name, uvm_component parent);
    super.new(name, parent);
    ap = new("ap", this);
  endfunction

  function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    if (!uvm_config_db#(virtual apb_if)::get(this, "", "apb_vif", vif))
      `uvm_fatal("APB_MON", "未从 config_db 取到 apb_vif")
  endfunction

  task run_phase(uvm_phase phase);
    apb_seq_item tr;
    forever begin
      @(vif.mon_cb);
      if (vif.mon_cb.psel === 1'b1 && vif.mon_cb.penable === 1'b1 &&
          vif.mon_cb.pready === 1'b1) begin
        tr = apb_seq_item::type_id::create("tr");
        tr.write  = vif.mon_cb.pwrite;
        tr.addr   = vif.mon_cb.paddr;
        tr.data   = vif.mon_cb.pwrite ? vif.mon_cb.pwdata : vif.mon_cb.prdata;
        tr.slverr = (vif.mon_cb.pslverr === 1'b1);
        ap.write(tr);
        `uvm_info("APB_MON", tr.convert2string(), UVM_HIGH)
      end
    end
  endtask

endclass
