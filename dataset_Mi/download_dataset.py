"""Restore the deduplicated MiND dataset with pinned SHA-256 verification.

Python 3.8+; standard library only. Existing different files are never replaced.
The historical Release is a file source: only this manifest's selected files
are restored. Use an empty output directory when migrating an older dataset.
"""

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import time
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath


MANIFEST_URL = (
    'https://raw.githubusercontent.com/bykarl/MRI-classification/'
    'main/dataset_Mi/dataset_manifest.json'
)
EXPECTED_MANIFEST_SHA256 = '8c36e85113f3a5b5e853b471f664397c74ed79eca71e014cd198aa82076da0a2'
SUBJECT_PATTERN = re.compile(r'sub-[A-Za-z0-9]+')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def validate_relative_path(relative):
    if not isinstance(relative, str) or not relative or '\\' in relative or ':' in relative:
        raise RuntimeError('Unsafe manifest path: ' + repr(relative))
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or path.as_posix() != relative or relative == '.':
        raise RuntimeError('Unsafe manifest path: ' + relative)
    return path


def inside(root, relative):
    validate_relative_path(relative)
    root = Path(root).resolve()
    destination = (root / relative).resolve()
    if destination == root or root not in destination.parents:
        raise RuntimeError('Unsafe manifest path: ' + relative)
    return destination


def temporary_path(target):
    temporary = target.with_name(target.name + '.download')
    if temporary.is_symlink():
        raise RuntimeError('Refusing a symlink at temporary path: ' + str(temporary))
    return temporary


def is_verified(path, expected, size=None):
    return (path.is_file()
            and (size is None or path.stat().st_size == size)
            and sha256(path) == expected)


def existing_status(target, expected, size=None):
    if target.exists():
        if is_verified(target, expected, size):
            return True
        raise RuntimeError(
            'Existing file differs; not overwritten: ' + str(target)
            + '. Use a new, empty output directory for the cleaned dataset.'
        )
    if target.is_symlink():
        raise RuntimeError('Refusing a dangling symlink: ' + str(target))
    return False


def fetch(url, target, expected, size=None):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if existing_status(target, expected, size):
        return 'existing'
    partial = temporary_path(target)
    for attempt in range(5):
        try:
            request = urllib.request.Request(
                url, headers={'User-Agent': 'MiND-deduplicated-downloader/2.0'}
            )
            with urllib.request.urlopen(request, timeout=120) as response, partial.open('wb') as stream:
                for block in iter(lambda: response.read(4 * 1024 * 1024), b''):
                    stream.write(block)
            if size is not None and partial.stat().st_size != size:
                raise RuntimeError('Size mismatch: ' + target.name)
            if sha256(partial) != expected:
                raise RuntimeError('SHA-256 mismatch: ' + target.name)
            # Recheck in case another process created a destination meanwhile.
            if existing_status(target, expected, size):
                partial.unlink()
                return 'existing'
            os.replace(str(partial), str(target))
            return 'downloaded'
        except Exception:
            if attempt == 4:
                raise
            time.sleep(min(2 ** attempt, 15))


def validate_digest(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value) is not None


