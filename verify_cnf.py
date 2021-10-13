import math
import numpy as np
import random
import argparse
import glob
import platform
import os
import sys

def read_assignment(circuit_name):
    assignemnt_file = './cnf/'+circuit_name+'.solution'
    assignement = open(assignemnt_file, 'r').readlines()[0]
    assignement = assignement.rstrip().split(' ')
    pattern = []
    for ele in assignement:
        pattern.append(int(ele))
    return pattern

def simulation(circuit_name, pattern):
    cnf_file = './cnf/'+circuit_name+'.dimacs'
    cnf_file = open(cnf_file, 'r').readlines()
    for idx, line in enumerate(cnf_file):
        if idx == 0:
            line = line.replace('\n', '')
            line = line.split(' ')
            no_var = int(line[2])
            no_clause = int(line[3])
            print('[INFO] CNF: {}'.format(circuit_name))
            print('[INFO] #Variables: {:}, #Clause: {:}'.format(no_var, no_clause))
        else:
            line = line.replace('\n', '')
            line = line.split(' ')
            res = 0
            for ele in line:
                if ele == '0':
                    break
                var_idx = abs(int(ele)) - 1
                if int(ele) < 0:
                    res += int(pattern[var_idx] == 0)
                else:
                    res += int(pattern[var_idx] == 1)
                if res > 0:
                    break
            if res == 0:
                print('[ERROR] UNSAT circuit: {}'.format(circuit_name))
                raise
                          
if __name__=='__main__':
    prj_path = os.path.dirname(os.path.realpath('__file__'))
    print(prj_path)

    for file in glob.glob('./cnf/*.dimacs'):
        name = file.split('/')
        name = name[-1].split('.')
        circuit_name = name[0]

        if circuit_name[-1] == '1':
            pattern = read_assignment(circuit_name)
            simulation(circuit_name, pattern)
    print('[SUCCESS] Done')