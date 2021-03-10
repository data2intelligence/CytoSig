import os, setuptools
from setuptools.command.install import install
from Expression_Database.util import script_path

with open("README.md", "r") as fh:
    long_description = fh.read()


class PostInstallCommand(install):
    def run(self):
        os.system('chmod +x ' + os.path.join(script_path, '*.R'))
        install.run(self)


setuptools.setup(
    name="Expression_Database-NCI",
    version="0.0.1",
    author="Peng Jiang",
    author_email="peng.jiang@nih.gov",
    description="Toolkits for NCBI GEO and ArrayExpress",
    
    long_description=long_description,
    long_description_content_type="text/markdown",
    
    url="https://github.com/pypa/Expression_Database",
    
    packages=setuptools.find_packages(),
    
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    
    python_requires = '>=3.6',
    
    install_requires=[
        'GEOparse',
        'Orange3',
        'bioservices',
        #'Orange-Bioinformatics',
    ],
    
    data_files=[
        ('bin', [
            os.path.join('scripts', 'rma_oligo.R'),
            os.path.join('scripts', 'rma_affy.R'),
            os.path.join('scripts', 'Rdata_Matrix.R'),
            ]),        
    ],
    
    cmdclass={
        'install': PostInstallCommand,
    },
)
