import pandas, numpy, sys
import ridge_significance

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


def ridge_significance_test(X, Y, alpha, alternative="two-sided", nrand=1000, cnt_thres=10):
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
