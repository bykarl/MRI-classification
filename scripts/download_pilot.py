"""Optional targeted helper; default is a plan, never a download.

Uses the UNCHANGED current downloader and its original pinned full manifest.
--record-id belongs to THIS helper, not dataset_Mi/download_dataset.py.
"""
from pathlib import Path
import argparse
import importlib.util
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from mri_pipeline.io import read_csv, unique_rows, verified
from mri_pipeline.manifest import PINNED_MANIFEST


def main():
    repo = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--record-id', required=True)
    p.add_argument('--output', type=Path)
    p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    manifest = json.loads(verified(repo/'dataset_Mi/dataset_manifest.json', PINNED_MANIFEST).read_text(encoding='utf-8'))
    row = unique_rows(read_csv(repo/'manifests/pilot_subjects.csv'))[args.record_id]
    selected = [f for f in manifest['files'] if f['path'] in {row['t1_path'],row['bold_path']}]
    if len(selected) != 2:
        raise ValueError('Expected exactly one T1 and one BOLD manifest entry')
    print(json.dumps({'mode':'execute' if args.execute else 'plan_only', 'images':selected,
        'support_archive_bytes':manifest['support_archive']['bytes'],
        'note':'Execute restores all allowed support metadata, then only these two MRI files.'},ensure_ascii=False,indent=2))
    if not args.execute:
        return
    if args.output is None:
        p.error('--output is required with --execute')
    downloader=verified(repo/'dataset_Mi/download_dataset.py','2c683e8916592f06d3d11215968a92c3adc19e1260939d2b42d1965409c7c4dc')
    spec = importlib.util.spec_from_file_location('current_dataset_downloader',downloader)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    if module.EXPECTED_MANIFEST_SHA256 != PINNED_MANIFEST:
        raise ValueError('Downloader/manifest pin mismatch')
    root = args.output.resolve()
    cache = root.parent/(root.name+'_deduplicated_download_cache')
    cache.mkdir(parents=True,exist_ok=True)
    loaded = module.load_manifest(repo/'dataset_Mi/dataset_manifest.json',cache)
    module.preflight_output(root,loaded)
    root.mkdir(parents=True,exist_ok=True)
    module.restore_support(root,cache,loaded)
    for item in selected:
        module.fetch(item['url'],module.inside(root,item['path']),item['sha256'],item['bytes'])
    print('Selected MRI verified. QC remains pending; no training_ready promotion.')


if __name__ == '__main__':
    main()
