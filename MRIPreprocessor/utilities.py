import requests
import os
from zipfile import ZipFile 
import MRIPreprocessor

import nibabel as nib
import SimpleITK as sitk
import numpy as np

def find_zeros(img_array):
    if len(img_array.shape) == 4:
        img_array = np.amax(img_array, axis=3)
    assert len(img_array.shape) == 3
    x_dim, y_dim, z_dim = tuple(img_array.shape)
    x_zeros, y_zeros, z_zeros = np.where(img_array == 0.)
    # x-plans that are not uniformly equal to zeros
    
    try:
        x_to_keep, = np.where(np.bincount(x_zeros) < y_dim * z_dim)
        x_min = min(x_to_keep)
        x_max = max(x_to_keep) + 1
    except Exception :
        x_min = 0
        x_max = x_dim
    try:
        y_to_keep, = np.where(np.bincount(y_zeros) < x_dim * z_dim)
        y_min = min(y_to_keep)
        y_max = max(y_to_keep) + 1
    except Exception :
        y_min = 0
        y_max = y_dim
    try :
        z_to_keep, = np.where(np.bincount(z_zeros) < x_dim * y_dim)
        z_min = min(z_to_keep)
        z_max = max(z_to_keep) + 1
    except:
        z_min = 0
        z_max = z_dim
    return x_min, x_max, y_min, y_max, z_min, z_max


def crop_scans(reference, inputs, outputs):
    img_crop = nib.load(reference)
    affine = img_crop.affine
    img_crop_data = img_crop.get_fdata()
    x_min, x_max, y_min, y_max, z_min, z_max = find_zeros(img_crop_data)

    x_max = img_crop_data.shape[0] - x_max
    y_max = img_crop_data.shape[1] - y_max
    z_max = img_crop_data.shape[2] - z_max
    bounds_parameters = [x_min, x_max, y_min, y_max, z_min, z_max]
    low = bounds_parameters[::2]
    high = bounds_parameters[1::2]
    low = [int(k) for k in low]
    high = [int(k) for k in high]

    for i,path_mod in enumerate(inputs):
        image = sitk.ReadImage(path_mod)
        image = sitk.Crop(image, low, high)
        sitk.WriteImage(image, outputs[i])



def get_mni(skull_stripping):
    tmp_folder = os.path.join(list(MRIPreprocessor.__path__)[0], "data")
    path_mni = os.path.join(tmp_folder, 'mni.nii.gz')
    path_mask = os.path.join(tmp_folder, 'mask.nii.gz')
    path_mni_sk = os.path.join(tmp_folder, 'mni_sk.nii.gz')
    if not os.path.exists(path_mni) or not os.path.exists(path_mni_sk):
        print('MNI template not found. Downloading...')
        URL = 'http://www.bic.mni.mcgill.ca/~vfonov/icbm/2009/mni_icbm152_nlin_sym_09a_nifti.zip'
        
        # download the file contents in binary format
        r = requests.get(URL)
        
        # doewnload the zip
        tmp_folder = os.path.join(list(MRIPreprocessor.__path__)[0], "data")
        if not os.path.exists(tmp_folder):
            os.makedirs(tmp_folder)
        
        local_path = os.path.join(tmp_folder, 'mni.zip')
        with open(local_path, "wb") as code:
            code.write(r.content)
            
        filname_mni = 'mni_icbm152_nlin_sym_09a/mni_icbm152_t1_tal_nlin_sym_09a.nii'
        filname_mask = 'mni_icbm152_nlin_sym_09a/mni_icbm152_t1_tal_nlin_sym_09a_mask.nii'
            
        # extracting MNI file
        with ZipFile(local_path, 'r') as z:
            with open(path_mni, 'wb') as f:
                f.write(z.read(filname_mni))
        
        # extracting mask file
        with ZipFile(local_path, 'r') as z:
            with open(path_mask, 'wb') as f:
                f.write(z.read(filname_mask))

        mask = sitk.ReadImage(path_mask)
        mni = sitk.ReadImage(path_mni)

        mni_sk = mask * mni
        sitk.WriteImage(mni_sk, path_mni_sk)
                
        os.remove(local_path)
    
    if skull_stripping:
        return path_mni
    else:
        return path_mni_sk 
