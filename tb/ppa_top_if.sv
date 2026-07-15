// ppa_top 顶层观测接口：仅采样 irq_o（§2.3 Top 表 irq_o，唯一权威顶层引脚）。
// M3 集成 test 经此接口观测中断路径（M3-05，§8.2）。只读采样，不驱动任何信号。
interface ppa_top_if (
  input logic pclk,
  input logic presetn
);

  logic irq_o;

  // ---- 运行中复位注入（M4-02e 覆盖率闭环：集成核 FSM 复位转移覆盖）----
  // 缺省 1'b1 → ppa_top 见到的复位 = 全局 presetn（既有行为不变）；集成复位 test
  // 将 force_rst_n 拉低若干拍，仅对 ppa_top 内部注入一次异步复位，APB 观测接口
  // （apb_top）的 presetn 不受影响，故 APB agent 复位后仍可继续读 STATUS 验证恢复。
  logic force_rst_n = 1'b1;

  // monitor 时钟块：采样 irq_o（§8.2 组合输出，在时钟沿采样即可）
  clocking mon_cb @(posedge pclk);
    input irq_o;
  endclocking

endinterface
