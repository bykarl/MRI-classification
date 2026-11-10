# First-case T1 pilot (2B)

This entry processes only `sub-mindo304_ses-placebo`; it is not a batch/clinical pipeline. Its output remains a candidate input for BrainIAC until QC and the feature-owner handoff review.

**Completed outcome:** continuation exited 0 at 2026-11-10T08:26:31Z. N4 originally took 62.186 s, registration 14.140 s, and CPU HD-BET 1,398.175 s. Final readback matched all 24 persisted files. See [T1_PILOT_RESULTS.md](T1_PILOT_RESULTS.md). Manual QC and feature-owner recipe acceptance remain pending.

## Preconditions

- Authorized Google Drive mounted at `/content/drive`; the existing `scripts/persist_step2a.py` must have produced a readback checkpoint. On 2026-11-10 it actually verified 25 files / 214,269,339 bytes under `MyDrive/FYP_MRI_LiYang`.
- The first-case original and `intake_v2` input hashes and the fixed BrainIAC reference template match the recorded values. T1 SimpleITK read actually passed in 2A.
- Isolated `/content/FYP_MRI_LiYang/venvs/t1/bin/python` and verified official legacy HD-BET 1.0 fast-fold weight available. No GPU allocation or paid service is required by this script.

## Processing recipe

1. **N4 on the native image.** Estimate its smooth log-bias field using an Otsu foreground mask (200 bins) and a factor-2 shrunk image/mask; evaluate the field on the original grid and divide the original image by its exponential. Keep the corrected native-resolution NIfTI, foreground mask and log-bias field. The N4 foreground mask is not the final brain mask. Default filter convergence/iteration values are recorded from the actual installed SimpleITK filter before execution.
2. **Rigid alignment.** Resample the fixed author template to 1 mm as in the author script; initialize Euler3D by geometry, optimize Mattes MI with 50 bins, 1% random sampling, fixed project seed 20261110, 100 iterations and the recorded three-level smoothing/shrink settings. Save both transform directions, initial alignment and the final registered T1. The fixed-to-moving transform maps template/output physical coordinates to native/input coordinates for resampling; its inverse maps native to template.
3. **Brain extraction.** Official legacy HD-BET CLI on CPU, fast mode, TTA disabled, largest-component postprocessing, retaining brain NIfTI and binary mask. Check shape/affine, finite values, binary mask and that the brain output equals the registered image inside the mask and zero outside.
4. **QC material.** Native input/N4 views, template-versus-T1 checkerboards, axial mask contours and additional sagittal/coronal/axial mask views. Percentile scaling is display-only. No anatomical ground-truth mask is available for this pilot; no Dice accuracy is inferred from these checks.

