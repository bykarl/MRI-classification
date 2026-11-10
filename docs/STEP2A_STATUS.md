# Step 2A — T1 tools and asset verification

Record: `sub-mindo304_ses-placebo`. Date: 2026-11-10.

## Actual state

- Colab login recovered with user participation. The runtime is a new CPU-only session: Python 3.13.18 host, 2 logical CPUs, 12.67 GiB RAM; previous temporary MRI files were absent. This does not imply Drive/Git data were deleted.
- An isolated Python 3.10.22 environment was actually created at `/content/FYP_MRI_LiYang/venvs/t1`. Installation finished successfully in about 23 seconds. The host environment was not replaced.
- Installed: numpy 1.26.4, scipy 1.14.1, SimpleITK 2.4.1, nibabel 5.3.2, scikit-image 0.24.0, matplotlib 3.9.4, torch 2.5.1+cpu; official HD-BET 1.0 source fixed at `3e3d2a5993e8288f2eae928744ffb496cfc7c651`.
- First CLI check failed because Colab exports an inline Matplotlib backend unavailable in the isolated environment. The verification script now sets `MPLBACKEND=Agg` for its CLI subprocess. The failure log/report is preserved as an earlier attempt; it is not represented as a passing check.
- The subsequent verification reached its final report without raising: audited raw and staged first-case T1/BOLD restored, template checksum/read checked, HD-BET `-h` and import checked, official fast-fold weight checksum and strict state-dict load passed. Per-image SimpleITK read status is in the actual runtime `step2a_logs/verification.json`; this note does not substitute for that detailed geometry result.
- Official HD-BET weight `0.model`: 65,443,735 bytes; Zenodo MD5 `46ed703cae7611c4f3a60d7b9d8fd666`; locally computed SHA-256 `6f75233753c4750672815e2b7a86db754995ae44b8f1cd77bccfc37becd2d83c`. Strict loading passed; no forward pass was run.
- **Persistent storage is pending user Drive authorization.** The notebook currently displays “Permit this notebook to access your Google Drive files?”. Neither this prompt nor installing tools proves that MRI files have been backed up.

## What each script does

1. `scripts/install_t1_tools.py`: installs the isolated CPU T1 environment; this exact installation code ran in Colab. Run the runtime-inspection cell first to create the project root. The scripts are first-case pilot utilities, not an unattended production/batch pipeline.
2. `scripts/verify_t1_environment.py`: restores only the two audited first-case images and matching public JSON, checks hashes, recreates the already agreed `intake_v2` copies without resampling, checks tool imports/CLI, reads T1/template with SimpleITK, and validates the single official HD-BET weight. Does not process patient images with N4/registration/HD-BET. Preserve prior reports/logs before reruns, as done in the executed notebook wrapper.
3. `scripts/persist_step2a.py`: **not executed yet**. After authorized `drive.mount('/content/drive')`, copies explicit project files and the HD-BET weight to `MyDrive/FYP_MRI_LiYang`, verifies hashes by reading them back, and refuses differing existing files. No unrelated Drive folders are inspected. Virtual environments are not copied; rebuild them from the script and actual freeze file. If a partial file is found, inspect it rather than silently overwriting.

## Candidate recipe and remaining boundary

BrainIAC author source is fixed at `ba60f45bed832ee0e5683c678caeaeefe2072f0d`; template SHA-256 remains `d8eba10e9528a5212b78fb1be477d5e8229751bfec5e1e1a648dc81ff83a622e` (170 × 206 × 162, LAS, 1 mm).

Candidate order: N4 → Euler3D rigid registration to the author template → HD-BET 1.0 (`-mode fast -tta 0 -device cpu`). Keep the transform, registered image, brain mask and QC images. A fixed registration seed is a proposed project reproducibility change; no registration has run and the exact processing implementation is not yet accepted.

The BrainIAC script imports `HD_BET.hd_bet`, which is absent in the inspected official legacy package. The verified legacy CLI / `HD_BET.run.run_hd_bet` is the explicit integration route; do not claim the unmodified author script runs. Modern HD-BET 2.x is not a silent drop-in replacement for the old command line.

The feature owner still needs to review/confirm the candidate recipe and T1 geometry read result before 2B. They alone handle the 96³ conversion and encoder intensity standardization. This is an engineering handoff decision, not a request to change the research hypothesis.

FreeSurfer is not installed/run (separate 2C, license and resource preparation needed). fMRI preprocessing/atlas extraction is not installed/run (separate 2D; exact atlas/order/QC recipe still needed). Missing SliceTiming remains an explicit reason to skip STC; no fieldmap SDC is claimed. Identity and diagnosis timing remain unconfirmed.

`scientific_preprocessing_started=false`, `qc_status=pending`, `training_ready=false`. **2A is not fully closed until Drive write/readback succeeds and the T1 recipe/geometry handoff is resolved.** No classification performance or completed patient preprocessing is reported.

## Recovery / rollback

Code and this status are tracked on `li-yang-preprocessing`, separate from `main`/`karl`. MRI, weights, private paths/credentials and large logs stay out of Git. Preserve the earlier step-1 report. Revert only this change with a new commit if needed; do not reset other branches, delete raw inputs or erase Drive files. Do not assume a free Colab session or its isolated environment survives disconnection.
