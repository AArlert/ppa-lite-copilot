// 功能覆盖率收集器：APB 事务维度（地址区域 × 读写 × 响应）
// 代码覆盖率（line/cond/fsm/tgl/branch）由 VCS -cm 收集，此处只管功能覆盖
class ppa_cov extends uvm_subscriber #(apb_seq_item);

  `uvm_component_utils(ppa_cov)

  apb_seq_item tr;

  covergroup apb_cg;
    option.per_instance = 1;
    cp_region: coverpoint tr.addr {
      bins csr      = {['h000 : 'h028]};
      bins rsvd_lo  = {['h02C : 'h03F]};
      bins pkt_mem  = {['h040 : 'h05C]};
      bins rsvd_hi  = {['h05D : 'h05F]};
      bins undef    = {['h060 : 'hFFF]};
    }
    cp_dir:    coverpoint tr.write { bins rd = {0}; bins wr = {1}; }
    cp_slverr: coverpoint tr.slverr;
    x_region_dir: cross cp_region, cp_dir;
  endgroup

  function new(string name, uvm_component parent);
    super.new(name, parent);
    apb_cg = new();
  endfunction

  function void write(apb_seq_item t);
    tr = t;
    apb_cg.sample();
  endfunction

endclass
