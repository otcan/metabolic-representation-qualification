"""Copy only hash-verified, required public inputs from the read-only original."""
import hashlib
import json
from pathlib import Path
import shutil
from datetime import datetime, timezone
from genotype_gated_metabolism.datasets.ccle import CCLE_FILES
from genotype_gated_metabolism.fetch_human_gem import FILES, TASK_FILES

ROOT = Path(__file__).resolve().parents[1]
OLD = Path('<local-path>)
NEW = ROOT/'work/release/data/raw'

def sha(p): return hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()

records = []
spec = {'st002081/ST002081_AN003790.txt': 'e5d68bea4f6adf113f9bafa0e8bd333b949f289f0dc645a18435d542c3ae9c9b'}
spec.update({f'ccle/2019/{k}':v for k,v in CCLE_FILES.items()})
spec.update({f'human-gem/v2.0.0/{k}':v for k,v in FILES.items()})
spec.update({f'human-gem/v2.0.0/metabolicTasks/{k}':v for k,v in TASK_FILES.items()})
manifest = json.loads((ROOT/'work/release/artifacts/pathway-score-st000818-replication/manifest.json').read_text())
for kind, endpoint in [('factors','factors'),('measurements','data')]:
    url = f'https://www.metabolomicsworkbench.org/rest/study/study_id/ST000818/{endpoint}/json'
    rel = 'public-intervention-registry/workbench-cache/'+hashlib.sha256(url.encode()).hexdigest()+'.txt'
    spec[rel] = manifest['source_sha256'][kind]
for rel, expected in spec.items():
    src, dest = OLD/rel, NEW/rel
    observed = sha(src)
    if observed != expected: raise RuntimeError(f'Input drift: {rel}: {observed} != {expected}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    assert sha(dest) == expected
    records.append({'source':str(src),'copy':str(dest),'bytes':src.stat().st_size,'sha256':observed})
out = {'created_at':datetime.now(timezone.utc).isoformat(),'files':records,'bytes':sum(r['bytes'] for r in records),'no_original_writes':True}
(ROOT/'receipts/m0-input-recovery.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'files':len(records),'bytes':out['bytes']}))
