#!/usr/bin/env python3
"""Build the documentation review and print extraction; never edits upstream articles."""
from pathlib import Path
import base64
import copy
import hashlib
import html
import importlib.metadata
import json
import mimetypes
import re
import subprocess
import warnings
from urllib.parse import urljoin

import markdown
import yaml
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from PIL import Image
from weasyprint import HTML

warnings.filterwarnings('ignore', category=MarkupResemblesLocatorWarning)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reports/security-review'
REV = '93a415bf928751d37fce6f83215c521658e20c93'
SOURCE = f'https://github.com/ros2/design/blob/{REV}/'
AUTHOR = 'Juan Carlos Nevarez · Gh0stlyKn1ght'
PROFILE = 'https://github.com/Gh0stlyKn1ght'
DATE = '2026-10-20'
PATTERN = re.compile(r'secur|threat|vulnerab|authenti|authoriz|encrypt|attack|confidential|integrity|certificate|permission', re.I)
CORE = sorted((ROOT / 'articles').glob('18*.md'))
EXTENSIONS = ['extra', 'md_in_html', 'toc', 'sane_lists']
STATS = {'matrix_tables': [], 'figures': [], 'layout_overflows': {}}

CSS = '''
@page { size: Letter; margin: .65in .65in .7in;
 @top-left { content: "ROS 2 · Security review / historical reference"; font: 8pt "DejaVu Sans"; color: #444; }
 @bottom-left { content: "Juan Carlos Nevarez · Gh0stlyKn1ght"; font: 8pt "DejaVu Sans"; }
 @bottom-right { content: counter(page) " / " counter(pages); font: 8pt "DejaVu Sans"; }
}
@page atlas { size: Letter landscape; margin: .5in; }
* { box-sizing: border-box; }
html { background: white; color: black; }
body { font-family: "DejaVu Sans", sans-serif; font-size: 10pt; line-height: 1.42; margin: 0; }
h1 { font-size: 23pt; line-height: 1.2; margin: 14pt 0; }
h2 { font-size: 16pt; margin: 18pt 0 8pt; }
h3 { font-size: 12pt; margin: 14pt 0 6pt; }
h4,h5,h6 { font-size: 10.5pt; margin: 12pt 0 5pt; }
h1,h2,h3,h4,h5,h6 { break-after: avoid; }
p,li { orphans: 3; widows: 3; }
p { margin: 6pt 0; }
a { color: black; text-decoration: underline; overflow-wrap: anywhere; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: .86em; overflow-wrap: anywhere; }
pre { font-family: "DejaVu Sans Mono", monospace; font-size: 8pt; line-height: 1.35; white-space: pre-wrap; overflow-wrap: anywhere; border-left: 1pt solid #888; padding: 6pt; }
blockquote { border-left: 2pt solid #888; margin: 10pt 0; padding-left: 12pt; }
table { border-collapse: collapse; width: 100%; table-layout: fixed; font-size: 8.8pt; margin: 10pt 0; }
th,td { border: .5pt solid #666; padding: 5pt; vertical-align: top; overflow-wrap: anywhere; }
th { text-align: left; font-weight: bold; background: white; }
thead { display: table-header-group; }
img { max-width: 100%; height: auto; }
figure { margin: 12pt 0; break-inside: avoid; }
figure img { display: block; margin: auto; max-height: 7.4in; object-fit: contain; }
figcaption { font-size: 8.5pt; margin: 5pt 0; }
ul,ol { padding-left: 19pt; }
.cover { break-after: page; padding-top: .65in; }
.cover .kicker { font-size: 12pt; letter-spacing: .05em; }
.cover .credit { margin-top: 24pt; font-size: 13pt; }
.notice { border: 1pt solid black; padding: 10pt; margin: 12pt 0; }
.chapter { break-before: page; }
.record { margin: 14pt 0; border-top: 1pt solid #555; padding-top: 5pt; }
.record h4 { font-size: 11pt; }
.field { margin: 7pt 0; }
.field-label { display: block; font-weight: bold; break-after: avoid; }
.field p:first-child { margin-top: 2pt; }
.small { font-size: 8.5pt; }
.atlas-cover,.atlas-page { page: atlas; break-after: page; }
.atlas-page img { display: block; max-width: 10in; max-height: 5.65in; margin: auto; object-fit: contain; }
.atlas-page h2 { margin-top: 0; }
.atlas-page p { font-size: 8.5pt; }
.license { font: 8pt "DejaVu Sans Mono"; white-space: pre-wrap; overflow-wrap: anywhere; }
@media screen { body { max-width: 940px; padding: 32px; margin: auto; } .atlas-page { border-top: 1px solid; margin-top: 30px; } }
'''

