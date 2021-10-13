yosys -import
foreach verilog_file [glob -dir ./verilog *.v] {
	set circuit_name [string range $verilog_file 10 end-2]
	set abc_file ./aig_verilog/
	append abc_file $circuit_name .v
	
	read_verilog $verilog_file
	synth -top $circuit_name
	abc -liberty aigcells.lib
		
	write_verilog $abc_file
	clean top
}
