"""First-case FreeSurfer preparation, three explicit stages, and checked checkpoints.

No stage is started by importing this file or running preflight/status.
The native intake T1 is used; the 2B template-space brain is never an input.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import time

STAGES=('autorecon1','autorecon2','autorecon3')
REPO=Path(__file__).resolve().parents[1]


def now(): return datetime.now(timezone.utc).isoformat()


def digest(path,algorithm='sha256'):
    h=hashlib.new(algorithm)
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): h.update(block)
    return h.hexdigest()


def read_json(path): return json.loads(Path(path).read_text())


def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream: json.dump(value,stream,indent=2)


def identifier(value):
    if not value or not value.replace('-','').replace('_','').isalnum():
        raise ValueError('Use a run ID containing only letters, digits, hyphens and underscores')
    return value


def load_config(path):
    cfg=read_json(path)
    if cfg['record_id']!='sub-mindo304_ses-placebo' or cfg['subject_id']!=cfg['record_id']:
        raise ValueError('This entry is first-case-only; do not silently change subject identity')
    if cfg['freesurfer_version']!='8.2.0' or cfg['FS_V8_XOPTS']!='0':
        raise ValueError('This recipe pins FreeSurfer 8.2.0 legacy mode')
    for key in ['raw_relative','input_relative']:
        p=Path(cfg[key])
        if p.is_absolute() or '..' in p.parts: raise ValueError('Unsafe input-relative path')
    return cfg


def runtime_info():
    info={}
    if Path('/etc/os-release').exists():
        for line in Path('/etc/os-release').read_text().splitlines():
            if '=' in line:
                k,v=line.split('=',1); info[k]=v.strip('"')
    mem={}
    if Path('/proc/meminfo').exists():
        for line in Path('/proc/meminfo').read_text().splitlines():
            k,v=line.split(':',1);mem[k]=int(v.split()[0])*1024
    limits=[mem.get('MemTotal',0)]
    for file in ['/sys/fs/cgroup/memory.max','/sys/fs/cgroup/memory/memory.limit_in_bytes']:
        try:
            value=Path(file).read_text().strip()
            if value!='max' and 0<int(value)<2**60: limits.append(int(value))
        except (FileNotFoundError,ValueError): pass
    flags=Path('/proc/cpuinfo').read_text().lower() if Path('/proc/cpuinfo').exists() else ''
    return {'checked_at_utc':now(),'os_id':info.get('ID'),'os_version':info.get('VERSION_ID'),
        'architecture':platform.machine(),'cpu_count':os.cpu_count(),
        'effective_memory_gib':min(limits)/2**30 if limits else 0.,
        'available_memory_gib':mem.get('MemAvailable',0)/2**30,
        'free_disk_gib':shutil.disk_usage('/content' if Path('/content').exists() else '/').free/2**30,
        'avx_present':' avx ' in flags,'python':platform.python_version()}


def preflight(cfg,require_install=False,require_license=False):
    info=runtime_info(); errors=[]
    if info['os_id']!='ubuntu' or info['os_version'] not in cfg['packages']:
        errors.append('Supported recipe requires Ubuntu 22.04 or 24.04')
    if info['architecture'] not in ('x86_64','amd64') or not info['avx_present']:
        errors.append('An x86_64 CPU with AVX is required')
    if info['effective_memory_gib']<cfg['minimum_memory_gib']:
        errors.append('This conservative gate needs about 32 GB RAM (>=30 GiB effective); current runtime is too small')
    if info['free_disk_gib']<cfg['minimum_free_disk_gib']:
        errors.append('Need >=40 GiB free local disk before installation/processing')
    persistent=Path(cfg['persistent_root'])
    for key,sha in [('raw_relative','raw_sha256'),('input_relative','input_sha256')]:
        p=persistent/cfg[key]
        if not p.is_file(): errors.append('Missing mounted Drive input: '+cfg[key])
        elif digest(p)!=cfg[sha]: errors.append('Input SHA-256 mismatch: '+cfg[key])
    if require_license:
        p=Path(cfg['fs_license'])
        if not p.is_file() or p.stat().st_size==0: errors.append('User-provided private license.txt is missing')
    if require_install:
        for name in ['SetUpFreeSurfer.sh','bin/recon-all','bin/mri_convert']:
            if not (Path(cfg['freesurfer_home'])/name).is_file(): errors.append('FreeSurfer install missing: '+name)
    return {'runtime':info,'errors':errors,'status':'blocked' if errors else 'pass',
            'freesurfer_installed_tested':False,'processing_started':False,'qc_status':'pending'}


def require_ready(report):
    if report['errors']: raise RuntimeError('\n'.join(report['errors']))


def fs_env(cfg,subjects=None):
    env=os.environ.copy()
    env.update(FREESURFER_HOME=cfg['freesurfer_home'],FS_LICENSE=cfg['fs_license'],
               FS_V8_XOPTS='0',OMP_NUM_THREADS=str(cfg['openmp_threads']))
    if subjects is not None: env['SUBJECTS_DIR']=str(subjects)
    return env


def fs_command(cfg,args):
    # Arguments remain positional data. No user-derived command interpolation.
    return ['bash','-c','source "$FREESURFER_HOME/SetUpFreeSurfer.sh" >/dev/null && exec "$@"','fs-pilot',*map(str,args)]


def fingerprint(cfg):
    home=Path(cfg['freesurfer_home'])
    p=subprocess.run(fs_command(cfg,['recon-all','-version']),env=fs_env(cfg),capture_output=True,text=True,check=True)
    version=(p.stdout+p.stderr).strip()
    if cfg['freesurfer_version'] not in version: raise RuntimeError('Installed FreeSurfer version differs from recipe')
    # Catch missing shared libraries before a multi-hour reconstruction starts.
    for name in ['mri_ca_register','mri_watershed','mris_register','mris_make_surfaces']:
        binary=home/'bin'/name
        if not binary.is_file():raise RuntimeError('Missing FreeSurfer binary: '+name)
        libraries=subprocess.run(['ldd',str(binary)],capture_output=True,text=True)
        if 'not found' in libraries.stdout+libraries.stderr:
            raise RuntimeError('Missing shared-library dependency for '+name+'; inspect supported vendor install/updates')
    return {'version_output':version,'recon_all_sha256':digest(home/'bin/recon-all'),
        'build_stamp_sha256':digest(home/'build-stamp.txt') if (home/'build-stamp.txt').exists() else None,
        'os_id':runtime_info()['os_id'],'os_version':runtime_info()['os_version'],
        'FS_V8_XOPTS':'0'}


def install(cfg,license_accepted=False):
    if not license_accepted: raise RuntimeError('Read/accept the official software license yourself before enabling install')
    require_ready(preflight(cfg,require_license=True))
    os_version=runtime_info()['os_version']; pkg=cfg['packages'][os_version]
    folder=Path(cfg['project_root'])/'step2c_downloads';folder.mkdir(parents=True,exist_ok=True)
    target=folder/Path(pkg['url']).name
    if not target.exists():
        part=target.with_name(target.name+'.partial')
        subprocess.run(['curl','--fail','--location','--proto','=https','--retry','3','--continue-at','-',
                        '--output',str(part),pkg['url']],check=True)
        if digest(part,'md5')!=pkg['md5']: raise RuntimeError('Official package MD5 mismatch; partial retained, not installed')
        part.rename(target)
    if digest(target,'md5')!=pkg['md5']: raise RuntimeError('Existing package MD5 mismatch')
    subprocess.run(['apt-get','update'],check=True)
    subprocess.run(['apt-get','install','-y',str(target)],check=True,
                   env={**os.environ,'DEBIAN_FRONTEND':'noninteractive'})
    fp=fingerprint(cfg)
    result={'checked_at_utc':now(),'official_url':pkg['url'],'official_md5':pkg['md5'],
        'download_sha256':digest(target),'package_bytes':target.stat().st_size,'fingerprint':fp,
        'note':'Pinned vendor package; no mutable remote patch script auto-run'}
    write_new(folder/('installation_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json'),result)
    print(json.dumps(result,indent=2))


def run_dir(cfg,run_id):
    return Path(cfg['project_root'])/'freesurfer_pilot/runs'/identifier(run_id)


def persistent_run(cfg,run_id):
    return Path(cfg['persistent_root'])/'freesurfer_pilot/runs'/identifier(run_id)


def copy_checked(source,target):
    target.parent.mkdir(parents=True,exist_ok=True); checksum=digest(source)
    if target.exists():
        if digest(target)!=checksum: raise RuntimeError('Refusing differing checkpoint: '+str(target))
    else:
        part=target.with_name(target.name+'.partial')
        if part.exists(): raise RuntimeError('Inspect incomplete checkpoint before retry: '+str(part))
        shutil.copyfile(source,part)
        if digest(part)!=checksum: raise RuntimeError('Checkpoint transfer SHA mismatch')
        part.rename(target)
    if digest(target)!=checksum: raise RuntimeError('Checkpoint readback failed')
    return checksum


def initialize(cfg,run_id):
    require_ready(preflight(cfg,require_install=True,require_license=True))
    run=run_dir(cfg,run_id)
    if run.exists() or persistent_run(cfg,run_id).exists(): raise RuntimeError('Choose a NEW run ID')
    fp=fingerprint(cfg)
    fsaverage=Path(cfg['freesurfer_home'])/'subjects/fsaverage'
    if not fsaverage.is_dir():raise RuntimeError('Installed fsaverage is missing; inspect the vendor installation')
    run.mkdir(parents=True);(run/'subjects').mkdir()
    (run/'subjects/fsaverage').symlink_to(fsaverage,target_is_directory=True)
    source=Path(cfg['persistent_root'])/cfg['input_relative']
    shutil.copyfile(source,run/'input_T1_native.nii.gz')
    if digest(run/'input_T1_native.nii.gz')!=cfg['input_sha256']: raise RuntimeError('Copied native T1 differs')
    meta={'record_id':cfg['record_id'],'run_id':run_id,'created_at_utc':now(),'recipe_id':cfg['recipe_id'],
        'input_sha256':cfg['input_sha256'],'raw_sha256':cfg['raw_sha256'],'config':cfg,
        'software_fingerprint':fp,'runner_sha256':digest(__file__),
        'source_snapshot':read_json(REPO/'source_snapshot.json') if (REPO/'source_snapshot.json').exists() else None,
        'qc_status':'pending','training_ready':False,'processing_started':False}
    write_new(run/'run.json',meta)
    shutil.copyfile(__file__,run/'executed_runner.py')
    for name in ['run.json','executed_runner.py','input_T1_native.nii.gz']:
        copy_checked(run/name,persistent_run(cfg,run_id)/name)
    return run


def stage_allowed(run,stage):
    index=STAGES.index(stage)
    if (run/(stage+'.completed.json')).exists(): raise RuntimeError('Stage already completed; do not recompute')
    if index and not (run/(STAGES[index-1]+'.completed.json')).exists(): raise RuntimeError('Previous stage checkpoint required')
    if list(run.glob('*.running.json')): raise RuntimeError('Active/interrupted job marker exists; inspect, do not remove blindly')


def checkpoint_subject(cfg,run,stage):
    sid=cfg['subject_id'];subject=run/'subjects'/sid
    if not subject.is_dir(): raise RuntimeError('Missing FreeSurfer subject directory')
    archive=run/(stage+'.subject.tar.gz')
    if archive.exists(): raise RuntimeError('Snapshot already exists')
    with tarfile.open(archive,'x:gz') as tar: tar.add(subject,arcname=sid)
    checksum=copy_checked(archive,persistent_run(cfg,run.name)/archive.name)
    return {'archive':archive.name,'owner_run_id':run.name,'sha256':checksum,'bytes':archive.stat().st_size,'readback':'pass'}


def execute_stage(cfg,run_id,stage):
    require_ready(preflight(cfg,require_install=True,require_license=True))
    run=run_dir(cfg,run_id);meta=read_json(run/'run.json');stage_allowed(run,stage)
    if meta['software_fingerprint']!=fingerprint(cfg) or meta['config']!=cfg:
        raise RuntimeError('Build/OS/config changed; do not mix processing recipes')
    if digest(run/'input_T1_native.nii.gz')!=cfg['input_sha256']: raise RuntimeError('Native input changed')
    subject=run/'subjects'/cfg['subject_id']
    if list((subject/'scripts').glob('IsRunning*')): raise RuntimeError('FreeSurfer IsRunning marker exists; inspect first')
    args=['recon-all','-sd',str(run/'subjects'),'-s',cfg['subject_id'],'-'+stage,'-openmp',str(cfg['openmp_threads'])]
    if stage=='autorecon1': args.extend(['-i',str(run/'input_T1_native.nii.gz')])
    marker=run/(stage+'.running.json');write_new(marker,{'pid':os.getpid(),'stage':stage,'started_at_utc':now()})
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');log=run/(stage+'.'+stamp+'.log')
    start=time.monotonic()
    try:
        with log.open('x') as stream:
            command=fs_command(cfg,args)
            print('RUNNING',stage,'log:',str(log),flush=True)
            subprocess.run(command,env=fs_env(cfg,run/'subjects'),stdout=stream,stderr=subprocess.STDOUT,check=True)
        if list((subject/'scripts').glob('IsRunning*')): raise RuntimeError('FreeSurfer lock remained after process exit')
        if stage=='autorecon3':
            for name in ['lh.aparc.stats','rh.aparc.stats','aseg.stats']:
                if not (subject/'stats'/name).is_file(): raise RuntimeError('Expected final stats missing: '+name)
        snapshot=checkpoint_subject(cfg,run,stage)
        result={'record_id':cfg['record_id'],'run_id':run_id,'stage':stage,'completed_at_utc':now(),
            'elapsed_seconds':time.monotonic()-start,'command':args,'snapshot':snapshot,
            'stats_sha256':{name:digest(subject/'stats'/name) for name in ['lh.aparc.stats','rh.aparc.stats','aseg.stats']} if stage=='autorecon3' else {},
            'exit_code':0,'qc_status':'pending','training_ready':False}
        write_new(run/(stage+'.completed.json'),result)
        for file in [log,run/(stage+'.completed.json')]: copy_checked(file,persistent_run(cfg,run_id)/file.name)
        print(json.dumps(result,indent=2))
        marker.unlink()
    except BaseException as error:
        failure=run/(stage+'.failed.'+stamp+'.json')
        write_new(failure,{'stage':stage,'failed_at_utc':now(),'error_type':type(error).__name__,
            'note':'Inspect local process/FreeSurfer locks. Restore a completed snapshot into a NEW run rather than blindly deleting locks.',
            'qc_status':'pending','training_ready':False})
        for file in [failure,log]:
            if file.exists():copy_checked(file,persistent_run(cfg,run_id)/file.name)
        raise


def safe_extract(archive,destination,subject_id):
    if not hasattr(tarfile,'data_filter'): raise RuntimeError('A patched Python supporting tarfile data_filter is required')
    with tarfile.open(archive,'r:gz') as tar:
        for member in tar.getmembers():
            path=Path(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0]!=subject_id:
                raise RuntimeError('Unsafe/non-subject archive member')
        tar.extractall(destination,filter='data')


def restore(cfg,new_id,old_id,stage):
    # Completed-stage snapshots only. Failed/interrupted work is not represented as success.
    old=persistent_run(cfg,old_id);oldmeta=read_json(old/'run.json')
    if oldmeta['software_fingerprint']!=fingerprint(cfg) or oldmeta['config']!=cfg:
        raise RuntimeError('Restoration requires identical FreeSurfer build/OS/config')
    mark=read_json(old/(stage+'.completed.json'))
    if mark['exit_code']!=0 or mark['snapshot']['readback']!='pass': raise RuntimeError('Source checkpoint not complete')
    archive=persistent_run(cfg,mark['snapshot'].get('owner_run_id',old_id))/mark['snapshot']['archive']
    if digest(archive)!=mark['snapshot']['sha256']: raise RuntimeError('Snapshot SHA mismatch')
    run=initialize(cfg,new_id)
    safe_extract(archive,run/'subjects',cfg['subject_id'])
    for previous in STAGES[:STAGES.index(stage)+1]:
        source=old/(previous+'.completed.json')
        copy_checked(source,run/source.name)
        copy_checked(source,persistent_run(cfg,new_id)/source.name)
    write_new(run/'restored_from.json',{'source_run':old_id,'stage':stage,'archive_sha256':digest(archive),'restored_at_utc':now()})
    copy_checked(run/'restored_from.json',persistent_run(cfg,new_id)/'restored_from.json')
    print('RESTORED',str(run),'next stage must be run explicitly')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,default=REPO/'configs/freesurfer_pilot.json')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('preflight');ins=sub.add_parser('install');ins.add_argument('--license-accepted',action='store_true')
    ini=sub.add_parser('init');ini.add_argument('--run-id',required=True)
    stage=sub.add_parser('run-stage');stage.add_argument('--run-id',required=True);stage.add_argument('--stage',choices=STAGES,required=True)
    rest=sub.add_parser('restore');rest.add_argument('--run-id',required=True);rest.add_argument('--from-run',required=True);rest.add_argument('--stage',choices=STAGES,required=True)
    status=sub.add_parser('status');status.add_argument('--run-id',required=True)
    args=p.parse_args();cfg=load_config(args.config)
    if args.command=='preflight':
        report=preflight(cfg);print(json.dumps(report,indent=2));return 2 if report['errors'] else 0
    if args.command=='install': install(cfg,args.license_accepted)
    elif args.command=='init': print(str(initialize(cfg,args.run_id)))
    elif args.command=='run-stage':execute_stage(cfg,args.run_id,args.stage)
    elif args.command=='restore':restore(cfg,args.run_id,args.from_run,args.stage)
    elif args.command=='status':
        run=run_dir(cfg,args.run_id)
        print(json.dumps({'run_dir':str(run),'completed':[s for s in STAGES if (run/(s+'.completed.json')).exists()],
            'job_markers':[p.name for p in run.glob('*.running.json')],'qc_status':'pending'},indent=2))
    return 0


if __name__=='__main__':sys.exit(main())
