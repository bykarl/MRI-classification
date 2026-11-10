# First-case 2B result — sub-mindo304_ses-placebo

**Technical T1 processing completed.** The process exited with code 0 at 2026-11-10 08:26:31 UTC (16:26:31 Asia/Shanghai). Independent final readback verified all 24 persisted files against their local SHA-256. Original raw and staged input hashes were unchanged.

| Stage | Actual time / result |
|---|---|
| N4 bias correction | 62.186 s; native-grid output retained; completed checkpoint reused after an interface fix |
| Rigid template alignment | 14.140 s; both physical transform directions saved |
| HD-BET 1.0, CPU fast, TTA off | 1,398.175 s (23 min 18 s); brain image and binary mask produced |
| Final readback | 24/24 saved files matched local SHA-256 |
| Brain output grid | 170 × 206 × 162; 1 × 1 × 1 mm; LAS orientation |
| QC material | N4 before/after, orthogonal alignment, axial alignment/mask, orthogonal mask contours |

Completed run: `pilot_resume_20261110T080241Z`. Executed source SHA-256: `9b6962391e6642c056911f484783760527c01127544bc8c231d5201c0d62a529`.

## Output locations

```text
MyDrive/FYP_MRI_LiYang/derivatives/t1_pilot/sub-mindo304_ses-placebo/pilot_resume_20261110T080241Z/
```

The feature owner will ultimately use `T1w_brain.nii.gz`, together with `T1w_brain_mask.nii.gz`, transforms, parameters and QC views. No 96³ conversion or encoder intensity standardization was applied here. `handoff_pilot.json` records technical evidence, not an automatically accepted final adapter handoff.

Small audit records are tracked in `reports/t1_pilot/sub-mindo304_ses-placebo/`. MRI, mask, bias field, template, weights and QC PNG binaries remain outside Git. The report ZIP contains QC PNGs, actual records and historical attempts, without NIfTI or model weights. Its SHA-256 is `ff7ee984ca7556b3fb522970d17980283db7f997d3f8a4d7d30fbe2ff3ade618` (4,679,927 bytes).

## Checks and limited visual review

Actually checked: finite values; matching output shapes and affines; binary mask; brain-output equality to registered T1 inside the mask and zero outside; unchanged inputs; template grid; persisted file hashes. Optimizer convergence is recorded but is not anatomical accuracy evidence.

Codex inspected input/N4 views, three orthogonal alignment views, six axial mask views and nine orthogonal mask views. On these sampled views, no gross axis flip, major global misalignment, widespread brain removal or large skull retention was apparent. This is a preliminary sampled visual review, not whole-volume expert QC or a segmentation accuracy measurement. Peripheral cortex, cerebellar/inferior coverage and complete-volume boundaries still require team review.

The mask contains 1,190,342 voxels (1,190.342 ml). This is mask volume, not ICV, the 82 FreeSurfer volumes, or anatomical ground truth. No Dice, classification accuracy or AUC is claimed.

## History and remaining work

The [runbook](T1_PILOT_RUNBOOK.md) retains the intentionally stopped full-grid N4 attempt and the subsequent float64/float32 registration failure. The successful continuation reused hash-verified N4 output and explicitly cast the registration input to float32. Earlier runs were not overwritten. The candidate differs from unchanged author-script execution through a fixed sampling seed, shrunk/Otsu-masked N4 field estimation and the verified legacy HD-BET CLI. No data augmentation was used.

The slow CPU forward was diagnosed read-only with py-spy, first at a late 3D convolution and subsequently at mask resizing/export. Profiling did not signal the target or change security settings or model weights.

`input_recipe_confirmed=false`, `qc_status=pending`, `training_ready=false` remain intentional. Confirm the recipe with the feature owner and complete manual QC before declaring a ready T1 handoff. Identity and diagnosis timing remain unverified for formal training.

FreeSurfer/82 volumes/ICV (2C), fMRI preprocessing/ROI extraction (2D), BrainIAC/Brain-JEPA feature inference and classification were not performed. The MRI branch's overall preprocessing is not yet complete.
