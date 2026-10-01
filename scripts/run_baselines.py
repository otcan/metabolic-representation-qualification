"""Execute archived primary calculations, then compare tables to frozen evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT/'work/release'
FROZEN = ROOT/'inputs/central-package/reproducible-release'
RUN = ROOT/'runs/m0-baseline'
RUN.mkdir(parents=True, exist_ok=True)
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', MPLBACKEND='Agg')
stages = [
    ('pathway_score_st002081', 'pathway-score-st002081'),
    ('pathway_score_st002081_structural', 'pathway-score-st002081-structural'),
    ('pathway_score_st000818_replication', 'pathway-score-st000818-replication'),
    ('pathway_score_ccle', 'pathway-score-ccle'),
    ('pathway_score_st002081_structural_null_sensitivity', 'pathway-score-st002081-structural-null-sensitivity'),
    ('pathway_score_ccle_null_ensemble', 'pathway-score-ccle-null-ensemble'),
    ('pathway_score_ccle_null_ensemble', 'pathway-score-ccle-property-matched-null'),
]
resource_changes = []
for config in (WORK/'config').glob('*.yaml'):
    original = config.read_text()
    import re
    modified = re.sub(r'(parallel_jobs: )\d+', r'\g<1>4', original)
    if modified != original:
        config.write_text(modified)
        resource_changes.append({'config':config.name,'change':'parallel_jobs to 4 only', 'frozen_sha256':hashlib.sha256(original.encode()).hexdigest(),'runtime_sha256':hashlib.sha256(modified.encode()).hexdigest()})
(RUN/'resource-overrides.json').write_text(json.dumps(resource_changes,indent=2)+'\n')
results = []
rc = 0
for module, artifact in stages:
    t = time.monotonic()
    command = [sys.executable, '-m', 'genotype_gated_metabolism.pipelines.'+module, '--config', 'config/'+artifact+'.yaml', '--output', 'artifacts/'+artifact]
    with (RUN/(artifact+'.log')).open('w') as log:
        process = subprocess.Popen(command, cwd=WORK, stdout=log, stderr=subprocess.STDOUT, env=os.environ)
        state = {'runner_pid':os.getpid(), 'state':'running', 'stage_pid':process.pid,'stage':artifact,'started_at':datetime.now(timezone.utc).isoformat(),'completed_stages':results,'command':command}
        (RUN/'live.json').write_text(json.dumps(state,indent=2)+'\n')
        rc = process.wait()
    entry = {'artifact':artifact, 'exit_code':rc,'elapsed_seconds':round(time.monotonic()-t,3),'completed_at':datetime.now(timezone.utc).isoformat()}
    if rc == 0:
        manifest = json.loads((FROZEN/'artifacts'/artifact/'manifest.json').read_text())
        comparisons = []
        for name, expected in manifest['output_sha256'].items():
            output = WORK/'artifacts'/artifact/name
            observed = hashlib.sha256(output.read_bytes()).hexdigest() if output.exists() else None
            comparisons.append({'file':name,'expected':expected,'observed':observed,'byte_identical':observed==expected})
        entry['comparisons'] = comparisons
    results.append(entry)
    (RUN/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(entry),flush=True)
    if rc: break
# Preserve the child's raw status in its result; map a signal to shell convention.
exit_code = rc if rc >= 0 else 128 - rc
final = {'runner_pid':os.getpid(),'state':'failed' if rc else 'finished',
         'exit_code':exit_code,'results':results}
if rc:
    final['failed_stage'] = results[-1]['artifact']
(RUN/'live.json').write_text(json.dumps(final,indent=2)+'\n')
sys.exit(exit_code)
