import glob
import platform

def convert_cnf(module_name, cnf_filename, verilog_filename):
    cnf_file = open(cnf_filename, 'r')
    cnf_file = cnf_file.readlines()

    clause_list = []

    # Parse cnf
    no_var = -1
    no_clause = -1
    for idx, line in enumerate(cnf_file):
        if idx == 0:
            line = line.replace('\n', '')
            line = line.split(' ')
            no_var = int(line[2])
            no_clause = int(line[3])
            print('[INFO] CNF: {}'.format(module_name))
            print('[INFO] #Variables: {:}, #Clause: {:}'.format(no_var, no_clause))
        else:
            line = line.replace('\n', '')
            line = line.split(' ')
            tmp_clause = []
            for ele in line:
                if ele == '0':
                    break
                tmp_clause.append(int(ele))
            clause_list.append(tmp_clause)
    
    # Output context
    v_file = open(verilog_filename, 'w')
    first_line = 'module ' + module_name + '( ';
    input_line = 'input '
    for idx in range(1, no_var+1, 1):
        PI_name = 'PI_' + str(idx); 
        first_line += PI_name + ', '
        input_line += PI_name;
        if idx != no_var:
            input_line += ', '
        else:
            input_line += '; '
    first_line += 'PO );'
    output_line = 'output PO; '
    v_file.write(first_line + '\n')
    v_file.write(input_line +' \n')
    v_file.write(output_line + '\n')

    for clause_idx, clause in enumerate(clause_list):
        clause_line = 'assign clause_' + str(clause_idx+1) + ' = '
        for ele_idx, ele in enumerate(clause):
            clause_line += '('
            if ele < 0:
                clause_line += '~'
            clause_line += 'PI_' + str(abs(ele))
            clause_line += ')'
            if ele_idx == len(clause) - 1:
                clause_line += '; '
            else:
                clause_line += ' | '
        v_file.write(clause_line + '\n')
    
    last_line = 'assign PO = '
    for clause_idx in range(1, no_clause+1, 1):
        last_line += 'clause_' + str(clause_idx)
        if clause_idx == no_clause:
            last_line += '; '
        else:
            last_line += ' & '
    v_file.write(last_line + '\n')
    v_file.write('endmodule \n')
    v_file.close()
            
if __name__ == '__main__':
    for file in glob.glob('./cnf/*.dimacs'):
        if platform.system() == 'Linux':
            name = file.split("/")
            name = name[-1].split(".")
        else:
            name = file.split("\\")
            name = name[1].split(".")
        circuit_name = ''
        for idx, name_ele in enumerate(name):
            if idx != len(name) - 1:
                circuit_name += name_ele
        circuit_name = circuit_name.replace('=', '_')
        verilog_filename = './verilog/' + circuit_name + '.v'
        convert_cnf(circuit_name, file, verilog_filename)
        print('[SUCCESS] Convert {} done'.format(name[0]))
