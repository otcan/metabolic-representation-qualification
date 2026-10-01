import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen
import zipfile
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
meta=json.loads((ROOT/'readiness/m1-public-release-check.json').read_text())['zenodo']
destination=ROOT/'inputs/public-archive'/meta['file_name']
destination.parent.mkdir(parents=True,exist_ok=True)
if not destination.exists():
    with urlopen(meta['file_content_url'],timeout=60) as response: data=response.read()
    if hashlib.md5(data).hexdigest()!=meta['reported_file_checksum'].split(':')[1]: raise RuntimeError('Archive checksum mismatch')
    destination.write_bytes(data); destination.chmod(0o444)
else: data=destination.read_bytes()
assert hashlib.md5(data).hexdigest()==meta['reported_file_checksum'].split(':')[1]
local=ROOT/'inputs/central-package/reproducible-release'
records=[]
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    files=[n for n in archive.namelist() if not n.endswith('/')]
    prefix=files[0].split('/')[0]+'/'
    for name in files:
        rel=name[len(prefix):] if name.startswith(prefix) else name
        p=local/rel
        payload=archive.read(name)
        records.append({'path':rel,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest(),
                        'local_exists':p.is_file(),'local_byte_identical':p.is_file() and p.read_bytes()==payload})
local_extra=sorted(str(p.relative_to(local)) for p in local.rglob('*') if p.is_file() and str(p.relative_to(local)) not in {r['path'] for r in records})
out={'checked_at':datetime.now(timezone.utc).isoformat(),'source_url':meta['file_content_url'],'archive_sha256':hashlib.sha256(data).hexdigest(),
     'archive_md5_verified':True,'files':records,'local_extra':local_extra,
     'all_archive_files_identical':all(r['local_byte_identical'] for r in records)}
(ROOT/'receipts/m0-public-archive-comparison.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='files'}))
