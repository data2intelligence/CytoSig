CellSig prediction model of cytokine signaling activity

Prerequisite:  
1, ridge_significance: https://github.com/data2intelligence/ridge_significance/releases    
You will need numpy, gsl, gcc to install this package. Please read its README.md for details.

2, pandas: You may install anaconda (https://www.anaconda.com) to include all required python packages.

Install:
python setup.py install

Test:
python -m unittest tests.prediction

Usage:
CellSig.py -i input_profile -o output_prefix -r random_count -a penalty_alpha -e generate_excel


1, input_profile: input matrix of biological profiles. Each column is a biological condition, and each row should be a human gene symbol
2, output_prefix: prefix of output files.


random_count: default: 1000
penalty_alpha: default: 10000
generate_excel: default 0