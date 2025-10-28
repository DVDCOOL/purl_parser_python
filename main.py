from purl_parserproject.purls import purls
from purl_parserproject.purl_parser import PurlParser
from database.duckDB.functionsForDB import Database
from database.DBConfigs import dbPath
from purl_parserproject.fakePurls import generate_fake_purls


def main():
    uidb = Database(dbPath)
    newpurls = generate_fake_purls()
    prozent = 0
    total = len(newpurls)
    
    for purl in newpurls:
        prozent += 1
        print(f"Processing {prozent}/{total} PURLs", end='\r')
        
        parsedPurl = PurlParser(purl)
        if parsedPurl.validPurl:
            uidb.insertPackage(parsedPurl.type, parsedPurl.namespace, parsedPurl.name, parsedPurl.version, parsedPurl.listOfQualifiers, parsedPurl.subpath)
        else:
            print(f"Invalid purl skipped: {purl}")
    
    print("Inserted PURLs into the database:")
    uidb.showAllTables()
    allPackages = uidb.getAllPackages()
    count = len(allPackages)
    print(f"Total Packagess: {count}")

    with open('packages.txt', 'w', encoding='utf-8') as f:
        for package in allPackages:
            f.write(str(package) + '\n')
    
if __name__ == "__main__":
    main()