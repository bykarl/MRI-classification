"""Create sampled FreeSurfer label-overlay views; never grants manual QC approval."""
import argparse
import json
import os
from pathlib import Path
os.environ['MPLBACKEND']='Agg'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from freesurfer_pilot import REPO,load_config,read_json,run_dir,persistent_run,digest,copy_checked,write_new,now


def main():
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=REPO/'configs/freesurfer_pilot.json');p.add_argument('--run-id',required=True)
    args=p.parse_args();cfg=load_config(args.config);run=run_dir(cfg,args.run_id)
    complete=read_json(run/'autorecon3.completed.json')
    if complete['exit_code']!=0:raise RuntimeError('autorecon3 has not completed')
    mri=run/'subjects'/cfg['subject_id']/'mri';names=['norm.mgz','aseg.mgz','aparc+aseg.mgz']
    images=[nib.as_closest_canonical(nib.load(mri/name)) for name in names]
    if any(im.shape!=images[0].shape or not np.allclose(im.affine,images[0].affine,atol=1e-4) for im in images):
        raise RuntimeError('FS QC images are not on one physical grid')
    gray=images[0].get_fdata(dtype=np.float32);values=gray[gray>0]
    if not len(values) or not np.isfinite(gray).all():raise RuntimeError('Invalid norm image')
    lo,hi=np.percentile(values,[1,99]);gray=np.clip((gray-lo)/max(float(hi-lo),1e-6),0,1)
    labels=[im.get_fdata(dtype=np.float32) for im in images[1:]]
    if any(not np.isfinite(a).all() or not np.allclose(a,np.round(a)) for a in labels):raise RuntimeError('Nonfinite/noninteger FS labels')
    fig,axes=plt.subplots(6,5,figsize=(15,18))
    for axis,name in enumerate(['Sagittal','Coronal','Axial']):
        for col,fraction in enumerate([.2,.35,.5,.65,.8]):
            index=int((gray.shape[axis]-1)*fraction);view=np.rot90(np.take(gray,index,axis))
            for kind in range(2):
                row=2*axis+kind;lab=np.rot90(np.take(labels[kind],index,axis))
                axes[row,col].imshow(view,cmap='gray',vmin=0,vmax=1)
                axes[row,col].imshow(np.ma.masked_where(lab==0,lab),cmap='gist_ncar',alpha=.32,interpolation='nearest')
                axes[row,col].set_title(f'{name} {index} | '+['aseg','aparc+aseg'][kind],fontsize=9);axes[row,col].axis('off')
    fig.suptitle(cfg['record_id']+' | predicted labels, sampled QC only; review white/pial surfaces separately')
    fig.tight_layout();folder=run/'qc';folder.mkdir(exist_ok=False)
    fig.savefig(folder/'freesurfer_regions.png',dpi=120);plt.close(fig)
    write_new(folder/'provenance.json',{'created_at_utc':now(),'record_id':cfg['record_id'],
        'images':{name:digest(mri/name) for name in names},'display_orientation':'canonical RAS',
        'display_scaling':'nonzero 1st/99th percentile; not a model transform','manual_qc':'pending',
        'no_segmentation_GT':True,'surfaces_reviewed':False})
    for file in folder.iterdir():copy_checked(file,persistent_run(cfg,args.run_id)/file.relative_to(run))
    print(str(folder/'freesurfer_regions.png'))


if __name__=='__main__':main()
