from purl_parserproject.purls import purls
from purl_parserproject.purl_parser import PurlParser
from database.duckDB.functionsForDB import Database
from database.DBConfigs import dbPath


def main():
    uidb = Database(dbPath)
    uidb.dropTables()
    uidb.createTables()
    
    for purl in purls:
        parsedPurl = PurlParser(purl)
        if parsedPurl.validPurl:
            uidb.insertPurl(parsedPurl.inputPurl)
        else:
            print(f"Invalid purl skipped: {purl}")
    
    print("Inserted PURLs into the database:")
    uidb.showAllTables()
    count = uidb.con.execute("SELECT COUNT(*) FROM Purls").fetchone()[0]
    print(f"Total PURLs: {count}")
    
if __name__ == "__main__":
    main()