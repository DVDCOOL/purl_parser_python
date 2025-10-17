import unittest
import json
from purl_parser import purlparser

def loadTestCases():
    with open('purl_parserproject/tests_package/testcases.json') as file:
        return json.load(file)

class test_components(unittest.TestCase):
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
        description = case['description']
        purl = case['purl']
        title = case['title']
        namespace = case['namespace']
        name = case['name']
        version = case['version']
        qualifiers = case['qualifiers']
        subpath = case['subpath']
        test_method = createTestMethods(description, purl, title, namespace, name, version, qualifiers, subpath)
        setattr(test_components, test_method.__name__, test_method)

def load_tests(loader, tests, pattern):
    generate_tests()
    return loader.loadTestsFromTestCase(test_components)

if __name__ == '__main__':
    generate_tests()
    unittest.main()