import json
from purl_parserproject.purls import purls
from purl_parserproject.purl_parser import PurlParser
from database.dbmanager import DBManager


def main():
    database = DBManager()

    for i in purls:
        purl = PurlParser(i)
        if purl.validPurl:
            json_str = {
                "type": purl.type,
                "namespace": purl.namespace,
                "name": purl.name,
                "version": purl.version,
                "qualifiers": purl.qualifiers,
                "subpath": purl.subpath
            }
            json_str = json.dumps(json_str)
            database.insert_purl(json_str)


if __name__ == "__main__":
    main()
