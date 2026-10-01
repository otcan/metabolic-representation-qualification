import hashlib
import json
from pathlib import Path
import time
import yaml
from genotype_gated_metabolism.pipelines.ccle_proof import _candidate_catalog
ROOT=Path(__file__).resolve().parents[1]; work=ROOT/'work/release'
out=ROOT/'runs/m0-mapping'; out.mkdir(parents=True,exist_ok=True)
config=yaml.safe_load((work/'config/ccle-expanded.yaml').read_text())
t=time.monotonic()
mapping,catalog=_candidate_catalog(config,work)
results=[]
for name,data in [('ccle_metabolite_mapping.csv',mapping),('ccle_candidate_hypotheses.csv',catalog)]:
    p=out/name; data.to_csv(p,index=False)
    old=ROOT/'inputs/central-package/reproducible-release/artifacts/ccle-expanded'/name
    results.append({'file':name,'rows':len(data),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'byte_identical':old.read_bytes()==p.read_bytes()})
receipt={'elapsed_seconds':time.monotonic()-t,'outputs':results,'scope':'De novo map and direct reaction candidate enumeration from verified raw HumanGEM and assay panel. Does not rerun supporting association discovery.'}
(ROOT/'receipts/m0-mapping-rebuild.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
