import gzip
import hashlib
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
checks=[]
for accepted,fresh in [('m2-human-r2-st000818-primary','m3-fresh-st000818'),('m2-ccle','m3-fresh-ccle')]:
    a=ROOT/'runs'/accepted; b=ROOT/'runs'/fresh
    am=json.loads((a/'manifest.json').read_text()); bm=json.loads((b/'manifest.json').read_text())
    assert am['code_sha256']==bm['code_sha256'] and am['protocol_sha256']==bm['protocol_sha256']
    for file in sorted(a.glob('*.csv')):
        if not (b/file.name).exists(): continue
        x=pd.read_csv(file); y=pd.read_csv(b/file.name)
        assert list(x)==list(y) and x.shape==y.shape,file.name
        volatile=[c for c in x if c in ['seconds','elapsed_seconds']]
        semantic=x.drop(columns=volatile).equals(y.drop(columns=volatile))
        assert semantic,(accepted,file.name)
        checks.append({'accepted':accepted,'fresh':fresh,'file':file.name,
                       'byte_identical':file.read_bytes()==(b/file.name).read_bytes(),
                       'all_nonruntime_columns_exact':semantic,'excluded_runtime_columns':volatile})
    if accepted=='m2-ccle':
        for name in ['primary-comparison.json']:
            assert (a/name).read_bytes()==(b/name).read_bytes()
        def gzsha(path):
            with gzip.open(path,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
        h1=gzsha(ROOT/'work/m2-ccle/full/predictions.csv.gz')
        h2=gzsha(ROOT/'work/m3-fresh-ccle/predictions.csv.gz')
        assert h1==h2
        prediction_sha=h1
pd.DataFrame(checks).to_csv(ROOT/'receipts/m3-fresh-comparison.csv',index=False)
out={'state':'PASS','reruns':['ST000818 full25outer nested fits','CCLE full60targets/600outer fits'],
     'csv_files_checked':len(checks),'byte_identical_csvs':sum(c['byte_identical'] for c in checks),
     'nonruntime_columns_all_exact':True,'ccle_decompressed_prediction_sha256':prediction_sha,
     'environment':'new .venv-check independently installed from requirements.lock; verified inputs reused',
     'scope':'Scientific reruns by execution agent, separate from Academic read-only arithmetic review.'}
(ROOT/'receipts/m3-fresh-reproduction.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
