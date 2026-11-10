"""Export 82 uncorrected mm3 volumes + FreeSurfer eTIV; never infer human QC."""
import argparse
import csv
import json
import math
from pathlib import Path
import shutil
from freesurfer_pilot import (REPO,load_config,read_json,write_new,digest,run_dir,persistent_run,
                              copy_checked,fingerprint,identifier,now)

STATS=('lh.aparc.stats','rh.aparc.stats','aseg.stats')
ICV_METHOD='FreeSurfer_eTIV_talairach_MNI305'
QC_ITEMS=('skull_strip','aseg_regions','left_white_and_pial','right_white_and_pial',
          'aparc_regions','talairach_registration','subject_matches_native_input')


def stats_table(path,kind):
    text=Path(path).read_text();header=None;result={}
    expected=('StructName','GrayVol') if kind=='aparc' else ('StructName','Volume_mm3')
    for line in text.splitlines():
        if line.startswith('# ColHeaders '): header=line.split()[2:]
        if not line.strip() or line.startswith('#'):continue
        if header is None or expected[0] not in header or expected[1] not in header:
            raise ValueError('Missing/incompatible FreeSurfer column header: '+str(path))
        name_index=header.index(expected[0]);vol_index=header.index(expected[1])
        if (name_index,vol_index)!=((0,3) if kind=='aparc' else (4,3)):
            raise ValueError('Column positions differ from the peer structure.py contract')
        row=line.split()
        if len(row)!=len(header):raise ValueError('Malformed FreeSurfer stats row')
        name=row[name_index]
        if name in result:raise ValueError('Duplicate stats region: '+name)
        value=float(row[vol_index])
        if not math.isfinite(value):raise ValueError('Nonfinite stats volume')
        result[name]=value
    if not result:raise ValueError('No FreeSurfer rows found')
    return result


def etiv(path):
    values=[]
    for line in Path(path).read_text().splitlines():
        if not line.startswith('# Measure '):continue
        row=next(csv.reader([line[len('# Measure '):]],skipinitialspace=True))
        if row[0].strip()!='EstimatedTotalIntraCranialVol':continue
        if len(row)!=5 or row[1].strip()!='eTIV' or row[4].strip() not in ('mm^3','mm3','mm³'):
            raise ValueError('Unexpected eTIV definition or units')
        value=float(row[3])
        if not math.isfinite(value) or value<=0:raise ValueError('Invalid positive finite eTIV')
        values.append(value)
    if len(values)!=1:raise ValueError('Expected exactly one eTIV measure, not brain-mask volume')
    return values[0]


def extract82(stats,names):
    if len(names)!=82 or len(set(names))!=82:raise ValueError('Expected 82 unique schema names')
    left=stats_table(Path(stats)/STATS[0],'aparc');right=stats_table(Path(stats)/STATS[1],'aparc')
    sub=stats_table(Path(stats)/STATS[2],'aseg');values=[]
    for name in names:
        if not name.endswith('_mm3'):raise ValueError('Schema units must be raw mm3')
        if name.startswith(('lh_','rh_')):
            side,region=name[:-4].split('_',1);value=({'lh':left,'rh':right}[side])[region]
        else:
            side,region=name[:-4].split('_',1)
            keys=[side+'-'+region]
            if region=='Thalamus':keys.append(side+'-Thalamus-Proper')
            found=[k for k in keys if k in sub]
            if len(found)!=1:raise ValueError('Missing/ambiguous aseg region: '+name)
            value=sub[found[0]]
        if not math.isfinite(value) or value<=0:raise ValueError('Volume must be positive finite: '+name)
        values.append(value)
    return values,etiv(Path(stats)/STATS[2])


def write_csv(path,rid,names,values,icv,version,qc_status):
    columns=['record_id',*names,'icv_mm3','icv_method','freesurfer_version','qc_status']
    row={'record_id':rid,**dict(zip(names,values)),'icv_mm3':icv,'icv_method':ICV_METHOD,
         'freesurfer_version':version,'qc_status':qc_status}
    with Path(path).open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerow(row)


