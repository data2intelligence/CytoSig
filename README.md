CellSig prediction model of cytokine signaling activity

Prerequisite:  
1, ridge_significance: https://github.com/data2intelligence/ridge_significance  
Please read its README.md and run test to make sure the successful installation.  

2, pandas >= 1.1.4: You may install anaconda (https://www.anaconda.com) to include all required python packages.  
3, xlrd >= 1.2.0: pip install --upgrade xlrd  


Install:
python setup.py install

Test:
python -m unittest tests.prediction

Usage:  
CellSig.py -i input_profile -o output_prefix -r random_count -a penalty_alpha -e generate_excel

1, input_profile: input matrix of biological profiles. Each column is a biological condition, and each row should be a human gene symbol. Please see "tests/GSE147507.diff.gz" as an example.  

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
In the directory of README.md, please type: CellSig.py -i tests/GSE147507.diff.gz -o tests/output_test -e 1  
Then, open "tests/output_test.xlsx" to view results  
