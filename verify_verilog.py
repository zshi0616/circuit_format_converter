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

def NOT(input_value):
    if input_value == 1:
        return 0
    else:
        return 1

def proc_inv(ele, name2idx, y):
    if ele[0] == '~':
        gate_name = ele[1:]
    else:
        gate_name = ele
    return y[name2idx[gate_name]]

def dec2list(dec_num, length):
    tmp_str = bin(dec_num)[2:]
    while len(tmp_str) < length:
        tmp_str = '0' + tmp_str
    res = []
    for ele in tmp_str:
        res.append(int(ele))
    return res

def simulation(circuit_name, pattern):
    v_file = './abc_verilog/'+circuit_name+'.v'
    v_file = open(v_file, 'r').readlines()
    name2idx = {}
    y = []
    max_pi_cnt = 0

    word = pp.Word(pp.srange("[a-zA-Z0-9_]"))
    op = pp.oneOf('& | ^')
    sct_op = pp.oneOf('( )')
    not_op = pp.oneOf('~')
    unit_word = pp.ZeroOrMore(not_op) + pp.ZeroOrMore(sct_op) + pp.ZeroOrMore(not_op) + word('src1') + pp.ZeroOrMore(sct_op) + op('op')

    for idx, line in enumerate(v_file):
        if 'module' in line:
            line = line.split('(')[-1]
            line = line.split(',')
            for ele in line:
                ele = ele.replace(' ', '')
                if 'PI' in ele:
                    pi_idx = int(ele.replace('PI_', ''))
                    if pi_idx > max_pi_cnt:
                        max_pi_cnt = pi_idx
            name2idx, y = new_node('PO', name2idx, -1, y)
            for pi_idx in range(1, max_pi_cnt+1, 1):
                name2idx, y = new_node('PI_'+str(pi_idx), name2idx, pattern[pi_idx-1], y)
        elif 'endmodule' in line:
            break
        elif 'wire' in line:
            continue
        elif 'input' in line:
            continue
        elif 'output' in line:
            continue
        elif '(*' in line:
            continue
        elif 'assign' in line:
            line = line.replace(' ;', '')
            line = line.replace(';', '')
            line = line.replace('\n', '')
            line = line.lstrip().rstrip()
            test = line.split(" ")
            # assign a = ~b
            if len(test) == 4:
                if test[3][0] == '~':
                    src_name = test[3][1:]
                    dst_name = test[1]
                    src_idx = name2idx[src_name]
                    name2idx, y = new_node(dst_name, name2idx, NOT(y[src_idx]), y)
            # assign a = c ? b : d
            elif '?' in line:
                dst_name = test[1]
                con_val = proc_inv(test[3], name2idx, y)
                if con_val:
                    res = proc_inv(test[5], name2idx, y)
                else:
                    res = proc_inv(test[7], name2idx, y)
                name2idx, y = new_node(dst_name, name2idx, res, y)
            # assign a b c
            else:
                equ1 = 'assign'+word('dst')+'='+\
                        pp.ZeroOrMore(not_op('not_all')) + pp.ZeroOrMore(sct_op('left')) + \
                        unit_word + \
                        pp.ZeroOrMore(not_op) + pp.ZeroOrMore(sct_op) + pp.ZeroOrMore(not_op) + word('src2') + pp.ZeroOrMore(sct_op) + \
                        pp.ZeroOrMore(sct_op('right'))
                pp_res = equ1.parseString(line)
                eval_equ = ''
                dst_name = pp_res['dst']
                start_flag = False
                for ele in pp_res:
                    if start_flag: 
                        if  ele == '~':
                            eval_equ += 'not '
                        elif ele == '&':
                            eval_equ += 'and '
                        elif ele == '|':
                            eval_equ += 'or '
                        elif ele == '^':
                            eval_equ += '^ '
                        elif ele == '(' or ele == ')':
                            eval_equ += ele
                        else:
                            if y[name2idx[ele]] == 1:
                                eval_equ += ' True '
                            else:
                                eval_equ += ' False '
                    else:
                        if ele == '=':
                            start_flag = True

                if eval(eval_equ):
                    name2idx, y = new_node(dst_name, name2idx, 1, y)
                else:
                    name2idx, y = new_node(dst_name, name2idx, 0, y)

    PO_res = y[name2idx['PO']]
    return PO_res        
    
                          
if __name__=='__main__':
    prj_path = os.path.dirname(os.path.realpath('__file__'))
    print(prj_path)

    for file in glob.glob('./abc_verilog/*.v'):
        name = file.split('/')
        name = name[-1].split('.')
        circuit_name = name[0]

        print('[INFO] Checking {}'.format(circuit_name))

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