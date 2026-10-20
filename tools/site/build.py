#!/usr/bin/env python3
"""Build Jekyll, then copy exact historical source files as unprocessed downloads."""
from pathlib import Path
import argparse
import shutil
import hashlib
import json
import subprocess
ROOT=Path(__file__).resolve().parents[2]
args=argparse.ArgumentParser();args.add_argument('--destination',type=Path,default=ROOT/'_site');options=args.parse_args()
destination=options.destination.resolve()
subprocess.run(['bundle','exec','jekyll','build','--strict_front_matter','--destination',str(destination)],cwd=ROOT,check=True)
shutil.copytree(ROOT/'articles/security_history',destination/'articles/security_history',dirs_exist_ok=True)
print('Copied archived source downloads without Liquid/front-matter processing.')

metadata={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'dirty_source':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'pdf_sha256':hashlib.sha256((destination/'reports/security-handbook/security-handbook.pdf').read_bytes()).hexdigest()}
(destination/'site-build.json').write_text(json.dumps(metadata,indent=2)+'\n')
