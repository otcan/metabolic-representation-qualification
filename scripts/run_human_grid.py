import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
results=[]
code=0
for mode in ['primary','missingness','resolution']:
    for dataset in ['st002081','st000818']:
        name=f'm2-human-r2-{dataset}-{mode}'
        command=[sys.executable,str(ROOT/'scripts/human_extension.py'),'--dataset',dataset,'--mode',mode,'--output',str(ROOT/'runs'/name)]
        with (ROOT/'receipts'/f'{name}.log').open('w') as log:
            p=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            (ROOT/'runs/m2-human-live.json').write_text(json.dumps({'runner_pid':os.getpid(),'state':'running','stage_pid':p.pid,'stage':name,'started_at':datetime.now(timezone.utc).isoformat(),'completed':results},indent=2)+'\n')
            code=p.wait()
        results.append({'stage':name,'exit_code':code})
        print(json.dumps(results[-1]),flush=True)
        if code: break
    if code: break
# Preserve the child's raw status in its result; map a signal to shell convention.
exit_code=code if code>=0 else 128-code
final={'runner_pid':os.getpid(),'state':'failed' if code else 'finished',
       'exit_code':exit_code,'completed':results}
if code:
    final['failed_stage']=results[-1]['stage']
(ROOT/'runs/m2-human-live.json').write_text(json.dumps(final,indent=2)+'\n')
sys.exit(exit_code)
