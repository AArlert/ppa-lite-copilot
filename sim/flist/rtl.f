// RTL 文件清单（路径相对 sim/）。模块完成后逐行启用，并配合 +define+HAS_DUT（见 tb/tb_top.sv）
// M1（apb_slave_if+packet_sram）已交付并接入 tb_top，启用 HAS_DUT
+define+HAS_DUT
../rtl/apb_slave_if.sv
../rtl/packet_sram.sv
// ../rtl/packet_proc_core.sv
// ../rtl/ppa_top.sv
