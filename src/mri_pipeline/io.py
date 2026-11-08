"""Checksummed, non-overwriting artifacts and small configuration utilities."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
from datetime import datetime, timezone, timedelta
import importlib.metadata
import numpy as np


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def verified(path, expected):
    if not expected or len(expected) != 64:
        raise ValueError('An explicit SHA-256 is required: ' + str(path))
    if sha256(path) != expected:
        raise ValueError('SHA-256 mismatch: ' + str(path))
    return Path(path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    """Exclusive create: never silently replace a prior result."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    with p.open('x', encoding='utf-8', newline='\n') as f:
        f.write(payload)


def read_csv(path, delimiter=','):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=delimiter))


def unique_rows(rows, key='record_id'):
    result = {}
    for row in rows:
        value = row.get(key)
        if not value or value in result:
            raise ValueError(f'Missing or duplicate {key}: {value!r}')
        result[value] = row
    return result


def array_finite(x, *, ndim=None):
    a = np.asarray(x)
    if not np.issubdtype(a.dtype, np.number) or not np.isfinite(a).all():
        raise ValueError('Array must contain finite numeric values')
    if a.size == 0 or (ndim is not None and a.ndim != ndim):
        raise ValueError(f'Unexpected array shape: {a.shape}')
    return a


def inside(root, relative):
    root = Path(root).resolve()
    target = (root / relative).resolve()
    if target == root or root not in target.parents:
        raise ValueError(f'Path escapes root: {relative}')
    return target


def environment():
    versions = {}
    for name in ['numpy', 'scipy', 'scikit-learn', 'torch', 'monai', 'nibabel', 'flash-attn']:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    try:
        ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    except (AttributeError, ValueError, OSError):
        ram = None
    package=Path(__file__).resolve().parent
    root=package.parents[1]
    digest=hashlib.sha256()
    source_files=sorted([*package.glob('*.py'),*(root/'scripts').glob('*.py')])
    for p in source_files:
        digest.update(str(p.relative_to(root)).replace('\\','/').encode('utf-8'))
        digest.update(bytes.fromhex(sha256(p)))
    base_commit=None
    if (root/'.git').exists():
        result=subprocess.run(['git','-C',str(root),'rev-parse','HEAD'],capture_output=True,text=True)
        if result.returncode==0:base_commit=result.stdout.strip()
    elif (root/'CODE_SNAPSHOT.json').is_file():
        base_commit=read_json(root/'CODE_SNAPSHOT.json').get('base_commit')
    return {'time': datetime.now(timezone(timedelta(hours=8))).isoformat(),
            'python': platform.python_version(), 'os': platform.platform(),
            'system_ram_bytes': ram, 'versions': versions,
            'implementation_sha256':digest.hexdigest(),'project_base_commit':base_commit}


def save_component(root, feature_set_id, record_id, component, values, metadata):
    if component not in {'s_t1_raw', 's_fmri', 'z_t1', 'z_fmri'}:
        raise ValueError('Unknown feature component')
    a = array_finite(values, ndim=1)
    for field in ['pipeline_id', 'qc_status', 'source_files', 'names']:
        if not metadata.get(field):
            raise ValueError('Missing feature provenance: ' + field)
    if metadata['qc_status'] != 'pass' or len(metadata['names']) != len(a):
        raise ValueError('QC must pass and feature names must match array length')
    if len(set(metadata['names'])) != len(a):
        raise ValueError('Duplicate feature names')
    path = inside(root, f'features/{feature_set_id}/{record_id}')
    path.mkdir(parents=True, exist_ok=True)
    array_path = path / f'{component}.npy'
    if (path / f'{component}.json').exists():
        raise FileExistsError('Completed component already exists: ' + component)
    with array_path.open('xb') as f:
        np.save(f, a, allow_pickle=False)
    record = {**metadata, 'record_id': record_id, 'feature_set_id': feature_set_id,
              'component': component, 'shape': list(a.shape), 'dtype': str(a.dtype),
              'array_sha256': sha256(array_path), 'environment': environment()}
    write_json(path / f'{component}.json', record)
    return path


def load_component(path, component):
    path = Path(path)
    meta = read_json(path / f'{component}.json')
    verified(path / f'{component}.npy', meta['array_sha256'])
    values = array_finite(np.load(path / f'{component}.npy', allow_pickle=False), ndim=1)
    if list(values.shape) != meta['shape'] or len(meta['names']) != len(values):
        raise ValueError('Feature schema/array mismatch')
    return values, meta


def finalize_features(path, components=('s_t1_raw', 's_fmri', 'z_t1', 'z_fmri')):
    path = Path(path)
    records = {name: load_component(path, name)[1] for name in components}
    if len({m['record_id'] for m in records.values()}) != 1:
        raise ValueError('Component record IDs disagree')
    write_json(path / 'features.json', {'components': records})