def md(text):
    return markdown.markdown(text, extensions=EXTENSIONS, extension_configs={'toc': {'toc_depth': '1-3'}})

def snapshot_bytes(path):
    """Read the reviewed baseline, regardless of later working-tree revisions."""
    relative = path.relative_to(ROOT).as_posix()
    return subprocess.check_output(['git', 'show', f'{REV}:{relative}'], cwd=ROOT)

def snapshot_text(path):
    return snapshot_bytes(path).decode('utf-8')


def split_source(path):
    text = snapshot_text(path)
    _, front, body = text.split('---', 2)
    return yaml.safe_load(front), body

def clean_liquid(path, meta, body):
    def include(m):
        target = path.parent / m.group(1)
        assert target.is_file(), target
        return snapshot_text(target)
    body = re.sub(r'{%\s*include_relative\s+(\S+)\s*%}', include, body)
    for key, value in meta.items():
        if isinstance(value, str):
            body = re.sub(r'{{\s*page\.' + key + r'\s*}}', lambda m: value, body)
    body = re.sub(r'Last Modified:.*', 'Last Modified: ' + str(meta.get('last_modified', meta['date_written'])), body)
    body = re.sub(r'\{:[^}\n]*\}|\{::[^}\n]*\}', '', body)
    body = re.sub(r'<style>.*?</style>', '', body, flags=re.S)
    if path.name.startswith('183'):
        body = re.sub(r'## Table of Contents.*?(?=## Document Scope)', '', body, flags=re.S)
    assert not re.search(r'{[{%]', body), f'Unresolved template in {path}'
    return body

def serialized_cell(cell):
    return cell.decode_contents().strip()

def expand_rows(table, header_count, width):
    carry = {}
    for row in table.find_all('tr', recursive=False):
        cells = row.find_all(['th', 'td'], recursive=False)
        if row.get('data-header'):
            continue
        if len(cells) == 1 and cells[0].name == 'th':
            yield ('section', cells[0].get_text(' ', strip=True))
            continue
        if not cells or not row.find('td', recursive=False):
            continue
        values = [None] * width
        new_carry = {}
        for col, (remaining, value) in carry.items():
            values[col] = value
            if remaining > 1:
                new_carry[col] = (remaining - 1, value)
        col = 0
        for cell in cells:
            while col < width and values[col] is not None:
                col += 1
            span = int(cell.get('colspan', 1))
            value = serialized_cell(cell)
            for offset in range(span):
                if col + offset >= len(values):
                    values.extend([None] * (col + offset + 1 - len(values)))
                values[col + offset] = value
                remaining = int(cell.get('rowspan', 1)) - 1
                if remaining:
                    new_carry[col + offset] = (remaining, value)
            col += span
        missing = [i + 1 for i, v in enumerate(values) if v is None]
        if missing:
            STATS.setdefault('source_table_omissions', []).append({'columns': width, 'missing_positions': missing, 'threat': BeautifulSoup(values[0] or '', 'html.parser').get_text(' ', strip=True)})
            values = [v if v is not None else '<p>(No cell supplied in source row; position follows original column order.)</p>' for v in values]
        if len(values) > width:
            STATS.setdefault('source_table_extra_cells', []).append({'columns':width, 'actual_columns':len(values), 'threat':BeautifulSoup(values[0], 'html.parser').get_text(' ', strip=True)})
        carry = new_carry
        yield ('ambiguous' if missing or len(values) != width else 'data', values)
    assert not carry, 'Unfinished rowspans'

