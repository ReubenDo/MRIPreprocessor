# MRIPreprocessor

This repository provides a simple pipeline to co-register different imaging modalities and skull strip them.

This package uses HD-BET (https://github.com/MIC-DKFZ/HD-BET) and ANTsPy (https://github.com/ANTsX/ANTsPy).

For example, this pipeline is designed for the BraTS dataset.

## To install the package:
```
pip install  git+https://github.com/ReubenDo/MRIPreprocessor#egg=MRIPreprocessor
```

## Example case 1:
Let's assume we have access to 4 imaging modalities (e.g. T1, T1c, T2, FLAIR) and we want to:
- co-register the scans using T1 as reference
- in the MNI space (1x1x1 mm)
- skull strip the scans using T1 as reference
- crop the skull-stripped scans to remove the zero padding 

```python
from MRIPreprocessor.mri_preprocessor import Preprocessor

# 4 Modalities to co-register to MNI space using an affine transformation
# T1 is used as reference for the coregistration
# No labelmap is used 
ppr = Preprocessor({'T1':'./data/example_T1.nii.gz',
                    'T2':'./data/example_T2.nii.gz',
                    'T1c':'./data/example_T1c.nii.gz',
                    'FLAIR':'./data/example_FLAIR.nii.gz'},
                    output_folder = './data/output',
                    reference='T1',
                    label=None,
                    prefix='patient001_',
                    already_coregistered=False,
                    mni=True,
                    crop=True)

ppr.run_pipeline()
```
The output folder will contain three folders nammed `coregistration`, `skullstripping` and `cropping` containing respectively the co-registered modalities, the skull-stripped and co-registered imaging modalities and the cropped versions of these latter skull-stripped scans. (example output `'./data/output/cropping/patient001_T1.nii.gz'`)

## Example case 2:
Let's assume we have access to 4 **co-registered** imaging modalities (e.g. T1, T1c, T2, FLAIR) and we want to:
- co-registered them in the MNI space (1x1x1 mm) using T1 as reference
- skull strip the scans using T1 as reference
- crop the skull-stripped scans to remove the zero padding 

```python
from MRIPreprocessor.mri_preprocessor import Preprocessor

# 4 Modalities to co-register to MNI space using an affine transformation
# T1 is used as reference for the coregistration
# No labelmap is used 
ppr = Preprocessor({'T1':'./data/example_T1.nii.gz',
                    'T2':'./data/example_T2.nii.gz',
                    'T1c':'./data/example_T1c.nii.gz',
                    'FLAIR':'./data/example_FLAIR.nii.gz'},
                    output_folder = './data/output',
                    reference='T1',
                    label=None,
                    prefix='patient001_',
                    already_coregistered=True,
                    mni=True,
                    crop=True)

ppr.run_pipeline()
```
The output folder will contain three folders nammed `coregistration`, `skullstripping` and `cropping` containing respectively the co-registered modalities in the MNI space, the skull-stripped and co-registered imaging modalities and the cropped versions of these latter skull-stripped scans. (example output `'./data/output/cropping/patient001_T1.nii.gz'`)



## Example case 3:
Let's assume we have access to 4 imaging modalities (T1, T1c, T2, FLAIR) and one segmentation drawn on the T1c scan. We want to:
- co-register the scans using T1c as reference
- in the MNI space (1x1x1 mm), including the labelmap
- skull strip the scans using T1c as reference
- crop the skull-stripped scans to remove the zero padding and apply the same cropping to the registered labelmap

**Note that the reference scan must be the scan employed for the segmentation, here the T1c scan.**
```python
from MRIPreprocessor.mri_preprocessor import Preprocessor

# 4 Modalities to co-register to MNI space using an affine transformation
# T1 is used as reference for the coregistration
# A labelmap is used
ppr = Preprocessor({'T1':'./data/example_T1.nii.gz',
                    'T2':'./data/example_T2.nii.gz',
                    'T1c':'./data/example_T1c.nii.gz',
                    'FLAIR':'./data/example_FLAIR.nii.gz'},
                    output_folder = './data/output',
                    reference='T1c',
                    label='./data/example_Label.nii.gz',
                    prefix='patient001_',
                    already_coregistered=False,
                    mni=True,
                    crop=True)

ppr.run_pipeline()
```
The output folder will contain three folders nammed `coregistration`, `skullstripping` and `cropping` containing respectively the co-registered modalities and labelmap, the skull-stripped and co-registered imaging modalities and labelmap and the cropped versions of these latter skull-stripped scans. (example output `'./data/output/cropping/patient001_T1.nii.gz'`)
