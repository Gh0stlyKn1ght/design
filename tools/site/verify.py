#!/usr/bin/env python3
"""Check the built security pages, local links/assets, archives and public auth surface."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote
import hashlib
import json
import re
import yaml
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
SITE=ROOT/'_site'
config=yaml.safe_load((ROOT/'_config.yml').read_text())
base=config.get('baseurl','')
routes=['/','/articles/ros2_dds_security.html','/articles/ros2_access_control_policies.html','/articles/ros2_security_enclaves.html','/articles/ros2_threat_model.html']
checked=0
for route in routes:
    page=SITE/('index.html' if route=='/' else route.lstrip('/'))
    text=page.read_text();parsed=BeautifulSoup(text,'html.parser')
    assert parsed.find('main',id='main-content'),route
    assert not parsed.find_all('script'),route
    assert 'Juan Carlos Nevarez' in parsed.get_text(),route
    for term in ['github_oauth_token','auth.design.ros2.org','google-analytics.com']:
        assert term not in text,(route,term)
    for element in parsed.select('[href], [src]'):
        raw=element.get('href',element.get('src',''))
        if not raw or raw.startswith(('mailto:','data:','#')):continue
        target=urlsplit(urljoin('https://local.test'+base+route,raw))
        if target.netloc!='local.test':continue
        assert target.path.startswith(base+'/'),(route,raw,'base path missing')
        local=SITE/unquote(target.path[len(base):]).lstrip('/')
        if target.path.endswith('/'):local=local/'index.html'
        assert local.is_file(),(route,raw,str(local))
        checked+=1
for path in (ROOT/'articles/security_history').glob('*.md.txt'):
    assert (SITE/'articles/security_history'/path.name).read_bytes()==path.read_bytes()
assert not (SITE/'CNAME').exists()
assert not (SITE/'login.html').exists()
assert not (SITE/'js/login.js').exists()
result={'status':'passed','focused_pages':len(routes),'local_links_and_assets_checked':checked,'archives_unprocessed':True,'public_oauth_flow':False,'custom_domain_claim':False,'baseurl':base,'deployed':False}
(ROOT/'reports/security-handbook/site-build-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
