"""Configure one already-authorized Colab Python 3.12 runtime; no MRI/weights."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import subprocess
import sys
import time
import venv
import zipfile


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    assert sys.version_info[:2] == (3, 12), 'Use the authorized 2026.07 Python 3.12 kernel.'
    root = Path('/content/MRI-classification')
    drive = Path('/content/drive/MyDrive/FYP_MRI')
    assert drive.is_dir(), 'Mount the existing Drive first; do not create a fake mount.'
    assert all((drive / x).is_dir() for x in ('data', 'weights', 'artifacts'))
    actual = hashlib.sha256(args.package.read_bytes()).hexdigest()
    assert actual == args.sha256, 'Code package hash mismatch.'
    with zipfile.ZipFile(args.package) as archive:
        members = archive.namelist()
        for name in members:
            p = PurePosixPath(name)
            assert p.parts[0] == root.name and '..' not in p.parts and not p.is_absolute()
        snapshot = json.loads(archive.read(root.name + '/CODE_SNAPSHOT.json'))
        assert snapshot['branch'] == 'karl'
        assert snapshot['base_commit'] == '7bc3e6fc3c9685cc713ea4288705a63740ef2bd6'
        # Check all existing files before writing anything; never overwrite differences.
        for name in members:
            target = Path('/content') / name
            if not name.endswith('/') and target.exists():
                assert target.is_file() and target.read_bytes() == archive.read(name), str(target)
        for name in members:
            if name.endswith('/'):
                continue
            target = Path('/content') / name
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as output:
                    output.write(archive.read(name))
        for name, digest in snapshot['files'].items():
            assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
    print('Code snapshot verified:', len(snapshot['files']), 'files', flush=True)

    backup = drive / 'artifacts/configs/ye_boyang'
    for name in ('paths.local.yaml', 'pilot.local.yaml'):
        source, target = backup / name, root / 'configs' / name
        assert source.is_file(), f'Missing existing private backup: {source}'
        if target.exists():
            assert target.read_bytes() == source.read_bytes(), f'Keep and review differing config: {target}'
        else:
            with target.open('xb') as output:
                output.write(source.read_bytes())
    # Read only project configuration, never authentication files.
    # Original paths backup was saved as JSON (also valid YAML).
    paths = json.loads((root / 'configs/paths.local.yaml').read_text())
    assert paths['code_root'] == str(root)
    assert paths['artifact_root'] == str(drive / 'artifacts')
    assert paths['brainiac_repo'] == str(root / 'third_party/BrainIAC')

    env = Path('/content/venvs/brainiac')
    python = env / 'bin/python'
    if not python.exists():
        assert not env.exists(), 'Review partial environment before retrying.'
        venv.EnvBuilder(with_pip=False).create(env)
    run([sys.executable, '-m', 'pip', '--python', python, 'install',
         '-r', root / 'envs/brainiac.txt', '-r', root / 'envs/core.txt'])
    check = """import json, torch, monai, nibabel, numpy, yaml, einops, scipy, sklearn
assert torch.__version__.split('+')[0] == '2.5.1'
assert torch.cuda.is_available(), 'CUDA unavailable'
x = torch.ones((2, 2), device='cuda'); assert (x @ x).sum().item() == 8
print(json.dumps({'torch':torch.__version__, 'monai':monai.__version__,
 'numpy':numpy.__version__, 'gpu':torch.cuda.get_device_name(0),
 'cuda':torch.version.cuda, 'cuda_smoke_test':'passed'}))
"""
    result = run([python, '-c', check], capture_output=True, text=True)
    print(result.stdout, flush=True)
    freeze = run([sys.executable, '-m', 'pip', '--python', python, 'freeze'],
                 capture_output=True, text=True).stdout
    logs = drive / 'artifacts/logs'
    logs.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime()) + '_' + str(time.time_ns())
    log = logs / ('vscode_brainiac_environment_' + stamp + '.txt')
    with log.open('x') as output:
        output.write('UTC timestamp; no model inference performed.\n' + result.stdout + '\n' + freeze)

    author = root / 'third_party/BrainIAC'
    commit = 'ba60f45bed832ee0e5683c678caeaeefe2072f0d'
    if not author.exists():
        author.parent.mkdir(parents=True, exist_ok=True)
        run(['git', 'init', author])
        run(['git', '-C', author, 'remote', 'add', 'origin', 'https://github.com/AIM-KannLab/BrainIAC.git'])
        run(['git', '-C', author, 'sparse-checkout', 'init', '--no-cone'])
        run(['git', '-C', author, 'sparse-checkout', 'set', '--no-cone',
             '/README.md', '/LICENSE', '/requirements.txt', '/src/model.py',
             '/src/dataset.py', '/src/load_brainiac.py', '/src/get_brainiac_features.py',
             '/src/quickstart.ipynb'])
        run(['git', '-C', author, 'fetch', '--filter=blob:none', '--depth=1', 'origin', commit])
        run(['git', '-C', author, 'checkout', '--detach', 'FETCH_HEAD'])
    head = run(['git', '-C', author, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    assert head == commit, 'Preserve and review existing author checkout.'
    run(['git', '-C', author, 'diff', '--exit-code', 'HEAD', '--', 'src/model.py', 'src/dataset.py'])
    assert (author / 'LICENSE').is_file() and (author / 'src/model.py').is_file()
    print('Author code pinned:', head, flush=True)
    print('Environment log:', log, flush=True)
    print('SETUP COMPLETE. Checkpoint, input recipe/template and real QC still required; no inference or training.', flush=True)


if __name__ == '__main__':
    main()
