"""Create an orthogonal alignment QC preview from this run's completed registration."""
from pathlib import Path
import importlib.util
import json
import os
os.environ['MPLBACKEND']='Agg'
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np

root=Path('/content/FYP_MRI_LiYang')
state=json.loads((root/'step2b_active.json').read_text())
run=Path(state['run_dir'])
assert (run/'stage_registration.json').is_file()
spec=importlib.util.spec_from_file_location('executed_t1_pilot',run/'executed_script.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
volumes=[pipeline.normalized(nib.load(run/name).get_fdata(dtype=np.float32)) for name in
         ['reference_1mm.nii.gz','T1w_initial_alignment.nii.gz','T1w_registered_0000.nii.gz']]
fig,axes=plt.subplots(3,4,figsize=(15,12))
for axis,plane in enumerate(['Sagittal','Coronal','Axial']):
    index=volumes[0].shape[axis]//2
    views=[np.rot90(np.take(data,index,axis)) for data in volumes]
    ii,jj=np.indices(views[0].shape)
    checker=np.where((ii//12+jj//12)%2,views[0],views[2])
    for col,(view,label) in enumerate(zip(views+[checker],['Template','Initial alignment','Final alignment','Template / final checkerboard'])):
        axes[axis,col].imshow(view,cmap='gray',vmin=0,vmax=1)
        axes[axis,col].set_title(f'{plane} {index} | {label}',fontsize=10)
        axes[axis,col].axis('off')
fig.suptitle('sub-mindo304_ses-placebo | alignment preview, stored LAS axes; anatomical QC pending')
fig.tight_layout()
target=run/'qc_alignment_orthogonal_preview.png'
assert not target.exists()
fig.savefig(target,dpi=125);plt.close(fig)
pipeline.checkpoint(run,[target])
print(str(target))