def matrices(soup):
    for table in list(soup.find_all('table')):
        first = table.find('tr').get_text(' ', strip=True)
        if 'Threat Category (STRIDE)' in first:
            kind = 'generic'
        elif 'TurtleBot Assets' in first:
            kind = 'turtlebot'
        elif 'MARA Assets' in first:
            kind = 'mara'
        else:
            continue
        if kind == 'generic':
            labels = ['Threat'] + ['STRIDE · ' + s for s in ['Spoofing','Tampering','Repudiation','Information disclosure','Denial of service','Elevation of privilege']] + ['DREAD · ' + s for s in ['Damage','Reproducibility','Exploitability','Affected users','Discoverability','Total']] + ['Asset · ' + s for s in ['Robot compute resources','Physical safety','Robot availability','Robot integrity','Data integrity','Data availability','Data privacy']] + ['Entry point · ' + s for s in ['Embedded hardware','Robot communication channels','Robot administration tools','Remote application interface','Deployment infrastructure']] + ['Mitigation strategies','Similar attacks in the literature']
            title, prefix, groups = 'Generic threats', 'GEN', [(1,7,'STRIDE'),(7,13,'Historical DREAD scores'),(13,20,'Impacted assets'),(20,25,'Impacted entry points')]
        else:
            name = 'TurtleBot' if kind == 'turtlebot' else 'MARA'
            entry = ['DDS topic','OSRF build farm','SSH'] if kind == 'turtlebot' else ['ROS 2 API (DDS)','Manufacturer CI/CD','End-user CI/CD','H-ROS API','OTA','Physical']
            labels = ['Threat','Asset · Human assets','Asset · Robot application'] + ['Entry point · ' + s for s in entry] + ['SROS Enabled? (historical legend)','Attack','Mitigation','Mitigation result','Additional notes / open questions']
            title, prefix = name + ' threats', 'TB3' if kind == 'turtlebot' else 'MARA'
            groups = [(1,3,'Impacted assets'),(3,3+len(entry),'Impacted entry points')]
        rows = table.find_all('tr', recursive=False)
        for r in rows[:2]:
            r['data-header'] = 'true'
        output = BeautifulSoup('<div class="threat-records"></div>', 'html.parser').div
        note = soup.new_tag('p', attrs={'class':'notice small'})
        note.string = 'Historical matrix reflowed as vertical records. ✓, ✘ and ▲ retain their source meanings. SROS Enabled? means the attack can occur with SROS enabled, not that SROS prevents it. Scores and mitigation claims are historical and unverified in this review.'
        output.append(note)
        count = 0
        for kind, values in expand_rows(table, 2, len(labels)):
            if kind == 'section':
                h = soup.new_tag('h3'); h.string = values; output.append(h); continue
            count += 1
            record = soup.new_tag('section', attrs={'class':'record','id':f'{prefix}-{count:03}'})
            h = soup.new_tag('h4'); h.string = f'{prefix}-{count:03} · ' + BeautifulSoup(values[0], 'html.parser').get_text(' ',strip=True); record.append(h)
            if kind == 'ambiguous':
                notice = soup.new_tag('p', attrs={'class':'notice small'})
                notice.string = 'Malformed original row: the supplied cell count does not match the header. All cells are retained below in source order; column alignment is unresolved. Do not infer a corrected meaning from these positions.'
                record.append(notice)
                for i, value in enumerate(values):
                    field = soup.new_tag('div', attrs={'class':'field'})
                    label = soup.new_tag('span', attrs={'class':'field-label'}); label.string = f'Source column {i+1}'; field.append(label)
                    field.extend(list(BeautifulSoup(value, 'html.parser').contents));record.append(field)
                output.append(record)
                continue
            grouped = set()
            for start,end,label in groups:
                field = soup.new_tag('div', attrs={'class':'field'})
                heading = soup.new_tag('span', attrs={'class':'field-label'});heading.string=label;field.append(heading)
                text = '; '.join(labels[i].split(' · ')[-1] + ': ' + BeautifulSoup(values[i], 'html.parser').get_text(' ',strip=True) for i in range(start,end))
                p=soup.new_tag('p');p.string=text;field.append(p);record.append(field);grouped.update(range(start,end))
            for i in range(1,len(labels)):
                if i in grouped: continue
                field=soup.new_tag('div',attrs={'class':'field'})
                heading=soup.new_tag('span',attrs={'class':'field-label'});heading.string=labels[i];field.append(heading)
                fragment=BeautifulSoup(values[i] or '<p>(Empty in source.)</p>','html.parser')
                field.extend(list(fragment.contents));record.append(field)
            output.append(record)
        assert count > 0, f'No records extracted for {title}'
        STATS['matrix_tables'].append({'name':title,'columns':len(labels),'records':count})
        table.replace_with(output)

def image_data(path):
    return 'data:' + mimetypes.guess_type(path)[0] + ';base64,' + base64.b64encode(path.read_bytes()).decode()

