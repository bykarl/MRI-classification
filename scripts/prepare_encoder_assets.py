"""Acquire official encoder assets and verify loading without patient data.

Run only in the user's already authorized Colab server with Drive mounted.
Does not allocate resources, download participant MRI, fit models, or train.
"""
from pathlib import Path
from html.parser import HTMLParser
import hashlib
import http.cookiejar
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import venv

IAC_COMMIT = 'ba60f45bed832ee0e5683c678caeaeefe2072f0d'
JEPA_COMMIT = 'b1dfa93eb331d1e70476446b06fc8a1ac3c92345'
ROOT = Path('/content/MRI-classification')
DRIVE = Path('/content/drive/MyDrive/FYP_MRI')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.action = None
        self.fields = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'form' and a.get('id') == 'download-form':
            self.action = a.get('action')
        if tag == 'input' and a.get('name'):
            self.fields[a['name']] = a.get('value', '')


def download(url, path, size, *, expected_sha256=None, git_blob=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        assert shutil.disk_usage('/content').free > size + 1024**3
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        response = opener.open(url, timeout=90)
        if 'text/html' in response.headers.get('Content-Type', ''):
            html = response.read(2_000_000).decode('utf-8')
            response.close()
            form = DownloadForm()
            form.feed(html)
            assert form.action and urllib.parse.urlparse(form.action).hostname == 'drive.usercontent.google.com', 'Public download unavailable; do not log in automatically.'
            response = opener.open(form.action + '?' + urllib.parse.urlencode(form.fields), timeout=90)
        assert 'text/html' not in response.headers.get('Content-Type', ''), 'Expected binary asset'
        partial = path.with_name(path.name + '.partial_' + str(time.time_ns()))
        total = 0
        with response, partial.open('xb') as output:
            while True:
                block = response.read(4 * 1024 * 1024)
                if not block:
                    break
                total += len(block)
                assert total <= size, 'Download exceeds verified public file size'
                output.write(block)
        assert total == size, f'Incomplete asset retained at {partial}'
        if expected_sha256:
            assert digest(partial) == expected_sha256
        if git_blob:
            assert hashlib.sha1(b'blob ' + str(size).encode() + b'\0' + partial.read_bytes()).hexdigest() == git_blob
        assert not path.exists()
        partial.rename(path)
    assert path.stat().st_size == size
    sha = digest(path)
    if expected_sha256:
        assert sha == expected_sha256
    if git_blob:
        assert hashlib.sha1(b'blob ' + str(size).encode() + b'\0' + path.read_bytes()).hexdigest() == git_blob
    print('ASSET VERIFIED', path.name, size, sha, flush=True)
    return {'path': str(path), 'size_bytes': size, 'sha256': sha, 'source': url}


def command(args, **kwargs):
    result = subprocess.run([str(x) for x in args], check=False, **kwargs)
    if result.returncode:
        for value in (result.stdout, result.stderr):
            if isinstance(value, str) and value:
                print(value[-12000:], flush=True)
        result.check_returncode()
    return result


def main():
    assert sys.version_info[:2] == (3, 12)
    assert DRIVE.is_dir() and (DRIVE / 'weights').is_dir()
    import yaml
    stamp = time.strftime('%Y%m%d_%H%M%S', time.gmtime()) + '_' + str(time.time_ns())
    report = {'utc_stamp': stamp, 'patient_data_used': False, 'training': False, 'assets': {}}
    weights = DRIVE / 'weights'
    assets = report['assets']
    assets['brainiac'] = download(
        'https://www.dropbox.com/scl/fo/i51xt63roognvt7vuslbl/AMblt6reQVvlSrORTB3_2lE/BrainIAC.ckpt?rlkey=9w55le6tslwxlfz6c0viylmjb&dl=1',
        weights / 'brainiac/BrainIAC.ckpt', 362119240)
    assets['brainiac_template'] = download(
        f'https://raw.githubusercontent.com/AIM-KannLab/BrainIAC/{IAC_COMMIT}/src/preprocessing/atlases/temp_head.nii.gz',
        weights / 'reference/brainiac_temp_head.nii.gz', 11976113,
        git_blob='24ec2d4f133c871002f0a57d3cb3dbdb74e9c93b')
    assets['jepa_gradient'] = download(
        f'https://raw.githubusercontent.com/Eric-LRL/Brain-JEPA/{JEPA_COMMIT}/data/gradient_mapping_450.csv',
        weights / 'brain_jepa/gradient_mapping_450.csv', 344558,
        expected_sha256='c9bc667e49aae442e12607bee8be86c31c330f2844cf72e7c84b16de312ed007')
    assets['brain_jepa'] = download(
        'https://drive.usercontent.google.com/uc?id=1LL3gM-i5SLDWCFyvj71M3peLeU6V2qMR&export=download',
        weights / 'brain_jepa/jepa-ep300.pth.tar', 1513861285)

    author = ROOT / 'third_party/Brain-JEPA'
    if not author.exists():
        command(['git', 'init', author])
        command(['git', '-C', author, 'remote', 'add', 'origin', 'https://github.com/Eric-LRL/Brain-JEPA.git'])
        command(['git', '-C', author, 'sparse-checkout', 'init', '--no-cone'])
        command(['git', '-C', author, 'sparse-checkout', 'set', '--no-cone', '/README.md', '/requirement.txt', '/src/', '/configs/', '/downstream_tasks/'])
        command(['git', '-C', author, 'fetch', '--filter=blob:none', '--depth=1', 'origin', JEPA_COMMIT])
        command(['git', '-C', author, 'checkout', '--detach', 'FETCH_HEAD'])
    head = command(['git', '-C', author, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    assert head == JEPA_COMMIT
    command(['git', '-C', author, 'diff', '--exit-code', 'HEAD'])
    env = Path('/content/venvs/brain_jepa')
    python = env / 'bin/python'
    if not python.exists():
        assert not env.exists(), 'Review partial environment'
        venv.EnvBuilder(with_pip=False).create(env)
    command([sys.executable, '-m', 'pip', '--python', python, 'install', '-r', ROOT / 'envs/brain_jepa_t4.txt'])

    # Official checkpoint loading and synthetic forward smoke tests, not MRI inference.
    iac_test = '''import sys,json,importlib.util,torch,numpy as np,nibabel as nib
from pathlib import Path
repo=Path(sys.argv[1]); checkpoint=sys.argv[2]; template=sys.argv[3]
spec=importlib.util.spec_from_file_location('brainiac_author',repo/'src/model.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
model=m.ViTBackboneNet(checkpoint).eval().requires_grad_(False).cuda()
torch.manual_seed(0)
with torch.inference_mode(): z=model(torch.randn(1,1,96,96,96,device='cuda'))
assert z.shape==(1,768) and torch.isfinite(z).all()
img=nib.load(template)
print('VERIFY_JSON='+json.dumps({'test':'SYNTHETIC_ONLY','strict_backbone_load':True,'shape':list(z.shape),'finite':True,'template_shape':list(img.shape),'template_axcodes':list(nib.aff2axcodes(img.affine)),'template_spacing':list(map(float,img.header.get_zooms()))}))
'''
    result = command(['/content/venvs/brainiac/bin/python', '-c', iac_test,
                      ROOT / 'third_party/BrainIAC', assets['brainiac']['path'], assets['brainiac_template']['path']], capture_output=True, text=True)
    report['brainiac_check'] = json.loads(next(x.split('=', 1)[1] for x in result.stdout.splitlines() if x.startswith('VERIFY_JSON=')))
    print('BRAINIAC_CHECK', json.dumps(report['brainiac_check']), flush=True)
    jepa_test = '''import sys,json,torch,numpy as np
from pathlib import Path
root=Path(sys.argv[1]); repo=root/'third_party/Brain-JEPA'
sys.path.insert(0,str(root/'src')); sys.path.insert(0,str(repo))
from mri_pipeline.jepa_compat import normal_attention_module
vit=normal_attention_module(repo)
gradient=np.loadtxt(sys.argv[3],delimiter=','); assert gradient.shape==(450,30) and np.isfinite(gradient).all()
ckpt=torch.load(sys.argv[2],map_location='cpu',weights_only=False)
branches=[k for k in ['encoder','target_encoder'] if k in ckpt]
assert set(branches)=={'encoder','target_encoder'}, 'Inspect checkpoint branch names'
reports=[]
for branch in branches:
 model=vit.vit_base(img_size=(450,160),patch_size=16,in_chans=1,gradient_pos_embed=torch.tensor(gradient,dtype=torch.float32,device='cuda').unsqueeze(0),attn_mode='normal',add_w='mapping',gradient_checkpointing=False)
 state={k.removeprefix('module.'):v for k,v in ckpt[branch].items()}
 model.load_state_dict(state,strict=True);model=model.cuda().eval().requires_grad_(False)
 torch.manual_seed(0)
 with torch.inference_mode(): tokens=model(torch.randn(1,1,450,160,device='cuda'))
 assert tokens.shape==(1,4500,768) and torch.isfinite(tokens).all()
 reports.append({'branch':branch,'strict_load':True,'token_shape':list(tokens.shape),'finite':True})
 del model,tokens;torch.cuda.empty_cache()
print('VERIFY_JSON='+json.dumps({'test':'SYNTHETIC_ONLY','attention':'author_normal_import_only_compat','torch':torch.__version__,'gpu':torch.cuda.get_device_name(0),'gradient_shape':list(gradient.shape),'branches':reports,'normalization_confirmed':False,'pooling_confirmed':False}))
'''
    result = command([python, '-c', jepa_test, ROOT, assets['brain_jepa']['path'], assets['jepa_gradient']['path']], capture_output=True, text=True)
    report['brain_jepa_check'] = json.loads(next(x.split('=', 1)[1] for x in result.stdout.splitlines() if x.startswith('VERIFY_JSON=')))
    print('JEPA_CHECK', json.dumps(report['brain_jepa_check']), flush=True)
    report['brain_jepa_license'] = 'No root LICENSE at pinned commit; do not assume a license or redistribute weights.'

    paths_file, config_file = ROOT / 'configs/paths.local.yaml', ROOT / 'configs/pilot.local.yaml'
    paths, config = yaml.safe_load(paths_file.read_text()), yaml.safe_load(config_file.read_text())
    backup = DRIVE / 'artifacts/configs/ye_boyang' / ('assets_' + stamp)
    backup.mkdir(parents=True, exist_ok=False)
    for f in (paths_file, config_file):
        shutil.copyfile(f, backup / ('before_' + f.name))
    paths['brainiac_checkpoint'] = assets['brainiac']['path']
    paths['brain_jepa_checkpoint'] = assets['brain_jepa']['path']
    paths['brain_jepa_repo'] = str(author)
    config['brainiac']['checkpoint_sha256'] = assets['brainiac']['sha256']
    config['brainiac']['template_sha256'] = assets['brainiac_template']['sha256']
    config['brainiac']['input_recipe_confirmed'] = False
    config['brain_jepa'].update(checkpoint_sha256=assets['brain_jepa']['sha256'], gradient_csv=assets['jepa_gradient']['path'], gradient_sha256=assets['jepa_gradient']['sha256'], attention_backend='normal_no_flash')
    config['brain_jepa']['recipe_confirmed'] = False
    # No automatic choice of branch/pooling/normalization or atlas contract.
    for target, value in [(paths_file, paths), (config_file, config)]:
        target.write_text(yaml.safe_dump(value, sort_keys=False), encoding='utf-8')
        shutil.copyfile(target, backup / ('after_' + target.name))
    report['configuration_backup'] = str(backup)
    report['brain_jepa_environment'] = command([sys.executable, '-m', 'pip', '--python', python, 'freeze'], capture_output=True, text=True).stdout
    output = DRIVE / 'artifacts/reports' / ('encoder_assets_' + stamp + '.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print('ASSET_REPORT', output, flush=True)
    print('WAITING FOR REAL QC INPUT AND AGREED RECIPES. Synthetic checks are not patient features or classification results.', flush=True)


if __name__ == '__main__':
    main()
