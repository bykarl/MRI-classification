"""Deterministic continuous windows and signed 77-summary connectivity."""
import itertools
import numpy as np
from .io import array_finite

NETWORKS = ('Vis', 'SomMot', 'DorsAttn', 'SalVentAttn', 'Limbic', 'Cont', 'Default')
STRUCTURES = ('thalamus', 'caudate', 'putamen', 'pallidum', 'hippocampus', 'amygdala', 'accumbens')


def select_window(fd, acceptable, frame_indices, length=160):
    """QC decisions are caller-supplied; do not invent a motion threshold."""
    fd = array_finite(fd, ndim=1)
    good = np.asarray(acceptable)
    index = np.asarray(frame_indices)
    if good.dtype != bool or good.shape != fd.shape or index.shape != fd.shape:
        raise ValueError('FD, boolean QC mask, and original frame mapping must align')
    if np.any(fd < 0) or not np.issubdtype(index.dtype, np.integer) or np.any(index<0) or np.any(np.diff(index) <= 0):
        raise ValueError('Original frame indices must increase uniquely')
    if length < 2:
        raise ValueError('Invalid window length')
    options = []
    for start in range(len(fd) - length + 1):
        end = start + length
        if good[start:end].all() and np.all(np.diff(index[start:end]) == 1):
            options.append((float(fd[start:end].mean()), start, end))
    if not options:
        raise ValueError('No acceptable continuous window')
    mean_fd, start, end = min(options)  # earliest start breaks exact ties
    return {'row_start': start, 'row_end_exclusive': end,
            'start_frame': int(index[start]), 'end_frame_exclusive': int(index[end-1]+1),
            'frame_indices': index[start:end].tolist(), 'mean_fd_mm': mean_fd}


def window_data(timeseries, window):
    x = array_finite(timeseries, ndim=2)
    start, end = window['row_start'], window['row_end_exclusive']
    indices = np.asarray(window['frame_indices'])
    if not (0 <= start < end <= len(x)) or end-start != 160 or len(indices) != 160:
        raise ValueError('Expected a valid 160-frame window within supplied full series')
    if not np.issubdtype(indices.dtype,np.integer) or indices[0]<0 or not np.all(np.diff(indices) == 1) or indices[0] != window['start_frame'] or indices[-1]+1 != window['end_frame_exclusive']:
        raise ValueError('Window is not a contiguous original-time segment')
    return x[start:end]


def validate_roi_order(rows):
    if len(rows) != 450:
        raise ValueError('Expected 450 explicitly ordered ROIs')
    labels = set()
    for i, r in enumerate(rows):
        if int(r['column_index']) != i or not r.get('roi_name') or not r.get('atlas_label'):
            raise ValueError('ROI column indices/names/labels must be explicit and ordered')
        if r['atlas_label'] in labels:
            raise ValueError('Duplicate atlas label')
        labels.add(r['atlas_label'])
        if r.get('hemisphere') not in {'L', 'R'}:
            raise ValueError('Unspecified ROI hemisphere')
        kind = r['structure_type']
        if kind == 'cortical' and r.get('network7') not in NETWORKS:
            raise ValueError('Missing/unrecognized cortical network7 mapping')
        if kind == 'subcortical' and r.get('parent_structure') not in STRUCTURES:
            raise ValueError('Missing subcortical anatomical parent mapping')
        if kind not in {'cortical', 'subcortical'}:
            raise ValueError('Unknown structure_type')
    if sum(r['structure_type'] == 'cortical' for r in rows) != 400:
        raise ValueError('Expected exactly 400 cortical and 50 subcortical ROIs')
    return rows


def connectivity77(timeseries, roi_order, epsilon=1e-6):
    x = array_finite(timeseries, ndim=2).astype(float)
    validate_roi_order(roi_order)
    if x.shape != (160, 450) or not (0 < epsilon < 0.01):
        raise ValueError('FC requires the shared [160,450] window and explicit clipping')
    if np.any(np.std(x, axis=0) == 0):
        raise ValueError('Zero variance ROI; cannot compute Pearson correlation')
    r = np.corrcoef(x, rowvar=False)
    z = np.arctanh(np.clip(r, -1+epsilon, 1-epsilon))
    groups = {n: [i for i, a in enumerate(roi_order) if a['structure_type']=='cortical' and a['network7']==n] for n in NETWORKS}
    sub = {n: [i for i, a in enumerate(roi_order) if a['structure_type']=='subcortical' and a['parent_structure']==n] for n in STRUCTURES}
    values, names, counts = [], [], []
    def summarize(name, edges):
        edges = list(edges)
        if not edges:
            raise ValueError('Empty FC edge set: ' + name)
        values.append(float(np.mean([z[a,b] for a,b in edges])))
        names.append(name)
        counts.append(len(edges))
    for a, b in itertools.combinations_with_replacement(NETWORKS, 2):
        edges = itertools.combinations(groups[a], 2) if a == b else itertools.product(groups[a], groups[b])
        summarize(f'cortex_{a}__{b}', edges)
    for a in STRUCTURES:
        for b in NETWORKS:
            summarize(f'subcortex_{a}__{b}', itertools.product(sub[a], groups[b]))
    return np.asarray(values), {'names': names, 'edge_counts': counts, 'fisher_clip_epsilon': epsilon}
