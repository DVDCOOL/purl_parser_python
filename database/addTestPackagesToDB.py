import duckDB.functionsForDB as db
import DBConfigs as conf
import TestPackages as tp



def main():
    dbToAdd = db.Database(conf.dbPath)
    dbToAdd.insertPackage(tp.packages)
    print("Test packages added.")
    dbToAdd.showAllPackages()
    
if __name__ == "__main__":
    main()