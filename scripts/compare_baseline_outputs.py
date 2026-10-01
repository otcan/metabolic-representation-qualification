"""Numerical and content audit; no arbitrary pass-by-tolerance conversion."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
FROZEN=ROOT/'inputs/central-package/reproducible-release'
WORK=ROOT/'work/release'
results=json.loads((ROOT/'runs/m0-baseline/results.json').read_text())
records=[]; provenance=[]
for item in results:
    name=item['artifact']; a=FROZEN/'artifacts'/name; b=WORK/'artifacts'/name
    old=json.loads((a/'manifest.json').read_text()); new=json.loads((b/'manifest.json').read_text())
    provenance.append({'artifact':name,**{k+'_matches':old.get(k)==new.get(k) for k in ['decision','source_sha256','config_sha256','protocol_sha256','implementation_sha256']}})
    for comparison in item['comparisons']:
        f=comparison['file']
        if f.endswith('.csv'):
            x=pd.read_csv(a/f); y=pd.read_csv(b/f)
            if x.shape!=y.shape or list(x)!=list(y): raise ValueError('Table schema changed: '+name+'/'+f)
            for c in x:
                base={'artifact':name,'file':f,'column':c,'rows':len(x),'byte_identical_file':comparison['byte_identical']}
                if pd.api.types.is_numeric_dtype(x[c]) and not pd.api.types.is_bool_dtype(x[c]):
                    delta=(x[c]-y[c]).abs()
                    records.append({**base,'max_absolute_difference':float(delta.max()),'unequal_values':int((x[c]!=y[c]).sum()),'matching_nan_pattern':bool(x[c].isna().equals(y[c].isna()))})
                else:
                    if not x[c].equals(y[c]): raise ValueError('Non-numeric values differ: '+name+'/'+f+'/'+c)
                    records.append({**base,'max_absolute_difference':0.,'unequal_values':0,'matching_nan_pattern':True})
pd.DataFrame(records).to_csv(ROOT/'receipts/m0-numeric-differences.csv',index=False)
(ROOT/'receipts/m0-provenance-comparison.json').write_text(json.dumps(provenance,indent=2)+'\n')
# Independently reduce frozen per-sample sufficient statistics to group-weighted RMSE.
reductions=[]
for name in ['pathway-score-st002081','pathway-score-st002081-structural']:
    d=pd.read_csv(FROZEN/'artifacts'/name/'sample-metrics.csv')
    table=pd.read_csv(FROZEN/'artifacts'/name/'model-metrics.csv').set_index('model')
    for model,f in d.groupby('model'):
        value=float(np.sqrt(f.groupby('subject_id')['mean_squared_error'].mean().mean()))
        expected=float(table.loc[model,'equal_subject_weighted_rmse_sd'])
        reductions.append({'artifact':name,'model':model,'recomputed':value,'archived':expected,'absolute_difference':abs(value-expected)})
pd.DataFrame(reductions).to_csv(ROOT/'receipts/m0-independent-table-reduction.csv',index=False)
print(json.dumps({'stages':len(results),'declared_outputs':sum(len(x['comparisons']) for x in results),
                  'byte_identical_outputs':sum(c['byte_identical'] for x in results for c in x['comparisons']),
                  'max_table_reduction_difference':max(r['absolute_difference'] for r in reductions)}))
