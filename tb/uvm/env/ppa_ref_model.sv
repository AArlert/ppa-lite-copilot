// 参考模型（golden model，硬件语言实现）
// 硬规则：本文件的一切行为只准从 doc/spec.md 推导（每条注明章节），禁止参照 RTL 实现修改。
// 修改本文件如依赖歧义裁决，必须引用 bugs.md 条目号。

// 单帧处理的期望结果（spec §3.4/§5.2/§9.1）
typedef struct packed {
  bit [5:0] res_pkt_len;
  bit [7:0] res_pkt_type;
  bit [7:0] res_payload_sum;
  bit [7:0] res_payload_xor;
  bit       length_error;
  bit       type_error;
  bit       chk_error;
  bit       format_ok;
} ppa_exp_result_t;

class ppa_ref_model extends uvm_object;

  `uvm_object_utils(ppa_ref_model)

  function new(string name = "ppa_ref_model");
    super.new(name);
  endfunction

  // 输入：完整包字节流（含 4B 头部）+ CFG/PKT_LEN_EXP 配置
  // 输出：期望结果。三类错误并行判定、互不屏蔽（spec §9.2）。
  static function ppa_exp_result_t golden_calc(
    input byte unsigned pkt[],          // pkt[0..N-1]，至少含头部 4 字节
    input bit           algo_mode,      // CFG.algo_mode（spec §5.2）
    input bit [3:0]     type_mask,      // CFG.type_mask：bit[n]=1 允许 pkt_type=(1<<n)
    input bit [5:0]     exp_pkt_len     // PKT_LEN_EXP（BUG-001 暂定：0 = 未配置）
  );
    ppa_exp_result_t r;
    byte unsigned pkt_len, pkt_type, flags, hdr_chk;
    r = '0;

    pkt_len  = pkt[0];
    pkt_type = pkt[1];
    flags    = pkt[2];
    hdr_chk  = pkt[3];

    // 结果字段直接来自头部解析（spec §3.4）
    r.res_pkt_len  = pkt_len[5:0];
    r.res_pkt_type = pkt_type;

    // length_error：范围 [4,32] 越界，或与已配置的 PKT_LEN_EXP 不符（spec §9.1；BUG-001 暂定 0=未配置）
    // 显式类型转换消除 Lint-[ULCO]（8-bit pkt_len 与 32-bit PKT_LEN_MIN/MAX、6-bit
    // exp_pkt_len 比较位宽不等）：均为向上扩展至 32-bit，取值域内（pkt_len<=255，
    // exp_pkt_len<=63）无截断风险，比较语义不变，见 doc/bugs.md BUG-006 裁决
    r.length_error = (int'(pkt_len) < ppa_reg_defs_pkg::PKT_LEN_MIN) ||
                     (int'(pkt_len) > ppa_reg_defs_pkg::PKT_LEN_MAX) ||
                     ((exp_pkt_len != 0) && (int'(pkt_len) != int'(exp_pkt_len)));

    // type_error：非 one-hot（0x01/0x02/0x04/0x08）或被 type_mask 屏蔽（spec §9.1）
    case (pkt_type)
      8'h01:   r.type_error = !type_mask[0];
      8'h02:   r.type_error = !type_mask[1];
      8'h04:   r.type_error = !type_mask[2];
      8'h08:   r.type_error = !type_mask[3];
      default: r.type_error = 1'b1;
    endcase

    // chk_error：仅 algo_mode=1 时有效（spec §9.1）
    r.chk_error = algo_mode && (hdr_chk != (pkt[0] ^ pkt[1] ^ pkt[2]));

    // format_ok：三类检查均通过（spec §5.2 STATUS.format_ok）
    r.format_ok = !r.length_error && !r.type_error && !r.chk_error;

    // payload sum/XOR：仅对合法包长计算（spec §3.4；非法包长时行为未定义，见 BUG-002，
    // scoreboard 对非法包不得比对 sum/xor）
    if (int'(pkt_len) >= ppa_reg_defs_pkg::PKT_LEN_MIN &&
        int'(pkt_len) <= ppa_reg_defs_pkg::PKT_LEN_MAX) begin
      for (int i = 4; i < int'(pkt_len); i++) begin
        r.res_payload_sum += pkt[i];
        r.res_payload_xor ^= pkt[i];
      end
    end

    return r;
  endfunction

endclass