def prepare_export(cfg,run_id):
    run=run_dir(cfg,run_id);meta=read_json(run/'run.json');complete=read_json(run/'autorecon3.completed.json')
    if meta['config']!=cfg or meta['software_fingerprint']!=fingerprint(cfg):raise RuntimeError('Changed FS/OS/config')
    if complete['exit_code']!=0 or complete['snapshot']['readback']!='pass':raise RuntimeError('Final reconstruction checkpoint not complete')
    schema=REPO/'schemas/t1_volume_names.json'
    if digest(schema)!=cfg['volume_schema_sha256']:raise RuntimeError('Peer 82-column schema changed')
    names=read_json(schema)['names'];stats=run/'subjects'/cfg['subject_id']/'stats'
    for name in STATS:
        if digest(stats/name)!=complete['stats_sha256'][name]:raise RuntimeError('Stats changed after completed checkpoint')
        for line in (stats/name).read_text().splitlines():
            if line.startswith('# subjectname ') and line.split(maxsplit=2)[2].strip()!=cfg['subject_id']:
                raise RuntimeError('Stats subject header differs from first case')
    qc=run/'qc/freesurfer_regions.png'
    if not qc.is_file() or not (run/'qc/provenance.json').is_file():raise RuntimeError('Generate real QC views first')
    values,icv=extract82(stats,names)
    folder=run/'structure/draft';folder.mkdir(parents=True,exist_ok=False)
    (folder/'stats').mkdir();(folder/'qc').mkdir()
    for name in STATS:shutil.copyfile(stats/name,folder/'stats'/name)
    for name in ['freesurfer_regions.png','provenance.json']:shutil.copyfile(run/'qc'/name,folder/'qc'/name)
    write_csv(folder/'t1_volumes_raw.csv',cfg['record_id'],names,values,icv,cfg['freesurfer_version'],'pending')
    files={key:{'path':path,'sha256':digest(folder/path)} for key,path in {
        'volumes_csv':'t1_volumes_raw.csv','lh_aparc':'stats/lh.aparc.stats','rh_aparc':'stats/rh.aparc.stats',
        'aseg':'stats/aseg.stats','qc_image':'qc/freesurfer_regions.png','qc_provenance':'qc/provenance.json'}.items()}
    handoff={'record_id':cfg['record_id'],'pipeline_id':None,'training_ready':False,
        'identity_status':'unconfirmed','diagnosis_status':'timing_unverified',
        'stages':{'structure':{'status':'pending','qc_status':'pending','qc_reviewer':None,
            'icv_mm3':icv,'icv_method':ICV_METHOD,'freesurfer_version':cfg['freesurfer_version'],
            'recipe_id':cfg['recipe_id'],'files':files}}}
    write_new(folder/'handoff.structure.pending.json',handoff)
    write_new(folder/'qc_review.template.json',{'reviewer':'','decision':'pending',
        'checks':dict.fromkeys(QC_ITEMS,False),'notes':'Inspect complete volumes and white/pial surfaces, not only PNG samples.'})
    write_new(folder/'export_provenance.json',{'exported_at_utc':now(),'run_id':run_id,'raw_volumes_corrected':False,
        'input_sha256':cfg['input_sha256'],'stats_sha256':complete['stats_sha256'],
        'volume_schema_sha256':cfg['volume_schema_sha256'],'qc_status':'pending','training_ready':False})
    for path in folder.rglob('*'):
        if path.is_file():copy_checked(path,persistent_run(cfg,run_id)/path.relative_to(run))
    print('DRAFT EXPORTED',str(folder),'human QC and agreed pipeline ID still required')


def finalize(cfg,run_id,review_path,pipeline_id,recipe_confirmed=False):
    if not recipe_confirmed:raise RuntimeError('Team must accept this FS recipe explicitly')
    identifier(pipeline_id);review=read_json(review_path)
    if not review.get('reviewer','').strip() or review.get('decision')!='pass':raise RuntimeError('Named human QC pass required')
    if set(review.get('checks',{}))!=set(QC_ITEMS) or not all(v is True for v in review['checks'].values()):
        raise RuntimeError('Every required anatomical/identity QC check must be explicitly true')
    run=run_dir(cfg,run_id);draft=run/'structure/draft'
    h=read_json(draft/'handoff.structure.pending.json')
    for file in h['stages']['structure']['files'].values():
        if digest(draft/file['path'])!=file['sha256']:raise RuntimeError('Draft output changed after export')
    accepted=run/'structure/accepted';accepted.mkdir(exist_ok=False)
    for file in h['stages']['structure']['files'].values():
        relative=Path(file['path'])
        if relative.is_absolute() or '..' in relative.parts:raise RuntimeError('Unsafe handoff path')
        target=accepted/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(draft/relative,target)
    csvpath=accepted/'t1_volumes_raw.csv'
    with csvpath.open(newline='') as stream:reader=csv.DictReader(stream);columns=reader.fieldnames;rows=list(reader)
    if len(rows)!=1 or rows[0]['record_id']!=cfg['record_id']:raise RuntimeError('CSV identity mismatch')
    rows[0]['qc_status']='pass'
    with csvpath.open('w',newline='') as stream:writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader();writer.writerows(rows)
    h['pipeline_id']=pipeline_id;stage=h['stages']['structure'];stage.update(status='ready',qc_status='pass',qc_reviewer=review['reviewer'])
    stage['files']['volumes_csv']['sha256']=digest(csvpath)
    shutil.copyfile(review_path,accepted/'qc_review.json')
    stage['files']['qc_review']={'path':'qc_review.json','sha256':digest(accepted/'qc_review.json')}
    write_new(accepted/'handoff.json',h)
    write_new(accepted/'acceptance_provenance.json',{'accepted_at_utc':now(),
        'draft_handoff_sha256':digest(draft/'handoff.structure.pending.json'),
        'reviewer':review['reviewer'],'recipe_confirmed':True,'training_ready':False})
    for path in accepted.rglob('*'):
        if path.is_file():copy_checked(path,persistent_run(cfg,run_id)/path.relative_to(run))
    print('STRUCTURE HANDOFF READY:',str(accepted/'handoff.json'),'training_ready remains False')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,default=REPO/'configs/freesurfer_pilot.json')
    sub=p.add_subparsers(dest='command',required=True)
    exp=sub.add_parser('export');exp.add_argument('--run-id',required=True)
    acc=sub.add_parser('finalize');acc.add_argument('--run-id',required=True);acc.add_argument('--review',type=Path,required=True)
    acc.add_argument('--pipeline-id',required=True);acc.add_argument('--recipe-confirmed',action='store_true')
    args=p.parse_args();cfg=load_config(args.config)
    if args.command=='export':prepare_export(cfg,args.run_id)
    else:finalize(cfg,args.run_id,args.review,args.pipeline_id,args.recipe_confirmed)


if __name__=='__main__':main()
