import unittest
import json
from purl_parser import purlparser

def loadTestCases():
    with open('purl_parserproject/tests_package/testcases.json') as file:
        return json.load(file)

class test_components(unittest.TestCase):
    pass

class test_content(unittest.TestCase):
    pass

class test_purls(unittest.TestCase):
    pass

def createTestMethods(description, purl, title, namespace, name, version, qualifiers, subpath):
        def test_method(self):
            parsedpurl = purlparser(purl)
            self.assertEqual(parsedpurl.title, title)
            self.assertEqual(parsedpurl.namespace, namespace)
            self.assertEqual(parsedpurl.name, name)
            self.assertEqual(parsedpurl.version, version)
            self.assertEqual(parsedpurl.qualifiers, qualifiers)
            self.assertEqual(parsedpurl.subpath, subpath)
        test_method.__name__ = description
        return test_method

def generate_tests():
    for case in loadTestCases():
        test_method = createTestMethods(case['description'], case['purl'], case['title'], case['namespace'], case['name'], case['version'], case['qualifiers'], case['subpath'])
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
