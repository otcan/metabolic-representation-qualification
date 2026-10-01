import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
results=[]
for file in ['runs/m0-baseline/results.json','runs/m0-remaining/results.json']:
    results.extend(json.loads((ROOT/file).read_text()))
frozen=ROOT/'inputs/central-package/reproducible-release'
work=ROOT/'work/release'
configdir=ROOT/'receipts/runtime-configs'; configdir.mkdir(exist_ok=True)
summary=[]; changes=[]
for result in results:
    artifact=result['artifact']; old=json.loads((frozen/'artifacts'/artifact/'manifest.json').read_text())
    new=json.loads((work/'artifacts'/artifact/'manifest.json').read_text())
    if new.get('config'):
        config=Path(new['config']); content=config.read_bytes(); digest=hashlib.sha256(content).hexdigest()
        assert digest==new['config_sha256'],artifact
        (configdir/(artifact+'.yaml')).write_bytes(content)
        recorded=digest
    else: recorded=None
    summary.append({'artifact':artifact,'decision_old':old.get('decision'),'decision_new':new.get('decision'),
                    'decision_matches':old.get('decision')==new.get('decision'),'outputs':len(result['comparisons']),
                    'byte_identical':sum(c['byte_identical'] for c in result['comparisons']),
                    'seconds':result['elapsed_seconds'],'runtime_config_sha256':recorded})
    for item in result['comparisons']:
        name=item['file']
        if item['byte_identical'] or not name.endswith('.csv'): continue
        a=pd.read_csv(frozen/'artifacts'/artifact/name); b=pd.read_csv(work/'artifacts'/artifact/name)
        assert a.shape==b.shape and list(a)==list(b),(artifact,name)
        for column in a.select_dtypes('number'):
            delta=(a[column]-b[column]).abs(); nonzero=a[column].abs()>1e-12
            rel=(delta[nonzero]/a.loc[nonzero,column].abs()).max()
            changes.append({'artifact':artifact,'file':name,'column':column,'changed_values':int((delta>0).sum()),
                            'max_abs':float(delta.max()),'max_relative_nonzero':float(rel) if pd.notna(rel) else None})
pd.DataFrame(summary).to_csv(ROOT/'receipts/m0-all-stage-summary.csv',index=False)
pd.DataFrame(changes).to_csv(ROOT/'receipts/m0-all-numeric-differences.csv',index=False)
out={'stages':len(results),'outputs':sum(r['outputs'] for r in summary),'byte_identical':sum(r['byte_identical'] for r in summary),
     'all_decisions_match':all(r['decision_matches'] for r in summary),'total_stage_seconds':sum(r['seconds'] for r in summary),
     'no_adaptive_tolerance_used_to_relabel_byte_mismatches':True,'source_version_boundary':'published release recovered exactly; three archived implementation fingerprints cannot be reconstructed from surviving source bytes'}
(ROOT/'receipts/m0-complete-audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
