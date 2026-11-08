"""Single-record stage execution with explicit handoff and failure evidence."""
from pathlib import Path
import argparse
import json
import sys
import time
import uuid
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import yaml
from mri_pipeline.io import (read_csv, read_json, write_json, sha256, verified,
    save_component, finalize_features, inside, environment)
from mri_pipeline.encoders import check_handoff, brainiac, brain_jepa
from mri_pipeline.fmri import window_data, connectivity77
from mri_pipeline.structure import volumes82, volume_record


def run(args, paths, config):
    root = Path(paths['artifact_root'])
    stage = 't1' if args.stage == 'brainiac' else 'structure' if args.stage == 'structure' else 'fmri'
    handoff, item = check_handoff(args.handoff,stage)
    rid = handoff['record_id']
    def file(key):
        return inside(Path(args.handoff).resolve().parent,item['files'][key]['path'])
    meta = {'pipeline_id':handoff['pipeline_id'],'qc_status':'pass',
            'source_files':item['files'],'handoff_sha256':sha256(args.handoff)}
    if args.stage == 'brainiac':
        model = config['brainiac']
        if item.get('template_sha256') != model.get('template_sha256'):
            raise ValueError('Handoff template differs from confirmed BrainIAC recipe')
        z, detail = brainiac(file('processed_t1'), paths['brainiac_checkpoint'],paths['brainiac_repo'],model,args.device)
        meta.update(detail)
        meta['names'] = [f'brainiac_{i}' for i in range(len(z))]
        meta['recipe'] = model
        component = 'z_t1'
    elif args.stage == 'structure':
        if 'volumes_csv' in item['files']:
            z,names,attributes=volume_record(file('volumes_csv'),rid)
            for key,value in attributes.items():
                if item.get(key) is not None and item[key] != value:
                    raise ValueError('Volume CSV/handoff metadata conflict: '+key)
                item[key]=value
        else:
            z, names = volumes82(file('lh_aparc'),file('rh_aparc'),file('aseg'))
        if not item.get('icv_method') or not np.isfinite(float(item.get('icv_mm3',0))) or float(item.get('icv_mm3',0))<=0 or not item.get('freesurfer_version'):
            raise ValueError('Raw ICV value/method and FreeSurfer version required')
        meta.update(names=names,icv_mm3=float(item['icv_mm3']),icv_method=item['icv_method'])
        meta['recipe'] = {'freesurfer_version':item['freesurfer_version'],'icv_method':item['icv_method'],'units':'mm3'}
        component = 's_t1_raw'
    else:
        full = np.load(file('roi_timeseries'),allow_pickle=False)
        window = read_json(file('window'))
        if not window.get('qc_rule_id') or window.get('tr_sec') != 2.0 or not isinstance(window.get('discarded_initial_frames'),int) or window['discarded_initial_frames']<0:
            raise ValueError('Pilot window must record QC rule, verified TR=2 seconds and discarded initial frames')
        data = window_data(full,window)
        order = read_csv(file('roi_order'),'\t')
        meta['window_id'] = sha256(file('window'))
        meta['roi_order_sha256'] = sha256(file('roi_order'))
        if args.stage == 'fc':
            z, detail = connectivity77(data,order,config['fmri']['fisher_clip_epsilon'])
            meta.update(detail)
            meta['recipe'] = {'roi_order_sha256':meta['roi_order_sha256'],
                              'fisher_clip_epsilon':config['fmri']['fisher_clip_epsilon']}
            component = 's_fmri'
        else:
            model = config['brain_jepa']
            if not model.get('atlas_contract'):
                raise ValueError('Configure the confirmed Brain-JEPA atlas_contract file first')
            contract = read_json(model['atlas_contract'])
            verified(file('roi_order'),contract['roi_order_sha256'])
            z, detail = brain_jepa(data,order,contract,paths['brain_jepa_checkpoint'],paths['brain_jepa_repo'],model,args.device)
            meta.update(detail)
            meta['names'] = [f'brain_jepa_{i}' for i in range(len(z))]
            # Absolute private paths do not define the shared mathematical recipe.
            meta['recipe'] = {k:v for k,v in model.items() if k not in {'atlas_contract','gradient_csv','normalization_params'}}
            meta['recipe']['atlas_contract'] = contract
            component = 'z_fmri'
    target = save_component(root,config['feature_set_id'],rid,component,z,meta)
    return {'record_id':rid,'pipeline_id':handoff['pipeline_id'],'component':component,
            'output_uri':str(target/f'{component}.npy'),'checksum':sha256(target/f'{component}.npy'),
            'output_dim':len(z),'status':'ready','qc_status':'pass','qc_reviewer':item['qc_reviewer']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['brainiac','structure','fc','jepa'])
    p.add_argument('--paths',required=True,type=Path)
    p.add_argument('--config',default='configs/pilot.yaml',type=Path)
    p.add_argument('--handoff',required=True,type=Path)
    p.add_argument('--device',default='cpu')
    args = p.parse_args()
    paths = yaml.safe_load(args.paths.read_text(encoding='utf-8'))
    config = yaml.safe_load(args.config.read_text(encoding='utf-8'))
    if not paths.get('artifact_root'):
        p.error('Set artifact_root to a persistent writable location in your private paths YAML')
    log = {'stage':args.stage,'environment':environment(),'config_sha256':sha256(args.config),
           'handoff':str(args.handoff),'status':'running'}
    log['started_at']=log['environment']['time']
    start=time.perf_counter()
    try:
        if args.handoff.is_file():
            h=read_json(args.handoff)
            log.update(record_id=h.get('record_id'),pipeline_id=h.get('pipeline_id'))
        log.update(run(args,paths,config))
    except Exception as exc:
        log.update(status='failed',error_type=type(exc).__name__,error_message=str(exc),traceback=traceback.format_exc())
        raise
    finally:
        log['elapsed_sec']=time.perf_counter()-start
        log['finished_at']=environment()['time']
        write_json(Path(paths['artifact_root'])/'logs'/f'{args.stage}_{uuid.uuid4().hex}.json',log)
    print(json.dumps(log,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
