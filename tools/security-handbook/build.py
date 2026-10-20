#!/usr/bin/env python3
"""Build the revised handbook from working-tree articles, leaving the historical PDF intact."""
from pathlib import Path
import base64
import hashlib
import html
import importlib.util
import importlib.metadata
import json
import re
import subprocess
from urllib.parse import urlsplit, unquote

from bs4 import BeautifulSoup
import markdown
import yaml
from weasyprint import HTML

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/security-handbook'
DATE='2026-10-20'
AUTHOR='Juan Carlos Nevarez · Gh0stlyKn1ght'
CORE=sorted((ROOT/'articles').glob('18*.md'))
spec=importlib.util.spec_from_file_location('historical_print',ROOT/'tools/security-review/build.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
CSS=base.CSS.replace('ROS 2 · Security review / historical reference','ROS 2 · Revised security handbook · October 2026')
CSS+='''
@page :first { @top-left { content: none; } }
.cover h1 { font-size: 29pt; }
.source-credit { border-left: 2pt solid black; padding-left: 10pt; font-size: 9pt; }
.threat-record { border-top: 1pt solid black; margin-top: 14pt; padding-top: 5pt; }
.threat-record dt { font-weight: bold; break-after: avoid; margin-top: 7pt; }
.threat-record dd { margin-left: 0; margin-bottom: 5pt; }
figure img { max-height: 6.5in; }
.diagram-sheet { page: atlas; }
.diagram-sheet img { max-height: 5.8in; width: 100%; object-fit: contain; }
'''
MANIFEST={'edition':DATE,'author':AUTHOR,'source_state':'Technical revision; consult publication verification for release state','historical_baseline_revision':base.REV,'documents':{},'runtime_tested':False,'physical_print_verified':False}

def meta_body(path):
    _,front,body=path.read_text().split('---',2)
    return yaml.safe_load(front),body


def md(text):
    return markdown.markdown(text,extensions=['extra','md_in_html','toc','sane_lists'])


def source_section(path,identifier,front_matter=False):
    if front_matter:
        meta,body=meta_body(path)
        for key,value in meta.items():
            if isinstance(value,str):body=re.sub(r'{{\s*page\.'+key+r'\s*}}',lambda m:value,body)
        body=re.sub(r'\{:[^}\n]*\}', '',body)
    else:body=path.read_text()
    assert not re.search(r'{[{%]',body), f'Unresolved template in {path}'
    soup=BeautifulSoup(md(body),'html.parser')
    for image in soup.find_all('img',src=True):
        asset=(path.parent/image['src']).resolve()
        assert asset.is_relative_to(ROOT) and asset.is_file(),asset
        mime='image/svg+xml' if asset.suffix=='.svg' else 'image/png'
        image['src']='data:'+mime+';base64,'+base64.b64encode(asset.read_bytes()).decode()
    for element in soup.find_all(id=True):element['id']=identifier+'-'+element['id']
    core_by_name={p.name:'chapter-'+p.stem[:3] for p in CORE}
    core_by_route={Path(meta_body(p)[0]['permalink']).name:'chapter-'+p.stem[:3] for p in CORE}
    all_routes={}
    for item in (ROOT/'articles').glob('*.md'):
        try:
            route=meta_body(item)[0].get('permalink')
            if route:all_routes[Path(route).name]=item
        except (ValueError, AttributeError):continue
    for a in soup.find_all('a',href=True):
        href=a['href']
        if href.startswith('#'):
            a['href']='#'+identifier+'-'+href[1:];continue
        if urlsplit(href).scheme:continue
        parts=urlsplit(href);filename=Path(parts.path).name
        target=core_by_name.get(filename) or core_by_route.get(filename)
        if target:
            a['href']='#'+target+('-'+parts.fragment if parts.fragment else '');continue
        if filename=='README.md' and 'security-lab' in parts.path:
            a['href']='#lab';continue
        if filename=='technology-choices.md':a['href']='#technology';continue
        if filename in ('runtime-observations.md','runtime-lab-results.md'):a['href']='#runtime-results';continue
        if filename=='threat-register.json':a['href']='#threat-records';continue
        candidate=all_routes.get(filename,(path.parent/unquote(parts.path)).resolve())
        # Generated SVGs and source assets must exist locally; source-link check follows separately.
        if candidate.is_relative_to(ROOT):
            relative=candidate.relative_to(ROOT).as_posix()
            a['href']='https://github.com/Gh0stlyKn1ght/design/blob/gh-pages/'+relative+('#'+parts.fragment if parts.fragment else '')
    return f'<section class="chapter" id="{identifier}">{soup}</section>'


def render(stem,title,content):
    html_text='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="author" content="'+AUTHOR+'"><meta name="description" content="October 2026 revised ROS 2 security handbook"><title>'+html.escape(title)+'</title><style>'+CSS+'</style></head><body>'+content+'</body></html>'
    parsed=BeautifulSoup(html_text,'html.parser')
    ids=[e['id'] for e in parsed.find_all(id=True)]
    assert len(ids)==len(set(ids)), 'Duplicate HTML IDs'
    for link in parsed.find_all('a',href=True):
        if link['href'].startswith('#'):assert link['href'][1:] in ids,link['href']
    (OUT/(stem+'.html')).write_text(html_text)
    doc=HTML(string=html_text,base_url=str(ROOT)).render()
    overflows=[]
    for number,page in enumerate(doc.pages,1):
        box=page._page_box;left=box.margin_left;right=left+box.width;top=box.margin_top;bottom=top+box.height
        root=next(child for child in box.children if child.element_tag=='html')
        for child in root.descendants():
            if child.__class__.__name__ not in ('TextBox','InlineReplacedBox','BlockReplacedBox'):continue
            x,y,w,h=child.position_x,child.position_y,child.width,child.height
            if x<left-2 or x+w>right+2 or y<top-2 or y+h>bottom+2:
                overflows.append({'page':number,'text':getattr(child,'text','')[:100],'bounds':[round(v,2) for v in (x,y,w,h)]})
    MANIFEST['documents'][stem]={'pages':len(doc.pages),'overflow_flags':overflows}
    doc.write_pdf(OUT/(stem+'.pdf'),pdf_tags=True)
    print(stem,len(doc.pages),'pages',len(overflows),'overflow flags',flush=True)


def threat_records():
    data=json.loads((ROOT/'examples/security-lab/threat-register.json').read_text())
    records=data['records']
    assert {r['id'] for r in records}=={f'TM-{i:03}' for i in range(1,9)}
    content='<section class="chapter" id="threat-records"><h1>Full teaching-system threat records</h1><p>Owner roles are responsibilities to assign. Offline-checked status covers named local assertions only. The runtime observations record six passed ROS cases and one inconclusive separate-authority case. Other controls remain proposed.</p>'
    for record in records:
        assert record['evidence_status'] in ('proposed','offline-checked','runtime-observed')
        content+=f'<section class="threat-record" id="record-{record["id"]}"><h2>{record["id"]} · {html.escape(record["title"])}</h2><dl>'
        for key,value in record.items():
            if key in ('id','title'):continue
            content+='<dt>'+html.escape(key.replace('_',' ').capitalize())+'</dt><dd>'+html.escape(value)+'</dd>'
        content+='</dl></section>'
    content+='</section>'
    return content


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run(['dot','-Tsvg',str(ROOT/'img/security/trust-boundaries.dot'),'-o',str(ROOT/'img/security/trust-boundaries.svg')],check=True)
    subprocess.run(['dot','-Tpdf',str(ROOT/'img/security/trust-boundaries.dot'),'-o',str(ROOT/'img/security/trust-boundaries.pdf')],check=True)
    subprocess.run(['python3',str(ROOT/'examples/security-lab/check_policy.py')],check=True)
    title='ROS 2 Security and Threat Modeling'
    cover=f'<section class="cover"><p class="kicker">OCTOBER 2026 EDITION</p><h1>{title}</h1><h2>Trust boundaries, access control, and a practical SROS 2 lab</h2><p class="credit">{AUTHOR}</p><p>Security review, technical revision, and additional material<br><a href="https://github.com/Gh0stlyKn1ght">@Gh0stlyKn1ght</a></p><p class="small">Adapted from the ROS 2 design documents.<br>Original authors are credited in each chapter.</p></section>'
    entries=[('scope','Scope and evidence')]+[('chapter-'+p.stem[:3],meta_body(p)[0]['title']) for p in CORE]+[('threat-records','Full teaching-system threat records'),('research-cases','Published middleware case studies'),('technology','Libraries and technology choices'),('lab','Bounded SROS 2 teaching lab'),('runtime-results','Recorded lab results'),('policy-source','Complete example policy'),('notices','Credits and license notices')]
    contents='<h1>Contents</h1><ol>'+''.join('<li><a href="#'+key+'">'+html.escape(label)+'</a></li>' for key,label in entries)+'</ol>'
    scope='<section class="chapter" id="scope"><h1>Scope and evidence</h1><p>This handbook explains DDS security, least-privilege policies, enclave boundaries, and threat modeling through a non-actuating talker/listener system. The practical baseline is ROS 2 Jazzy on Ubuntu 24.04 with Fast DDS. The four chapters lead into a structured threat register, published middleware case studies, technology choices, a reproducible lab, and its recorded results.</p><p>The recorded software run passed six cases; the independently generated authority case remains inconclusive. These observations apply to the named versions and settings. They do not establish host isolation, actuator safety, or the security of a physical robot. Use the results chapter to distinguish observed behavior from controls that still require testing.</p></section>'
    chapters=''.join(source_section(p,'chapter-'+p.stem[:3],True) for p in CORE)
    records=threat_records()
    research=source_section(OUT/'research-case-studies.md','research-cases')
    research_audit=source_section(OUT/'research-source-audit.md','research-source-audit')
    technology=source_section(OUT/'technology-choices.md','technology')
    lab=source_section(ROOT/'examples/security-lab/README.md','lab')
    runtime=source_section(OUT/'runtime-lab-results.md','runtime-results')
    policy='<section class="chapter" id="policy-source"><h1>Complete example policy</h1><p>Source: examples/security-lab/policy.xml. Offline-checked scope for the selected example; not signed runtime credentials.</p><pre>'+html.escape((ROOT/'examples/security-lab/policy.xml').read_text())+'</pre></section>'
    changes=source_section(OUT/'changes.md','change-record')
    notices='<section class="chapter" id="notices"><h1>Credits and license notices</h1><p>2026 revision and new material: '+AUTHOR+'. Original design-document attribution: Open Source Robotics Foundation, Inc. Original article authors remain identified in the revised chapters.</p><p>The original site specifies Creative Commons Attribution 3.0 for design documents except where otherwise noted. This edition preserves that attribution context and identifies changes. <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>.</p><p>The published middleware case-study chapter is adapted from Juan Carlos Nevarez’s ROS2X Research writeups under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>; its source revision and adaptation notice appear in that chapter. Original source snapshots are stored in articles/security_history. The historical reader remains in reports/security-review. The project also supplies an Apache 2.0 code license; its full text follows. New example scripts and policy are under the repository code license.</p>'+md((ROOT/'examples/security-lab/vendor/NOTICE.md').read_text())+'<h2>Repository code license</h2><pre class="license">'+html.escape((ROOT/'LICENSE').read_text())+'</pre></section>'
    remaining=source_section(OUT/'remaining-work.md','remaining-work')
    render('security-handbook',title+' — Revised October 2026',cover+contents+scope+chapters+records+research+technology+lab+runtime+policy+notices)
    render('update-summary','ROS 2 Security — Revision, Validation and Technology Choices',changes+runtime+technology+research_audit+remaining)
    svg=base64.b64encode((ROOT/'img/security/trust-boundaries.svg').read_bytes()).decode()
    render('trust-boundaries-landscape','ROS 2 Security — Teaching System Diagram','<section class="diagram-sheet"><h1>Teaching system: trust boundaries</h1><img alt="Provisioner, talker, listener, untrusted transport and peer" src="data:image/svg+xml;base64,'+svg+'"><p>'+AUTHOR+' · October 2026 · Intended boundaries; see recorded runtime results and limits.</p></section>')
    source_files=CORE+[ROOT/'articles/160_ros_command_line_arguments.md',ROOT/'articles/170_node_to_participant_mapping.md',ROOT/'articles/020_ros_with_dds.md',ROOT/'articles/actions.md',ROOT/'articles/unique_network_flows.md',ROOT/'README.md',OUT/'changes.md',OUT/'technology-choices.md',OUT/'runtime-observations.md',OUT/'runtime-lab-results.md',OUT/'remaining-work.md',OUT/'research-case-studies.md',OUT/'research-source-audit.md',OUT/'research-source-review.json']
    source_files+=sorted(p for p in (ROOT/'examples/security-lab').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    source_files+=sorted((ROOT/'img/security').glob('*'))
    source_files+=sorted(p for p in (OUT/'runtime-evidence').glob('*') if p.is_file())
    if (OUT/'source-review.json').is_file(): source_files.append(OUT/'source-review.json')
    source_files+=sorted(p for p in (ROOT/'tools/security-handbook').glob('*') if p.is_file())
    source_files.append(ROOT/'tools/security-review/build.py')
    source_files+=sorted(p for p in (ROOT/'tools/site').glob('*') if p.is_file())
    source_files+=[ROOT/'Gemfile',ROOT/'Gemfile.lock',ROOT/'_config.yml',ROOT/'_includes/header.html',ROOT/'_includes/footer.html',ROOT/'_includes/sidebar.html',ROOT/'_layouts/default.html',ROOT/'css/ros2-design.css',ROOT/'index.md']
    MANIFEST['sources']=[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in source_files]
    MANIFEST['versions']={name:importlib.metadata.version(name) for name in ['weasyprint','Markdown','beautifulsoup4','PyYAML','lxml']}
    MANIFEST['graphviz']=subprocess.run(['dot','-V'],capture_output=True,text=True,check=True).stderr.strip()
    runtime_data=json.loads((OUT/'runtime-evidence/results.json').read_text())
    MANIFEST['runtime_tested']=runtime_data['status']=='runtime-observed'
    MANIFEST['runtime_cases_summary']={status:sum(c['outcome']==status for c in runtime_data['cases']) for status in ['pass','fail','inconclusive']}
    MANIFEST['runtime_suite_all_passed']=all(c['outcome']=='pass' for c in runtime_data['cases'])
    MANIFEST['site_build_verified']=json.loads((OUT/'site-build-check.json').read_text())['status']=='passed'
    MANIFEST['validation']={'policy':'offline-checked','boundary_tests':'run separately with unittest','runtime_cases':'recorded observations; not repeated by PDF build'}
    (OUT/'build-manifest.json').write_text(json.dumps(MANIFEST,indent=2)+'\n')
    assert not any(d['overflow_flags'] for d in MANIFEST['documents'].values()),'Print overflow; inspect manifest'

if __name__=='__main__':main()
