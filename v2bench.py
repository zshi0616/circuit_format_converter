from os import replace
import sys
import re
import glob
import platform

def convert_verilog_bench(verilog_file, bench_file):
    v_file = open(verilog_file, 'r')
    v_lineList = v_file.readlines()
    b_file = open(bench_file, 'w')

    inv_node_exist = {}
    node_cnt = 0

    line_idx = 0
    while True:
        line = v_lineList[line_idx]
        line_idx += 1
        if '(*' in line:
            continue
        if "endmodule" in line:  # assume that netlist file has only one module!
            break
        elif "//" == line[:2]:  # ignore lines that start with comments ... e.g., synopsys header
            line = ''
        elif ';' in line:
            line = line.lstrip()
            line = line.replace('\n', '')
            # print(line)
            new_lines = process_cell(line, inv_node_exist)
            # print(new_lines)
            # print('------------------------\n')
            for new_line in new_lines:
                b_file.write(new_line)
                if not 'INPUT' in new_line:
                    node_cnt += 1
    
    print("[SUCCESS] Convert {:} Done, with {:} nodes".format(verilog_file, node_cnt))

    b_file.close()
    v_file.close()

def process_cell(line, inv_node_exist):
    res = []
    newline = ''
    line = line.replace(' ;', '')
    line = line.replace(';', '')

    if "input " in line:
        to_process = line.replace("input ", "").replace(' ', '').replace(";", '').split(",")
        # print(to_process)
        for port in to_process:
            newline += "INPUT(" + port + ")\n"
        return [newline]
    elif "output " in line:
        to_process = line.replace("output ", "").replace(' ', '').replace(";", '').split(",")
        # print(to_process)
        for port in to_process:
            newline += "OUTPUT(" + port + ")\n"
        return [newline]
    elif "module " in line:
        return ["###\n"]
    elif "wire " in line:
        return [""]
    elif "assign" in line:
        if '= ~(' in line:
            dst_name = line.rstrip().split(' ')[1]
            src_list = line.split('= ~(')[-1].replace(')', '')
            src_list = src_list.split(' ')
            operator = symbol2text(src_list[1])
            res.append(dst_name+'_e = '+operator+'('+src_list[0]+', '+src_list[2]+')\n')
            res.append(dst_name+' = NOT('+dst_name+'_e)\n')
            return res
        else:
            line = line.replace('(', '')
            line = line.replace(')', '')
            test = line.split(" ")
            # assign a = ~b
            if len(test) == 4:
                if test[3][0] == '~':
                    newline = test[1] + ' = NOT(' + test[3][1:] + ')\n'
                else:
                    newline = test[1] + ' = ' + test[3] + '\n'
                return [newline]
                
            # assign a = c ? x : y
            elif len(test) == 8 and '?' in line:
                dst_node = test[1]
                res, con_node = proc_inv(test[3], res, [], inv_node_exist)
                con_node = con_node[0]
                res, true_node = proc_inv(test[5], res, [], inv_node_exist)
                true_node = true_node[0]
                res, false_node = proc_inv(test[7], res, [], inv_node_exist)
                false_node = false_node[0]

                con_true = '{}_T = AND({}, {})\n'.format(dst_node, con_node, true_node)
                res.append(con_true)
                if not con_node+'_inv' in inv_node_exist.keys():
                    inv_node_exist[con_node+'_inv'] = True
                    res.append(con_node + '_inv' + ' = NOT(' + con_node + ')\n')
                con_false = '{}_F = AND({}, {})\n'.format(dst_node, con_node + '_inv', false_node)
                res.append(con_false)
                res.append('{} = OR({}_T, {}_F)\n'.format(dst_node, dst_node, dst_node))
                return res
            
            # assign a = b & c
            elif len(test) == 6:
                src_node = []
                operator = ''
                for idx, ele in enumerate(test):
                    if idx < 3:
                        continue
                    if idx % 2 == 1:
                        res, src_node = proc_inv(test[idx], res, src_node, inv_node_exist)
                    else:
                        operator = symbol2text(test[idx])
                newline = test[1] + ' = ' + operator + '(' + src_node[0] + ', ' + src_node[1] + ')\n'
                res.append(newline)
                return res
            
            else:
                print('[Error] Not legal format'.format(line))
                raise

    else:
        newline = line
        print('[Warning] No info: {}'.format(newline))
        return [newline + '\n']

def proc_inv(ele, res, src_node, inv_node_exist):
    if ele[0] == '~':
        gate_name = ele[1:]
        gate_name_inv = gate_name + '_inv'
        if not gate_name_inv in inv_node_exist.keys():
            inv_node_exist[gate_name_inv] = True
            res.append(gate_name_inv + ' = NOT(' + gate_name + ')\n')
        src_node.append(gate_name_inv)
    else:
        src_node.append(ele)
    return res, src_node


def symbol2text(symbol):
    gate_type = ''
    if symbol == '&':
        gate_type = 'AND'
    elif symbol == '|':
        gate_type = 'OR'
    elif symbol == '^':
        gate_type = 'XOR'
    else:
        print('[ERROR] Unknown symbol : {}'.format(symbol))
        raise
    return gate_type

def main():
    # verilog_folder_1 = '../../EPFL_benchmarks/arithmetic/*.v'
    # verilog_folder_2 = '../../EPFL_benchmarks/random_control/*.v'
    # bench_folder = '../../EPFL_benchmarks/bench/'
    
    verilog_folder = './abc_verilog/*.v'
    for file in glob.glob(verilog_folder):
        if (platform.system() == 'Linux'):
            name = file.split("/")
            name = name[-1].split(".")
        else:
            name = file.split("\\")
            name = name[1].split(".")
        
        # if name[0] != 'sr_n_0003_pk2_030_pg_040_t_9_sat_1':
        #     continue
        print('[INFO] Converting Circuit: {}'.format(name[0]))
        bench_file = './bench/' + name[0] + '.bench'
        convert_verilog_bench(file, bench_file)


if __name__ == "__main__":
    # main()
    main()
