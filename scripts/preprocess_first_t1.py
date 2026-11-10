"""First-case technical pilot: N4 -> author-template rigid alignment -> legacy HD-BET.

Immutable run directories and hash-verified Drive checkpoints after each stage.
No classification, 96-cubed conversion, FreeSurfer or fMRI processing. Final
handoff stays pending human QC and feature-owner recipe confirmation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import itertools
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys
import time
import traceback

os.environ['MPLBACKEND']='Agg'
os.environ.setdefault('OMP_NUM_THREADS','2')
os.environ.setdefault('MKL_NUM_THREADS','2')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import SimpleITK as sitk

ROOT=Path('/content/FYP_MRI_LiYang')
DRIVE=Path('/content/drive/MyDrive/FYP_MRI_LiYang')
RID='sub-mindo304_ses-placebo'
INPUT=ROOT/'intake_v2/t1'/f'{RID}_T1w.nii.gz'
TEMPLATE=ROOT/'assets/brainiac/temp_head.nii.gz'
RAW=ROOT/'dataset_Mi/rawdata/sub-mindo304/ses-placebo/anat'/f'{RID}_T1w.nii.gz'
INPUT_SHA='8e6d3104d6171e3528aefe6288357f8cfee97724f0044232bac7c2fd3641dccb'
RAW_SHA='89ea431ba0e912d1b73643a4ce691dbe13ad54da394b645942e4e12dceaf73b5'
TEMPLATE_SHA='d8eba10e9528a5212b78fb1be477d5e8229751bfec5e1e1a648dc81ff83a622e'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def utc(): return datetime.now(timezone.utc).isoformat()


def emit(message): print(utc(),message,flush=True)


def json_new(path, value):
    with path.open('x') as stream: json.dump(value,stream,indent=2)


def checkpoint(run,paths):
    records=[]
    for source in paths:
        rel=source.relative_to(ROOT)
        target=DRIVE/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        checksum=sha(source)
        if target.exists():
            assert sha(target)==checksum, 'Different existing checkpoint: '+str(rel)
        else:
            part=target.with_name(target.name+'.partial')
            assert not part.exists(), 'Inspect previous partial checkpoint: '+str(part)
            shutil.copyfile(source,part)
            assert sha(part)==checksum
            part.rename(target)
        assert sha(target)==checksum
        records.append({'path':str(source.relative_to(run)), 'sha256':checksum,'bytes':source.stat().st_size})
    return records


def write_image(image,path):
    assert not path.exists()
    sitk.WriteImage(image,str(path),True)
    loaded=sitk.ReadImage(str(path))
    values=sitk.GetArrayViewFromImage(loaded)
    assert np.isfinite(values).all()
    return path


def spatial(image):
    # Nibabel RAS affine reconstructed from ITK LPS geometry for reader audit.
    affine=np.eye(4)
    affine[:3,:3]=np.array(image.GetDirection()).reshape(3,3)@np.diag(image.GetSpacing())
    affine[:3,3]=image.GetOrigin()
    return np.diag([-1.,-1.,1.,1.])@affine


def normalized(array):
    array=np.asarray(array,dtype=np.float32)
    positive=array[array>0]
    lo,hi=np.percentile(positive,[1,99]) if positive.size else (0,1)
    return np.clip((array-lo)/max(float(hi-lo),1e-6),0,1)


def make_qc(run):
    source=nib.load(INPUT).get_fdata(dtype=np.float32)
    corrected=nib.load(run/'T1w_N4_native.nii.gz').get_fdata(dtype=np.float32)
    fig,axes=plt.subplots(3,2,figsize=(9,12))
    for axis,name in enumerate(['Sagittal','Coronal','Axial']):
        index=source.shape[axis]//2
        for column,(data,label) in enumerate([(source,'Input'),(corrected,'N4')]):
            axes[axis,column].imshow(np.rot90(np.take(normalized(data),index,axis)),cmap='gray',vmin=0,vmax=1)
            axes[axis,column].set_title(f'{name} {index} | {label}'); axes[axis,column].axis('off')
    fig.suptitle(RID+' | native grid, display-only percentile scaling')
    fig.tight_layout(); fig.savefig(run/'qc_n4.png',dpi=130); plt.close(fig)
    fixed=normalized(nib.load(run/'reference_1mm.nii.gz').get_fdata(dtype=np.float32))
    registered=normalized(nib.load(run/'T1w_registered_0000.nii.gz').get_fdata(dtype=np.float32))
    brain=nib.load(run/'T1w_brain.nii.gz').get_fdata(dtype=np.float32)
    mask=nib.load(run/'T1w_brain_mask.nii.gz').get_fdata(dtype=np.float32)>0
    fractions=[0.25,0.35,0.45,0.55,0.65,0.75]
    fig,axes=plt.subplots(4,len(fractions),figsize=(18,12))
    for column,fraction in enumerate(fractions):
        z=int(round((fixed.shape[2]-1)*fraction))
        f=np.rot90(fixed[:,:,z]); r=np.rot90(registered[:,:,z]); m=np.rot90(mask[:,:,z])
        axes[0,column].imshow(f,cmap='gray',vmin=0,vmax=1)
        axes[0,column].set_title(f'Template | z={z}')
        axes[1,column].imshow(r,cmap='gray',vmin=0,vmax=1)
        axes[1,column].set_title('Registered T1')
        xx,yy=np.indices(f.shape)
        checker=np.where((xx//12+yy//12)%2,f,r)
        axes[2,column].imshow(checker,cmap='gray',vmin=0,vmax=1)
        axes[2,column].set_title('Template / T1 checkerboard')
        axes[3,column].imshow(r,cmap='gray',vmin=0,vmax=1)
        if m.any() and not m.all(): axes[3,column].contour(m,levels=[.5],colors=['lime'],linewidths=.7)
        axes[3,column].set_title('Brain mask boundary')
        for row in range(4): axes[row,column].axis('off')
    fig.suptitle(RID+' | QC review required; no anatomical ground-truth mask')
    fig.tight_layout(); fig.savefig(run/'qc_registration_mask.png',dpi=135); plt.close(fig)
    # Orthogonal mask views supplement the axial contact sheet.
    fig,axes=plt.subplots(3,3,figsize=(11,11))
    for axis,name in enumerate(['Sagittal','Coronal','Axial']):
        for column,fraction in enumerate([.35,.5,.65]):
            index=int((mask.shape[axis]-1)*fraction)
            view=np.rot90(np.take(registered,index,axis)); m=np.rot90(np.take(mask,index,axis))
            axes[axis,column].imshow(view,cmap='gray',vmin=0,vmax=1)
            if m.any() and not m.all(): axes[axis,column].contour(m,levels=[.5],colors=['lime'],linewidths=.7)
            axes[axis,column].set_title(f'{name} {index}'); axes[axis,column].axis('off')
    fig.tight_layout(); fig.savefig(run/'qc_mask_orthogonal.png',dpi=140); plt.close(fig)
    assert np.isfinite(brain).all()
    return [run/'qc_n4.png',run/'qc_registration_mask.png',run/'qc_mask_orthogonal.png']


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--run-id',required=True)
    parser.add_argument('--resume-n4-from',help='Previously completed lowmem N4 run ID; verify local/Drive hashes before reuse')
    args=parser.parse_args()
    assert args.run_id.replace('-','').replace('_','').isalnum()
    assert DRIVE.is_dir(), 'Authorized Drive mount is required'
    assert list((DRIVE/'step2a_logs').glob('persistence_*.json')), '2A readback checkpoint missing'
    assert sha(INPUT)==INPUT_SHA and sha(RAW)==RAW_SHA and sha(TEMPLATE)==TEMPLATE_SHA
    assert sha(DRIVE/INPUT.relative_to(ROOT))==INPUT_SHA
    run=ROOT/'derivatives/t1_pilot'/RID/args.run_id
    run.mkdir(parents=True,exist_ok=False)
    sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(2)
    params={'record_id':RID,'run_id':args.run_id,'started_at_utc':utc(),
        'purpose':'single-case technical pilot; candidate recipe not yet feature-owner accepted',
        'input_recipe_confirmed':False,'raw_sha256':RAW_SHA,'input_sha256':INPUT_SHA,
        'template_sha256':TEMPLATE_SHA,'script_sha256':sha(__file__),
        'software':{n:metadata.version(n) for n in ['SimpleITK','HD_BET','torch','nibabel','numpy']},
        'order':['N4_native','Euler3D_rigid_to_author_template','legacy_HDBET_fast_tta0'],
        'threads':2,'random_seed':20261110,'fixed_seed_added_relative_to_author':True,
        'n4_input_mask':'Otsu foreground, 200 bins; not a brain segmentation mask', 'n4_shrink_factor':2,
        'n4_recipe_version':'pilot_lowmem_v2',
        'resume_n4_from':args.resume_n4_from,'registration_input_cast':'sitkFloat32',
        'n4_change_relative_to_author':'Shrink image and Otsu foreground mask by 2 for field estimation, evaluate field on original grid and divide original image; not identical to author no-mask full-grid call.',
        'n4_method_reference':'https://simpleitk.readthedocs.io/en/master/link_N4BiasFieldCorrection_docs.html',
        'registration':{'initializer':'GEOMETRY','metric':'MattesMutualInformation','bins':50,
            'sampling':'RANDOM','sampling_fraction':.01,'seed':20261110,
            'learning_rate':1.,'iterations':100,'convergence_minimum':1e-6,'convergence_window':10,
            'shrink_factors':[4,2,1],'smoothing_sigmas_mm':[2,1,0],'interpolator':'linear','outside_value':0.},
        'hdbet':{'device':'cpu','mode':'fast','tta':0,'postprocess_largest_component':1,'save_mask':1},
        'no_96_cube_resize':True,'no_encoder_intensity_standardization':True,
        'qc_status':'pending','training_ready':False}
    json_new(run/'run.json',params)
    shutil.copyfile(__file__,run/'executed_script.py')
    checkpoint(run,[run/'run.json',run/'executed_script.py'])
    timings={}
    try:
        emit('START N4 | shrink=2 foreground field estimation, native-resolution application')
        start=time.monotonic()
        image=sitk.ReadImage(str(INPUT),sitk.sitkFloat32)
        corners=np.array(list(itertools.product(*[(0,s-1) for s in image.GetSize()])))
        delta=spatial(image)-nib.load(INPUT).affine
        errors=np.linalg.norm((delta@np.column_stack([corners,np.ones(len(corners))]).T)[:3],axis=0)
        assert errors.max()<.001, 'ITK/nibabel world-coordinate disagreement >0.001 mm'
        if args.resume_n4_from:
            assert args.resume_n4_from.replace('-','').replace('_','').isalnum()
            prior=run.parent/args.resume_n4_from
            previous=json.loads((prior/'run.json').read_text())
            assert previous['input_sha256']==INPUT_SHA and previous['template_sha256']==TEMPLATE_SHA
            assert previous['n4_recipe_version']=='pilot_lowmem_v2' and previous['n4_shrink_factor']==2
            stage=json.loads((prior/'stage_n4.json').read_text())
            files=['n4_parameters.json','T1w_N4_native.nii.gz','N4_log_bias_native.nii.gz','N4_foreground_mask_native.nii.gz']
            for name in files:
                source=prior/name
                assert sha(source)==sha(DRIVE/source.relative_to(ROOT)), 'N4 local/Drive hash mismatch'
                shutil.copyfile(source,run/name)
            corrected=sitk.ReadImage(str(run/'T1w_N4_native.nii.gz'))
            assert corrected.GetSize()==image.GetSize()
            assert np.allclose(spatial(corrected),spatial(image),atol=1e-4)
            timings['n4_seconds']=0.0
            timings['reused_n4_original_seconds']=stage['seconds']
            n4_status={'stage':'n4','completed_at_utc':utc(),'seconds':0.,'reused_from_run':args.resume_n4_from,
                       'original_compute_seconds':stage['seconds'],'local_drive_hash_checks':'pass','anatomical_qc':'pending'}
            json_new(run/'stage_n4.json',n4_status)
            checkpoint(run,[run/name for name in files]+[run/'stage_n4.json'])
            emit('SAVED N4 REUSED; NO N4 RECOMPUTATION')
        else:
            n4=sitk.N4BiasFieldCorrectionImageFilter()
            params_n4={k:getattr(n4,'Get'+k)() for k in ['MaximumNumberOfIterations','ConvergenceThreshold','SplineOrder','NumberOfControlPoints']}
            json_new(run/'n4_parameters.json',params_n4)
            checkpoint(run,[run/'n4_parameters.json'])
            def n4_progress():
                iteration=n4.GetElapsedIterations()
                if iteration%10==0:
                    emit(f'N4 level={n4.GetCurrentLevel()} iteration={iteration} convergence={n4.GetCurrentConvergenceMeasurement():.6g}')
            n4.AddCommand(sitk.sitkIterationEvent,n4_progress)
            foreground=sitk.OtsuThreshold(image,0,1,200)
            write_image(foreground,run/'N4_foreground_mask_native.nii.gz')
            small=sitk.Shrink(image,[2,2,2]); small_mask=sitk.Shrink(foreground,[2,2,2])
            n4.Execute(small,small_mask)
            field=n4.GetLogBiasFieldAsImage(image)
            corrected=image/sitk.Exp(field)
            write_image(corrected,run/'T1w_N4_native.nii.gz')
            write_image(field,run/'N4_log_bias_native.nii.gz')
            timings['n4_seconds']=round(time.monotonic()-start,3)
            n4_status={'stage':'n4','completed_at_utc':utc(),'seconds':timings['n4_seconds'],
                       'itk_nibabel_max_corner_error_mm':float(errors.max()),'anatomical_qc':'pending'}
            json_new(run/'stage_n4.json',n4_status)
            checkpoint(run,[run/'T1w_N4_native.nii.gz',run/'N4_log_bias_native.nii.gz',run/'N4_foreground_mask_native.nii.gz',run/'stage_n4.json'])
        emit('N4 COMPLETE AND DRIVE READBACK PASS')
        emit('START RIGID REGISTRATION')
        start=time.monotonic()
        moving_pixel_type_before_cast=corrected.GetPixelIDTypeAsString()
        emit('Registration moving input before Float32 cast: '+moving_pixel_type_before_cast)
        corrected=sitk.Cast(corrected,sitk.sitkFloat32)
        fixed=sitk.ReadImage(str(TEMPLATE),sitk.sitkFloat32)
        reference=sitk.ResampleImageFilter()
        reference.SetOutputSpacing((1.,1.,1.))
        reference.SetSize([int(round(s*z)) for s,z in zip(fixed.GetSize(),fixed.GetSpacing())])
        reference.SetOutputOrigin(fixed.GetOrigin()); reference.SetOutputDirection(fixed.GetDirection())
        reference.SetInterpolator(sitk.sitkLinear)
        reference.SetDefaultPixelValue(float(fixed.GetPixelIDValue()))
        reference.SetOutputPixelType(sitk.sitkFloat32)
        fixed=reference.Execute(fixed)
        write_image(fixed,run/'reference_1mm.nii.gz')
        initial=sitk.CenteredTransformInitializer(fixed,corrected,sitk.Euler3DTransform(),sitk.CenteredTransformInitializerFilter.GEOMETRY)
        sitk.WriteTransform(initial,str(run/'initial_template_to_native.tfm'))
        baseline=sitk.Resample(corrected,fixed,initial,sitk.sitkLinear,0.,sitk.sitkFloat32)
        write_image(baseline,run/'T1w_initial_alignment.nii.gz')
        reg=sitk.ImageRegistrationMethod()
        reg.SetMetricAsMattesMutualInformation(numberOfHistogramBins=50)
        reg.SetMetricSamplingStrategy(reg.RANDOM); reg.SetMetricSamplingPercentage(.01,20261110)
        reg.SetInterpolator(sitk.sitkLinear)
        reg.SetOptimizerAsGradientDescent(learningRate=1.,numberOfIterations=100,convergenceMinimumValue=1e-6,convergenceWindowSize=10)
        reg.SetOptimizerScalesFromPhysicalShift()
        reg.SetShrinkFactorsPerLevel([4,2,1]); reg.SetSmoothingSigmasPerLevel([2,1,0])
        reg.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn(); reg.SetInitialTransform(initial)
        trace=[]
        reg.AddCommand(sitk.sitkIterationEvent,lambda:trace.append({'level':reg.GetCurrentLevel(),'iteration':reg.GetOptimizerIteration(),'metric':float(reg.GetMetricValue())}))
        final=reg.Execute(fixed,corrected)
        sitk.WriteTransform(final,str(run/'template_to_native.tfm'))
        sitk.WriteTransform(final.GetInverse(),str(run/'native_to_template.tfm'))
        registered=sitk.Resample(corrected,fixed,final,sitk.sitkLinear,0.,sitk.sitkFloat32)
        write_image(registered,run/'T1w_registered_0000.nii.gz')
        timings['registration_seconds']=round(time.monotonic()-start,3)
        json_new(run/'registration_trace.json',trace)
        json_new(run/'stage_registration.json',{'stage':'registration','completed_at_utc':utc(),
            'seconds':timings['registration_seconds'],'optimizer_stop':reg.GetOptimizerStopConditionDescription(),
            'moving_pixel_type_before_cast':moving_pixel_type_before_cast,'moving_pixel_type_used':'32-bit float',
            'metric_final':float(reg.GetMetricValue()),'metric_not_anatomical_QC':True,
            'transform_direction':'template_to_native maps output/template physical coordinates to input/native for resampling',
            'anatomical_qc':'pending'})
        checkpoint(run,[run/n for n in ['reference_1mm.nii.gz','initial_template_to_native.tfm','T1w_initial_alignment.nii.gz',
            'template_to_native.tfm','native_to_template.tfm','T1w_registered_0000.nii.gz','registration_trace.json','stage_registration.json']])
        emit('REGISTRATION COMPLETE AND DRIVE READBACK PASS')
        emit('START HD-BET CPU fast tta=0')
        start=time.monotonic()
        command=[str(Path(sys.executable).parent/'hd-bet'),'-i',str(run/'T1w_registered_0000.nii.gz'),
            '-o',str(run/'T1w_brain.nii.gz'),'-mode','fast','-tta','0','-device','cpu','-pp','1','-s','1','-b','1','--overwrite_existing','0']
        env=os.environ.copy(); env['PYTHONUNBUFFERED']='1'
        with (run/'hdbet.log').open('x') as stream:
            subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,env=env,check=True)
        timings['hdbet_seconds']=round(time.monotonic()-start,3)
        brain=nib.load(run/'T1w_brain.nii.gz'); mask=nib.load(run/'T1w_brain_mask.nii.gz')
        ref=nib.load(run/'T1w_registered_0000.nii.gz')
        assert brain.shape==mask.shape==ref.shape
        assert np.allclose(brain.affine,ref.affine,atol=1e-4) and np.allclose(mask.affine,ref.affine,atol=1e-4)
        m=mask.get_fdata(dtype=np.float32); b=brain.get_fdata(dtype=np.float32); r=ref.get_fdata(dtype=np.float32)
        assert np.isfinite(m).all() and np.isfinite(b).all()
        assert set(np.unique(m))=={0.,1.} and np.any(b[m>0]!=0)
        assert np.allclose(b[m==0],0) and np.allclose(b[m>0],r[m>0])
        json_new(run/'stage_hdbet.json',{'stage':'hdbet','completed_at_utc':utc(),'command':command,
            'seconds':timings['hdbet_seconds'],'mask_voxels':int((m>0).sum()),
            'mask_volume_ml':float((m>0).sum()*np.prod(mask.header.get_zooms())/1000),
            'technical_checks':'pass','anatomical_qc':'pending'})
        checkpoint(run,[run/'T1w_brain.nii.gz',run/'T1w_brain_mask.nii.gz',run/'stage_hdbet.json',run/'hdbet.log'])
        emit('HD-BET COMPLETE AND DRIVE READBACK PASS')
        qcs=make_qc(run); checkpoint(run,qcs)
        assert sha(RAW)==RAW_SHA and sha(INPUT)==INPUT_SHA
        outputs=[p for p in run.iterdir() if p.is_file()]
        handoff={'record_id':RID,'run_id':args.run_id,'completed_at_utc':utc(),
            'processing_status':'completed_technical_checks_only','scientific_preprocessing_started':True,
            't1_stage':'processed_pending_manual_QC_and_recipe_review','input_recipe_confirmed':False,
            'qc_status':'pending','training_ready':False,'timings':timings,
            'peak_self_rss_mib_linux':round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,2),
            'peak_child_rss_mib_linux':round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/1024,2),
            'freesurfer':'not_run','fmri':'not_run','classification':'not_run',
            'raw_unchanged':True,'staged_input_unchanged':True,
            'output_shape':list(brain.shape),'output_orientation':list(nib.aff2axcodes(brain.affine)),
            'output_spacing_mm':list(map(float,brain.header.get_zooms())),
            'outputs':[{'path':str(p.relative_to(run)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in outputs]}
        json_new(run/'handoff_pilot.json',handoff)
        checkpoint(run,[run/'handoff_pilot.json'])
        emit('2B TECHNICAL PROCESSING COMPLETE; MANUAL QC / RECIPE ACCEPTANCE PENDING')
        print(json.dumps(handoff,indent=2),flush=True)
    except Exception as error:
        failure={'record_id':RID,'failed_at_utc':utc(),'error':str(error),'traceback':traceback.format_exc(),
            'timings':timings,'qc_status':'failed_processing','training_ready':False}
        json_new(run/'failure.json',failure)
        try: checkpoint(run,[run/'failure.json'])
        except Exception: traceback.print_exc()
        raise


if __name__=='__main__': main()
