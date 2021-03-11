#!/usr/bin/env python

import os
import sys
import getopt
import numpy
import pandas
import pathlib
import ridge_significance

fpath = pathlib.Path(__file__).parent.absolute()


def dataframe_to_array(x, dtype = None):
    x = x.to_numpy(dtype=dtype)
    if x.flags.f_contiguous: x = numpy.array(x, order='C')
    return x


def array_to_dataframe(x, row_names, col_names):
    if type(x) == list:
        for i in range(len(x)): x[i] = pandas.DataFrame(x[i], index=row_names, columns=col_names)
    else:
        x = pandas.DataFrame(x, index=row_names, columns=col_names)
    
    return x


def ridge_significance_test(X, Y, alpha, alternative, nrand, cnt_thres):
    verbose = True
    
    # if X Y index doesn't align
    if X.index.shape[0] != Y.index.shape[0] or sum(X.index != Y.index) > 0:
        common = Y.index.intersection(X.index)
        
        if common.shape[0] < cnt_thres:
            sys.stderr.write('X dimension %d < %s\n' % (common.shape[0], cnt_thres))
            sys.exit(1)
        
        Y, X = Y.loc[common], X.loc[common]
    
    # normalize to zero mean and unit variation
    X = (X - X.mean())/X.std()
    Y = (Y - Y.mean())/Y.std()
    
    # decorate the results later
    X_columns = X.columns
    Y_columns = Y.columns
    
    # turn pandas data frame in column major order to numpy 2d array in row major order (compatible with GSL)
    X = dataframe_to_array(X)
    Y = dataframe_to_array(Y)
    
    # start computation by different alpha formats (arrays or single values)
    if type(alpha) in [list, numpy.ndarray]:
        # if a series of alpha values are considered
        N_alpha = len(alpha)
         
        result = [None] * N_alpha
            
        for i in range(N_alpha):
            result[i] = ridge_significance.fit(X,Y, alpha[i], alternative, nrand, verbose)
            result[i] = array_to_dataframe(result[i], X_columns, Y_columns)
    else:
        # if only one alpha value
        result = ridge_significance.fit(X,Y, alpha, alternative, nrand, verbose)
        result = array_to_dataframe(result, X_columns, Y_columns)

    return result


def main():
    count_thres = 50
    alpha = 10000
    nrand = 1000
    flag_report = False
    
    inputfile = outputfile = response = None
    
    prompt_msg = 'Usage:\nCellSig.py -i <input profiles> -o <output prefix> -r <randomization count, default: %d> -a <penalty alpha, default: %s> -e <generate excel report: 0|1, default: %d>\n' % (nrand, alpha, flag_report)
    
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hi:o:r:a:e:", [])
    
    except getopt.GetoptError:
        sys.stderr.write('Error input\n' + prompt_msg)
        sys.exit(2)
    
    if len(opts) == 0:
        sys.stderr.write('Please input some parameters or try: CellSig.py -h\n')
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
        outputfile = inputfile + '.CellSig_output'
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
        result = ridge_significance_test(signature, response, alpha, 'two-sided', nrand, count_thres)
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
