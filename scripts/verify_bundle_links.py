"""Validate relative Markdown links against the exported ZIP namespace."""
import argparse
import json
import posixpath
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import zipfile

def validate(entries):
    checked=[];broken=[]
    for name,data in entries.items():
        if not name.endswith('.md'):continue
        for target in re.findall(r'!?\[[^\]]*\]\(([^)\n]+)\)',data.decode()):
            target=target.strip()
            target=target[1:target.index('>')] if target.startswith('<') else target.split()[0]
            parsed=urlsplit(target)
            if parsed.scheme or target.startswith(('#','/')):continue
            path=unquote(parsed.path)
            if not path:continue
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),path))
            entry={'source':name,'target':target,'resolved':resolved}
            checked.append(entry)
            if resolved not in entries and not any(p.startswith(resolved.rstrip('/')+'/') for p in entries):broken.append(entry)
    return {'relative_links_checked':len(checked),'broken_links':broken}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('archive');parser.add_argument('--receipt')
    args=parser.parse_args()
    with zipfile.ZipFile(args.archive) as archive:
        result=validate({n:archive.read(n) for n in archive.namelist() if not n.endswith('/')})
    if args.receipt:Path(args.receipt).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    raise SystemExit(1 if result['broken_links'] else 0)
