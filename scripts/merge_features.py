from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from mri_pipeline.io import read_csv, write_json, finalize_features, sha256
from mri_pipeline.features import merge_features


def main():
    p=argparse.ArgumentParser(description='Merge real checked features by record_id; never fit a model')
    p.add_argument('--manifest',required=True,type=Path)
    p.add_argument('--feature-root',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    p.add_argument('--components',nargs='+',default=['s_t1_raw','s_fmri','z_t1','z_fmri'])
    args=p.parse_args()
    data, schemas=merge_features(read_csv(args.manifest),args.feature_root,args.components)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.with_suffix('.json').exists() or args.output.exists():
        raise FileExistsError(args.output)
    with args.output.open('xb') as f:
        np.savez_compressed(f,**data)
    provenance={str(rid):{c:sha256(args.feature_root/str(rid)/f'{c}.json') for c in args.components} for rid in data['record_id']}
    write_json(args.output.with_suffix('.json'),{'schemas':schemas,'record_count':len(data['label']),
        'manifest_sha256':sha256(args.manifest),'component_metadata_sha256':provenance,
        'notice':'Feature merge is not formal training eligibility or classification performance.'})
    for rid in data['record_id']:
        target=args.feature_root/str(rid)
        if set(args.components)=={'s_t1_raw','s_fmri','z_t1','z_fmri'} and not (target/'features.json').exists():
            finalize_features(target,args.components)
    print('Merged',len(data['label']),'records; training flags preserved.')


if __name__=='__main__':
    main()
