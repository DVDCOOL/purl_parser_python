import unittest
import purl_parser

class testParser(unittest.TestCase):
    
    def test_istRichtigerPurl(self):
        resultTrue = purl_parser.istRichtigerPurl("pkg:", "title/namespace/name@version?qualifier#subpath".split("/"))
        self.assertTrue(resultTrue)

        resultSchemaFalse = purl_parser.istRichtigerPurl("pk:", "title/namespace/name@version?qualifier#subpath".split("/"))
        self.assertFalse(resultSchemaFalse)

        resultKomponentenFalse = purl_parser.istRichtigerPurl("pkg:", "name@version?qualifier#subpath".split("/"))
        self.assertFalse(resultKomponentenFalse)

    def test_teileInOptionaleKomponenten(self):
        result1 = purl_parser.teileInOptionaleKomponenten("name@version?qualifier#subpath")
        self.assertEquals(result1, ["name", "version", "qualifier", "subpath"])

        result2 = purl_parser.teileInOptionaleKomponenten("name?qualifier")
        self.assertEquals(result2, ["name", "qualifier"])

        result3 = purl_parser.teileInOptionaleKomponenten("name#subpath")
        self.assertEquals(result3, ["name", "subpath"])

        result4 = purl_parser.teileInOptionaleKomponenten("name")
        self.assertEquals(result4, ["name"])

    def test_parser(self):
        result = purl_parser.parse("pkg:titel/namespace/name@version?qualifiers#subpath")
        self.assertEquals(result, ["titel", "namespace", "name", "version", "qualifiers", "subpath"])

        result2 = purl_parser.parse("pkg:pygments-main@244fd47e07d1014f0aed9c")
        self.assertEquals(result2, None)