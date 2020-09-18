import requests
import os
from zipfile import ZipFile 

from MRIPreprocessor.mri_preprocessor import Preprocessor

# for this test we use the data provided by the bratstoolkit
URL = 'https://neuronflow.github.io/BraTS-Preprocessor/downloads/example_data.zip'
PATHS = {
		'T1':'exam_import/OtherEXampleFromTCIA/T1_AX_OtherEXampleTCIA_TCGA-FG-6692_Si_TCGA-FG-6692_T1_AX_SE_10_se2d1_t1.nii.gz',
		'T1c':'exam_import/OtherEXampleFromTCIA/MRHR_T1_AX_POST_GAD_OtherEXampleTCIA_TCGA-FG-6692_Si_TCGA-FG-6692_MRHR_T1_AX_POST_GAD_SE_13_se2d1r_t1c.nii.gz',
		'T2':'exam_import/OtherEXampleFromTCIA/MRHR_T2_AX_OtherEXampleTCIA_TCGA-FG-6692_Si_TCGA-FG-6692_MRHR_T2_AX_SE_2_tse2d1_11_t2.nii.gz',
		'FLAIR':'exam_import/OtherEXampleFromTCIA/MRHR_FLAIR_AX_OtherEXampleTCIA_TCGA-FG-6692_Si_TCGA-FG-6692_MRHR_FLAIR_AX_SE_IR_5_tir2d1_21_fla.nii.gz'
		} 

# download the file contents in binary format
r = requests.get(URL)

# doewnload the zip
local_path = "data/example_data.zip"
if not os.path.exists('data'):
    os.makedirs('data')
 
with open(local_path, "wb") as code:
    code.write(r.content)

# extracting 4 modalities from patient 'OtherEXampleFromTCIA'
with ZipFile(local_path, 'r') as z:
	for mod, path_mod in PATHS.items():
	    with open(f'data/example_{mod}.nii.gz', 'wb') as f:
	        f.write(z.read(path_mod))
print('Images have been downloaded properly')

# Preprocessed data
ppr = Preprocessor({'T1':'data/example_T1.nii.gz',
                    'T2':'data/example_T2.nii.gz',
                    'T1c':'data/example_T1c.nii.gz',
                    'FLAIR':'data/example_FLAIR.nii.gz'},
                    output_folder = 'data/output',
                    reference='T1')

ppr.run_pipeline()