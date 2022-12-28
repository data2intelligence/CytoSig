import unittest, os, sys, pandas, pathlib, subprocess, CytoSig

fpath = pathlib.Path(__file__).parent.absolute()

output = os.path.join(fpath, 'output')

class TestPrediction(unittest.TestCase):
    def max_difference(self, A, B):
        self.assertTrue(A.shape == B.shape)
        self.assertTrue((A-B).abs().max().max() < 1e-8)

    def test_bulk(self):
        Y = os.path.join(fpath, 'GSE147507.diff.gz')
        
        # run command line as usage 1
        cmd = ['CytoSig_run.py', '-i', Y, '-o', output, '-e', '1']
        
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out,err = p.communicate()
        out,err = out.decode().strip(), err.decode().strip()
        
        print('Output:\n', out)
        if len(err) > 0: print('Error:\n', err)
        
        result_map = {}
        
        for title in ['Coef', 'StdErr', 'Zscore', 'Pvalue', 'xlsx']:
            flag = os.path.exists(output + '.' + title)
            
            if not flag:
                sys.stderr.write('Cannot find file %s\n' % (output + '.' + title))
            else:
                if title not in ['xlsx']:
                    result_map[title] = pandas.read_csv(output + '.' + title, sep='\t', index_col=0)
                
                os.remove(output + '.' + title) # clear results for the next test
            
            self.assertTrue(flag)
        
        # run python functions as usage 2
        signature = os.path.join(sys.prefix, 'bin', 'signature.centroid') # load cytokine response signature installed in your python system path    
        signature = pandas.read_csv(signature, sep='\t', index_col=0)
        Y = pandas.read_csv(Y, sep='\t', index_col=0)
        
        try:
            beta, std, zscore, pvalue = CytoSig.ridge_significance_test(signature, Y, alpha=1E4, alternative="two-sided", nrand=1000, cnt_thres=10, flag_normalize=True, verbose = True)
        except Exception as err:
            print('Error:', err)
            self.assertTrue(False)
            
        # make sure the two usages get the same result        
        self.max_difference(result_map['Coef'], beta)
        self.max_difference(result_map['StdErr'], std)
        self.max_difference(result_map['Zscore'], zscore)
        self.max_difference(result_map['Pvalue'], pvalue)

if __name__ == '__main__': unittest.main()
