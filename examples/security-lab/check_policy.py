#!/usr/bin/env python3
"""Check the trusted teaching policy using pinned schemas/XSLT. No ROS or signing keys."""
from pathlib import Path
import argparse
import hashlib
import json
from lxml import etree

HERE = Path(__file__).resolve().parent
VENDOR = HERE/'vendor'
DOMAIN = '42'
PREFIX = '/security_lab/'

class LocalSchemaResolver(etree.Resolver):
    def resolve(self, url, public_id, context):
        if url in ('http://www.w3.org/2001/03/xml.xsd', 'https://www.w3.org/2001/03/xml.xsd'):
            return self.resolve_filename(str(VENDOR/'xml.xsd'), context)
        candidate = Path(url).resolve()
        if candidate.is_relative_to(VENDOR.resolve()) and candidate.is_file():
            return self.resolve_filename(str(candidate), context)
        raise ValueError('Unapproved XML resource resolution')

def parser():
    p = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
    p.resolvers.add(LocalSchemaResolver())
    return p

def parse_bytes(data):
    if b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise ValueError('DTD/entity declarations are outside this example policy format')
    tree = etree.ElementTree(etree.fromstring(data, parser()))
    if tree.docinfo.doctype:
        raise ValueError('DTD declarations are outside this example policy format')
    if tree.xpath('//*[local-name()="include" and (namespace-uri()="http://www.w3.org/2001/XInclude" or namespace-uri()="http://www.w3.org/2003/XInclude")]'):
        raise ValueError('XInclude is outside this example policy format')
    return tree

def verify_vendor():
    manifest = json.loads((VENDOR/'sources.json').read_text())
    for record in manifest['files']:
        path = (VENDOR/record['file']).resolve()
        if not path.is_relative_to(VENDOR.resolve()):
            raise ValueError('Vendor path escapes bundle')
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Pinned vendor file changed: '+record['file'])
    return manifest

def schema(filename):
    return etree.XMLSchema(etree.parse(str(VENDOR/'sros2'/filename), parser()))

def policy_to_permissions(policy):
    schema('policy.xsd').assertValid(policy)
    transformer = etree.XSLT(
        etree.parse(str(VENDOR/'sros2/permissions.xsl'), parser()),
        access_control=etree.XSLTAccessControl.DENY_ALL,
    )
    # Preserve the /policy/enclaves path expected by the pinned stylesheet.
    document = policy
    result = transformer(
        document,
        not_valid_before=etree.XSLT.strparam('2026-10-20T00:00:00'),
        not_valid_after=etree.XSLT.strparam('2027-10-20T00:00:00'),
        allow_ros_discovery_topic=etree.XSLT.strparam('1'),
    )
    # The pinned ROS helper substitutes ROS_DOMAIN_ID after its transform.
    for element in result.findall('permissions/grant/*/domains/id'):
        element.text = DOMAIN
    schema('permissions.xsd').assertValid(result)
    return result

def check_grants(result):
    grants = result.findall('permissions/grant')
    assert {g.get('name') for g in grants} == {PREFIX+'talker', PREFIX+'listener'}
    services = ['describe_parameters','get_parameter_types','get_parameters','list_parameters','set_parameters','set_parameters_atomically','get_type_description']
    checked = []
    for grant in grants:
        name = grant.get('name'); role = name.rsplit('/',1)[-1]
        assert grant.findtext('subject_name') == 'CN='+name
        assert grant.findtext('default') == 'DENY'
        assert set(grant.xpath('./allow_rule/domains/id/text()')) == {DOMAIN}
        assert not grant.findall('deny_rule')
        publish = set(grant.xpath('./allow_rule/publish/topics/topic/text()'))
        subscribe = set(grant.xpath('./allow_rule/subscribe/topics/topic/text()'))
        shared_pub = {'rt/rosout','rt/parameter_events','ros_discovery_info'}
        shared_sub = {'rt/parameter_events','rt/clock','ros_discovery_info'}
        expected_pub = shared_pub | {f'rr/{role}/{s}Reply' for s in services}
        expected_sub = shared_sub | {f'rq/{role}/{s}Request' for s in services}
        if role == 'talker': expected_pub.add('rt/chatter')
        else: expected_sub.add('rt/chatter')
        assert publish == expected_pub, (role,'publish',publish ^ expected_pub)
        assert subscribe == expected_sub, (role,'subscribe',subscribe ^ expected_sub)
        assert all('*' not in name and '?' not in name for name in publish|subscribe)
        checked.append({'enclave':name,'publish':sorted(publish),'subscribe':sorted(subscribe),'default':'DENY','domain':DOMAIN})
    return checked

def check(data):
    policy = parse_bytes(data)
    result = policy_to_permissions(policy)
    return result, check_grants(result)

def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--output', type=Path, default=HERE/'generated')
    options = args.parse_args()
    vendor = verify_vendor()
    result, grants = check((HERE/'policy.xml').read_bytes())
    options.output.mkdir(parents=True,exist_ok=True)
    (options.output/'permissions.xml').write_bytes(etree.tostring(result,pretty_print=True,xml_declaration=True,encoding='UTF-8'))
    report = {'status':'offline-checked','runtime_tested':False,'source_policy_sha256':hashlib.sha256((HERE/'policy.xml').read_bytes()).hexdigest(),'sros2_commit':vendor['sros2_commit'],'validity_note':'Illustrative offline interval; runtime SROS 2 derives permission validity from generated certificates.','grants':grants}
    (options.output/'policy-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: policy schema, DDS schema, two exact grant sets, default denial, domain 42, no wildcards. No runtime test performed.')

if __name__ == '__main__': main()
