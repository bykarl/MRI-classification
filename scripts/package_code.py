"""Package version-controlled and nonignored new source for manual Colab upload."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import zipfile


def main():
    repo=Path(__file__).resolve().parents[1]
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    files=subprocess.check_output(['git','-C',str(repo),'ls-files','-z','--cached','--others','--exclude-standard']).decode('utf-8').split('\0')
    snapshot={'branch':subprocess.check_output(['git','-C',str(repo),'branch','--show-current'],text=True).strip(),
              'base_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),
              'notice':'Uncommitted source snapshot; not a new Git commit.','files':{}}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.output,'x',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(set(filter(None,files))):
            path=repo/name
            if path.is_file():
                snapshot['files'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
                z.write(path,'MRI-classification/'+name)
        z.writestr('MRI-classification/CODE_SNAPSHOT.json',json.dumps(snapshot,ensure_ascii=False,indent=2))
    print(args.output,'SHA-256',hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__=='__main__': main()
