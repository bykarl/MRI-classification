"""Prepare one FreeSurfer pilot without running any reconstruction stage."""
import argparse
from pathlib import Path
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

def run_capture(command, env=None):
    result = subprocess.run(list(map(str, command)), env=env, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Preparation command failed: " + repr(command) + "\n" + result.stdout[-3000:] + "\n" + result.stderr[-3000:])
    return result.stdout

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-root", type=Path, required=True)
    parser.add_argument("--qc-python", type=Path, required=True)
    args = parser.parse_args()
    root = args.code_root.resolve()
    sys.path.insert(0, str(root / "scripts"))
    import freesurfer_pilot as fs
    cfg = fs.load_config(root / "configs/freesurfer_pilot.json")
    snapshot = fs.read_json(root / "source_snapshot.json")
    for relative, expected in snapshot["files_sha256"].items():
        if fs.digest(root / relative) != expected:
            raise RuntimeError("Pinned source differs: " + relative)
    if fs.digest(root / "schemas/t1_volume_names.json") != cfg["volume_schema_sha256"]:
        raise RuntimeError("82-volume schema differs")
    preflight = fs.preflight(cfg, require_install=True, require_license=True)
    fs.require_ready(preflight)
    Path(cfg["fs_license"]).chmod(0o600)
    active = fs.read_json(Path(cfg["project_root"]) / "software_install/active.json")
    software_dir = Path(active["output"])
    installed = fs.read_json(software_dir / "completed.json")
    probe = fs.read_json(software_dir / "vendor_license_probe/verification.json")
    fingerprint = fs.fingerprint(cfg)
    if installed.get("software_checks") != "pass" or probe.get("licensed_vendor_template_conversion") != "pass":
        raise RuntimeError("Software/license evidence missing")
    if fingerprint != installed["fingerprint"] or fingerprint != probe["fingerprint"]:
        raise RuntimeError("Verified software build differs")
    qc_env = {**os.environ, "MPLBACKEND": "Agg"}
    qc_versions = run_capture([args.qc_python, "-c",
        "import json,sys,numpy,nibabel,matplotlib; assert matplotlib.get_backend().lower()=='agg'; "
        "print(json.dumps({'python':sys.version.split()[0],'numpy':numpy.__version__,"
        "'nibabel':nibabel.__version__,'matplotlib':matplotlib.__version__,'backend':matplotlib.get_backend()}))"], qc_env)
    versions = json.loads(qc_versions)
    assert (versions["numpy"], versions["nibabel"], versions["matplotlib"]) == ("1.26.4", "5.3.2", "3.9.4")
    for script in ["freesurfer_qc.py", "freesurfer_volumes.py"]:
        run_capture([args.qc_python, root / "scripts" / script, "--help"], qc_env)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    prep = Path(cfg["project_root"]) / "freesurfer_pilot/preparation" / ("ready_" + stamp)
    prep.mkdir(parents=True, exist_ok=False)
    input_probe = r'''
import json,sys
from pathlib import Path
import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
image=nib.load(sys.argv[1])
values=np.asarray(image.dataobj,dtype=np.float32)
assert values.ndim==3 and np.isfinite(values).all()
assert all(float(v)>0 for v in image.header.get_zooms()[:3])
assert np.isfinite(image.affine).all() and abs(np.linalg.det(image.affine[:3,:3]))>1e-9
assert float(values.max())>float(values.min())
canonical=nib.as_closest_canonical(image)
display=np.asarray(canonical.dataobj,dtype=np.float32)
lo,hi=np.percentile(display,[1,99])
fig,axes=plt.subplots(1,3,figsize=(10,4))
for axis,name in enumerate(["Sagittal","Coronal","Axial"]):
    axes[axis].imshow(np.rot90(np.take(display,display.shape[axis]//2,axis)),cmap="gray",vmin=lo,vmax=hi)
    axes[axis].set_title(name);axes[axis].axis("off")
fig.suptitle("Native T1 input preview only; not a segmentation or manual QC approval")
fig.tight_layout();fig.savefig(sys.argv[2],dpi=100);plt.close(fig)
report={"shape":list(image.shape),"spacing_mm":list(map(float,image.header.get_zooms()[:3])),
        "axis_codes":list(nib.aff2axcodes(image.affine)),"spatial_units":image.header.get_xyzt_units()[0],
        "finite_voxels":True,"nonconstant":True,"affine_invertible":True,"manual_qc":"pending",
        "preview_only":True}
Path(sys.argv[3]).write_text(json.dumps(report,indent=2))
'''
    input_probe_path = prep / "input_read_check.py"
    input_probe_path.write_text(input_probe)
    native = Path(cfg["persistent_root"]) / cfg["input_relative"]
    run_capture([args.qc_python, input_probe_path, native, prep / "native_T1_preview.png", prep / "native_input_check.json"], qc_env)
    input_metadata = fs.read_json(prep / "native_input_check.json")
    # Preparation creates an immutable run and copies inputs/metadata, never calls recon-all.
    run_id = "fs820_" + stamp
    run = fs.initialize(cfg, run_id)
    job_markers = list(run.glob("*.running.json"))
    if job_markers or any((run / (stage + ".completed.json")).exists() for stage in fs.STAGES):
        raise RuntimeError("Fresh preparation unexpectedly contains reconstruction markers")
    if (run / "subjects" / cfg["subject_id"]).exists():
        raise RuntimeError("Fresh preparation unexpectedly contains a processed subject")
    software_evidence = {}
    for rel in ["state.json", "completed.json", "vendor_license_probe/verification.json"]:
        source = software_dir / rel
        target = Path(cfg["persistent_root"]) / "freesurfer_pilot/software_evidence" / software_dir.name / rel
        software_evidence[rel] = {"drive_relative":str(target.relative_to(Path(cfg["persistent_root"]))),
                                  "sha256":fs.copy_checked(source,target)}
    preparation_files = {}
    persistent_prep = Path(cfg["persistent_root"]) / "freesurfer_pilot/preparation" / prep.name
    for source in [input_probe_path, prep / "native_T1_preview.png", prep / "native_input_check.json"]:
        preparation_files[source.name] = fs.copy_checked(source, persistent_prep / source.name)
    # Persist all small pinned code/config/schema files for future recovery; never the license.
    for relative in list(snapshot["files_sha256"]) + ["source_snapshot.json"]:
        fs.copy_checked(root / relative, persistent_prep / "source_snapshot" / relative)
    self_copy = prep / "executed_prepare_case.py"
    self_copy.write_bytes(Path(__file__).read_bytes())
    preparation_files[self_copy.name] = fs.copy_checked(self_copy,persistent_prep/self_copy.name)
    report = {"checked_at_utc":fs.now(),"record_id":cfg["record_id"],"run_id":run_id,
        "ready_to_start_autorecon1_in_current_runtime":True,"source_commit":snapshot["commit"],
        "runtime":preflight["runtime"],"software_fingerprint":fingerprint,
        "software_checks":"pass","licensed_vendor_template_conversion":"pass",
        "raw_input_sha256":cfg["raw_sha256"],"native_input_sha256":cfg["input_sha256"],
        "native_input_read_check":input_metadata,"qc_environment":versions,
        "qc_and_volume_exporter_cli_imports":"pass","schema_sha256":cfg["volume_schema_sha256"],
        "local_run":str(run),"drive_run":str(fs.persistent_run(cfg,run_id)),
        "initial_run_files_drive_sha_readback":"pass","software_evidence":software_evidence,
        "preparation_files":preparation_files,"openmp_threads":cfg["openmp_threads"],
        "FS_V8_XOPTS":cfg["FS_V8_XOPTS"],"next_stage":"autorecon1",
        "reconstruction_started":False,"completed_reconstruction_stages":[],
        "qc_status":"pending","training_ready":False,
        "limitations":["Readiness applies to this Colab runtime; reset requires software/license restoration.",
            "Only initialization/small-file Drive persistence was tested; real stage archives have not been produced.",
            "Successful preflight does not guarantee reconstruction quality or completion within Colab session limits."]}
    report_path=prep/"readiness.json"
    fs.write_new(report_path,report)
    fs.copy_checked(report_path,persistent_prep/report_path.name)
    pointer={"run_id":run_id,"readiness_report":str(persistent_prep/report_path.name),
             "readiness_sha256":fs.digest(report_path),"reconstruction_started":False}
    fs.write_new(prep/"run_pointer.json",pointer)
    fs.copy_checked(prep/"run_pointer.json",persistent_prep/"run_pointer.json")
    print("READINESS_REPORT_JSON")
    print(json.dumps(report,indent=2))
    print("END_READINESS_REPORT")
    print("PASS: all preparation checks completed; next action is autorecon1. No reconstruction started.")
if __name__ == "__main__":
    main()

