# MRIPreprocessor

This repository provides a simple pipeline to co-register different imaging modalities and skull strip them.

This package uses HD-BET (https://github.com/MIC-DKFZ/HD-BET) and ANTsPy (https://github.com/ANTsX/ANTsPy).

For example, this pipeline is designed for the BraTS dataset.

## To install the package:
```
pip install  git+https://github.com/ReubenDo/MRIPreprocessor#egg=MRIPreprocessor
```

## Example case:
Let's assume we have access to 4 imaging modalities (e.g. T1, T1c, T2, FLAIR) and we want to co-register and skull strip them using T1 as reference:
```
from MRIPreprocessor.mri_preprocessor import Preprocessor

# 4 Modalities to co-register using an affine transformation
# T1 is used as reference for the coregistration
ppr = Preprocessor({'T1':'./data/example_T1.nii.gz',
                    'T2':'./data/example_T2.nii.gz',
                    'T1c':'./data/example_T1c.nii.gz',
                    'FLAIR':'./data/example_FLAIR.nii.gz'},
                    output_folder = './data/output',
                    reference='T1')

ppr.run_pipeline()
```
The output folder will contain two folders nammed `coregistration` and `skullstripping` containing respectively the co-registered modalities and the skull-stripped and co-registered imaging modalities.

