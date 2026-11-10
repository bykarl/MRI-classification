"""Install/check only the pinned FreeSurfer package, without Google Drive access.

This does not mount Drive, read patient inputs, initialize a subject, or run recon-all.
Full patient-input preflight remains mandatory before any reconstruction.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--code-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--license-accepted', action='store_true')
    a = p.parse_args()
    if not a.license_accepted:
        raise RuntimeError('User acceptance of the official license is required')
    root = a.code_root.resolve()
    snapshot = json.loads((root / 'source_snapshot.json').read_text())
    if snapshot['commit'] != 'd8bdfa7a125c9153943081f436eaf13966fea65d':
        raise RuntimeError('Unexpected source snapshot')
    for relative, expected in snapshot['files_sha256'].items():
        if sha(root / relative) != expected:
            raise RuntimeError('Pinned source hash differs: ' + relative)
    sys.path.insert(0, str(root / 'scripts'))
    import freesurfer_pilot as fs
    cfg = fs.load_config(root / 'configs/freesurfer_pilot.json')
    a.output.mkdir(parents=True, exist_ok=False)
    state = {'started_at_utc': fs.now(), 'source_commit': snapshot['commit'],
             'installer_sha256': sha(__file__), 'reconstruction_started': False,
             'drive_accessed': False, 'patient_inputs_checked': False,
             'qc_status': 'pending', 'training_ready': False}

    def phase(name, **extra):
        state.update(phase=name, updated_at_utc=fs.now(), **extra)
        temp = a.output / 'state.json.tmp'
        temp.write_text(json.dumps(state, indent=2))
        temp.replace(a.output / 'state.json')
        print(name, flush=True)

    try:
        resource = fs.runtime_info()
        if resource['os_id'] != 'ubuntu' or resource['os_version'] not in cfg['packages']:
            raise RuntimeError('Unsupported operating system')
        if resource['architecture'] not in ('x86_64', 'amd64') or not resource['avx_present']:
            raise RuntimeError('Need amd64 CPU with AVX')
        if resource['effective_memory_gib'] < cfg['minimum_memory_gib']:
            raise RuntimeError('Insufficient effective memory for the selected recipe')
        if resource['free_disk_gib'] < cfg['minimum_free_disk_gib']:
            raise RuntimeError('Insufficient local disk')
        license_file = Path(cfg['fs_license'])
        if not license_file.is_file() or not 0 < license_file.stat().st_size < 65536:
            raise RuntimeError('Private license file missing or unexpected size')
        license_file.chmod(0o600)
        phase('resource_and_license_file_checks_pass', runtime=resource, license_file_present=True)
        pkg = cfg['packages'][resource['os_version']]
        if not pkg['url'].startswith('https://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/8.2.0/'):
            raise RuntimeError('Unexpected package origin/version')
        cache = Path(cfg['project_root']) / 'step2c_downloads'
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / Path(pkg['url']).name
        partial = target.with_name(target.name + '.partial')
        phase('downloading_official_package', package_path=str(target), partial_path=str(partial),
              official_url=pkg['url'], official_md5=pkg['md5'])
        if not target.exists():
            subprocess.run(['curl', '--fail', '--location', '--proto', '=https', '--retry', '3',
                            '--continue-at', '-', '--output', str(partial), pkg['url']], check=True)
            if fs.digest(partial, 'md5') != pkg['md5']:
                raise RuntimeError('Official package MD5 mismatch; download retained, not installed')
            partial.rename(target)
        if fs.digest(target, 'md5') != pkg['md5']:
            raise RuntimeError('Cached package MD5 mismatch')
        phase('package_verified', package_bytes=target.stat().st_size, package_sha256=sha(target))
        subprocess.run(['apt-get', 'update'], check=True)
        phase('installing_vendor_package')
        subprocess.run(['apt-get', 'install', '-y', str(target)], check=True,
                       env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})
        phase('checking_installed_version_and_libraries')
        fingerprint = fs.fingerprint(cfg)
        subprocess.run(fs.fs_command(cfg, ['mri_convert', '--version']),
                       env=fs.fs_env(cfg), check=True)
        if not (Path(cfg['freesurfer_home']) / 'subjects/fsaverage').is_dir():
            raise RuntimeError('Installed fsaverage directory missing')
        phase('completed', software_checks='pass', fingerprint=fingerprint,
              finished_at_utc=fs.now(), note='Software checks only; patient preflight/QC remain pending')
        (a.output / 'completed.json').write_text(json.dumps(state, indent=2))
    except BaseException as error:
        phase('failed', error_type=type(error).__name__, error=str(error))
        raise


if __name__ == '__main__':
    main()
