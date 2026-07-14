// ppa_top 顶层观测接口：仅采样 irq_o（§2.3 Top 表 irq_o，唯一权威顶层引脚）。
// M3 集成 test 经此接口观测中断路径（M3-05，§8.2）。只读采样，不驱动任何信号。
interface ppa_top_if (
  input logic pclk,
  input logic presetn
);

  logic irq_o;

  // monitor 时钟块：采样 irq_o（§8.2 组合输出，在时钟沿采样即可）
  clocking mon_cb @(posedge pclk);
    input irq_o;
  endclocking

endinterface
