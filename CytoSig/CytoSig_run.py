#!/usr/bin/env python

import os
import sys
import getopt
import CytoSig
import pandas
import pathlib
import numpy

fpath = pathlib.Path(__file__).parent.absolute()



def main():
    count_thres = 50
    alpha = 10000
    nrand = 1000
    min_count = 1000
    zero_ratio = 0.95
    
    flag_report = False
    flag_expand = False
    
    inputfile = outputfile = response = None
    
    prompt_msg = 'Usage:\nCytoSig_run.py -i <input profiles> -o <output prefix> -r <randomization count, default: %d> -a <penalty alpha, default: %s> -e <generate excel report: 0|1, default: %d> -s <use an expanded response signature: 0|1, default: %d> -c <minimum read count if input cellranger mtx, default: %d> -z <maximum zero dropout ratio, default: %s>\n' % (nrand, alpha, flag_report, flag_expand, min_count, zero_ratio)
    
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hi:o:r:a:e:s:c:z:", [])
    
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
            
        elif opt in ("-s"):
            flag_expand = (int(arg) != False)
            
        elif opt in ("-c"):
            min_count = int(arg)
        
        elif opt in ("-z"):
            try:
                zero_ratio = float(arg)
            except:
                sys.stderr.write('zero_ratio %s is not a valid float number.\n' % arg)
                sys.exit(1)
            
            if zero_ratio <= 0:
                sys.stderr.write('zero_ratio %s <= 0. Please input a number > 0\n' % zero_ratio)
                sys.exit(1)
    
    if inputfile is None:
        sys.stderr.write('Please provide a input file\n')
        sys.exit(1)
    
    
    if outputfile is None:
        outputfile = inputfile + '.CytoSig_output'
        sys.stderr.write('No output file input. Automatically generate one as %s\n' % outputfile)
    
    ###############################################################
    # read input
    try:
        if os.path.isdir(inputfile) or not os.path.exists(inputfile):
            # two possibilities: 1, mtx file, 2, true not exist
            response = CytoSig.analyze_cellranger_lst(inputfile, min_count)
        
            if response is None:
                sys.stderr.write('Cannot find input file %s\n' % inputfile)
                sys.exit(1)
    
            response = response.loc[(response == 0).mean(axis=1) < zero_ratio]
            response = response.loc[:, response.sum() >= min_count]
            
            size_factor = 1E5/response.sum()
            response *= size_factor
            response = numpy.log2(response + 1)
            
            # always centralize on all cells, instead of included cells
            background = response.mean(axis=1)
            response = response.subtract(background, axis=0)
            
            response = response.sparse.to_dense()
            print(response.shape, 'created from cell ranger outputs')
            
            # save the merged matrix in pickle format
            response.to_pickle(outputfile + '.input.pickle.gz', compression='gzip')
        
        else:
            fields = inputfile.split('.')
            file_type = fields.pop().lower()
            
            if file_type in ['xls', 'xlsx']:
                response = pandas.read_excel(inputfile, index_col=0)
            
            elif file_type in ['pickle', 'pkl'] or (file_type == 'gz' and fields.pop().lower() in ['pickle', 'pkl']):
                response = pandas.read_pickle(inputfile)
            
            else:
                response = pandas.read_csv(inputfile, sep='\t', index_col=0)
        
    except:
        sys.stderr.write('Fail to open input file %s\n' % inputfile)
        sys.exit(1)
    
    if response.shape[1] == 0:
        sys.stderr.write('Input file %s has zero column.\n' % inputfile)
        sys.exit(1)
    
    
    signature = os.path.join(fpath, 'signature.centroid')
    if flag_expand: signature += '.expand'
    
    signature = pandas.read_csv(signature, sep='\t', index_col=0)
    
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
