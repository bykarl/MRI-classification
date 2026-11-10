# STEP 2A.2 - isolated T1 tools. No preprocessing or inference.
import subprocess, json, time
from pathlib import Path
root=Path('/content/FYP_MRI_LiYang')
env=root/'venvs/t1'
logdir=root/'step2a_logs'; logdir.mkdir(exist_ok=True)
commands=[
 ['uv','venv','--python','3.10',str(env)],
 ['uv','pip','install','--python',str(env/'bin/python'),'numpy==1.26.4','scipy==1.14.1','SimpleITK==2.4.1','nibabel==5.3.2','scikit-image==0.24.0','matplotlib==3.9.4','tqdm==4.67.1','PyYAML==6.0.2','setuptools==75.6.0','wheel==0.45.1'],
 ['uv','pip','install','--python',str(env/'bin/python'),'torch==2.5.1+cpu','--index-url','https://download.pytorch.org/whl/cpu'],
 ['uv','pip','install','--python',str(env/'bin/python'),'--no-deps','git+https://github.com/MIC-DKFZ/HD-BET.git@3e3d2a5993e8288f2eae928744ffb496cfc7c651']
]
results=[]
for i,cmd in enumerate(commands):
 print('INSTALL STEP',i+1,flush=True)
 t=time.monotonic()
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (logdir/f'install_{i+1}.log').write_text(p.stdout)
 results.append({'step':i+1,'returncode':p.returncode,'seconds':round(time.monotonic()-t,2)})
 print(p.stdout[-2200:],flush=True)
 (logdir/'install_results.json').write_text(json.dumps(results,indent=2))
 if p.returncode: raise RuntimeError(f'Install step {i+1} failed; inspect log')
print('TOOLS INSTALLED. No MRI preprocessing executed.')
