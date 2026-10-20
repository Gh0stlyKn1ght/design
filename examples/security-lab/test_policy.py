"""Boundary tests: prevent schema/grant checks from silently accepting expanded access."""
import unittest
from lxml import etree
import check_policy as policy

class PolicyBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.source=(policy.HERE/'policy.xml').read_bytes()

    def test_reviewed_policy_has_exact_grants(self):
        policy.verify_vendor()
        _,grants=policy.check(self.source)
        self.assertEqual(len(grants),2)

    def test_listener_cannot_gain_application_publish(self):
        source=policy.parse_bytes(self.source)
        node=source.xpath('//enclave[@path="/security_lab/listener"]/profiles/profile/topics[@publish="ALLOW"]')[0]
        etree.SubElement(node,'topic').text='/chatter'
        with self.assertRaises(AssertionError): policy.check(etree.tostring(source))

    def test_wildcard_expansion_is_rejected(self):
        source=self.source.replace(b'<topic>/chatter</topic>',b'<topic>/*</topic>')
        with self.assertRaises(AssertionError):policy.check(source)

    def test_invalid_rule_qualifier_is_rejected(self):
        with self.assertRaises(etree.DocumentInvalid):policy.check(self.source.replace(b'publish="ALLOW"',b'publish="YES"',1))

    def test_dtd_is_rejected(self):
        with self.assertRaises(ValueError):policy.parse_bytes(b'<!DOCTYPE policy [<!ENTITY x SYSTEM "file:///etc/passwd">]><policy>&x;</policy>')

    def test_utf16_dtd_is_rejected(self):
        source='<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE policy><policy/>'
        with self.assertRaises(ValueError):policy.parse_bytes(source.encode('utf-16'))

    def test_xinclude_is_rejected(self):
        with self.assertRaises(ValueError):policy.parse_bytes(b'<policy xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="file:///etc/passwd"/></policy>')

    def test_unapproved_schema_resolution_is_rejected(self):
        with self.assertRaises(ValueError):etree.parse('https://invalid.example/unapproved.xsd',policy.parser())

if __name__=='__main__': unittest.main()
