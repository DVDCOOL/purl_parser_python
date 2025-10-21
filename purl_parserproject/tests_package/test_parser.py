import unittest
import json
from purl_parser import PurlParser

def loadTestCases():
    with open('purl_parserproject/tests_package/testcases.json') as file:
        return json.load(file)

class test_components(unittest.TestCase):
    pass

class test_content(unittest.TestCase):
    pass

class test_purls(unittest.TestCase):
    pass

def createTestMethods(description, purl, type, namespace, name, version, listOfQualifiers, subpath, ispurl):
        def test_method(self):
            parsedpurl = PurlParser(purl)
            self.assertEqual(parsedpurl.type, type)
            self.assertEqual(parsedpurl.namespace, namespace)
            self.assertEqual(parsedpurl.name, name)
            self.assertEqual(parsedpurl.version, version)
            self.assertEqual(parsedpurl.listOfQualifiers, listOfQualifiers)
            self.assertEqual(parsedpurl.subpath, subpath)
            self.assertEqual(parsedpurl.validPurl, ispurl)
        test_method.__name__ = description
        return test_method

def generate_tests():
    for case in loadTestCases():
        test_method = createTestMethods(case['description'], case['purl'], case['type'], case['namespace'], case['name'], case['version'], case['listOfQualifiers'], case['subpath'], case['is_purl'])
        if case['test_type'] == "component_parsing":
            setattr(test_components, test_method.__name__, test_method)
        if case['test_type'] == "content_parsing":
            setattr(test_content, test_method.__name__, test_method)
        if case['test_type'] == "purl_parsing":
            setattr(test_purls, test_method.__name__, test_method)

def load_tests(loader, tests, pattern):
     generate_tests()
     suite = unittest.TestSuite()
     suite.addTests(loader.loadTestsFromTestCase(test_components))
     suite.addTests(loader.loadTestsFromTestCase(test_content))
     suite.addTests(loader.loadTestsFromTestCase(test_purls))
     return suite

