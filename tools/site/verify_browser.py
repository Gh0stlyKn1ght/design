#!/usr/bin/env python3
"""Browser-check the built security pages; use --url for local or deployed sites."""
from pathlib import Path
import argparse
import json
from playwright.sync_api import sync_playwright
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:4307/design');parser.add_argument('--output',type=Path,required=True);parser.add_argument('--chromium',default='/usr/bin/chromium');options=parser.parse_args()
results=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=options.chromium,headless=True,args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1000});failed=[];errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('response',lambda response:failed.append({'url':response.url,'status':response.status}) if response.status>=400 else None)
    for route in ['/', '/articles/ros2_dds_security.html','/articles/ros2_access_control_policies.html','/articles/ros2_security_enclaves.html','/articles/ros2_threat_model.html']:
        response=page.goto(options.url+route,wait_until='networkidle');assert response.status==200
        assert page.locator('script').count()==0
        if route!='/':assert 'Juan Carlos Nevarez' in page.locator('main').inner_text()
        results.append({'route':route,'status':response.status,'h1':page.locator('h1').first.inner_text()})
    page.set_viewport_size({'width':390,'height':844});page.goto(options.url+'/articles/ros2_dds_security.html',wait_until='networkidle')
    overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth');assert not overflow
    for target in ['/reports/security-handbook/security-handbook.pdf','/reports/security-handbook/update-summary.pdf','/img/security/trust-boundaries.svg','/articles/security_history/183_ros2_threat_model.md.txt']:
        response=page.request.get(options.url+target);assert response.status==200
    assert not errors and not failed,(errors,failed)
    options.output.write_text(json.dumps({'url':options.url,'pages':results,'asset_failures':failed,'javascript_errors':errors,'mobile_horizontal_overflow':overflow},indent=2)+'\n')
    browser.close()
print('Browser checks passed: five pages, downloads, mobile layout, no script errors.')
