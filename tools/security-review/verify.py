#!/usr/bin/env python3
"""Verify generated PDFs, source hashes, extraction coverage and paper dimensions."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess
import tempfile
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/security-review'
manifest = json.loads((OUT/'build-manifest.json').read_text())
inventory = json.loads((OUT/'inventory.json').read_text())
assert not any(manifest['layout_overflows'].values()), 'Render overflow flags remain'
assert len(manifest['matrix_tables']) == 3
assert all(t['records'] > 0 for t in manifest['matrix_tables'])
for source in inventory['files']:
    assert hashlib.sha256(subprocess.check_output(['git','show',inventory['source_revision']+':'+source['path']],cwd=ROOT)).hexdigest() == source['sha256'], source['path']
reader = BeautifulSoup((OUT/'security-reference-reader.html').read_text(), 'html.parser')
assert len(reader.find_all('img')) == len(manifest['figures']) == 15
assert all(im['src'].startswith('data:') for im in reader.find_all('img'))
assert not re.search(r'{[{%]', str(reader)), 'Unresolved template'
expected_records = Counter(re.match(r'183-(GEN|TB3|MARA)-', s['id'])[1] for s in reader.select('section.record') if re.match(r'183-(GEN|TB3|MARA)-', s['id']))
assert sum(expected_records.values()) == sum(t['records'] for t in manifest['matrix_tables'])
results = {'paper_sizes':{},'page_counts':{},'matrix_records':dict(expected_records),'preserved_table_cells':manifest['preserved_table_cells'],'embedded_figures':len(manifest['figures']),'render_overflows':0,'source_hashes_verified':len(inventory['files']),'physical_print_verified':False,'runtime_security_tested':False}
with tempfile.TemporaryDirectory() as temporary:
    texts={}
    for stem, dimensions in [('security-review-report',(612,792)),('security-reference-reader',(612,792)),('security-figure-atlas',(792,612))]:
        path=OUT/(stem+'.pdf')
        info=subprocess.check_output(['pdfinfo',str(path)],text=True)
        pages=int(re.search(r'^Pages:\s+(\d+)',info,re.M)[1])
        detailed=subprocess.check_output(['pdfinfo','-f','1','-l',str(pages),str(path)],text=True)
        sizes=re.findall(r'^Page\s+\d+ size:\s+(\d+(?:\.\d+)?) x (\d+(?:\.\d+)?) pts',detailed,re.M)
        assert len(sizes)==pages, (stem,len(sizes),pages)
        assert all(tuple(map(float,size))==dimensions for size in sizes), stem
        assert 'Author:          Juan Carlos Nevarez · Gh0stlyKn1ght' in info
        txt=Path(temporary)/(stem+'.txt')
        subprocess.run(['pdftotext','-layout',str(path),str(txt)],check=True)
        text=txt.read_text();texts[stem]=text
        assert '\ufffd' not in text and '{{' not in text and '{%' not in text
        fonts=subprocess.check_output(['pdffonts',str(path)],text=True).splitlines()[2:]
        for font in fonts:
            parts=font.split()
            assert parts[-5]=='yes', ('Font not embedded',font)
        results['page_counts'][stem]=pages
        results['paper_sizes'][stem]=list(dimensions)
    pdf_records=Counter(re.findall(r'\b(GEN|TB3|MARA)-\d{3}\b',texts['security-reference-reader']))
    assert pdf_records==expected_records,(pdf_records,expected_records)
    for word in ['✓','✘','▲']:
        assert word in texts['security-reference-reader'],word
    assert results['page_counts']['security-figure-atlas']==len(manifest['figures'])+1
(OUT/'verification.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
