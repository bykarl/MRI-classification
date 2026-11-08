"""Read raw FreeSurfer volumetric statistics without cohort-level fitting."""
from pathlib import Path
import numpy as np
from .io import array_finite, read_csv, unique_rows

CORTEX = ('bankssts caudalanteriorcingulate caudalmiddlefrontal cuneus entorhinal '
    'fusiform inferiorparietal inferiortemporal isthmuscingulate lateraloccipital '
    'lateralorbitofrontal lingual medialorbitofrontal middletemporal parahippocampal '
    'paracentral parsopercularis parsorbitalis parstriangularis pericalcarine '
    'postcentral posteriorcingulate precentral precuneus rostralanteriorcingulate '
    'rostralmiddlefrontal superiorfrontal superiorparietal superiortemporal '
    'supramarginal frontalpole temporalpole transversetemporal insula').split()
SUBCORTEX = ('Thalamus', 'Caudate', 'Putamen', 'Pallidum', 'Hippocampus', 'Amygdala', 'Accumbens-area')
VOLUME_NAMES = [f'{h}_{n}_mm3' for h in ('lh', 'rh') for n in CORTEX] + [
    f'{h}_{n}_mm3' for h in ('Left', 'Right') for n in SUBCORTEX]


def read_stats(path, name_col, volume_col):
    values = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        row = line.split()
        name = row[name_col]
        if name in values:
            raise ValueError('Duplicate stats region: ' + name)
        values[name] = float(row[volume_col])
    return values


def volumes82(lh_aparc, rh_aparc, aseg):
    left, right = read_stats(lh_aparc, 0, 3), read_stats(rh_aparc, 0, 3)
    sub = read_stats(aseg, 4, 3)
    result = [table[name] for table in (left, right) for name in CORTEX]
    for side in ('Left', 'Right'):
        for name in SUBCORTEX:
            candidates = [f'{side}-{name}']
            if name == 'Thalamus':
                candidates.append(f'{side}-Thalamus-Proper')
            present = [key for key in candidates if key in sub]
            if len(present) != 1:
                raise ValueError('Missing/ambiguous aseg region: ' + str(candidates))
            result.append(sub[present[0]])
    array = array_finite(result, ndim=1)
    if len(array) != 82 or np.any(array <= 0):
        raise ValueError('Expected 82 positive raw volumes in mm3')
    return array, list(VOLUME_NAMES)


def volume_record(csv_path, record_id):
    """Accept the agreed t1_volumes_raw.csv interface as well as raw stats."""
    row = unique_rows(read_csv(csv_path))[record_id]
    if row.get('qc_status') != 'pass' or not row.get('icv_method') or not row.get('freesurfer_version'):
        raise ValueError('Volume CSV needs QC pass, ICV method and FreeSurfer version')
    values = array_finite([float(row[n]) for n in VOLUME_NAMES], ndim=1)
    icv = float(row['icv_mm3'])
    if np.any(values<=0) or not np.isfinite(icv) or icv<=0:
        raise ValueError('Volumes and ICV must be positive finite mm3')
    return values, list(VOLUME_NAMES), {'icv_mm3':icv,'icv_method':row['icv_method'],
                                       'freesurfer_version':row['freesurfer_version']}
