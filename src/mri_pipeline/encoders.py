"""Frozen inference adapters. All real recipes/weights must be explicit."""
from pathlib import Path
import importlib.util
import subprocess
import sys
import time
import numpy as np
from .io import array_finite, read_json, sha256, verified, inside
from .fmri import validate_roi_order


def author_repo(path, commit, files):
    path = Path(path).resolve()
    head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    if head != commit:
        raise ValueError('Author code commit mismatch')
    subprocess.run(['git', '-C', str(path), 'diff', '--exit-code', 'HEAD', '--', *files], check=True, capture_output=True)
    return path


def check_handoff(handoff_path, stage):
    h = read_json(handoff_path)
    item = h['stages'][stage]
    if item['status'] != 'ready' or item['qc_status'] != 'pass':
        raise ValueError('Handoff stage has not passed QC: ' + stage)
    for key in ('record_id', 'pipeline_id'):
        if not h.get(key):
            raise ValueError('Missing handoff field: ' + key)
    if not item.get('qc_reviewer') or not item.get('files'):
        raise ValueError('QC reviewer and checksummed stage files are required')
    root = Path(handoff_path).resolve().parent
    for record in item['files'].values():
        verified(inside(root, record['path']), record['sha256'])
    return h, item


def brainiac(input_path, checkpoint, repo, config, device='cpu'):
    if not config.get('input_recipe_confirmed') or not config.get('template_sha256'):
        raise ValueError('BrainIAC spatial recipe and template hash are not confirmed')
    verified(checkpoint, config.get('checkpoint_sha256'))
    repo = author_repo(repo, config['code_commit'], ['src/model.py', 'src/dataset.py'])
    if config.get('pooling') != 'author_first_token':
        raise ValueError('Unsupported BrainIAC pooling recipe')
    import torch
    import nibabel as nib
    from monai.transforms import Compose, LoadImaged, EnsureChannelFirstd, Resized, NormalizeIntensityd, ToTensord
    image = nib.load(str(input_path))
    a = array_finite(image.get_fdata(), ndim=3)
    if not np.isfinite(image.affine).all() or abs(np.linalg.det(image.affine[:3,:3])) < 1e-12 or np.std(a) == 0:
        raise ValueError('Invalid spatial affine or constant T1 image')
    spec = importlib.util.spec_from_file_location('brainiac_author_model', repo/'src/model.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    start = time.perf_counter()
    model = module.ViTBackboneNet(str(checkpoint)).to(device).eval()
    model.requires_grad_(False)
    transform = Compose([LoadImaged(keys=['image']), EnsureChannelFirstd(keys=['image']),
        Resized(keys=['image'], spatial_size=(96,96,96), mode='trilinear'),
        NormalizeIntensityd(keys=['image'], nonzero=True, channel_wise=True), ToTensord(keys=['image'])])
    x = transform({'image': str(input_path)})['image'].unsqueeze(0).to(device)
    if str(device).startswith('cuda'):
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
    infer_start = time.perf_counter()
    with torch.inference_mode():
        z = model(x)
    if str(device).startswith('cuda'):
        torch.cuda.synchronize()
    inference_seconds = time.perf_counter()-infer_start
    z = array_finite(z.detach().cpu().numpy(), ndim=2)
    if z.shape != (1,768):
        raise ValueError('Unexpected BrainIAC representation shape: ' + str(z.shape))
    return z[0], {'input_shape': list(x.shape), 'inference_seconds': inference_seconds,
        'load_transform_inference_seconds': time.perf_counter()-start,
        'peak_gpu_bytes': torch.cuda.max_memory_allocated() if str(device).startswith('cuda') else None,
        'native_shape': list(a.shape), 'orientation': list(nib.aff2axcodes(image.affine)),
        'voxel_sizes': list(map(float, image.header.get_zooms())),
        'source_sha256': sha256(input_path), 'device':str(device),
        'torch_cuda_version':torch.version.cuda,
        'gpu_name':torch.cuda.get_device_name(device) if str(device).startswith('cuda') else None}


def jepa_tensor(window, roi_order, contract, config):
    x = array_finite(window, ndim=2).astype(np.float32)
    validate_roi_order(roi_order)
    if x.shape != (160,450) or np.any(x.std(axis=0) == 0):
        raise ValueError('Expected finite, nonconstant shared [160,450] window')
    if not contract.get('confirmed') or not config.get('recipe_confirmed'):
        raise ValueError('Brain-JEPA atlas/input recipe is not confirmed')
    for key in ['atlas_name','atlas_space','atlas_sha256','roi_order_sha256','gradient_sha256']:
        if not contract.get(key):
            raise ValueError('Missing atlas contract provenance: ' + key)
    if [r['atlas_label'] for r in roi_order] != contract['roi_labels']:
        raise ValueError('Atlas label order differs from confirmed encoder order')
    if any(r['structure_type'] != ('subcortical' if i<50 else 'cortical') for i,r in enumerate(roi_order)):
        raise ValueError('Author expects 50 subcortical ROIs followed by 400 cortical ROIs')
    mode = config.get('normalization')
    x = x.T
    if mode == 'global_sample_standardization':
        # Match torch.std() sample correction=1 across the complete single tensor.
        x = (x-x.mean()) / x.std(ddof=1)
    elif mode == 'frozen_roi_robust':
        p = verified(config['normalization_params'], config.get('normalization_params_sha256'))
        with np.load(p, allow_pickle=False) as f:
            median, iqr = f['medians'], f['iqrs']
        if median.shape != (450,) or iqr.shape != (450,) or not np.isfinite(median).all() or not np.isfinite(iqr).all() or np.any(iqr <= 0):
            raise ValueError('Invalid frozen normalization parameters')
        if config.get('normalization_origin') != 'external_pretraining':
            raise ValueError('Cohort-fitted normalization belongs inside CV, not cached extraction')
        x = (x-median[:,None])/iqr[:,None]
    else:
        raise ValueError('Select and confirm an explicit normalization recipe')
    return array_finite(x[None,None].astype(np.float32), ndim=4)


def brain_jepa(window, roi_order, contract, checkpoint, repo, config, device='cuda'):
    tensor = jepa_tensor(window, roi_order, contract, config)
    verified(checkpoint, config.get('checkpoint_sha256'))
    gradient = np.loadtxt(verified(config['gradient_csv'], config.get('gradient_sha256')), delimiter=',')
    if gradient.ndim != 2 or gradient.shape[0] != 450 or not np.isfinite(gradient).all():
        raise ValueError('Gradient mapping must have 450 ordered finite rows')
    if contract.get('gradient_sha256') != config['gradient_sha256']:
        raise ValueError('Gradient file is not tied to the confirmed ROI contract')
    if config.get('checkpoint_key') not in {'encoder', 'target_encoder'} or config.get('pooling') not in {'mean_tokens','first_token'}:
        raise ValueError('Explicit checkpoint branch and pooling are required')
    repo = author_repo(repo, config['code_commit'], ['src/models/vision_transformer.py'])
    # Separate process/kernel from BrainIAC: the author uses top-level src imports.
    sys.path.insert(0, str(repo))
    import torch
    if config.get('attention_backend') == 'normal_no_flash':
        from .jepa_compat import normal_attention_module
        vit = normal_attention_module(repo)
    else:
        from src.models import vision_transformer as vit
    if repo not in Path(vit.__file__).resolve().parents:
        raise RuntimeError('A different src module is cached; use a fresh separate kernel')
    start = time.perf_counter()
    model = vit.vit_base(img_size=(450,160), patch_size=16, in_chans=1,
        gradient_pos_embed=torch.tensor(gradient, dtype=torch.float32, device=device).unsqueeze(0),
        attn_mode='normal', add_w='mapping', gradient_checkpointing=False)
    ckpt = torch.load(checkpoint, map_location='cpu', weights_only=False)
    state = ckpt[config['checkpoint_key']]
    state = {k.removeprefix('module.'): v for k,v in state.items()}
    model.load_state_dict(state, strict=True)  # never swallow a loading error
    model = model.to(device).eval().requires_grad_(False)
    x = torch.from_numpy(tensor).to(device)
    with torch.inference_mode():
        tokens = model(x)
        z = tokens.mean(dim=1) if config['pooling']=='mean_tokens' else tokens[:,0]
    if str(device).startswith('cuda'):
        torch.cuda.synchronize()
    z = array_finite(z.detach().cpu().numpy(), ndim=2)
    if len(z) != 1:
        raise ValueError('Unexpected Brain-JEPA output batch')
    return z[0], {'input_shape': list(tensor.shape), 'output_dim': int(z.shape[1]),
                  'attention_backend':config.get('attention_backend', 'normal_with_author_flash_import'),
                  'load_inference_seconds': time.perf_counter()-start,'device':str(device),
                  'torch_cuda_version':torch.version.cuda,
                  'gpu_name':torch.cuda.get_device_name(device) if str(device).startswith('cuda') else None}
