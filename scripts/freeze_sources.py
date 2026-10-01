"""Freeze only the compact central package; never copy the original data tree."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('<local-path>)
ORIGINAL = Path('<local-path>)

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    target = ROOT / 'inputs/central-package'
    if target.exists():
        raise SystemExit('Snapshot exists; refusing to replace it')
    records = []
    for p in sorted(SOURCE.rglob('*')):
        if p.is_symlink():
            raise RuntimeError(f'Unexpected symlink: {p}')
        if p.is_file():
            rel = p.relative_to(SOURCE)
            sha = digest(p)
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            assert digest(dest) == sha and digest(p) == sha, str(rel)
            dest.chmod(0o444)
            records.append({'path': str(rel), 'bytes': p.stat().st_size, 'sha256': sha})
    manifest = {'created_at': datetime.now(timezone.utc).isoformat(),
                'source': str(SOURCE), 'snapshot': str(target),
                'files': records, 'file_count': len(records),
                'bytes': sum(r['bytes'] for r in records),
                'interpretation': 'Content provenance only; not scientific reproduction.'}
    receipt = ROOT / 'receipts/m0-source-freeze.json'
    receipt.parent.mkdir(exist_ok=True)
    receipt.write_text(json.dumps(manifest, indent=2)+'\n')
    (receipt.parent/'m0-source-freeze.sha256').write_text(digest(receipt)+'  m0-source-freeze.json\n')
    for p in sorted(target.rglob('*'), reverse=True):
        if p.is_dir(): p.chmod(0o555)
    target.chmod(0o555)
    work = ROOT / 'work/release'
    shutil.copytree(target/'reproducible-release', work)
    for p in [work, *work.rglob('*')]:
        p.chmod(0o755 if p.is_dir() else 0o644)
    status = subprocess.run(['git','--no-optional-locks','-C',str(ORIGINAL),'status','--porcelain=v1'], capture_output=True, text=True, check=True)
    head = subprocess.run(['git','-C',str(ORIGINAL),'rev-parse','HEAD'], capture_output=True, text=True, check=True)
    (receipt.parent/'m0-original-git-state.txt').write_text('READ ONLY inventory; HEAD is not the source identity.\nHEAD '+head.stdout+status.stdout)
    print(json.dumps({'files':len(records),'bytes':manifest['bytes'],'manifest_sha256':digest(receipt)}))

if __name__ == '__main__': main()
