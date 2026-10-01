"""Portable read-only-public retrieval. Run in a fresh Paper 1 workspace copy."""
import hashlib
import io
import json
from pathlib import Path
import shutil
from urllib.request import urlopen
import zipfile
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
URL='https://zenodo.org/api/records/22207315/files/factorized-pathway-scores-1.0.1.zip/content'
EXPECTED='826d7a19d33955587f1911f0b0850d475b487780c17ac5b026e165541221dc9a'
FROZEN=ROOT/'inputs/central-package/reproducible-release'
WORK=ROOT/'work/release'

def fetch(url,expected):
    with urlopen(url,timeout=120) as response: data=response.read()
    observed=hashlib.sha256(data).hexdigest()
    if observed!=expected: raise RuntimeError(f'Upstream drift at {url}: {observed}; expected {expected}')
    return data

def main():
    if FROZEN.exists() or WORK.exists(): raise RuntimeError('Use a fresh directory; existing inputs/work are never overwritten')
    payload=fetch(URL,EXPECTED)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names=[n for n in archive.namelist() if not n.endswith('/')]
        prefix=names[0].split('/')[0]+'/'
        for name in names:
            relative=Path(name[len(prefix):])
            if relative.is_absolute() or '..' in relative.parts: raise RuntimeError('Unsafe archive path')
            dest=FROZEN/relative; dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(archive.read(name)); dest.chmod(0o444)
    shutil.copytree(FROZEN,WORK)
    for p in WORK.rglob('*'):
        if p.is_file(): p.chmod(0o644)
    # This script deliberately uses only the standard library before environment setup.
    import ast
    def constant(path,name):
        tree=ast.parse(path.read_text())
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
                return ast.literal_eval(node.value)
        raise KeyError(name)
    source=WORK/'src/genotype_gated_metabolism'
    specification=[]
    for name,digest in constant(source/'datasets/ccle.py','CCLE_FILES').items():
        specification.append((f'ccle/2019/{name}',f'https://data.broadinstitute.org/ccle/{name}',digest))
    for name,digest in constant(source/'fetch_human_gem.py','FILES').items():
        specification.append((f'human-gem/v2.0.0/{name}',f'https://raw.githubusercontent.com/SysBioChalmers/Human-GEM/v2.0.0/model/{name}',digest))
    for name,digest in constant(source/'fetch_human_gem.py','TASK_FILES').items():
        specification.append((f'human-gem/v2.0.0/metabolicTasks/{name}',f'https://raw.githubusercontent.com/SysBioChalmers/Human-GEM/v2.0.0/data/metabolicTasks/{name}',digest))
    specification.append(('st002081/ST002081_AN003790.txt','https://www.metabolomicsworkbench.org/rest/study/analysis_id/AN003790/mwtab/txt','e5d68bea4f6adf113f9bafa0e8bd333b949f289f0dc645a18435d542c3ae9c9b'))
    old=json.loads((FROZEN/'artifacts/pathway-score-st000818-replication/manifest.json').read_text())
    for key,endpoint in [('factors','factors'),('measurements','data')]:
        url=f'https://www.metabolomicsworkbench.org/rest/study/study_id/ST000818/{endpoint}/json'
        specification.append(('public-intervention-registry/workbench-cache/'+hashlib.sha256(url.encode()).hexdigest()+'.txt',url,old['source_sha256'][key]))
    records=[]
    for relative,url,digest in specification:
        if relative.startswith('st002081/'):
            with urlopen(url,timeout=120) as response: data=response.read().rstrip(b'\r\n')
            if hashlib.sha256(data).hexdigest()!=digest: raise RuntimeError('ST002081 normalized source drift')
        else: data=fetch(url,digest)
        p=WORK/'data/raw'/relative; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data)
        records.append({'source':url,'copy':str(p),'sha256':digest,'bytes':len(data)})
    (ROOT/'receipts').mkdir(exist_ok=True)
    (ROOT/'receipts/m0-input-recovery.json').write_text(json.dumps({'created_at':datetime.now(timezone.utc).isoformat(),'files':records,'bytes':sum(r['bytes'] for r in records),'public_retrieval':True},indent=2)+'\n')
    print('Pinned public inputs recovered; install the archived environment and run the documented commands.')

if __name__=='__main__': main()
