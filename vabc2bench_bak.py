from os import name, replace
import sys
import re
import glob
import platform
from union_find import UnionFind

name2idx = {}
allGateVec = []

class Gate:
    def __init__(self, gate_name):
        self.gate_name = gate_name
        self.gate_type = ''
        self.pre_list = []
        self.next_list = []
        self.is_po = False
        self.enable = False

def new_gate(gate_name):
    gate_inst = Gate(gate_name)
    allGateVec.append(gate_inst)

def find_keys_list(name_list, find_keys):
    res = []
    for idx, ele in enumerate(name_list):
        if ele == find_keys[0]:
            res.append(name_list[idx+1])
            find_keys.pop(0)
            if len(find_keys) == 0:
                break
    return res

def back_non_buff(idx):
    res = idx
    gate = allGateVec[res]
    while gate.gate_type == 'BUF':
        res = gate.pre_list[0]
        gate = allGateVec[res]
    return res
    
def convert_verilog_bench(verilog_file, bench_file):
    v_file = open(verilog_file, 'r')
    v_lineList = v_file.readlines()
    proc_v_lineList = []
    b_file = open(bench_file, 'w')
    node_cnt = 0
    line_idx = 0

    name2idx.clear()
    allGateVec.clear()

    # Process content
    new_gate('1\'h0')
    name2idx['1\'h0'] = len(name2idx)
    node_cnt += 1
    new_gate('1\'h1')
    name2idx['1\'h1'] = len(name2idx)
    node_cnt += 1
    while line_idx < len(v_lineList):
        line = v_lineList[line_idx]
        if 'wire' in line or 'output' in line or 'input' in line:
            line = line.lstrip().rstrip().replace('\n', '').replace(';', '')
            text = line.split(' ')[-1]
            new_gate(text)
            name2idx[text] = len(name2idx)
            if 'input' in line:
                allGateVec[name2idx[text]].gate_type = 'INPUT'
            if 'output' in line:
                allGateVec[name2idx[text]].is_po = True
            proc_v_lineList.append(line)
            node_cnt += 1
        elif 'NOT' in line or 'AND' in line or 'BUF' in line or 'OR' in line:
            new_line = ''
            while not ';' in line:
                line = line.lstrip().rstrip().replace('\n', '')
                new_line += line
                line_idx += 1
                line = v_lineList[line_idx]
            line = line.lstrip().rstrip().replace('\n', '')
            new_line += line
            proc_v_lineList.append(new_line)
        elif 'assign' in line:
            line = line.lstrip().rstrip().replace('\n', '').replace(';', '')
            proc_v_lineList.append(line)
        line_idx += 1

    for line in proc_v_lineList:
        if 'NOT' in line or 'AND' in line or 'BUF' in line or 'OR' in line:
            line = line.replace(',', '').replace(';', '')
            gate_type = line.split(' ')[0]
            name_list_tmp = line.split('(')
            name_list = []
            for tmp_line in name_list_tmp:
                name_list += tmp_line.split(')')
            if gate_type == 'NOT' or gate_type == 'BUF':
                res = find_keys_list(name_list, ['.A', '.Y'])
                src_name = res[0]
                dst_name = res[1]
                allGateVec[name2idx[dst_name]].gate_type = gate_type
                allGateVec[name2idx[dst_name]].pre_list = [name2idx[src_name]]
            elif gate_type == 'AND' or gate_type == 'OR':
                res = find_keys_list(name_list, ['.A', '.B', '.Y'])
                src_name_1 = res[0]
                src_name_2 = res[1]
                dst_name = res[2]
                allGateVec[name2idx[dst_name]].gate_type = gate_type
                allGateVec[name2idx[dst_name]].pre_list = [name2idx[src_name_1], name2idx[src_name_2]]
        elif 'assign' in line:
            name_list = line.split(' ')
            dst_name = name_list[1]
            src_name = name_list[3]
            allGateVec[name2idx[dst_name]].gate_type = 'BUF'
            allGateVec[name2idx[dst_name]].pre_list = [name2idx[src_name]]

    # Find the non_buff gate
    for gate in allGateVec:
        if gate.gate_type != 'BUF':
            for idx, pre_idx in enumerate(gate.pre_list):
                gate.pre_list[idx] = back_non_buff(pre_idx)
    for idx, gate in enumerate(allGateVec):
        if gate.is_po and gate.gate_type == 'BUF':
            non_buf_idx = back_non_buff(idx)
            gate.is_po = False
            if allGateVec[non_buf_idx].gate_type != 'INPUT' and non_buf_idx !=0 and non_buf_idx!=1:
                allGateVec[non_buf_idx].is_po = True
    
    for idx, gate in enumerate(allGateVec):
        for pre_idx in gate.pre_list:
            allGateVec[pre_idx].next_list.append(idx)
    
    for gate in allGateVec:
        if gate.gate_type == 'INPUT':
            b_file.write('INPUT({:})\n'.format(gate.gate_name))
    b_file.write('\n')

    for gate in allGateVec:
        if gate.is_po:
            is_vaild = True
            for pre_idx in gate.pre_list:
                if pre_idx == 0 or pre_idx == 1:
                    is_vaild = False
            if is_vaild:
                b_file.write('OUTPUT({:})\n'.format(gate.gate_name))
    b_file.write('\n')

    no_gate = 0
    for gate in allGateVec:
        if gate.gate_type == 'AND' or gate.gate_type == 'OR' or gate.gate_type == 'NOT' or gate.is_po:
            line = gate.gate_name + ' = ' + gate.gate_type + '('
            for pre_idx in gate.pre_list:
                if pre_idx == gate.pre_list[-1]:
                    line += allGateVec[pre_idx].gate_name + ')\n'
                else:
                    line += allGateVec[pre_idx].gate_name + ', '
            b_file.write(line)
            no_gate += 1
    b_file.write('\n')

    b_file.close()
    v_file.close()
    print("[SUCCESS] Convert {:} Done, with {:} nodes".format(verilog_file, no_gate))


def main():
    # verilog_folder_1 = '../../EPFL_benchmarks/arithmetic/*.v'
    # verilog_folder_2 = '../../EPFL_benchmarks/random_control/*.v'
    # bench_folder = '../../EPFL_benchmarks/bench/'
    
    verilog_folder = './syn_verilog/*.v'
    for file in glob.glob(verilog_folder):
        if (platform.system() == 'Linux'):
            name = file.split("/")
            name = name[-1].split(".")
        else:
            name = file.split("\\")
            name = name[1].split(".")

        if name[0] != 'b01_C':
            continue
        
        print('[INFO] Converting Circuit: {}'.format(name[0]))
        bench_file = './syn_bench/' + name[0] + '.bench'
        convert_verilog_bench(file, bench_file)


if __name__ == "__main__":
    # main()
    main()
