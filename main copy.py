from database.duckDB.functionsForDB import Database
from database.DBConfigs import dbPath


def main():
    uidb = Database(dbPath)
    
    uidb.showAllTables()
    allPackages = uidb.getAllPackages()
    count = len(allPackages)
    print(f"Total Packagess: {count}")

    with open('packages.txt', 'w', encoding='utf-8') as f:
        for package in allPackages:
            f.write(str(package) + '\n')
    
if __name__ == "__main__":
    main()
    