def validate_manifest(manifest):
    if manifest.get('schema_version') != 2:
        raise RuntimeError('Expected a deduplicated schema_version=2 manifest.')
    retained = manifest.get('retained_ids')
    if (not isinstance(retained, list) or not retained
            or any(not isinstance(subject, str) or SUBJECT_PATTERN.fullmatch(subject) is None
                   for subject in retained)
            or len(set(retained)) != len(retained)):
        raise RuntimeError('Invalid or repeated retained participant IDs.')
    records = manifest.get('files')
    if not isinstance(records, list) or len(records) != manifest.get('file_count'):
        raise RuntimeError('Manifest file_count does not match the file list.')
    paths = set()
    sources = set()
    image_count = 0
    for record in records:
        path = record.get('path')
        validate_relative_path(path)
        key = path.casefold()
        if key in paths:
            raise RuntimeError('Repeated/colliding output path: ' + path)
        paths.add(key)
        if (type(record.get('bytes')) is not int or record['bytes'] < 0
                or not validate_digest(record.get('sha256'))):
            raise RuntimeError('Invalid size or SHA-256 for: ' + path)
        ids_in_path = SUBJECT_PATTERN.findall(path)
        if any(subject not in retained for subject in ids_in_path):
            raise RuntimeError('File path includes an excluded participant: ' + path)
        storage = record.get('storage')
        if storage == 'release_asset':
            image_count += 1
            if not isinstance(record.get('url'), str) or not record['url']:
                raise RuntimeError('Missing image download URL: ' + path)
        elif storage == 'support_archive':
            source = record.get('source_path')
            validate_relative_path(source)
            if source in sources:
                raise RuntimeError('Repeated selected ZIP source: ' + source)
            sources.add(source)
        elif storage == 'inline':
            content = record.get('content')
            if not isinstance(content, str):
                raise RuntimeError('Missing inline content: ' + path)
            data = content.encode('utf-8')
            if len(data) != record['bytes'] or hashlib.sha256(data).hexdigest() != record['sha256']:
                raise RuntimeError('Inline content checksum mismatch: ' + path)
        else:
            raise RuntimeError('Unknown storage kind for: ' + path)
    if image_count != manifest.get('mri_file_count'):
        raise RuntimeError('Manifest mri_file_count does not match image entries.')
    if sources:
        archive = manifest.get('support_archive', {})
        validate_relative_path(archive.get('asset_name'))
        if ('/' in archive['asset_name']
                or type(archive.get('bytes')) is not int or archive['bytes'] < 0
                or not validate_digest(archive.get('sha256'))
                or not isinstance(archive.get('url'), str) or not archive['url']):
            raise RuntimeError('Invalid pinned supporting ZIP description.')


def load_manifest(explicit_path, cache):
    if explicit_path is not None:
        path = explicit_path.resolve()
        if not is_verified(path, EXPECTED_MANIFEST_SHA256):
            raise RuntimeError('Supplied manifest does not match the pinned SHA-256: ' + str(path))
    else:
        adjacent = Path(__file__).resolve().with_name('dataset_manifest.json')
        if is_verified(adjacent, EXPECTED_MANIFEST_SHA256):
            path = adjacent
        else:
            path = cache / 'dataset_manifest.json'
            fetch(MANIFEST_URL, path, EXPECTED_MANIFEST_SHA256)
    manifest = json.loads(path.read_text(encoding='utf-8'))
    validate_manifest(manifest)
    return manifest


def preflight_output(root, manifest):
    if root.exists() and not root.is_dir():
        raise RuntimeError('Output is not a directory: ' + str(root))
    if (root / '_work').exists():
        raise RuntimeError(
            'The output contains a historical _work directory with unfiltered records. '
            'Use a new, empty output directory for the cleaned dataset.'
        )
    retained = set(manifest['retained_ids'])
    for parent_name in ('rawdata', 'qc/motion'):
        parent = inside(root, parent_name)
        if parent.is_dir():
            stale = sorted(path.name for path in parent.iterdir()
                           if path.name.startswith('sub-') and path.name not in retained)
            if stale:
                raise RuntimeError(
                    'The output still contains excluded IDs: ' + ', '.join(stale)
                    + '. Use a new, empty output directory; old files are not deleted automatically.'
                )
    # Fail before any data writes if an older cohort/participants file or any
    # other destination differs. Reruns of this exact selection remain safe.
    for record in manifest['files']:
        destination = inside(root, record['path'])
        existing_status(destination, record['sha256'], record['bytes'])


def write_inline(root, record):
    destination = inside(root, record['path'])
    if existing_status(destination, record['sha256'], record['bytes']):
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = temporary_path(destination)
    temporary.write_bytes(record['content'].encode('utf-8'))
    if not is_verified(temporary, record['sha256'], record['bytes']):
        raise RuntimeError('Inline file verification failed: ' + record['path'])
    if existing_status(destination, record['sha256'], record['bytes']):
        temporary.unlink()
        return
    os.replace(str(temporary), str(destination))


