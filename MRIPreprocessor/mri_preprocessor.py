import ants
import os
from HD_BET.run import run_hd_bet
import nibabel as nib
import SimpleITK as sitk
import torch

from .utilities import crop_scans, get_mni

class Preprocessor():
    def __init__(self,
                dict_img,
                output_folder,
                reference=None,
                mni=False,
                crop=False):
        
        self.dict_img = dict_img
        self.output_folder = output_folder
        self.mni = mni
        self.crop = crop

        if reference is None:
            self.reference = sorted(dict_img.keys())[0]
        else:
            assert reference in dict_img.keys(), "Reference has to be one the imaging modality in dict_img"
            self.reference = reference
        
        # Test files are existing
        for mod in dict_img.keys():
            assert os.path.exists(dict_img[mod]), f"{dict_img[mod]} doesn't exist"

        # Get mni if needed
        if self.mni:
            self.mni_path = get_mni()

        # Create relevant folders if needed
        self.coregistration_folder = os.path.join(self.output_folder, 'coregistration')
        if not os.path.exists(self.coregistration_folder):
            os.makedirs(self.coregistration_folder)

        self.skullstrip_folder = os.path.join(self.output_folder, 'skullstripping')
        if not os.path.exists(self.skullstrip_folder):
            os.makedirs(self.skullstrip_folder)

        if crop:
            self.cropping_folder = os.path.join(self.output_folder, 'cropping')
            if not os.path.exists(self.cropping_folder):
                os.makedirs(self.cropping_folder)

        self.device = 0 if torch.cuda.is_available() else "cpu"


        
    def _save_scan(self, img, modality, save_folder):
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        output_filename = os.path.join(save_folder, f"{modality}.nii.gz")
        ants.image_write(img, output_filename)

    def _apply_mask(self, input, output, reference, mask):
        # Reorient in case HD-BET changed the orientation of the raw file
        input_img = sitk.ReadImage(input)
        ref_img = sitk.ReadImage(reference)
        output_img = sitk.Resample(
            input_img,
            ref_img,
            sitk.Transform(),
            sitk.sitkNearestNeighbor,
        )
        sitk.WriteImage(output_img, output)
        
        # Apply mask
        output_img = nib.load(output)
        output_affine = output_img.affine 
        output_data = output_img.get_fdata()

        mask_data = nib.load(mask).get_fdata()

        output_data[mask_data==0] = 0
        output_img = nib.Nifti1Image(output_data, output_affine)
        nib.save(output_img, output)

    
    def _run_coregistration(self):
        print("[INFO] Performing Coregistration using ANTsPy")
        print(f"{self.reference} is used as reference")
        img_reference = ants.image_read(self.dict_img[self.reference], reorient=True)
        if self.mni:
            print("[INFO] Registering to 1x1x1mm MNI space")
            img_mni = ants.image_read(self.mni_path, reorient=True)
            reg = ants.registration(img_mni, img_reference, 'Affine')
            img_reference = reg['warpedmovout']
            self._save_scan(img_reference, self.reference, self.coregistration_folder)
             

        modalities_toregister = list(self.dict_img.keys())
        modalities_toregister.remove(self.reference)
        for mod in modalities_toregister:
            img_mod = ants.image_read(self.dict_img[mod], reorient=True)
            reg = ants.registration(img_reference, img_mod, 'Affine')
            self._save_scan(reg['warpedmovout'], mod, self.coregistration_folder)
            print(f"Registration performed for {mod}")
        
    
    def _run_skullstripping(self):
        print("[INFO] Performing Skull Stripping using HD-BET")
        ref_co = os.path.join(self.coregistration_folder, f"{self.reference}.nii.gz")
        ref_sk = os.path.join(self.skullstrip_folder, f"{self.reference}.nii.gz")
        mask_sk = os.path.join(self.skullstrip_folder, f"{self.reference}_mask.nii.gz")
        run_hd_bet(ref_co, ref_sk, device=self.device)

        modalities_tosk = list(self.dict_img.keys())
        modalities_tosk.remove(self.reference)
        for mod in modalities_tosk:
            registered_mod = os.path.join(self.coregistration_folder, f"{mod}.nii.gz")
            skullstripped_mod = os.path.join(self.skullstrip_folder, f"{mod}.nii.gz")
            self._apply_mask(input=registered_mod, output=skullstripped_mod, reference=ref_sk, mask=mask_sk)

    def _run_cropping(self):
        print("[INFO] Performing Cropping")
        ref_sk = os.path.join(self.skullstrip_folder, f"{self.reference}.nii.gz")

        sk_images = [os.path.join(self.skullstrip_folder, f"{mod}.nii.gz") for mod in self.dict_img.keys()]
        cropped_images = [os.path.join(self.cropping_folder, f"{mod}.nii.gz") for mod in self.dict_img.keys()]

        crop_scans(ref_sk, sk_images, cropped_images)


    def run_pipeline(self):
        self._run_coregistration()
        self._run_skullstripping()
        if self.crop:
            self._run_cropping()
