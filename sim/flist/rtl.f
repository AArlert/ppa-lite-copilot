// RTL 文件清单（路径相对 sim/），配合 +define+HAS_DUT 使用（见 tb/tb_top.sv 的 DUT 接入点）
// 下列四个模块均已交付并接入 tb_top（M1 单元/M2 单元/集成三条通路），故 HAS_DUT 常开
+define+HAS_DUT
../rtl/apb_slave_if.sv
../rtl/packet_sram.sv
../rtl/packet_proc_core.sv
../rtl/ppa_top.sv
