// packet_sram (M2)：8×32-bit 双端口同步 SRAM
// 职责：写端口来自 M1（APB 已译码），读端口来自 M3（处理阶段），不做包语义判断。
// spec 依据：§2.2 模块职责一览、§2.3 M2 端口表（含 r6 读时序契约注）、
//           §3.1/§3.2/§3.3、§6.1/§6.2/§6.3、§11.2 必做验收项2。
//
// 时序契约（BUG-003 / spec r6 裁决）：
//   - 写端口：同步写，clk 上升沿 wr_en=1 时将 wr_data 写入 mem[wr_addr]。
//   - 读端口：组合读，rd_en=1 当拍 rd_data = mem[rd_addr]（无 1 拍寄存延迟）；
//             rd_en=0 时 rd_data 输出 32'd0（spec 未规定 rd_en=0 时的值，此处取
//             确定性的 0 值以避免仿真中出现锁存/不定态告警；对外行为不做承诺）。
//
// 本模块不做地址译码、不做 busy 写保护仲裁（均为 M1 职责，§6.3），
// 不做包语义判断/FSM（M3 职责，§2.2 §7）。

module packet_sram
  import ppa_reg_defs_pkg::*;
(
    input  logic        clk,      // 时钟（来自 ppa_top.PCLK）
    input  logic        rst_n,    // 复位（低有效，来自 ppa_top.PRESETn 映射）

    input  logic        wr_en,    // 写使能（来自 M1）
    input  logic [2:0]  wr_addr,  // 写地址（0-7）
    input  logic [31:0] wr_data,  // 写数据

    input  logic        rd_en,    // 读使能（来自 M3）
    input  logic [2:0]  rd_addr,  // 读地址（0-7）
    output logic [31:0] rd_data   // 读数据
);

  // 存储阵列：8 × 32-bit（深度来自 ppa_reg_defs_pkg::PKT_MEM_WORDS，§6.1）
  // spec 未规定复位后阵列初值语义，本模块不对外承诺复位清零行为
  // （design-prompt "边界与约束"一节已注明，未定项走 §8 提案，不在此私定）。
  logic [31:0] mem [0:PKT_MEM_WORDS-1];

  // 同步写：clk 上升沿按 wr_en 写入（§2.3 M2 表注 r6）
  always_ff @(posedge clk) begin
    if (wr_en) begin
      mem[wr_addr] <= wr_data;
    end
  end

  // 组合读：rd_en=1 当拍 rd_data = mem[rd_addr]，无寄存延迟（§2.3 M2 表注 r6）
  always_comb begin
    if (rd_en) begin
      rd_data = mem[rd_addr];
    end else begin
      rd_data = 32'd0;
    end
  end

  // ------------------------------------------------------------------
  // 内部不变量断言（DE 撰写，design-prompt "内部断言建议"一节）
  // ------------------------------------------------------------------
`ifndef SYNTHESIS
  // disable iff 要求引用单一信号而非复合表达式（VCS lint Lint-[SVA-CE] "Complex
  // expression found"），故用一个连续赋值的高有效复位信号供各断言复用。
  logic rst;
  assign rst = !rst_n;

  // wr_addr/rd_addr 恒在合法范围内（3-bit 天然满足 0-7，仅断言无 X）
  a_wr_addr_no_x: assert property (@(posedge clk) disable iff (rst)
    wr_en |-> !$isunknown(wr_addr))
    else $error("packet_sram: wr_addr 存在 X 态且 wr_en=1");

  a_rd_addr_no_x: assert property (@(posedge clk) disable iff (rst)
    rd_en |-> !$isunknown(rd_addr))
    else $error("packet_sram: rd_addr 存在 X 态且 rd_en=1");

  // wr_en/rd_en 本身不得为 X（复位后信号确定性）
  a_wr_en_no_x: assert property (@(posedge clk) disable iff (rst)
    !$isunknown(wr_en))
    else $error("packet_sram: wr_en 为 X 态");

  a_rd_en_no_x: assert property (@(posedge clk) disable iff (rst)
    !$isunknown(rd_en))
    else $error("packet_sram: rd_en 为 X 态");

  // 写后读一致性：同拍无对同地址的新写入时，组合读结果应等于最近一次对该地址的写入
  // （读为组合输出，无寄存延迟，§2.3 r6）。此断言仅做设计自检，不替代 DV 的功能验证。
  a_read_after_write: assert property (@(posedge clk) disable iff (rst)
    (rd_en && !(wr_en && wr_addr == rd_addr)) |-> (rd_data == mem[rd_addr]))
    else $error("packet_sram: 组合读结果与存储内容不一致");
`endif

endmodule
