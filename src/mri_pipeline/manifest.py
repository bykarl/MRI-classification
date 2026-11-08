"""Generate pilot entries from the unchanged, pinned data inventory."""
import csv
import json
from pathlib import Path
from .io import read_csv, unique_rows, verified

PINNED_MANIFEST = '8c36e85113f3a5b5e853b471f664397c74ed79eca71e014cd198aa82076da0a2'
PILOT_IDS = ['sub-mindo304', 'sub-mindo379', 'sub-mindm324', 'sub-mindo365', 'sub-mindo404']


def pilot_rows(repo):
    d = Path(repo) / 'dataset_Mi'
    manifest = json.loads(verified(d / 'dataset_manifest.json', PINNED_MANIFEST).read_text(encoding='utf-8'))
    files = {f['path']: f for f in manifest['files']}
    subjects = unique_rows(read_csv(d / 'subjects.csv'), 'participant_id')
    people = unique_rows(read_csv(d / 'rawdata/participants.tsv', '\t'), 'participant_id')
    candidates = unique_rows(read_csv(d / 'qc/all_candidates.csv'), 'participant_id')
    result = []
    for pid in PILOT_IDS:
        s, p, q = subjects[pid], people[pid], candidates[pid]
        if s['group'] != p['group'] or s['group'] != q['group']:
            raise ValueError('Conflicting labels: ' + pid)
        if s['same_session'] != 'True' or s['scanner_upgrade'] != 'UHP_post_upgrade':
            raise ValueError('Unexpected pilot session/batch')
        t1, bold = s['primary_t1_path'], s['fmri_path']
        if '/ses-placebo/' not in t1 or '/ses-placebo/' not in bold:
            raise ValueError('Unexpected session')
        for name in [t1, bold, t1.replace('.nii.gz', '.json'), bold.replace('.nii.gz', '.json')]:
            if name not in files:
                raise ValueError('Missing manifest entry: ' + name)
        result.append(dict(record_id=pid + '_ses-placebo', participant_id=pid,
            session_id='ses-placebo', person_id='', identity_status='unconfirmed',
            diagnosis=s['group'], label=s['label'], age=p['age'], sex=p['sex'],
            education_code=p['education_years'], scanner_batch=s['scanner_upgrade'],
            same_session='True', t1_path=t1, bold_path=bold,
            t1_sha256=files[t1]['sha256'], bold_sha256=files[bold]['sha256'],
            tr_sec=q['tr_sec'], n_frames_source=q['n_volumes'],
            diagnosis_source='participants.tsv/group', diagnosis_status='timing_unverified',
            qc_status='pending', training_ready='False'))
    return result


def write_pilot(repo, output):
    rows = pilot_rows(repo)
    p = Path(output)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
