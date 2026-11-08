"""End-to-end CLI tests use SYNTHETIC files only; no MRI or encoder weights."""
from pathlib import Path
import csv
import json
import subprocess
import sys
import numpy as np
import yaml
from mri_pipeline.io import sha256
from mri_pipeline.structure import CORTEX, SUBCORTEX

ROOT=Path(__file__).resolve().parents[1]


def command(script,*args,expected=0):
    result=subprocess.run([sys.executable,str(ROOT/'scripts'/script),*map(str,args)],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==expected,(result.stdout,result.stderr)
    return result


def test_cli_synthetic_features_and_status_report(tmp_path,roi_order):
    hroot=tmp_path/'handoff';hroot.mkdir()
    files={}
    for hemi in ['lh','rh']:
        p=hroot/f'{hemi}.stats';p.write_text('\n'.join(f'{n} 1 2 100 4' for n in CORTEX))
        files[hemi+'_aparc']={'path':p.name,'sha256':sha256(p)}
    p=hroot/'aseg.stats';p.write_text('\n'.join(f'1 10 3 200 {side}-{n}' for side in ['Left','Right'] for n in SUBCORTEX))
    files['aseg']={'path':p.name,'sha256':sha256(p)}
    full=hroot/'full.npy';np.save(full,np.random.default_rng(1).normal(size=(240,450)))
    roi=hroot/'order.tsv'
    with roi.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(roi_order[0]),delimiter='\t');w.writeheader();w.writerows(roi_order)
    window=hroot/'window.json';window.write_text(json.dumps({'row_start':0,'row_end_exclusive':160,
        'start_frame':0,'end_frame_exclusive':160,'frame_indices':list(range(160)),
        'tr_sec':2.,'discarded_initial_frames':0,'qc_rule_id':'SYNTHETIC_ONLY'}))
    fmri_files={k:{'path':p.name,'sha256':sha256(p)} for k,p in [('roi_timeseries',full),('roi_order',roi),('window',window)]}
    handoff=hroot/'handoff.json'
    handoff.write_text(json.dumps({'record_id':'SYNTHETIC_record','pipeline_id':'SYNTHETIC_PIPELINE','stages':{
        'structure':{'status':'ready','qc_status':'pass','qc_reviewer':'SYNTHETIC_TEST',
            'icv_mm3':1500000,'icv_method':'SYNTHETIC_TEST','freesurfer_version':'SYNTHETIC_TEST','files':files},
        'fmri':{'status':'ready','qc_status':'pass','qc_reviewer':'SYNTHETIC_TEST','files':fmri_files}}}))
    paths=tmp_path/'paths.yaml';paths.write_text(yaml.safe_dump({'artifact_root':str(tmp_path/'artifacts')}))
    for stage in ['structure','fc']:
        command('run_features.py',stage,'--paths',paths,'--config',ROOT/'configs/pilot.yaml','--handoff',handoff)
    out=tmp_path/'artifacts/features/pilot_v1/SYNTHETIC_record'
    assert np.load(out/'s_t1_raw.npy').shape==(82,)
    assert np.load(out/'s_fmri.npy').shape==(77,)
    manifest=tmp_path/'manifest.csv'
    manifest.write_text('record_id,label,age\nSYNTHETIC_record,0,65\n')
    merged=tmp_path/'merged.npz'
    command('merge_features.py','--manifest',manifest,'--feature-root',out.parent,
            '--output',merged,'--components','s_t1_raw','s_fmri')
    with np.load(merged,allow_pickle=False) as f:
        assert f['record_id'][0]=='SYNTHETIC_record' and f['icv_mm3'][0]==1500000
    report=tmp_path/'status.csv'
    command('report_status.py','--logs',tmp_path/'artifacts/logs','--output',report)
    rows=list(csv.DictReader(report.open()))
    actual=[r for r in rows if r['record_id']=='SYNTHETIC_record']
    assert len(actual)==2 and all(r['status']=='ready' and r['checksum'] for r in actual)


def test_cli_failure_is_logged_without_fake_output(tmp_path):
    h=tmp_path/'handoff.json';h.write_text(json.dumps({'record_id':'SYNTHETIC_record','pipeline_id':'SYNTHETIC',
        'stages':{'t1':{'status':'pending','qc_status':'pending'}}}))
    p=tmp_path/'paths.yaml';p.write_text(yaml.safe_dump({'artifact_root':str(tmp_path/'artifacts')}))
    command('run_features.py','brainiac','--paths',p,'--config',ROOT/'configs/pilot.yaml','--handoff',h,expected=1)
    events=[json.loads(f.read_text()) for f in (tmp_path/'artifacts/logs').glob('*.json')]
    assert len(events)==1 and events[0]['status']=='failed'
    assert 'has not passed QC' in events[0]['error_message']
    assert not (tmp_path/'artifacts/features').exists()


def test_manual_colab_package_preserves_source_hashes_without_git(tmp_path):
    import zipfile
    package=tmp_path/'code.zip'
    command('package_code.py','--output',package)
    with zipfile.ZipFile(package) as z:
        assert not any('/.venv/' in n or '/.tmp/' in n or '/.git/' in n for n in z.namelist())
        z.extractall(tmp_path/'uploaded')
    root=tmp_path/'uploaded/MRI-classification'
    snapshot=json.loads((root/'CODE_SNAPSHOT.json').read_text(encoding='utf-8'))
    assert snapshot['branch']=='karl'
    for name,digest in snapshot['files'].items():assert sha256(root/name)==digest
    paths=tmp_path/'paths.yaml';paths.write_text(yaml.safe_dump({'code_root':str(root)}))
    result=command('preflight.py','--paths',paths,expected=2)
    missing=json.loads(result.stdout)['missing']
    assert not any('snapshot' in m or 'checkout' in m for m in missing)
