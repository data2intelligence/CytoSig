CytoSig prediction model of cytokine signaling activity

**Prerequisite**:  
1, ridge_significance: https://github.com/data2intelligence/ridge_significance  
Please read its README.md and run test to make sure the successful installation.  

2, pandas >= 1.1.4: You may install anaconda (https://www.anaconda.com) to include all required python packages.  
3, xlsxwriter >= 1.3.7: pip install --upgrade xlsxwriter  


**Install**:
python setup.py install

**Test**:
python -m unittest tests.prediction

Please see **tests/prediction.py** for examples of two usages explained below.  

**Usage 1, through command line**:  

CytoSig_run.py -i input_profile -o output_prefix -r random_count -a penalty_alpha -e generate_excel

1, input_profile: input matrix of biological profiles. Each column is a biological condition, and each row should be a human gene symbol. Please see "tests/GSE147507.diff.gz" as an example.  
The expression values, from either RNASeq or MicroArray, should be transformed by log2(x+1). x could be FPKM, RPKM, or TPM for RNASeq. For single-cell RNASeq data, we used log2(TPM/10 + 1). We also recommend quantile-normalization across conditions. Some software package, such as RMA or DESeq, will automatically include all normalizations. We recommend input differential profiles between the two conditions. If data is from a sample collection without pairs, please mean-centralize the value of each gene across all samples.

2, output_prefix: prefix of output files. Each column is a biological condition, and each row is a cytokine name  
    output_prefix.Coef: regression coefficients  
    output_prefix.StdErr: standard error  
    output_prefix.Zscore: Coef/StdErr  
    output_prefix.Pvalue: two-sided test p-value of Zscore, from permutation test if random_count > 0 or student t-test if random_count = 0  
    output_prefix.xlsx: only exist if generate_excel = 1. A excel summary of results, with each input condition as one tab  

3, random_count: number of randomizations in the permutation test, with a default value 1000. If value is 0, the program will use student t-test.    

4, penalty_alpha: penalty weight in the ridge regression, with a default value 10000.  

5, generate_excel: whether generate excel output. The value could be 1 (Yes) or 0 (No) with a default value 0. This option is only effective when the input condition count is less than 50.

Example:
In the directory of README.md, please type: CytoSig_run.py -i tests/GSE147507.diff.gz -o tests/output_test -e 1  
Then, open "tests/output_test.xlsx" to view results  


**Usage 2, through Python function inside your customized code**:  
Input:  
Y: the expression matrix of your samples in pandas data frame. Each column name is a sample ID. Each row name is a human gene symbol.  
  
Output: four pandas data frames  
beta: regression coefficients  
std: standard errors of coefficients  
zscore: beta/std  
pvalue: statistical significance  

Then, use the following code snippet in your program:  

import os, sys, pandas, CytoSig  
signature = os.path.join(sys.prefix, 'bin', 'signature.centroid') # load cytokine response signature installed in your python system path    
signature = pandas.read_csv(signature, sep='\t', index_col=0)  
beta, std, zscore, pvalue = CytoSig.ridge_significance_test(signature, Y, alpha=1E4, alternative="two-sided", nrand=1000, cnt_thres=10, flag_normalize=True, verbose = True)  
