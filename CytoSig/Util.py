import pandas, numpy, sys, os
import ridge_significance

from glob import glob
from scipy import io


def dataframe_to_array(x, dtype = None):
    """ convert data frame to numpy matrix in C order, in case numpy and gsl use different matrix order """
    
    x = x.to_numpy(dtype=dtype)
    if x.flags.f_contiguous: x = numpy.array(x, order='C')
    return x


def array_to_dataframe(x, row_names, col_names):
    if type(x) == list:
        for i in range(len(x)): x[i] = pandas.DataFrame(x[i], index=row_names, columns=col_names)
    else:
        x = pandas.DataFrame(x, index=row_names, columns=col_names)
    
    return x


def ridge_significance_test(X, Y, alpha, alternative="two-sided", nrand=1000, cnt_thres=10, flag_normalize=True, flag_const=False, verbose = True):
    # convert X from series to data frame if necessary
    if type(X) == pandas.Series: X = pandas.DataFrame(X)
    
    # if X Y index doesn't align
    if X.index.shape[0] != Y.index.shape[0] or sum(X.index != Y.index) > 0:
        common = Y.index.intersection(X.index)
        
        if common.shape[0] < cnt_thres:
            sys.stderr.write('X dimension %d < %s\n' % (common.shape[0], cnt_thres))
            sys.exit(1)
        
        Y, X = Y.loc[common], X.loc[common]
    
    if flag_normalize:
        # normalize to zero mean and unit variation
        X = (X - X.mean())/X.std()
        Y = (Y - Y.mean())/Y.std()
    
    if flag_const: X['const'] = 1
    
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



def load_cell_ranger(genes, features, barcodes, matrix, min_count):
    # when use this function, the previous function should make sure either genes or features exists
    if genes is not None:
        genes = pandas.read_csv(genes, sep='\t', header=None).iloc[:, -1]
    else:
        features = pandas.read_csv(features, sep='\t', header=None)
        genes = features.loc[features.iloc[:, -1] == 'Gene Expression', 1]
    
    matrix = io.mmread(matrix)
    matrix = pandas.DataFrame.sparse.from_spmatrix(matrix)
    
    # assume first column of barcodes
    barcodes = pandas.read_csv(barcodes, sep='\t', header=None).iloc[:,0]    
        
    assert matrix.shape[0] == genes.shape[0]
    assert matrix.shape[1] == barcodes.shape[0]
    
    matrix.index = genes
    matrix.columns = barcodes
    assert matrix.columns.value_counts().max() == 1
    
    # jump bad cells, if any
    barcode_cnt = matrix.sum()
    if barcode_cnt.min() < min_count:
        matrix = matrix.loc[:, matrix.sum() >= min_count]

    # jump ambiguous genes, if any
    cnt_map = matrix.index.value_counts()
    if cnt_map.max() > 1:
        matrix = matrix.loc[cnt_map.loc[matrix.index] == 1]
    
    assert matrix.index.value_counts().max() == 1
    
    # remove empty genes
    matrix = matrix.loc[(matrix == 0).mean(axis=1) < 1]
    
    return matrix


def analyze_cellranger_lst(inputfile, min_count):
    results = []
    
    # first split file path and file list
    fpath = os.path.dirname(inputfile)
    input_lst = os.path.basename(inputfile).split(',')
    
    fields = ['barcodes.tsv', 'genes.tsv', 'features.tsv', 'matrix.mtx']
    
    for condi in input_lst:
        fprefix = os.path.join(fpath, condi)
        
        flag_err = False
        vmap = {}
        
        for title in fields:
            files = glob(fprefix + title + '*')
            
            if len(files) > 1:
                sys.stderr.write('Ambiguous %s file for %s.\n' % (title, fprefix))
                flag_err = True
                continue
            
            if len(files) == 0:
                if title in ['barcodes.tsv', 'matrix.mtx']:
                    sys.stderr.write('Cannot find %s file for %s.\n' % (title, fprefix))
                    flag_err = True
                continue
            
            # len(files) == 1
            vmap[title] = files.pop()
        
        # find genes
        genes = vmap.get('genes.tsv')
        features = vmap.get('features.tsv')
        
        if genes is None and features is None:
            sys.stderr.write('Cannot find gene file for %s.\n' % fprefix)
            flag_err = True
        
        if flag_err: continue
        
        mat = load_cell_ranger(genes, features, vmap['barcodes.tsv'], vmap['matrix.mtx'], min_count)
        
        # multiple files, put file name as conditions
        if len(condi) > 0 and len(input_lst) > 0:
            mat.columns = condi + '.' + mat.columns
        
        results.append(mat)
    
    if len(results) == 0:
        sys.stderr.write('No matrix found.\n')
        return None
    
    return pandas.concat(results, axis=1, join='inner')
