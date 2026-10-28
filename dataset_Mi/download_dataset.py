"""Download this fixed Release and reconstruct every file with SHA-256 checks.
Requires Python 3.8+; uses only the standard library. No GitHub login for public assets.
"""
import argparse, concurrent.futures, hashlib, json, os, time, urllib.request, zipfile
from pathlib import Path

BASE_URL='https://github.com/bykarl/MRI-classification/releases/download/mind-ds007857-v1.0.1-team-20261028/'
EXPECTED_MANIFEST_SHA256='e65a8526e00315861cdf459138058970da890d3c569ed7837c9fe9fa9f8f05e0'

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def fetch(url,target,expected=None,size=None):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if expected and (size is None or target.stat().st_size==size) and sha256(target)==expected:return 'existing'
        raise RuntimeError('Existing file differs; not overwritten: '+str(target))
    partial=target.with_name(target.name+'.download')
    for attempt in range(5):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'MiND-team-dataset-downloader/1.0'})
            with urllib.request.urlopen(req,timeout=120) as response,partial.open('wb') as out:
                for block in iter(lambda:response.read(4*1024*1024),b''):out.write(block)
            if size is not None and partial.stat().st_size!=size:raise RuntimeError('Size mismatch: '+target.name)
            if expected and sha256(partial)!=expected:raise RuntimeError('SHA256 mismatch: '+target.name)
            os.replace(str(partial),str(target));return 'downloaded'
        except Exception:
            if attempt==4:raise
            time.sleep(min(2**attempt,15))

def inside(root,rel):
    p=(root/rel).resolve()
    if p!=root and root not in p.parents:raise RuntimeError('Unsafe manifest path: '+rel)
    return p

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('dataset_Mi'))
    p.add_argument('--workers',type=int,default=3)
    args=p.parse_args();root=args.output.resolve();root.mkdir(parents=True,exist_ok=True)
    cache=root.parent/(root.name+'_download_cache');cache.mkdir(parents=True,exist_ok=True)
    manifest_path=cache/'dataset_manifest.json'
    fetch(BASE_URL+'dataset_manifest.json',manifest_path,EXPECTED_MANIFEST_SHA256)
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    archive=manifest['support_archive'];archive_path=cache/archive['asset_name']
    print('Downloading supporting files...',flush=True)
    fetch(archive['url'],archive_path,archive['sha256'],archive['bytes'])
    support={r['path']:r for r in manifest['files'] if r['storage']=='support_archive'}
    with zipfile.ZipFile(archive_path) as z:
        if set(z.namelist())!=set(support):raise RuntimeError('Unexpected support ZIP paths')
        for rel,r in support.items():
            dest=inside(root,rel);dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():
                if sha256(dest)!=r['sha256']:raise RuntimeError('Existing file differs; not overwritten: '+rel)
                continue
            tmp=dest.with_name(dest.name+'.download');h=hashlib.sha256()
            with z.open(rel) as source,tmp.open('wb') as out:
                for b in iter(lambda:source.read(4*1024*1024),b''):out.write(b);h.update(b)
            if h.hexdigest()!=r['sha256']:raise RuntimeError('Support file checksum mismatch: '+rel)
            os.replace(str(tmp),str(dest))
    images=[r for r in manifest['files'] if r['storage']=='release_asset']
    def image_download(r):
        return r['path'],fetch(r['url'],inside(root,r['path']),r['sha256'],r['bytes'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(args.workers,8))) as pool:
        futures=[pool.submit(image_download,r) for r in images]
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):
            name,status=f.result();print(f'[{i}/{len(images)}] {status}: {name}',flush=True)
    for r in manifest['files']:
        dest=inside(root,r['path'])
        if not dest.is_file() or dest.stat().st_size!=r['bytes'] or sha256(dest)!=r['sha256']:
            raise RuntimeError('Final verification failed: '+r['path'])
    print(f"SUCCESS: restored and verified all {manifest['file_count']} files to {root}")
    print('QC remains preliminary; read GUIDE.md before using these data for training.')

if __name__=='__main__':main()
