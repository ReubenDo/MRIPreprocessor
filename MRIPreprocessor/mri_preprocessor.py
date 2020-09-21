import ants
import os
from HD_BET.run import run_hd_bet
import nibabel as nib
import SimpleITK as sitk


class Preprocessor():
    def __init__(self,
                dict_img,
                output_folder,
                reference = None):
        
        self.dict_img = dict_img
        self.output_folder = output_folder
        if reference is None:
            self.reference = sorted(dict_img.keys())
        else:
            assert reference in dict_img.keys(), "Reference has to be one the imaging modality in dict_img"
            self.reference = reference
        
        for mod in dict_img.keys():
            assert os.path.exists(dict_img[mod]), f"{dict_img[mod]} doesn't exist"

        self.coregistration_folder = os.path.join(self.output_folder, 'coregistration')
        if not os.path.exists(self.coregistration_folder):
            os.makedirs(self.coregistration_folder)

        self.skullstrip_folder = os.path.join(self.output_folder, 'skullstripping')
        if not os.path.exists(self.skullstrip_folder):
            os.makedirs(self.skullstrip_folder)       

        
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
        print("[INFO] Performing Coregistration")
        print(f"{self.reference} is used as reference")
        img_reference = ants.image_read(self.dict_img[self.reference], reorient=True)
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
        ref_sk = os.path.join(self.skullstrip_folder, f"{self.reference}.nii.gz")
        mask_sk = os.path.join(self.skullstrip_folder, f"{self.reference}_mask.nii.gz")
        run_hd_bet(self.dict_img[self.reference], ref_sk)

        modalities_tosk = list(self.dict_img.keys())
        modalities_tosk.remove(self.reference)
        for mod in modalities_tosk:
            registered_mod = os.path.join(self.coregistration_folder, f"{mod}.nii.gz")
            skullstripped_mod = os.path.join(self.skullstrip_folder, f"{mod}.nii.gz")
            self._apply_mask(input=registered_mod, output=skullstripped_mod, reference=ref_sk, mask=mask_sk)

    def run_pipeline(self):
        self._run_coregistration()
        self._run_skullstripping()