def article(path):
    meta, body = split_source(path)
    soup = BeautifulSoup(md(clean_liquid(path,meta,body)), 'html.parser')
    for el in soup.find_all(True):
        for attr in ('style','width','height','markdown','class'):
            el.attrs.pop(attr,None)
    if path.name.startswith('183'):
        source_cells = [re.sub(r'\s+', ' ', c.get_text(' ', strip=True)) for c in soup.find_all(['td'])]
        matrices(soup)
        assert len(STATS['matrix_tables']) == 3
        normalized_text = re.sub(r'\s+', ' ', soup.get_text(' ', strip=True))
        assert all(not cell or cell in normalized_text for cell in source_cells), 'Table data lost in reflow'
        STATS['preserved_table_cells'] = len(source_cells)
    # Resolve all links against the original article location. Images are embedded.
    for a in soup.find_all('a',href=True):
        href=a['href']
        if href.startswith('/'):
            a['href']='https://design.ros2.org'+href
        elif not re.match(r'[a-z]+:|#',href):
            a['href']=urljoin(SOURCE+str(path.relative_to(ROOT)),href)
    for img in list(soup.find_all('img',src=True)):
        local=(path.parent/img['src']).resolve()
        assert local.is_relative_to(ROOT) and local.is_file(), local
        number=len(STATS['figures'])+1
        width,height=Image.open(local).size
        STATS['figures'].append({'number':number,'path':str(local.relative_to(ROOT)),'alt':img.get('alt',''),'width':width,'height':height})
        img['src']=image_data(local)
        figure=soup.new_tag('figure'); img.replace_with(figure);figure.append(img)
        caption=soup.new_tag('figcaption');caption.string=f'Figure {number} · {local.name}. Original figure; a larger view appears in the companion atlas.';figure.append(caption)
    authors=md(meta['author'])
    provenance=f'<div class="notice small"><strong>Historical source: {html.escape(meta["title"])}</strong>{authors}<p>Written {meta["date_written"]}; declared modified {meta.get("last_modified")}. <a href="{SOURCE+str(path.relative_to(ROOT))}">Pinned original source</a>. Original OSRF design-document attribution and CC BY 3.0 notice retained. Presentation adapted for this reader; historical instructions and findings have not been modernized.</p></div>'
    # Prefix local IDs so reference links do not collide across articles.
    prefix=path.stem[:3]+'-'
    for el in soup.find_all(id=True): el['id']=prefix+el['id']
    for a in soup.find_all('a',href=True):
        if a['href'].startswith('#'): a['href']='#'+prefix+a['href'][1:]
    return f'<article class="chapter" id="article-{path.stem[:3]}">{provenance}{soup}</article>'

def inventory():
    tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',REV],cwd=ROOT,text=True).splitlines()
    files=[]
    for name in tracked:
        path=ROOT/name
        if name.startswith(('reports/', 'tools/security-review/')): continue
        if path.suffix not in ('.md','.html','.js','.yml','.xml','.xsd'): continue
        if name.startswith('js/bootstrap'): continue
        lines=snapshot_text(path).splitlines()
        headings=[]; hits=[]; stack=[]; in_code=False
        for number,line in enumerate(lines,1):
            if line.startswith('```'):in_code=not in_code
            m=re.match(r'^(#{1,6})\s+(.+)',line) if not in_code else None
            if m:
                level=len(m[1]); title=m[2]
                while stack and stack[-1][0]>=level:stack.pop()
                stack.append((level,title));headings.append({'level':level,'title':title,'line':number})
            if PATTERN.search(line): hits.append({'line':number,'heading':' / '.join(t for _,t in stack),'text':line})
        if not hits and path not in CORE:continue
        meta={}
        if lines and lines[0]=='---':
            try:meta=yaml.safe_load(snapshot_text(path).split('---',2)[1]) or {}
            except yaml.YAMLError:pass
        for i,h in enumerate(headings):
            h['end_line']=next((x['line']-1 for x in headings[i+1:] if x['level']<=h['level']),len(lines))
        files.append({'path':name,'sha256':hashlib.sha256(snapshot_bytes(path)).hexdigest(),'lines':len(lines),'title':meta.get('title',name),'date_written':str(meta.get('date_written','')),'last_modified':str(meta.get('last_modified','')),'core_security':path in CORE,'headings':headings,'matches':hits})
    data={'review_date':DATE,'source_revision':REV,'scope':'Tracked first-party Markdown, HTML, JavaScript, YAML, XML and XSD; third-party Bootstrap excluded. Keyword inventory plus all headings in four Security-category articles. Generated review files excluded.','upstream_core_comparison':'All four core files byte-matched live ros2/design gh-pages on 2026-10-20.','files':files}
    (OUT/'inventory.json').write_text(json.dumps(data,indent=2)+'\n')
    text=['# Security section inventory','',f'Review date: {DATE} · Source revision: `{REV}`','',data['scope'],'','## Dedicated security articles','']
    for f in files:
        if not f['core_security']:continue
        text += [f'### {f["title"]}', '', f'Source: [{f["path"]}]({SOURCE+f["path"]}) · {f["lines"]} lines · Declared modified: {f["last_modified"]}', '']
        for h in f['headings']:
            title=h['title'].replace('{{ page.title }}',f['title'])
            text.append(f'- Level {h["level"]} · lines {h["line"]}–{h["end_line"]} · [{title}]({SOURCE+f["path"]}#L{h["line"]})')
        text.append('')
    text += ['## Other explicit security matches','']
    for f in files:
        if f['core_security']:continue
        text += [f'### {f["path"]}','']
        for hit in f['matches']:
            text += [f'- [Line {hit["line"]}]({SOURCE+f["path"]}#L{hit["line"]}) · {hit["heading"] or "No Markdown heading"}: {hit["text"].strip()}']
        text.append('')
    (OUT/'inventory.md').write_text('\n'.join(text)+'\n')
    return data

