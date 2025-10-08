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
        result = purl_parser.teileInOptionaleKomponenten("name@version?qualifier#subpath")
        self.assertEquals(result, ["name", "version", "qualifier", "subpath"])

    def test_parser(self):
        result = purl_parser.parse("pkg:titel/namespace/name@version?qualifiers#subpath")
        self.assertEquals(result, ["titel", "namespace", "name", "version", "qualifiers", "subpath"])