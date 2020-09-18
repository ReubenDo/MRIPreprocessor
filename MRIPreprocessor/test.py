from mri_preprocessor import Preprocessor

ppr = Preprocessor({'T1':'./data/example_T1.nii.gz',
                    'T2':'./data/example_T2.nii.gz',
                    'T1c':'./data/example_T1c.nii.gz',
                    'FLAIR':'./data/example_FLAIR.nii.gz'},
                    output_folder = './data/output',
                    reference='T1')

ppr.run_pipeline()