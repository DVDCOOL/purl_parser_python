import unittest
import purl_parser_python.purl_parser.purl_parser as purl_parser

class testParser(unittest.TestCase):
    
    def test_isValidPurl(self):
        resultTrue = purl_parser.isValidPurl("pkg:", "title/namespace/name@version?qualifier#subpath".split("/"))
        self.assertTrue(resultTrue)

        resultSchemaFalse = purl_parser.isValidPurl("pk:", "title/namespace/name@version?qualifier#subpath".split("/"))
        self.assertFalse(resultSchemaFalse)

        resultKomponentenFalse = purl_parser.isValidPurl("pkg:", "name@version?qualifier#subpath".split("/"))
        self.assertFalse(resultKomponentenFalse)

    def test_splitOptionalComponents(self):
        result1 = purl_parser.splitOptionalComponents("name@version?qualifier#subpath")
        self.assertEquals(result1, ["name", "version", "qualifier", "subpath"])

        result2 = purl_parser.splitOptionalComponents("name?qualifier")
        self.assertEquals(result2, ["name", None, "qualifier", None])

        result3 = purl_parser.splitOptionalComponents("name#subpath")
        self.assertEquals(result3, ["name", None, None, "subpath"])

        result4 = purl_parser.splitOptionalComponents("name")
        self.assertEquals(result4, ["name", None, None, None])


    def test_parser(self):
        result = purl_parser.parse("pkg:titel/namespace/name@version?qualifiers#subpath")
        self.assertEquals(result, ["titel", "namespace", "name", "version", "qualifiers", "subpath"])

        result2 = purl_parser.parse("pkg:name@version?qualifiers#subpath")
        self.assertEquals(result2, None)

        result3 = purl_parser.parse("pkg:titel/name@version?qualifiers#subpath")
        self.assertEquals(result3, ["titel", None, "name", "version", "qualifiers", "subpath"])

        result4 = purl_parser.parse("pkg://titel//name@version?qualifiers#subpath")
        self.assertEquals(result4, ["titel", None, "name", "version", "qualifiers", "subpath"])



    def test_parseList(self):
        liste = ["pkg:titel/name@version", "pkg:name@version?qualifiers#subpath", "pkg:titel/namespace/name@version#subpath"]
        result = purl_parser.parseList(liste)
        self.assertEquals(result, [["titel", None, "name", "version", None, None], ["titel", "namespace", "name", "version", None, "subpath"]])