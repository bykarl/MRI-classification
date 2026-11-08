"""Strict record-key joins, provenance checks and formal-cohort eligibility."""
from pathlib import Path
import numpy as np
from .io import load_component, unique_rows


def merge_features(rows, feature_root, components=('s_t1_raw', 's_fmri', 'z_t1', 'z_fmri')):
    keyed = unique_rows(rows)
    ids = sorted(keyed)
    result = {'record_id': np.asarray(ids)}
    schemas, reference = {}, {}
    for component in components:
        arrays = []
        for rid in ids:
            values, meta = load_component(Path(feature_root) / rid, component)
            if meta['record_id'] != rid or meta['component'] != component or meta['qc_status'] != 'pass':
                raise ValueError('Feature ID/component/QC mismatch: ' + rid)
            signature = {'names': meta['names'], 'recipe': meta.get('recipe'),
                         'pipeline_id': meta['pipeline_id'], 'feature_set_id': meta['feature_set_id']}
            if signature['recipe'] is None:
                raise ValueError('Missing input/model recipe provenance')
            if component in reference and reference[component] != signature:
                raise ValueError('Inconsistent feature recipe/schema: ' + component)
            reference[component] = signature
            schemas[component] = signature
            if component == 's_t1_raw':
                if len(values) != 82 or not np.isfinite(meta.get('icv_mm3', np.nan)) or meta['icv_mm3'] <= 0 or not meta.get('icv_method'):
                    raise ValueError('82 raw volumes and explicit ICV metadata are required')
            if component == 's_fmri' and len(values) != 77:
                raise ValueError('Expected 77 FC summaries')
            arrays.append(values)
        result[component] = np.stack(arrays)
    for field in ('person_id', 'identity_status', 'diagnosis_status', 'qc_status', 'training_ready', 'sex', 'education_code'):
        result[field] = np.asarray([keyed[r].get(field, '') for r in ids], dtype=str)
    result['age'] = np.asarray([float(keyed[r]['age']) if keyed[r].get('age') not in ('', None, 'n/a') else np.nan for r in ids])
    labels = [keyed[r]['label'] for r in ids]
    if not set(labels) <= {'0', '1'}:
        raise ValueError('Labels must be explicit CN=0 / MCI=1')
    result['label'] = np.asarray(labels, dtype=int)
    if 's_t1_raw' in components:
        result['icv_mm3'] = np.asarray([load_component(Path(feature_root)/r, 's_t1_raw')[1]['icv_mm3'] for r in ids])
    # FC and encoder must use the same exact window; allow T1-only datasets.
    if 's_fmri' in components and 'z_fmri' in components:
        for rid in ids:
            fc = load_component(Path(feature_root)/rid, 's_fmri')[1]
            z = load_component(Path(feature_root)/rid, 'z_fmri')[1]
            if not fc.get('window_id') or fc['window_id'] != z.get('window_id'):
                raise ValueError('FC and Brain-JEPA window mismatch: ' + rid)
            for field in ('roi_order_sha256','pipeline_id'):
                if not fc.get(field) or fc[field] != z.get(field):
                    raise ValueError('FC and Brain-JEPA input/ROI mismatch: ' + rid)
            sources = [m.get('source_files',{}).get('roi_timeseries',{}).get('sha256') for m in (fc,z)]
            if not sources[0] or sources[0] != sources[1]:
                raise ValueError('FC and Brain-JEPA source timeseries mismatch: ' + rid)
    return result, schemas


def formal_eligibility(data):
    n = len(data['label'])
    if len(set(data['record_id'])) != n:
        raise ValueError('Duplicate record IDs')
    required = {'identity_status': 'confirmed', 'diagnosis_status': 'confirmed',
                'qc_status': 'pass', 'training_ready': 'True'}
    for field, expected in required.items():
        if not np.all(np.asarray(data[field]) == expected):
            raise ValueError(f'Formal validation blocked: {field} must be {expected}')
    groups = np.asarray(data['person_id'])
    if any(not str(g).strip() for g in groups):
        raise ValueError('Confirmed natural-person groups are required')
    for g in np.unique(groups):
        if len(set(np.asarray(data['label'])[groups == g])) != 1:
            raise ValueError('Conflicting diagnoses within a person; resolve visit policy first')
    return True
