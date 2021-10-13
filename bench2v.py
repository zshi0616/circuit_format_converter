from os import replace
import sys
import re
import glob
import platform

gate_to_index = {"INPUT": 0, "AND": 1, "NAND": 2, "OR": 3, "NOR": 4, "NOT": 5, "XOR": 6}

def convert_bench_verilog(module_name, bench_file, verilog_file):
    b_file = open(bench_file, 'r')
    b_lineList = b_file.readlines()

    x_data, edge_index_data, level_list, fanin_list, fanout_list = prase_bench(b_lineList)
    if len(x_data) == 0:
        return 

    v_file = open(verilog_file, 'w')
    print('[INFO] Number of nodes: {:}'.format(len(x_data)))

    # find PI
    pi_list = []
    for idx, fanin in enumerate(fanin_list):
        if len(fanin) == 0 and len(fanout_list[idx]) != 0:
            pi_list.append(idx)
    po_list = []
    for idx, fanout in enumerate(fanout_list):
        if len(fanout) == 0 and len(fanin_list[idx]) != 0:
            po_list.append(idx)

    # Verilog head 
    first_line = 'module ' + module_name + '( ';
    for idx, pi_idx in enumerate(pi_list):
        first_line += x_data[pi_idx][0] + ', '
    for idx, po_idx in enumerate(po_list):
        if idx == len(po_list) - 1:
            first_line += x_data[po_idx][0]
        else:
            first_line += x_data[po_idx][0] + ', '
    first_line += '); \n'
    v_file.write(first_line);

    # PI and PO
    input_line = 'input '
    for k, pi_idx in enumerate(pi_list):
        if k == len(pi_list) -1:
            input_line += x_data[pi_idx][0] + '; \n'
        else:
            input_line += x_data[pi_idx][0] + ', '
    v_file.write(input_line)
    output_line = 'output '
    for k, po_idx in enumerate(po_list):
        if k == len(po_list) -1:
            output_line += x_data[po_idx][0] + '; \n'
        else:
            output_line += x_data[po_idx][0] + ', '
    v_file.write(output_line)
    
    # Gate
    wire_line = 'wire '
    wire_list = []
    for idx, x_data_info in enumerate(x_data):
        if len(fanin_list[idx]) > 0 and len(fanout_list[idx]) > 0:
            wire_list.append(idx)
    for k, idx in enumerate(wire_list):
        if k == len(wire_list) - 1:
            wire_line += x_data[idx][0] + '; \n'
        else:
            wire_line += x_data[idx][0] + ', '
    v_file.write(wire_line)
    
    # Gates
    for level in range(len(level_list)):
        if level == 0:
            continue
        for idx in level_list[level]:
            x_data_info = x_data[idx]
            new_line = 'assign ' + x_data_info[0] + ' = '
            gate_type = get_gate_name(x_data_info[1], gate_to_index)
            if gate_type == 'NOT':
                new_line += '~{}; \n'.format(x_data[fanin_list[idx][0]][0])
            elif gate_type == 'AND':
                for k, fanin_idx in enumerate(fanin_list[idx]):
                    if k == len(fanin_list[idx])-1:
                        new_line += x_data[fanin_idx][0] + '; \n'
                    else:
                        new_line += x_data[fanin_idx][0] + ' & '
            elif gate_type == 'OR':
                for k, fanin_idx in enumerate(fanin_list[idx]):
                    if k == len(fanin_list[idx])-1:
                        new_line += x_data[fanin_idx][0] + '; \n'
                    else:
                        new_line += x_data[fanin_idx][0] + ' | '
            elif gate_type == 'XOR':
                for k, fanin_idx in enumerate(fanin_list[idx]):
                    if k == len(fanin_list[idx])-1:
                        new_line += x_data[fanin_idx][0] + '; \n'
                    else:
                        new_line += x_data[fanin_idx][0] + ' ^ '
            elif gate_type == 'NAND':
                new_line += '~('
                for k, fanin_idx in enumerate(fanin_list[idx]):
                    if k == len(fanin_list[idx])-1:
                        new_line += x_data[fanin_idx][0]
                    else:
                        new_line += x_data[fanin_idx][0] + ' & '
                new_line += '); \n'
            elif gate_type == 'NOR':
                new_line += '~('
                for k, fanin_idx in enumerate(fanin_list[idx]):
                    if k == len(fanin_list[idx])-1:
                        new_line += x_data[fanin_idx][0]
                    else:
                        new_line += x_data[fanin_idx][0] + ' | '
                new_line += '); \n'
            v_file.write(new_line)
    
    v_file.write('endmodule \n')
    b_file.close()
    v_file.close()

