"""Close the first-record intake with an explicit, reversible pilot header policy.

No resampling, voxel edits, MRI preprocessing, motion estimation or QC approval.
Only sub-mindo304_ses-placebo is supported; do not generalize to other records.
"""
from pathlib import Path
import hashlib
import json
import re
import urllib.request
from datetime import datetime, timezone

import nibabel as nib
import numpy as np

UPSTREAM = "0b11e8604142ebb9d335f57877238f3aad44e194"
BASE = f"https://raw.githubusercontent.com/OpenNeuroDatasets/ds007857/{UPSTREAM}/"
RID = "sub-mindo304_ses-placebo"
EXPECTED = {
    "t1": ("sub-mindo304/ses-placebo/anat/" + RID + "_T1w.nii.gz",
           "89ea431ba0e912d1b73643a4ce691dbe13ad54da394b645942e4e12dceaf73b5", 8425883),
    "bold": ("sub-mindo304/ses-placebo/func/" + RID + "_task-rest_bold.nii.gz",
             "7469f562c6fb134d53508297710e446a0d943ee4b196d2c06fb30cd8b1c2877d", 60013116),
}


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def public_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": "FYP-MRI-intake-audit"})
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read()


def close_step1(root):
    root = Path(root)
    previous = json.loads((root / "input_check_with_geometry.json").read_text())
    assert previous["record_id"] == RID
    output = root / "intake_v2"
    output.mkdir(exist_ok=True)
    evidence = {
        "upstream_commit": UPSTREAM, "upstream_tag": "1.0.1",
        "protocol": "https://doi.org/10.1186/s12883-019-1294-6",
        "protocol_rest_fov_mm": [220, 220],
        "protocol_rest_tr_sec": 2.0, "protocol_rest_slices": 43,
        "protocol_rest_volumes": 240, "protocol_rest_slice_thickness_mm": 3.0,
        "policy": "pilot_sform_preserving_header_harmonization_v1",
        "inference_limit": "FOV/matrix corroborates sform; not a subject DICOM or scanner-author confirmation.",
        "sources": {}, "images": {},
    }
    # Source directories were checked for inheritance; repeat and record actual entries.
    for directory in ["", "sub-mindo304", "sub-mindo304/ses-placebo"]:
        url = "https://api.github.com/repos/OpenNeuroDatasets/ds007857/contents/" + directory + "?ref=" + UPSTREAM
        entries = json.loads(public_bytes(url))
        paths = [e["path"] for e in entries if e["type"] == "file" and e["name"].endswith(".json")]
        assert not any(p.endswith("_bold.json") for p in paths), "New inherited BOLD metadata: review policy"
        evidence["sources"][directory or "dataset_root"] = {"url": url, "json_files": paths}
    description = json.loads(public_bytes(BASE + "dataset_description.json"))
    assert "Michigan Neural Distinctiveness" in description["Name"]
    for kind, (relative, expected_sha, expected_size) in EXPECTED.items():
        raw = root / "dataset_Mi" / "rawdata" / relative
        assert raw.stat().st_size == expected_size and sha(raw) == expected_sha
        # Git-annex symlink binds the actual original image content to the SHA-256.
        annex_url = BASE + relative
        annex_target = public_bytes(annex_url).decode().strip()
        assert f"SHA256E-s{expected_size}--{expected_sha}.nii.gz" in annex_target
        json_relative = relative.removesuffix(".nii.gz") + ".json"
        original_json = public_bytes(BASE + json_relative)
        local_json = raw.with_name(raw.name.removesuffix(".nii.gz") + ".json")
        assert original_json == local_json.read_bytes(), "Local/source JSON differ"
        metadata = json.loads(original_json)
        source = nib.load(raw)
        affine, code = source.get_sform(coded=True)
        assert affine is not None and code != 0 and np.isfinite(affine).all()
        assert np.allclose(source.affine, affine)
        spacing = nib.affines.voxel_sizes(affine)
        if kind == "bold":
            assert source.shape == (64, 64, 43, 240)
            assert np.allclose(spacing, [220 / 64, 220 / 64, 3.0], atol=1e-5)
            assert metadata["RepetitionTime"] == 2.0
            assert not metadata.get("SliceTiming"), "SliceTiming newly available: review policy"
            # Do not invent timing from scanner model, number of slices or generic defaults.
            assert int(source.header["slice_code"]) == 0, "NIfTI timing code needs review"
        else:
            assert source.shape == (256, 256, 156) and np.allclose(spacing, [1, 1, 1], atol=1e-5)
        unscaled = np.asarray(source.dataobj.get_unscaled())
        destination = output / kind / raw.name
        destination.parent.mkdir(exist_ok=True)
        if not destination.exists():
            header = source.header.copy()
            header.set_xyzt_units("mm", "sec")
            header.set_zooms(tuple(spacing) + ((2.0,) if kind == "bold" else ()))
            staged = nib.Nifti1Image(unscaled, affine, header=header)
            # Preserve the full coded affine, including tiny non-orthogonality.
            # qform cannot encode shear without changing that mapping; disable it.
            staged.set_sform(affine, int(code))
            staged.set_qform(None, code=0)
            staged.header.set_xyzt_units("mm", "sec")
            staged.header.set_slope_inter(source.dataobj.slope, source.dataobj.inter)
            temporary = destination.with_name(destination.name.removesuffix(".nii.gz") + ".partial.nii.gz")
            nib.save(staged, temporary)
            temporary.rename(destination)
        check = nib.load(destination)
        assert np.array_equal(unscaled, np.asarray(check.dataobj.get_unscaled()))
        assert np.array_equal(source.get_fdata(), check.get_fdata()), "Scaled voxel values changed"
        assert check.shape == source.shape
        assert np.allclose(check.affine, source.affine, atol=1e-5)
        assert int(check.header["qform_code"]) == 0
        assert np.allclose(check.get_sform(), source.get_sform(), atol=1e-5)
        assert np.allclose(check.header.get_zooms()[:3], spacing, atol=1e-5)
        assert check.header.get_xyzt_units() == ("mm", "sec")
        assert sha(raw) == expected_sha, "Original raw image changed"
        if kind == "bold":
            assert check.header.get_zooms()[3] == 2.0
        sidecar_copy = destination.with_name(destination.name.removesuffix(".nii.gz") + ".json")
        # Preserve original JSON byte-for-byte; discrepancy is resolved by a separate explicit recipe.
        if sidecar_copy.exists():
            assert sidecar_copy.read_bytes() == original_json
        else:
            sidecar_copy.write_bytes(original_json)
        evidence["images"][kind] = {
            "raw_path": str(raw), "raw_sha256": expected_sha,
            "upstream_annex_url": annex_url, "upstream_annex_target": annex_target,
            "json_url": BASE + json_relative,
            "json_sha256": hashlib.sha256(original_json).hexdigest(),
            "staged_path": str(destination), "staged_sha256": sha(destination),
            "shape": list(source.shape), "spacing_mm": list(map(float, spacing)),
            "chosen_affine": affine.tolist(), "sform_code": int(code),
            "raw_slice_code": int(source.header["slice_code"]),
            "raw_slice_duration": float(source.header["slice_duration"]),
            "raw_header_spacing": list(map(float, source.header.get_zooms())),
            "staged_qform_code": 0,
            "coordinate_policy": "preserve exact coded sform; disable ambiguous qform instead of approximating shear",
            "original_voxels_identical": True, "world_affine_preserved": True,
        }
        if kind == "bold":
            evidence["images"][kind]["original_json_VoxelSize"] = metadata.get("VoxelSize")
            evidence["images"][kind]["VoxelSize_discrepancy"] = "Original JSON says 3,3,3; do not use that field to rescale data. Effective pilot spacing follows coded sform plus protocol FOV corroboration."
    result = {
        "record_id": RID, "closed_at_utc": datetime.now(timezone.utc).isoformat(),
        "step1_status": "complete_for_technical_pilot_with_documented_limitations",
        "file_integrity_status": "pass", "staged_geometry_checks": "pass",
        "spatial_policy": evidence["policy"],
        "slice_timing_correction": "skip_missing_source_metadata_and_unknown_nifti_slice_code",
        "fieldmap_based_sdc": "unavailable_no_fieldmap_acquisition_in_checked_session",
        "tr_sec": 2.0, "resampling_performed": False, "voxel_values_changed": False,
        "scientific_preprocessing_started": False, "preprocessed_handoff_ready": False,
        "qc_status": "pending", "training_ready": False,
        "identity_status": previous["identity_status"], "diagnosis_status": previous["diagnosis_status"],
        "runtime": "2 logical CPUs / 12.67 GiB RAM / CPU only; no full FreeSurfer/fMRIPrep environment verified",
        "remaining_stage2_requirements": [
            "Install and verify preprocessing software and persistent checkpoint storage",
            "Confirm BrainIAC template/input recipe with feature owner",
            "Lock fMRI denoising/QC parameters and exact Brain-JEPA atlas/order before extraction",
            "Perform actual preprocessing and subsequent manual QC; do not mark ready now",
        ],
        "evidence": evidence,
    }
    (output / "step1_closeout.json").write_text(json.dumps(result, indent=2))
    return result
