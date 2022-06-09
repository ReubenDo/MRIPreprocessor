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
                label=None,
                prefix="",
                reference=None,
                skull_stripping=True,
                already_coregistered=False,
                mni=False,
                crop=False):
        
        self.dict_img = dict_img
        self.modalities = dict_img.keys()
        self.output_folder = output_folder
        self.label = label
        self.prefix = prefix
        self.skull_stripping = skull_stripping
        self.already_coregistered = already_coregistered
        self.mni = mni
        self.crop = crop


        if reference is None:
            self.reference = sorted(self.modalities)[0]
        else:
            assert reference in dict_img.keys(), "Reference has to be one the imaging modality in dict_img"
            self.reference = reference
    
        # Test files are existing
        for mod in dict_img.keys():
            assert os.path.exists(dict_img[mod]), f"{dict_img[mod]} doesn't exist"
        if not label is None:
            assert os.path.exists(label), "Label map doesn't exist"

        

        # Get mni if needed
        if self.mni:
            self.mni_path = get_mni(self.skull_stripping)

        # Create relevant folders if needed
        self.coregistration_folder = os.path.join(self.output_folder, "coregistration")
        if not os.path.exists(self.coregistration_folder):
            os.makedirs(self.coregistration_folder)

        if self.skull_stripping:
            self.skullstrip_folder = os.path.join(self.output_folder, "skullstripping")
            if not os.path.exists(self.skullstrip_folder):
                os.makedirs(self.skullstrip_folder)
        else:
            self.skullstrip_folder = self.coregistration_folder

        if crop:
            self.cropping_folder = os.path.join(self.output_folder, "cropping")
            if not os.path.exists(self.cropping_folder):
                os.makedirs(self.cropping_folder)

        self.device = 0 if torch.cuda.is_available() else "cpu"


        
    def _save_scan(self, img, name, save_folder):
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        output_filename = os.path.join(save_folder, f"{name}.nii.gz")
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
        img_reference = ants.image_read(self.dict_img[self.reference], reorient=True)

        # Register the reference to MNI, if needed
        if self.mni:
            print(f"[INFO] Registering to 1x1x1mm MNI space using ANTsPy")
            print(f"{self.reference} is used as reference")
            img_mni = ants.image_read(self.mni_path, reorient=True)
            reg = ants.registration(img_mni, img_reference, "Affine")
            img_reference = reg["warpedmovout"]
            self._save_scan(img_reference, f"{self.prefix}{self.reference}", self.coregistration_folder)
            reg_tomni = reg["fwdtransforms"]
            if not self.label is None:
                img_label = ants.image_read(self.label, reorient=True)
                warped_label = ants.apply_transforms(img_mni, img_label, reg_tomni, interpolator="nearestNeighbor")
                self._save_scan(warped_label, f"{self.prefix}Label", self.coregistration_folder)
        else:
            self._save_scan(img_reference, f"{self.prefix}{self.reference}", self.coregistration_folder)
            if not self.label is None:
                img_label = ants.image_read(self.label, reorient=True)
                self._save_scan(img_label, f"{self.prefix}Label", self.coregistration_folder)

        # Register the other scans, if needed
        modalities_toregister = list(self.modalities)
        modalities_toregister.remove(self.reference)
        for mod in modalities_toregister:
            if self.already_coregistered: 
                if self.mni: # if the scans are already co-registered we reuse the ref to MNI transformation
                    img_mod = ants.image_read(self.dict_img[mod], reorient=True)
                    warped_img = ants.apply_transforms(img_mni, img_mod, reg_tomni, interpolator="linear")
                    self._save_scan(warped_img, f"{self.prefix}{mod}", self.coregistration_folder)
                    print(f"[INFO] Registration performed to MNI for {mod}")
                else:
                    img_mod = ants.image_read(self.dict_img[mod], reorient=True)
                    self._save_scan(img_mod, f"{self.prefix}{mod}", self.coregistration_folder)
                    print(f"No co-registration performed for {mod}")

            else: # Scans are not co-registered
                img_mod = ants.image_read(self.dict_img[mod], reorient=True)
                reg = ants.registration(img_reference, img_mod, "Affine")
                self._save_scan(reg["warpedmovout"], f"{self.prefix}{mod}", self.coregistration_folder)
                print(f"[INFO] Registration using ANTsPy for {mod} with {self.reference} as reference")
        
    
    def _run_skullstripping(self):
        print("[INFO] Performing Skull Stripping using HD-BET")
        ref_co = os.path.join(self.coregistration_folder, f"{self.prefix}{self.reference}.nii.gz")
        ref_sk = os.path.join(self.skullstrip_folder, f"{self.prefix}{self.reference}.nii.gz")
        mask_sk = os.path.join(self.skullstrip_folder, f"{self.prefix}{self.reference}_mask.nii.gz")
        run_hd_bet(ref_co, ref_sk, mode="fast", device=self.device, do_tta=False)

        modalities_tosk = list(self.modalities)
        modalities_tosk.remove(self.reference)
        for mod in modalities_tosk:
            registered_mod = os.path.join(self.coregistration_folder, f"{self.prefix}{mod}.nii.gz")
            skullstripped_mod = os.path.join(self.skullstrip_folder, f"{self.prefix}{mod}.nii.gz")
            self._apply_mask(input=registered_mod, output=skullstripped_mod, reference=ref_sk, mask=mask_sk)

        if not self.label is None:
            registered_lab = os.path.join(self.coregistration_folder, f"{self.prefix}Label.nii.gz")
            skullstripped_lab = os.path.join(self.skullstrip_folder, f"{self.prefix}Label.nii.gz")
            self._apply_mask(input=registered_lab, output=skullstripped_lab, reference=ref_sk, mask=mask_sk)


    def _run_cropping(self):
        print("[INFO] Performing Cropping")
        ref_sk = os.path.join(self.skullstrip_folder, f"{self.prefix}{self.reference}.nii.gz")

        sk_images = [os.path.join(self.skullstrip_folder, f"{self.prefix}{mod}.nii.gz") for mod in self.modalities]
        cropped_images = [os.path.join(self.cropping_folder, f"{self.prefix}{mod}.nii.gz") for mod in self.modalities]

        if not self.label is None:
            sk_images.append(os.path.join(self.skullstrip_folder, f"{self.prefix}Label.nii.gz"))
            cropped_images.append(os.path.join(self.cropping_folder, f"{self.prefix}Label.nii.gz"))

        crop_scans(ref_sk, sk_images, cropped_images)



    def run_pipeline(self):
        self._run_coregistration()
        if self.skull_stripping:
            self._run_skullstripping()
        if self.crop:
            self._run_cropping()
