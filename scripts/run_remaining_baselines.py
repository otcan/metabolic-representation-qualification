"""Regenerate remaining core sensitivities/reports with two-worker ceiling."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]; WORK=ROOT/'work/release'
RUN=ROOT/'runs/m0-remaining'; RUN.mkdir(parents=True,exist_ok=True)
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLBACKEND='Agg')
for name in ['pathway-score-human-sensitivity','pathway-score-ccle-sensitivity']:
    p=WORK/'config'/f'{name}.yaml'
    p.write_text(re.sub(r'(parallel_jobs: )\d+',r'\g<1>2',p.read_text()))
stages=['pathway_score_human_sensitivity','pathway_score_human_graph_mixing',
        'pathway_score_ccle_sensitivity','pathway_score_ccle_reaction_cluster',
        'pathway_score_mapping_supplement','pathway_score_publication_figures','factorized_pathway_publication']
results=[]
code=0
for module in stages:
    artifact=module.replace('_','-'); t=time.monotonic()
    command=[sys.executable,'-m','genotype_gated_metabolism.pipelines.'+module]
    with (RUN/f'{artifact}.log').open('w') as log:
        p=subprocess.Popen(command,cwd=WORK,stdout=log,stderr=subprocess.STDOUT,env=os.environ)
        (RUN/'live.json').write_text(json.dumps({'runner_pid':os.getpid(),'state':'running','stage_pid':p.pid,'stage':artifact,'completed':results},indent=2)+'\n')
        code=p.wait()
    comparisons=[]
    if code==0:
        old=json.loads((ROOT/'inputs/central-package/reproducible-release/artifacts'/artifact/'manifest.json').read_text())
        for name,expected in old['output_sha256'].items():
            path=WORK/'artifacts'/artifact/name
            observed=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
            comparisons.append({'file':name,'expected':expected,'observed':observed,'byte_identical':observed==expected})
    results.append({'artifact':artifact,'exit_code':code,'elapsed_seconds':time.monotonic()-t,'comparisons':comparisons})
    (RUN/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results[-1]),flush=True)
    if code: break
# Preserve the child's raw status in its result; map a signal to shell convention.
exit_code=code if code>=0 else 128-code
final={'runner_pid':os.getpid(),'state':'failed' if code else 'finished',
       'exit_code':exit_code,'results':results}
if code:
    final['failed_stage']=results[-1]['artifact']
(RUN/'live.json').write_text(json.dumps(final,indent=2)+'\n')
sys.exit(exit_code)
