"""Small licensed conversion of a vendor template; never reads patient MRI."""
import argparse
import gzip
import json
from pathlib import Path
import struct
import subprocess
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--code-root', type=Path, required=True)
    p.add_argument('--completed', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    sys.path.insert(0, str(a.code_root / 'scripts'))
    import freesurfer_pilot as fs
    cfg = fs.load_config(a.code_root / 'configs/freesurfer_pilot.json')
    installed = fs.read_json(a.completed)
    if installed.get('phase') != 'completed' or installed.get('software_checks') != 'pass':
        raise RuntimeError('Require actual completed software checks before the probe')
    if fs.fingerprint(cfg) != installed['fingerprint']:
        raise RuntimeError('Installed build changed after verification')
    mri = Path(cfg['freesurfer_home']) / 'subjects/fsaverage/mri'
    candidates = [mri / name for name in ('T1.mgz', 'brain.mgz', 'orig.mgz')]
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        raise RuntimeError('No expected vendor fsaverage MRI available for the probe')
    a.output.mkdir(parents=True, exist_ok=False)
    output = a.output / 'vendor_template_probe.nii.gz'
    command = fs.fs_command(cfg, ['mri_convert', str(source), str(output)])
    with (a.output / 'conversion.log').open('x') as log:
        subprocess.run(command, env=fs.fs_env(cfg), stdout=log, stderr=subprocess.STDOUT, check=True)
    with gzip.open(output, 'rb') as stream:
        header = stream.read(348)
    if len(header) != 348 or header[344:348] != b'n+1\0':
        raise RuntimeError('Expected a complete NIfTI-1 single-file output header')
    endian = '<' if struct.unpack('<i', header[:4])[0] == 348 else '>'
    dims = struct.unpack(endian + '8h', header[40:56])
    if any(size <= 0 for size in dims[1:4]):
        raise RuntimeError('Invalid generated spatial dimensions')
    report = {'checked_at_utc': fs.now(), 'software_checks': 'pass',
              'license_file_present': Path(cfg['fs_license']).is_file(),
              'licensed_vendor_template_conversion': 'pass',
              'probe_input': 'FreeSurfer vendor fsaverage/mri/' + source.name,
              'probe_input_sha256': fs.digest(source), 'probe_output_sha256': fs.digest(output),
              'output_shape': list(dims[1:4]), 'fingerprint': installed['fingerprint'],
              'patient_inputs_checked': False, 'drive_accessed': False,
              'reconstruction_started': False, 'qc_status': 'pending', 'training_ready': False}
    fs.write_new(a.output / 'verification.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
