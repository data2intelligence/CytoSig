#!/usr/bin/env python

import os
import sys
import getopt
import CytoSig
import pandas
import pathlib

fpath = pathlib.Path(__file__).parent.absolute()

def main():
    count_thres = 50
    alpha = 10000
    nrand = 1000
    flag_report = False
    
    inputfile = outputfile = response = None
    
    prompt_msg = 'Usage:\nCytoSig_run.py -i <input profiles> -o <output prefix> -r <randomization count, default: %d> -a <penalty alpha, default: %s> -e <generate excel report: 0|1, default: %d>\n' % (nrand, alpha, flag_report)
    
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hi:o:r:a:e:", [])
    
    except getopt.GetoptError:
        sys.stderr.write('Error input\n' + prompt_msg)
        sys.exit(2)
    
    if len(opts) == 0:
        sys.stderr.write('Please input some parameters or try: CytoSig_run.py -h\n')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-h':
            print(prompt_msg)
            sys.exit()
        
        elif opt in ("-i"):
            inputfile = arg
        
        elif opt in ("-o"):
            outputfile = arg
        
        elif opt in ("-r"):
            try:
                nrand = int(arg)
            except:
                sys.stderr.write('random count %s is not a valid integer number.\n' % arg)
                sys.exit(1)
            
            if nrand < 0:
                sys.stderr.write('random count %d < 0. Please input a number >= 0\n' % nrand)
                sys.exit(1)
    
        elif opt in ("-a"):
            try:
                alpha = float(arg)
            except:
                sys.stderr.write('alpha %s is not a valid float number.\n' % arg)
                sys.exit(1)
            
            if alpha < 0:
                sys.stderr.write('alpha %s < 0. Please input a number >= 0\n' % alpha)
                sys.exit(1)
            
        elif opt in ("-e"):
            flag_report = (int(arg) != False)
    
    if inputfile is None:
        sys.stderr.write('Please provide a input file\n')
        sys.exit(1)
    
    elif not os.path.exists(inputfile):
        sys.stderr.write('Cannot find input file %s\n' % inputfile)
        sys.exit(1)
    
    if outputfile is None:
        outputfile = inputfile + '.CytoSig_output'
        sys.stderr.write('No output file input. Automatically generate one as %s\n' % outputfile)
    
    ###############################################################
    # read input
    
    try:
        file_type = inputfile.split('.').pop().lower()
        
        if file_type in ['xls', 'xlsx']:
            response = pandas.read_excel(inputfile, index_col=0)
        else:
            response = pandas.read_csv(inputfile, sep='\t', index_col=0)
    
    except:
        sys.stderr.write('Fail to open input file %s\n' % inputfile)
        sys.exit(1)
    
    if response.shape[1] == 0:
        sys.stderr.write('Input file %s has zero column.\n' % inputfile)
        sys.exit(1)
    
    signature = pandas.read_csv(os.path.join(fpath, 'signature.centroid'), sep='\t', index_col=0)
    
    ###############################################################
    # run regression
    
    fields = ['Coef', 'StdErr', 'Zscore', 'Pvalue']
    
    try:
        result = CytoSig.ridge_significance_test(signature, response, alpha, 'two-sided', nrand, count_thres)
    except:
        sys.stderr.write('Regression failure. Please contact author to trouble shoot\n')
        sys.exit(1)
    
    assert len(result) == len(fields)
    
    for i, title in enumerate(fields):
        result[i].to_csv(outputfile + '.' + title, sep='\t', index_label=False)
    
    
    if flag_report:
        
        if response.shape[1] > count_thres:
            sys.stderr.write('Will not generate report when variable count %d is larger than %d\n' % (response.shape[1], count_thres))
            sys.exit(0)
        
        writer = pandas.ExcelWriter(outputfile + '.xlsx', engine='xlsxwriter')
        
        for title in result[0]:
            merge = []
            
            for result_sub in result: merge.append(result_sub[title])
            
            merge = pandas.concat(merge, axis=1, join='inner')
            merge.columns = fields
            merge.sort_values(fields[2], inplace=True, ascending=False)
            merge.to_excel(writer, sheet_name=title, index_label='Signal')
        
        
        format_align = writer.book.add_format({'align': 'center'})
        format_number = writer.book.add_format({'num_format': '#,##0.000', 'align': 'center'})
        
        for worksheet in writer.sheets:
            worksheet = writer.sheets[worksheet]
            
            worksheet.set_column(1, len(fields), 10, format_align)
            worksheet.set_column(1, len(fields)-1, 10, format_number)
            worksheet.set_zoom(150)
        
        writer.close()
        
    

if __name__ == '__main__': main()