def document(title,body):
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="author" content="'+html.escape(AUTHOR)+'"><meta name="description" content="ROS 2 security documentation review and historical extraction"><title>'+html.escape(title)+'</title><style>'+CSS+'</style></head><body>'+body+'</body></html>'

def render(name,title,body):
    source=document(title,body)
    (OUT/(name+'.html')).write_text(source)
    doc=HTML(string=source,base_url=str(ROOT)).render()
    # Check rendered text, cells, code and images against printable page boundaries.
    overflows=[]
    for i,page in enumerate(doc.pages,1):
        box=page._page_box
        left=box.margin_left;right=box.width+left;top=box.margin_top;bottom=box.height+top
        content_root = next(child for child in box.children if child.element_tag == 'html')
        for b in content_root.descendants():
            if b.__class__.__name__ not in ('TextBox','InlineReplacedBox','BlockReplacedBox'):continue
            x,y,w,h=b.position_x,b.position_y,b.width,b.height
            if x<left-2 or x+w>right+2 or y+h>bottom+2:
                overflows.append({'page':i,'type':b.__class__.__name__,'text':getattr(b,'text','')[:80],'bounds':[round(v,2) for v in (x,y,w,h)]})
    STATS['layout_overflows'][name]=overflows
    doc.write_pdf(OUT/(name+'.pdf'))
    print(name,len(doc.pages),'pages',len(overflows),'overflow flags',flush=True)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    data=inventory()
    report=md((OUT/'report.md').read_text())
    render('security-review-report','ROS 2 Security — Review Report',report)
    cover=f'<section class="cover"><p class="kicker">ROS 2 DESIGN · SECURITY COLLECTION</p><h1>Security and Threat Modeling</h1><h2>Historical reference reader</h2><p class="credit">{AUTHOR}</p><p>Security review, editorial direction, and print adaptation<br><a href="{PROFILE}">github.com/Gh0stlyKn1ght</a></p><p>October 20, 2026</p><div class="notice"><strong>Historical source edition.</strong><p>The four original articles are reproduced with original authors and dates. Technical claims, scores, and findings remain historical. Read the companion review report before using the instructions. The 27-, 11-, and 14-column matrices are converted into vertical records without dropping fields. Diagram previews are retained; larger views appear in the companion figure atlas.</p></div><p>Original document attribution: Open Source Robotics Foundation, Inc. Design documents: CC BY 3.0 except where otherwise noted. Repository LICENSE: Apache 2.0, reproduced in the appendix. No upstream endorsement is implied.</p></section>'
    contents='<h1>Contents</h1><ol>'+''.join(f'<li><a href="#article-{p.stem[:3]}">{html.escape(split_source(p)[0]["title"])}</a></li>' for p in CORE)+'<li><a href="#support">Supporting security passages</a></li><li><a href="#notices">Sources and license notices</a></li></ol><p>PDF bookmarks provide section navigation. The separate inventory lists every section and source line range. All source hyperlinks point to the reviewed revision.</p>'
    chapters=''.join(article(p) for p in CORE)
    selections=[('articles/160_ros_command_line_arguments.md',250,268),('articles/170_node_to_participant_mapping.md',127,132),('articles/170_node_to_participant_mapping.md',147,161),('articles/actions.md',423,428),('articles/020_ros_with_dds.md',84,84),('articles/unique_network_flows.md',58,58)]
    support='<section class="chapter" id="support"><h1>Supporting security passages</h1><p>Historical excerpts from the same source revision; retained for context. Website OAuth code is inventoried in the report rather than included as robot-security instruction.</p>'
    for name,start,end in selections:
        p=ROOT/name;meta,body=split_source(p)
        excerpt='\n'.join(snapshot_text(p).splitlines()[start-1:end])
        support+=f'<h2>{html.escape(meta["title"])}</h2>{md(meta["author"])}<p><a href="{SOURCE+name}#L{start}">Original lines {start}–{end}</a></p>'+md(excerpt)
    support+='</section>'
    notices=f'<section class="chapter" id="notices"><h1>Sources and license notices</h1><p>Source: ros2/design, revision {REV}. Reviewed {DATE}. Article author bylines and original dates appear at the beginning of each article.</p><p>Original attribution: © Open Source Robotics Foundation, Inc. The source site footer states: “Except where otherwise noted, these design documents are licensed under Creative Commons Attribution 3.0.” <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>.</p><p>Adaptation credit: {AUTHOR}. Changes: extraction into a standalone reader; resolved templates/schema include; source links pinned; wide matrices expanded into vertical records with inherited rowspan values; images embedded and numbered; print pagination added. Original factual errors and historical mitigation claims remain present for comparison.</p><h2>Repository LICENSE (verbatim)</h2><pre class="license">{html.escape((ROOT/"LICENSE").read_text())}</pre></section>'
    render('security-reference-reader','ROS 2 Security — Historical Reference Reader',cover+contents+chapters+support+notices)
    atlas=f'<section class="atlas-cover"><h1>ROS 2 Security · Figure Atlas</h1><h2>Historical diagrams</h2><p class="credit">{AUTHOR}<br>Security review and print adaptation<br><a href="{PROFILE}">github.com/Gh0stlyKn1ght</a> · {DATE}</p><div class="notice">Original figures from the Robotic Systems Threat Model, by Thomas Moulard, Juan Hortala, Xabi Perez, Gorka Olalde, Borja Erice, Odei Olalde, and David Mayoral. Original OSRF attribution; CC BY 3.0 except where otherwise noted. Source revision {REV}. Figures are resized for paper; content is unchanged. The source sometimes repeats inaccurate image alt labels, so filenames identify each figure. Enlarging a raster does not improve its underlying detail.</div><p>Figures use the same numbering as the historical reader. <a href="https://creativecommons.org/licenses/by/3.0/">CC BY 3.0</a>.</p></section>'
    for figure in STATS['figures']:
        p=ROOT/figure['path']
        atlas+=f'<section class="atlas-page"><h2>Figure {figure["number"]} · {p.stem.replace("_"," ")}</h2><img alt="{html.escape(figure["alt"])}" src="{image_data(p)}"><p>{figure["path"]} · Original {figure["width"]} × {figure["height"]} px · <a href="{SOURCE+figure["path"]}">Pinned source</a></p></section>'
    render('security-figure-atlas','ROS 2 Security — Landscape Figure Atlas',atlas)
    STATS['source_revision']=REV
    STATS['review_date']=DATE
    STATS['dependencies']={name:importlib.metadata.version(name) for name in ['weasyprint','Markdown','beautifulsoup4','PyYAML','Pillow']}
    STATS['core_source_lines']=sum(f['lines'] for f in data['files'] if f['core_security'])
    (OUT/'build-manifest.json').write_text(json.dumps(STATS,indent=2)+'\n')
    artifacts=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='SHA256SUMS')
    (OUT/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name+'\n' for p in artifacts))
    assert not any(STATS['layout_overflows'].values()), 'Print overflow detected; inspect build-manifest.json before delivery.'

if __name__=='__main__':main()