def get_gate_name(var, gate_to_index):
    for key in gate_to_index:
        if var == gate_to_index[key]:
            return key
    return 'UNKNOWN'

def new_node(name2idx, x_data, node_name, gate_type):
    x_data.append([node_name, gate_type])
    name2idx[node_name] = len(name2idx)

def get_gate_type(line, gate_to_index):
    vector_row = -1
    for (gate_name, index) in gate_to_index.items():
        if gate_name  in line:
            vector_row = index

    if vector_row == -1:
        raise KeyError('[ERROR] Find unsupported gate')

    return vector_row

def prase_bench(data):
    name2idx = {}
    node_cnt = 0
    x_data = []
    edge_index_data = []

    for line in data:
        if 'INPUT(' in line:
            node_name = line.split("(")[-1].split(')')[0]
            new_node(name2idx, x_data, node_name, get_gate_type('INPUT', gate_to_index))
        elif 'AND(' in line or 'NAND(' in line or 'OR(' in line or 'NOR(' in line \
                or 'NOT(' in line or 'XOR(' in line:
            node_name = line.split('=')[0].replace(' ', '')
            gate_type = line.split('=')[-1].split('(')[0].replace(' ', '')
            new_node(name2idx, x_data, node_name, get_gate_type(gate_type, gate_to_index))

    for line_idx, line in enumerate(data):
        if 'AND(' in line or 'NAND(' in line or 'OR(' in line or 'NOR(' in line \
                or 'NOT(' in line or 'XOR(' in line:
            node_name = line.split('=')[0].replace(' ', '')
            gate_type = line.split('=')[-1].split('(')[0].replace(' ', '')
            src_list = line.split('(')[-1].split(')')[0].replace(' ', '').split(',')
            dst_idx = name2idx[node_name]
            for src_node in src_list:
                src_node_idx = name2idx[src_node]
                edge_index_data.append([src_node_idx, dst_idx])

    fanout_list = []
    fanin_list = []
    bfs_q = []
    x_data_level = [-1] * len(x_data)
    max_level = 0
    for idx, x_data_info in enumerate(x_data):
        fanout_list.append([])
        fanin_list.append([])
        if x_data_info[1] == 0:
            bfs_q.append(idx)
            x_data_level[idx] = 0
    for edge in edge_index_data:
        fanout_list[edge[0]].append(edge[1])
        fanin_list[edge[1]].append(edge[0])
    while len(bfs_q) > 0:
        idx = bfs_q[-1]
        bfs_q.pop()
        tmp_level = x_data_level[idx] + 1
        for next_node in fanout_list[idx]:
            if x_data_level[next_node] < tmp_level:
                x_data_level[next_node] = tmp_level
                bfs_q.insert(0, next_node)
                if x_data_level[next_node] > max_level:
                    max_level = x_data_level[next_node]
    level_list = []
    for level in range(max_level+1):
        level_list.append([])
    if -1 in x_data_level:
        print('Wrong')
        raise
    else:
        if max_level == 0:
            level_list = [[]]
        else:
            for idx in range(len(x_data)):
                x_data[idx].append(x_data_level[idx])
                level_list[x_data_level[idx]].append(idx)
    return x_data, edge_index_data, level_list, fanin_list, fanout_list

def main():
    
    bench_folder = './bench/*.bench'
    for file in glob.glob(bench_folder):
        if (platform.system() == 'Linux'):
            name = file.split("/")
            name = name[-1].split(".")
        else:
            name = file.split("\\")
            name = name[1].split(".")
        
        # if name[0] != 'b01_C':
        #     continue

        print('[INFO] Converting Circuit: {}'.format(name[0]))
        verilog = './verilog/' + name[0] + '.v'
        convert_bench_verilog(name[0], file, verilog)


if __name__ == "__main__":
    # main()
    main()
