import unittest
import os, sys
import pathlib
import subprocess

fpath = pathlib.Path(__file__).parent.absolute()

output = os.path.join(fpath, 'output')

class TestPrediction(unittest.TestCase):    
    def test_bulk(self):
        cmd = ['CytoSig_run.py', '-i', os.path.join(fpath, 'GSE147507.diff.gz'), '-o', output, '-e', '1']
        
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.communicate()
        
        for title in ['Coef', 'StdErr', 'Zscore', 'Pvalue', 'xlsx']:
            flag = os.path.exists(output + '.' + title)
            
            if not flag:
                sys.stderr.write('Cannot find file %s\n' % (output + '.' + title))
            else:
                os.remove(output + '.' + title) # clear results for the next test
            
            self.assertTrue(flag)

if __name__ == '__main__': unittest.main()
