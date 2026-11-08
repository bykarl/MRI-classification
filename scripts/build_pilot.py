"""Create fixed pilot manifest. No MRI download, preprocessing or training."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from mri_pipeline.manifest import write_pilot

if __name__ == '__main__':
    repo = Path(__file__).resolve().parents[1]
    write_pilot(repo, repo/'manifests/pilot_subjects.csv')
    print('Created manifests/pilot_subjects.csv; all records remain pending QC.')
