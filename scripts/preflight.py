"""Report missing pilot assets; never installs, downloads or runs a model."""
from pathlib import Path
import argparse
import importlib.util
import json
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import yaml
from mri_pipeline.io import environment, sha256, read_json, inside, verified


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--paths',default='configs/paths.example.yaml',type=Path)
    p.add_argument('--config',default='configs/pilot.yaml',type=Path)
    p.add_argument('--encoder',choices=['brainiac','brain_jepa'],default='brainiac')
    args=p.parse_args()
    paths=yaml.safe_load(args.paths.read_text(encoding='utf-8'))
    cfg=yaml.safe_load(args.config.read_text(encoding='utf-8'))
    missing=[]
    for key in ['code_root','data_root','artifact_root',args.encoder+'_repo',args.encoder+'_checkpoint']:
        if not paths.get(key):
            missing.append('Set paths.'+key)
        elif key != 'artifact_root' and not Path(paths[key]).exists():
            missing.append('Path does not exist: '+key)
    model=cfg[args.encoder]
    deps = ['torch','monai','nibabel'] if args.encoder=='brainiac' else ['torch']
    if args.encoder == 'brain_jepa' and model.get('attention_backend') != 'normal_no_flash':
        deps += ['flash_attn']
    for dep in deps:
        if importlib.util.find_spec(dep) is None:
            missing.append('Install in isolated encoder environment: '+dep)
    for key in (['checkpoint_sha256','template_sha256','input_recipe_confirmed'] if args.encoder=='brainiac' else
                ['checkpoint_sha256','checkpoint_key','atlas_contract','gradient_csv','gradient_sha256','normalization','pooling','recipe_confirmed']):
        if not model.get(key): missing.append('Confirm '+args.encoder+'.'+key)
    checkpoint=paths.get(args.encoder+'_checkpoint')
    if checkpoint and Path(checkpoint).is_file() and model.get('checkpoint_sha256'):
        if sha256(checkpoint)!=model['checkpoint_sha256']: missing.append('Checkpoint SHA-256 mismatch')
    root=paths.get('code_root')
    if root and Path(root).is_dir():
        check=subprocess.run(['git','-C',root,'branch','--show-current'],capture_output=True,text=True)
        if not (Path(root)/'.git').exists() or check.returncode:
            snapshot=Path(root)/'CODE_SNAPSHOT.json'
            if not snapshot.is_file():
                missing.append('Use a karl checkout or a verified packaged code snapshot')
            else:
                try:
                    metadata=read_json(snapshot)
                    if metadata['branch']!='karl' or not metadata.get('base_commit') or not metadata.get('files'):
                        raise ValueError('Invalid snapshot branch/base/files')
                    for name,digest in metadata['files'].items():verified(inside(root,name),digest)
                except (ValueError,KeyError,OSError) as exc:
                    missing.append('Code snapshot verification failed: '+str(exc))
        elif check.stdout.strip()!='karl': missing.append('Project checkout must be on karl')
    print(json.dumps({'status':'blocked' if missing else 'configured_not_runtime_verified',
        'encoder':args.encoder,'missing':missing,'environment':environment()},ensure_ascii=False,indent=2))
    return 2 if missing else 0


if __name__=='__main__':
    raise SystemExit(main())
