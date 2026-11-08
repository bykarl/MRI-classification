"""Materialize a new status report from immutable per-run JSON events."""
from pathlib import Path
import argparse
import csv
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from mri_pipeline.io import read_csv, read_json


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template',type=Path,default=Path('manifests/processing_status.csv'))
    p.add_argument('--logs',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    rows=read_csv(args.template)
    by_key={(r['record_id'],r['stage'],r['pipeline_id']):r for r in rows}
    stage_map={'fc':'fc77','jepa':'brain_jepa'}
    events=[read_json(f) for f in args.logs.glob('*.json')]
    skipped=0
    for event in sorted(events,key=lambda e:e.get('finished_at','')):
        if not event.get('record_id') or not event.get('pipeline_id') or event.get('stage') not in {'brainiac','structure','fc','jepa'}:
            skipped+=1;continue
        stage=stage_map.get(event['stage'],event['stage'])
        key=(event['record_id'],stage,event['pipeline_id'])
        initial=(event['record_id'],stage,'')
        row=by_key.get(key)
        if row is None:
            row=dict(by_key.get(initial,{k:'' for k in rows[0]}))
            row.update(record_id=event['record_id'],stage=stage,pipeline_id=event['pipeline_id'],owner='Ye Boyang')
            by_key[key]=row
            by_key.pop(initial,None)
        for field in ['status','qc_status','started_at','finished_at','elapsed_sec','output_uri','checksum','error_message','qc_reviewer']:
            if field in event:row[field]=event[field]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(by_key.values())
    print('Wrote new report:',args.output,'; unmatched events retained in logs:',skipped)


if __name__=='__main__':main()
