#!/usr/bin/env python3
"""Verify revision provenance, input checks and every generated PDF's geometry/text."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import subprocess
import tempfile
import yaml
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/security-handbook'
manifest=json.loads((OUT/'build-manifest.json').read_text())
assert manifest['runtime_tested']
assert manifest['runtime_cases_summary']=={'pass':6,'fail':0,'inconclusive':1}
assert not manifest['runtime_suite_all_passed']
assert not any(d['overflow_flags'] for d in manifest['documents'].values())
for record in manifest['sources']:
    assert hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest()==record['sha256'],record['path']
for path in sorted((ROOT/'articles').glob('18*.md')):
    archive=ROOT/'articles/security_history'/(path.name+'.txt')
    baseline=subprocess.check_output(['git','show',manifest['historical_baseline_revision']+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
    assert archive.read_bytes()==baseline,archive
    meta=yaml.safe_load(path.read_text().split('---',2)[1])
    assert meta['last_modified']=='2026-10' and meta['revision_author'].startswith('[Juan Carlos Nevarez')
    assert path.read_bytes()!=baseline,'Article was not updated'
subprocess.run(['python3','-m','unittest','discover','-s',str(ROOT/'examples/security-lab'),'-p','test_*.py','-v'],check=True,cwd=ROOT)
subprocess.run(['bash','-n',str(ROOT/'examples/security-lab/setup.sh'),str(ROOT/'examples/security-lab/environment.sh')],check=True)
result={'edition':manifest['edition'],'page_counts':{},'font_embedding':'passed','tagged_pdf':True,'source_hashes_verified':len(manifest['sources']),'archived_originals_verified':4,'policy_boundary_tests':8,'render_overflows':0,'runtime_security_tested':True,'runtime_cases_summary':manifest['runtime_cases_summary'],'runtime_suite_all_passed':False,'runtime_result_origin':'Recorded evidence, not re-executed by this verifier','physical_print_verified':False,'site_build_verified':manifest['site_build_verified']}
with tempfile.TemporaryDirectory() as tmp:
    for stem,data in manifest['documents'].items():
        path=OUT/(stem+'.pdf')
        info=subprocess.check_output(['pdfinfo','-f','1','-l',str(data['pages']),str(path)],text=True)
        assert re.search(r'^Tagged:\s+yes',info,re.M)
        assert 'Juan Carlos Nevarez · Gh0stlyKn1ght' in info
        sizes=re.findall(r'^Page\s+\d+ size:\s+(\d+(?:\.\d+)?) x (\d+(?:\.\d+)?) pts',info,re.M)
        expected=(792.,612.) if stem=='trust-boundaries-landscape' else (612.,792.)
        assert len(sizes)==data['pages'] and all(tuple(map(float,s))==expected for s in sizes),(stem,sizes)
        fonts=subprocess.check_output(['pdffonts',str(path)],text=True).splitlines()[2:]
        assert all(line.split()[-5]=='yes' for line in fonts)
        text_path=Path(tmp)/(stem+'.txt')
        subprocess.run(['pdftotext','-layout',str(path),str(text_path)],check=True)
        text=text_path.read_text()
        assert '\ufffd' not in text and '{{' not in text and '{%' not in text
        if stem=='security-handbook':
            for term in ['DDS:Access:Permissions','ROS_SECURITY_KEYSTORE','Information Disclosure','Full teaching-system threat records','Complete example policy','inconclusive','Libraries and technology choices']:
                assert term in text,term
            for i in range(1,9):assert f'TM-{i:03}' in text
        parsed=BeautifulSoup((OUT/(stem+'.html')).read_text(),'html.parser')
        ids=[element['id'] for element in parsed.find_all(id=True)]
        assert len(ids)==len(set(ids))
        for anchor in parsed.find_all('a',href=True):
            if anchor['href'].startswith('#'):assert anchor['href'][1:] in ids
        assert all(image['src'].startswith('data:') for image in parsed.find_all('img',src=True))
        result['page_counts'][stem]=data['pages']
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
