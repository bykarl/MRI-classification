"""Step 2A: restore audited first-case inputs and validate T1 tool/asset readiness.

No N4, registration, skull stripping, FreeSurfer, fMRI processing or inference.
Only the previously audited first case is supported. Outputs remain QC pending.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
import os
import subprocess
import sys
import urllib.request

os.environ['MPLBACKEND'] = 'Agg'  # Colab's inline backend is absent in this isolated CLI environment.

import nibabel as nib
import numpy as np
import SimpleITK as sitk
import torch

ROOT = Path('/content/FYP_MRI_LiYang')
RID = 'sub-mindo304_ses-placebo'
UPSTREAM = '0b11e8604142ebb9d335f57877238f3aad44e194'
BRAIN = 'ba60f45bed832ee0e5683c678caeaeefe2072f0d'
HDBET = '3e3d2a5993e8288f2eae928744ffb496cfc7c651'
RELEASE = 'https://github.com/bykarl/MRI-classification/releases/download/mind-ds007857-v1.0.1-team-20261028/'
BASE = 'https://raw.githubusercontent.com/OpenNeuroDatasets/ds007857/' + UPSTREAM + '/'
EXPECTED = {
    't1': ('anat', RID+'_T1w.nii.gz', 8425883,
           '89ea431ba0e912d1b73643a4ce691dbe13ad54da394b645942e4e12dceaf73b5',
           '8e6d3104d6171e3528aefe6288357f8cfee97724f0044232bac7c2fd3641dccb'),
    'bold': ('func', RID+'_task-rest_bold.nii.gz', 60013116,
             '7469f562c6fb134d53508297710e446a0d943ee4b196d2c06fb30cd8b1c2877d',
             'a4bf9ceeccaab0978bc9f8927ddec63eff23ff5c436e9881c82004c66e31d747'),
}


def digest(path, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def public_bytes(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'FYP-MRI-step2a'})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def receive(url, path, expected_sha=None, expected_size=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if expected_sha is None:
            raise RuntimeError('Refusing unverified existing asset: '+path.name)
    else:
        part = path.with_name(path.name+'.partial')
        if part.exists():
            raise RuntimeError('Partial download exists; inspect before retry: '+str(part))
        part.write_bytes(public_bytes(url))
        if expected_sha and digest(part) != expected_sha:
            raise RuntimeError('SHA mismatch: '+path.name)
        if expected_size and part.stat().st_size != expected_size:
            raise RuntimeError('Size mismatch: '+path.name)
        part.rename(path)
    if expected_sha:
        assert digest(path) == expected_sha
    if expected_size:
        assert path.stat().st_size == expected_size
    return path


def main():
    ROOT.mkdir(exist_ok=True)
    report = {
        'record_id': RID, 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'python': sys.version, 'source_project_commit': 'fc31648b8cde9f048a0e8e8506b0e42c1da1daa3',
        'brainiac_source_commit': BRAIN, 'hdbet_source_commit': HDBET,
        'software': {name: metadata.version(name) for name in
                     ['numpy','scipy','SimpleITK','nibabel','scikit-image','matplotlib','torch','HD_BET']},
        'scientific_preprocessing_started': False, 'patient_inference_executed': False,
        'qc_status': 'pending', 'training_ready': False,
        'identity_status': 'unconfirmed', 'diagnosis_status': 'timing_unverified',
        'input_recipe_confirmed_by_feature_owner': False,
        'images': {}, 'readiness': {},
    }
    out = ROOT/'step2a_logs'; out.mkdir(exist_ok=True)
    def save():
        (out/'verification.json').write_text(json.dumps(report,indent=2))
    save()
    print('IMPORTS PASS', json.dumps(report['software']),flush=True)
    # A real command/import check only; no image is passed to HD-BET.
    cli = subprocess.run([str(Path(sys.executable).parent/'hd-bet'),'-h'],
                         capture_output=True,text=True)
    (out/'hdbet_help.txt').write_text(cli.stdout+cli.stderr)
    assert cli.returncode == 0, cli.stderr
    assert '-mode' in cli.stdout and '-tta' in cli.stdout
    report['readiness']['legacy_cli'] = 'pass'
    freeze = subprocess.run(['uv','pip','freeze','--python',sys.executable],capture_output=True,text=True,check=True)
    (out/'requirements.freeze.txt').write_text(freeze.stdout)
    from HD_BET.run import run_hd_bet
    import inspect
    report['hdbet_entrypoint'] = str(inspect.signature(run_hd_bet))
    report['brainiac_author_import_note'] = 'Author script imports HD_BET.hd_bet, absent in inspected official legacy package. Use verified CLI/run_hd_bet explicitly; author script not executed unchanged.'
    save()
    for kind,(folder,name,size,raw_sha,staged_sha) in EXPECTED.items():
        relative = 'sub-mindo304/ses-placebo/'+folder+'/'+name
        annex = public_bytes(BASE+relative).decode().strip()
        assert f'SHA256E-s{size}--{raw_sha}.nii.gz' in annex
        raw = receive(RELEASE+name,ROOT/'dataset_Mi/rawdata'/relative,raw_sha,size)
        side = raw.with_name(name.removesuffix('.nii.gz')+'.json')
        side_bytes = public_bytes(BASE+relative.removesuffix('.nii.gz')+'.json')
        if side.exists():
            assert side.read_bytes() == side_bytes
        else:
            side.write_bytes(side_bytes)
        source=nib.load(raw)
        affine,code=source.get_sform(coded=True)
        assert code and np.allclose(source.affine,affine)
        spacing=nib.affines.voxel_sizes(affine)
        header=source.header.copy()
        header.set_xyzt_units('mm','sec')
        if kind=='bold':
            assert source.shape == (64,64,43,240)
            assert json.loads(side_bytes)['RepetitionTime']==2.0
            header.set_zooms(tuple(spacing)+(2.0,))
        else:
            assert source.shape == (256,256,156)
            header.set_zooms(tuple(spacing))
        image=nib.Nifti1Image(np.asarray(source.dataobj.get_unscaled()),affine,header=header)
        image.set_sform(affine,code=int(code)); image.set_qform(None,code=0)
        image.header.set_xyzt_units('mm','sec')
        image.header.set_slope_inter(source.dataobj.slope,source.dataobj.inter)
        target=ROOT/'intake_v2'/kind/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():
            temporary=target.with_name(target.name.removesuffix('.nii.gz')+'.partial.nii.gz')
            assert not temporary.exists()
            nib.save(image,temporary)
            temporary.rename(target)
        assert digest(target)==staged_sha, 'Restored staged bytes differ from audited step1'
        staged_side=target.with_name(name.removesuffix('.nii.gz')+'.json')
        if staged_side.exists():
            assert staged_side.read_bytes()==side_bytes
        else:
            staged_side.write_bytes(side_bytes)
        restored=nib.load(target)
        assert np.array_equal(np.asanyarray(source.dataobj),np.asanyarray(restored.dataobj))
        assert np.array_equal(source.affine,restored.affine)
        entry={'raw_sha256':raw_sha,'staged_sha256':staged_sha,'raw_relative':str(raw.relative_to(ROOT)),
               'staged_relative':str(target.relative_to(ROOT)),'voxel_values_unchanged':True,
               'world_affine_unchanged':True,'shape':list(source.shape),'spacing_mm':spacing.tolist()}
        if kind=='t1':
            try:
                actual=sitk.ReadImage(str(target),sitk.sitkFloat32)
                entry['sitk_read']='pass'; entry['sitk_size']=list(actual.GetSize())
                entry['sitk_direction']=list(actual.GetDirection())
                entry['sitk_spacing']=list(actual.GetSpacing())
                report['readiness']['t1_itk_read']='pass'
            except RuntimeError as error:
                entry['sitk_read']='failed'; entry['sitk_error']=str(error)
                report['readiness']['t1_itk_read']='blocked_geometry_review_required'
        report['images'][kind]=entry; save()
        print('INPUT RESTORED',kind,entry.get('sitk_read','nibabel_pass'),flush=True)
    template_url=f'https://raw.githubusercontent.com/AIM-KannLab/BrainIAC/{BRAIN}/src/preprocessing/atlases/temp_head.nii.gz'
    template=receive(template_url,ROOT/'assets/brainiac/temp_head.nii.gz',
                     'd8eba10e9528a5212b78fb1be477d5e8229751bfec5e1e1a648dc81ff83a622e')
    template_img=sitk.ReadImage(str(template),sitk.sitkFloat32)
    report['template']={'sha256':digest(template),'source_url':template_url,
                        'shape':list(nib.load(template).shape),'orientation':list(nib.aff2axcodes(nib.load(template).affine)),
                        'spacing_mm':list(template_img.GetSpacing()),'relative':str(template.relative_to(ROOT))}
    report['readiness']['template_read']='pass'; save()
    # Official Zenodo record and checksum. Download one fast-mode fold, never run prediction.
    record=json.loads(public_bytes('https://zenodo.org/api/records/2540695'))
    item=next(x for x in record['files'] if x['key']=='0.model')
    checksum=item['checksum']; assert checksum.startswith('md5:')
    weight=Path.home()/'hd-bet_params/0.model'
    if weight.exists():
        assert digest(weight,'md5') == checksum.split(':',1)[1]
    else:
        receive(item['links']['self'],weight,expected_size=item['size'])
    assert digest(weight,'md5') == checksum.split(':',1)[1]
    from HD_BET.config import config
    network,_=config().get_network(False,None)
    state=torch.load(weight,map_location='cpu',weights_only=True)
    network.load_state_dict(state,strict=True)
    report['hdbet_weight']={'source_record':'https://zenodo.org/records/2540695',
        'file':'0.model','bytes':weight.stat().st_size,'zenodo_checksum':checksum,
        'sha256':digest(weight),'strict_load':'pass','inference_executed':False}
    report['readiness']['hdbet_fast_weight']='strict_load_pass_no_inference'
    report['readiness']['n4_and_registration_api']='available_not_executed'
    report['readiness']['freesurfer']='not_installed_separate_2C_license_and_resources_needed'
    report['readiness']['fmri_tools']='not_installed_separate_2D_recipe_needed'
    report['readiness']['persistent_storage']='pending_mount_and_readback'
    report['candidate_recipe']={
        'name':'brainiac_author_order_legacy_hdbet_pilot_v1',
        'order':['N4','Euler3D_rigid_to_author_1mm_template','HD-BET_1.0_fast_tta0'],
        'registration_seed':20261110,'registration_seed_note':'Project reproducibility addition; author unseeded.',
        'retain_intermediates':True,'resize_96_cubed':'feature_owner_only',
        'input_recipe_confirmed':False,
        'note':'Not an unchanged execution of author script; verified legacy CLI replaces incompatible import.'}
    report['step2a_status']='tools_and_assets_checked_storage_pending'
    save()
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
