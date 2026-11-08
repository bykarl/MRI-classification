"""Explicit formal-validation entry; fails closed on pilot/unconfirmed cohorts."""
from pathlib import Path
from dataclasses import asdict
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import yaml
from mri_pipeline.io import write_json, sha256, environment
from mri_pipeline.features import formal_eligibility
from mri_pipeline.models import Parameters, nested_evaluate, bootstrap_auc


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',required=True,type=Path)
    p.add_argument('--config',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    cfg=yaml.safe_load(args.config.read_text(encoding='utf-8'))
    if not cfg.get('decision_confirmed') or any(not cfg.get(k) for k in ['outer_folds','inner_folds','crossfit_folds','repeats','paired_selection_rule']):
        p.error('Fold plan and tuning decisions must be explicitly confirmed after QC')
    with np.load(args.data,allow_pickle=False) as f:
        data={k:f[k] for k in f.files}
    formal_eligibility(data)
    # A new output directory prevents accidental replacement of a prior run.
    args.output.mkdir(parents=True,exist_ok=False)
    result=nested_evaluate(data,[Parameters(**c) for c in cfg['candidates']],
        **{k:cfg[k] for k in ['outer_folds','inner_folds','crossfit_folds','repeats','paired_selection_rule','seed']})
    np.savez_compressed(args.output/'heldout_predictions.npz',probabilities=result.pop('probabilities'),
                       thresholds=result.pop('thresholds'),record_id=data['record_id'],person_id=data['person_id'],label=data['label'])
    with np.load(args.output/'heldout_predictions.npz',allow_pickle=False) as f:
        intervals=bootstrap_auc(data['label'],f['probabilities'],data['person_id'])
    intervals={k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in intervals.items()}
    write_json(args.output/'evaluation.json',{**result,'intervals':intervals,'configuration':cfg,
        'data_sha256':sha256(args.data),'config_sha256':sha256(args.config),'environment':environment()})


if __name__=='__main__':
    main()
