"""Copy only this project's first-case assets/reports into a mounted Drive.

Run after the user authorizes google.colab.drive.mount separately. Does not
inspect unrelated Drive folders, overwrite differing files, or copy venvs.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()


def main():
    root=Path('/content/FYP_MRI_LiYang')
    mount=Path('/content/drive/MyDrive')
    assert mount.is_dir(), 'Google Drive must be mounted by authorized user first'
    destination=mount/'FYP_MRI_LiYang'
    destination.mkdir(exist_ok=True)
    report=json.loads((root/'step2a_logs/verification.json').read_text())
    assert report['record_id']=='sub-mindo304_ses-placebo'
    # Copy explicit project subtrees only. Keep previous attempts as evidence.
    paths=[]
    for folder in ['dataset_Mi/rawdata/sub-mindo304','intake_v2','assets','step2a_logs']:
        paths.extend(p for p in (root/folder).rglob('*') if p.is_file())
    for name in ['verify_t1_environment.py','step2a_runtime.json','install_t1_tools.py','persist_step2a.py']:
        path=root/name
        if path.exists(): paths.append(path)
    entries=[]
    for source in sorted(set(paths)):
        rel=source.relative_to(root)
        target=destination/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        original=sha(source)
        if target.exists():
            assert sha(target)==original, 'Refusing different existing output: '+str(rel)
        else:
            temporary=target.with_name(target.name+'.partial')
            assert not temporary.exists(), 'Inspect previous partial file: '+str(temporary)
            shutil.copyfile(source,temporary)
            assert sha(temporary)==original
            temporary.rename(target)
        assert sha(target)==original
        entries.append({'path':str(rel),'bytes':target.stat().st_size,'sha256':original})
    weight=Path.home()/'hd-bet_params/0.model'
    assert sha(weight)==report['hdbet_weight']['sha256']
    target=destination/'assets/hdbet_legacy/0.model'
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        assert sha(target)==sha(weight)
    else:
        shutil.copyfile(weight,target)
    assert sha(target)==sha(weight)
    entries.append({'path':str(target.relative_to(destination)), 'bytes':target.stat().st_size,'sha256':sha(target)})
    summary={'saved_at_utc':datetime.now(timezone.utc).isoformat(),
             'record_id':report['record_id'],'persistent_readback':'pass','files':entries,
             'venv_copied':False,'reinstall_from_scripts_and_freeze':True,
             'scientific_preprocessing_started':False,'qc_status':'pending','training_ready':False,
             'recipe_confirmation':'pending_feature_owner_review'}
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for directory in [root/'step2a_logs',destination/'step2a_logs']:
        path=directory/f'persistence_{stamp}.json'
        with path.open('x') as stream: json.dump(summary,stream,indent=2)
    print(json.dumps({'persistent_readback':'pass','files_verified':len(entries),
                      'total_bytes':sum(x['bytes'] for x in entries),'destination':str(destination),
                      'preprocessing_started':False,'input_recipe_confirmed':False},indent=2))


if __name__=='__main__':
    main()
