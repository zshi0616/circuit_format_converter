import math
import numpy as np
import random
import argparse
import glob
import platform
import os
import sys
import pyparsing as pp

def read_assignment(circuit_name):
    assignemnt_file = './cnf/'+circuit_name+'.solution'
    assignement = open(assignemnt_file, 'r').readlines()[0]
    assignement = assignement.rstrip().split(' ')
    pattern = []
    for ele in assignement:
        pattern.append(int(ele))
    return pattern

def new_node(node_name, name2idx, new_y, y):
    name2idx[node_name] = len(name2idx)
    y.append(new_y)
    return name2idx, y

def dec2list(dec_num, length):
    tmp_str = bin(dec_num)[2:]
    while len(tmp_str) < length:
        tmp_str = '0' + tmp_str
    res = []
    for ele in tmp_str:
        res.append(int(ele))
    return res

def logic(op, src_list, name2idx, y):
    src_val = []
    for ele in src_list:
        src_val.append(y[name2idx[ele]])
    if op == 'NOT':
        if src_val[0] == 1:
            return 0
        else:
            return 1
    elif op == 'AND':
        res = 1
        for ele in src_val:
            if ele == 0:
                res = 0
                break
        return res
    elif op == 'OR':
        res = 0
        for ele in src_val:
            if ele == 1:
                res = 1
                break
        return res
    elif op == 'XOR':
        if src_val[0] == 1 and src_val[1] == 1:
            return 0
        elif src_val[0] == 0 and src_val[1] == 0:
            return 0
        else:
            return 1
    else:
        print('Unknown')
        raise

def simulation(circuit_name, pattern):
    bench_file = './bench/'+circuit_name+'.bench'
    bench_file = open(bench_file, 'r').readlines()
    name2idx = {}
    y = []
    max_pi_cnt = 0

    for idx, line in enumerate(bench_file):
        if 'INPUT' in line:
            max_pi_cnt += 1
        elif 'OUTPUT' in line:
            for pi_idx in range(1, max_pi_cnt+1, 1):
                name2idx, y = new_node('PI_'+str(pi_idx), name2idx, pattern[pi_idx-1], y)
        elif '=' in line:
            line = line.replace('\n', '')
            line.lstrip().rstrip()
            op = line.split('=')[-1].split('(')[0].replace(' ', '')
            dst_name = line.split('=')[0].replace(' ', '')
            src_list = line.split('(')[-1].replace(')', '').replace(' ', '')
            src_list = src_list.split(',')
            dst_val = logic(op, src_list, name2idx, y)
            name2idx, y = new_node(dst_name, name2idx, dst_val, y)

    PO_res = y[name2idx['PO']]
    return PO_res        
                          
if __name__=='__main__':
    prj_path = os.path.dirname(os.path.realpath('__file__'))
    print(prj_path)

    for file in glob.glob('./cnf/*.dimacs'):
        name = file.split('/')
        name = name[-1].split('.')
        circuit_name = name[0]

        if circuit_name[-1] == '1':
            pattern = read_assignment(circuit_name)
            res = simulation(circuit_name, pattern)
            if not res:
                print('[ERROR] Circuit {}'.format(circuit_name))
                raise
            print('[SUCCESS] Check {}'.format(circuit_name))
        # else:
        #     for pattern_num in range(0, 1024, 1):
        #         pattern = dec2list(pattern_num, 10)
        #         res = simulation(circuit_name, pattern)
        #         if res:
        #             print('[ERROR] Circuit {}'.format(circuit_name))
        #             raise
        #     print('[SUCCESS] Check {}'.format(circuit_name))


    print('[SUCCESS] Done')