def restore_support(root, cache, manifest):
    selected = [record for record in manifest['files'] if record['storage'] == 'support_archive']
    if selected:
        archive = manifest['support_archive']
        archive_path = cache / archive['asset_name']
        print('Downloading/verifying the pinned supporting ZIP...', flush=True)
        fetch(archive['url'], archive_path, archive['sha256'], archive['bytes'])
        with zipfile.ZipFile(archive_path) as source:
            members = Counter(source.namelist())
            for record in selected:
                name = record['source_path']
                if members[name] != 1:
                    raise RuntimeError('Missing or duplicate selected ZIP entry: ' + name)
                info = source.getinfo(name)
                if info.is_dir() or info.file_size != record['bytes']:
                    raise RuntimeError('ZIP entry size/type mismatch: ' + name)
            for record in selected:
                destination = inside(root, record['path'])
                if existing_status(destination, record['sha256'], record['bytes']):
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                temporary = temporary_path(destination)
                digest = hashlib.sha256()
                with source.open(record['source_path']) as incoming, temporary.open('wb') as outgoing:
                    for block in iter(lambda: incoming.read(4 * 1024 * 1024), b''):
                        outgoing.write(block)
                        digest.update(block)
                if (temporary.stat().st_size != record['bytes']
                        or digest.hexdigest() != record['sha256']):
                    raise RuntimeError('Supporting file checksum mismatch: ' + record['path'])
                if existing_status(destination, record['sha256'], record['bytes']):
                    temporary.unlink()
                    continue
                os.replace(str(temporary), str(destination))
    for record in manifest['files']:
        if record['storage'] == 'inline':
            write_inline(root, record)


def restore_images(root, manifest, workers):
    images = [record for record in manifest['files'] if record['storage'] == 'release_asset']

    def download(record):
        status = fetch(record['url'], inside(root, record['path']), record['sha256'], record['bytes'])
        return record['path'], status

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(workers, 8))) as pool:
        pending = [pool.submit(download, record) for record in images]
        for index, future in enumerate(concurrent.futures.as_completed(pending), 1):
            name, status = future.result()
            print('[{}/{}] {}: {}'.format(index, len(images), status, name), flush=True)


def final_verification(root, manifest, support_only):
    checked = 0
    for record in manifest['files']:
        if support_only and record['storage'] == 'release_asset':
            continue
        if not is_verified(inside(root, record['path']), record['sha256'], record['bytes']):
            raise RuntimeError('Final verification failed: ' + record['path'])
        checked += 1
    return checked


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('dataset_Mi'))
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--manifest', type=Path, help='Local manifest; must match this script\'s pinned SHA-256.')
    parser.add_argument('--support-only', action='store_true',
                        help='Restore metadata, matching JSON and QC files only; do not download MRI.')
    args = parser.parse_args(argv)
    root = args.output.resolve()
    cache = root.parent / (root.name + '_deduplicated_download_cache')
    cache.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(args.manifest, cache)
    preflight_output(root, manifest)
    root.mkdir(parents=True, exist_ok=True)
    restore_support(root, cache, manifest)
    if not args.support_only:
        restore_images(root, manifest, args.workers)
    checked = final_verification(root, manifest, args.support_only)
    if args.support_only:
        print('SUPPORT-ONLY SUCCESS: restored and verified {} supporting files to {}. '
              '{} MRI files were not downloaded.'.format(checked, root, manifest['mri_file_count']))
    else:
        print('SUCCESS: restored and verified all {} files for {} retained IDs to {}.'.format(
            checked, len(manifest['retained_ids']), root))
    print('Prior QC remains preliminary; read GUIDE.md before using the data for training.')


if __name__ == '__main__':
    main()