The order/template/registration family follows the [fixed BrainIAC author script](https://github.com/AIM-KannLab/BrainIAC/blob/ba60f45bed832ee0e5683c678caeaeefe2072f0d/src/preprocessing/mri_preprocess_3d_simple.py). This is **not unchanged author-script reproduction**: the author HD_BET import is replaced by a verified official legacy CLI; registration randomness is seeded; N4 field estimation is shrunk/masked to fit available resources. The latter approach follows the [SimpleITK N4 example](https://simpleitk.readthedocs.io/en/master/link_N4BiasFieldCorrection_docs.html). All such differences remain in `run.json`; no downstream performance equivalence is asserted.

The initial full-grid, no-mask N4 attempt `pilot_20261110T075350Z` was intentionally stopped before its N4 stage completed, at 2026-11-10T07:58:59Z, after roughly five minutes. The observed Colab RAM indicator had briefly reached about 10.46/12.67 GB. This is not evidence of OOM, input corruption, or a scientific failure. Return code -15 reflects deliberate termination. Its executed source, run/N4 parameters, process log and stopped-attempt record were preserved separately.

The low-memory run `pilot_lowmem_20261110T075859Z` (source SHA-256 `d2a440542d123ba128534bd175f5f4b86f1203a870925336e6aaf64361ccfae7`) completed N4 in 62.186 seconds and passed Drive readback, then failed at registration initialization. Applying the log-bias field produced a 64-bit image, while the fixed reference was 32-bit; the actual continuation log confirms that type. The fix explicitly casts the moving registration input to `sitkFloat32`; it does not change the saved N4 computation. The failed run's output and error are retained.

The continuation is `pilot_resume_20261110T080241Z`, executed source SHA-256 `9b6962391e6642c056911f484783760527c01127544bc8c231d5201c0d62a529`. It reuses the previously completed N4 files only after checking the old input/template hashes, recipe version, grid geometry, and matching local/Drive file hashes. It does not recompute N4 or overwrite the failed attempt. Completion is established by actual `handoff_pilot.json`, process exit and persisted readback; a launched process alone is not completion.

## Execution and files

Use a new run ID, never reuse an existing run directory:

```bash
/content/FYP_MRI_LiYang/venvs/t1/bin/python -u /content/FYP_MRI_LiYang/preprocess_first_t1.py --run-id UNIQUE_RUN_ID
```

For an inspected completed low-memory N4 stage, add `--resume-n4-from PRIOR_RUN_ID`. This supports N4 reuse only; it does not automatically resume later registration/HD-BET stages. The destination still needs a new run ID, and both local and persisted source files must be available and hash-matched.

The authorized Colab launcher starts one subprocess and records its PID/log/run ID in `step2b_active.json`. The read-only progress cell checks that same process and its log. Starting the launcher again is not a progress check. Do not run the full notebook with “Run all”: historical cells include downloads, earlier attempts and launchers.

`preview_t1_registration.py` makes a persisted orthogonal alignment contact sheet from completed registration and refuses to overwrite an existing preview. `export_t1_pilot_reports.py` checks the completed final run against Drive and exports review evidence excluding NIfTI and weights. Both utilities actually ran for this first case.

Files live under `derivatives/t1_pilot/sub-mindo304_ses-placebo/<run-id>/` locally and in the mirrored project folder on Drive. Each completed stage is copied and read back with SHA-256 checks before proceeding. Original input files are never overwritten. Existing differing checkpoints or partial copies stop the script for inspection. There is no promise that a Colab runtime survives disconnection; checkpoints preserve completed work. The script refuses reusing a run directory. After an interrupted session, inspect the saved stages before preparing a continuation; the explicit N4-reuse option does not implement general unattended recovery.

Final files of interest:

| File | Role |
|---|---|
| `run.json`, `executed_script.py` | Exact parameters, provenance and executed source |
| `T1w_N4_native.nii.gz`, `N4_log_bias_native.nii.gz` | Corrected original grid and estimated field |
| `N4_foreground_mask_native.nii.gz` | N4 foreground mask, distinct from brain mask |
| `reference_1mm.nii.gz`, `T1w_initial_alignment.nii.gz` | Actual registration reference and initialization |
| `T1w_registered_0000.nii.gz` | Corrected T1 resampled onto reference grid |
| `template_to_native.tfm`, `native_to_template.tfm` | Both physical-coordinate transform directions |
| `T1w_brain.nii.gz`, `T1w_brain_mask.nii.gz` | Candidate BrainIAC image and mask |
| `stage_*.json`, `registration_trace.json`, `hdbet.log` | Actual execution, timings and trace |
| `qc_*.png` | QC contact sheets for review |
| `handoff_pilot.json` | Output hashes, technical status and remaining acceptance gates |

## Handoff boundary

No 96³ resizing or encoder intensity standardization here; the feature owner handles those. No FreeSurfer volumes, fMRI denoising/ROI time series, features, classifier training or AUC are produced by this step. Identity and diagnosis timing are still unconfirmed.

`qc_status=pending`, `input_recipe_confirmed=false`, `training_ready=false` are deliberate. `handoff_pilot.json` documents this technical run; it is not the final adapter-ready `handoff.json`. Inspect all QC views, resolve any anatomical concerns, and accept the recipe jointly before marking the T1 handoff ready. Update the pipeline contract consistently rather than quietly setting a readiness boolean.
