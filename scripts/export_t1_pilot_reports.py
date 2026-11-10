"""Verify completed 2B checkpoints and export small review evidence, without MRI/weights."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import zipfile

ROOT=Path('/content/FYP_MRI_LiYang')
DRIVE=Path('/content/drive/MyDrive/FYP_MRI_LiYang')
ALLOWED={'.json','.py','.txt','.log','.png'}


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    state=json.loads((ROOT/'step2b_active.json').read_text())
    run=Path(state['run_dir'])
    assert run.is_relative_to(ROOT/'derivatives/t1_pilot/sub-mindo304_ses-placebo')
    result=json.loads((run/'handoff_pilot.json').read_text())
    assert result['processing_status']=='completed_technical_checks_only' and not (run/'failure.json').exists()
    checks=[]
    for path in sorted(run.iterdir()):
        if not path.is_file():continue
        mirrored=DRIVE/path.relative_to(ROOT)
        assert mirrored.is_file() and sha(path)==sha(mirrored), 'Final checkpoint differs: '+path.name
        checks.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':sha(path)})
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    audit={'record_id':result['record_id'],'run_id':state['run_id'],'checked_at_utc':datetime.now(timezone.utc).isoformat(),
           'final_checkpoint_readback':'pass','files':checks,'qc_status':'pending','training_ready':False}
    audit_path=ROOT/'step2a_logs'/f'2b_final_readback_{stamp}.json'
    with audit_path.open('x') as stream:json.dump(audit,stream,indent=2)
    shutil.copyfile(audit_path,DRIVE/audit_path.relative_to(ROOT))
    assert sha(audit_path)==sha(DRIVE/audit_path.relative_to(ROOT))
    # Preserve the orchestration stdout now that processing has exited.
    processlog=Path(state['log']); target=DRIVE/processlog.relative_to(ROOT)
    if not target.exists():shutil.copyfile(processlog,target)
    assert sha(processlog)==sha(target)
    paths=[]
    for folder in [ROOT/'step2a_logs',run]:
        paths.extend(p for p in folder.rglob('*') if p.is_file() and p.suffix in ALLOWED)
    paths += [processlog,ROOT/'step2a_runtime.json']
    for folder in sorted(run.parent.iterdir()):
        if folder==run or not folder.is_dir():continue
        paths.extend(p for p in folder.iterdir() if p.is_file() and p.suffix in {'.json','.py','.log'})
    for path in ROOT.glob('pilot_*.process.log'):paths.append(path)
    for path in (ROOT/'diagnostics').glob('*.txt'):
        target=DRIVE/path.relative_to(ROOT);target.parent.mkdir(exist_ok=True)
        if not target.exists():shutil.copyfile(path,target)
        assert sha(path)==sha(target)
        paths.append(path)
    name='MRI_sub-mindo304_step2B_reports_'+stamp+'.zip'
    bundle=ROOT/name
    summary={'record_id':result['record_id'],'run_id':result['run_id'],
        'result':'T1 technical preprocessing complete; manual anatomical QC and recipe acceptance still required',
        'n4_seconds_original':result['timings'].get('reused_n4_original_seconds',result['timings']['n4_seconds']),
        'timings':result['timings'],'output_shape':result['output_shape'],
        'output_spacing_mm':result['output_spacing_mm'],'output_orientation':result['output_orientation'],
        'final_checkpoint_readback':'pass','nifti_and_weights_in_this_zip':False,
        'input_recipe_confirmed':False,'qc_status':'pending','training_ready':False,
        'freesurfer':'not_run','fmri':'not_run','classification':'not_run'}
    with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('SUMMARY.json',json.dumps(summary,indent=2))
        archive.writestr('README.txt','First-case 2B technical evidence. Read SUMMARY.json and the final handoff_pilot.json. Historical failed/stopped attempts are retained with separate run IDs. qc_status=pending and input_recipe_confirmed=false are deliberate. Review QC PNGs before accepting the T1 handoff. This ZIP excludes all NIfTI files and model weights; they remain in the project Drive folder. No FreeSurfer, fMRI processing, encoder feature extraction, classifier training or AUC is included. No anatomical segmentation GT was used to validate these brain masks.')
        for path in sorted(set(paths)):
            assert path.suffix in ALLOWED
            archive.write(path,arcname=str(path.relative_to(ROOT)))
    target=DRIVE/'reports'/name;target.parent.mkdir(exist_ok=True)
    shutil.copyfile(bundle,target);assert sha(bundle)==sha(target)
    print(json.dumps({'bundle':str(bundle),'bytes':bundle.stat().st_size,'sha256':sha(bundle),
                     'verified_final_files':len(checks),'summary':summary},indent=2))


if __name__=='__main__':main()
