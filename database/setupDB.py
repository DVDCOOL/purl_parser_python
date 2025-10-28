import duckDB.functionsForDB as db
import DBConfigs as conf
import TestPackages as tp



def main():
    dbToSetup = db.Database(conf.dbPath)
    dbToSetup.createTables()
    dbToSetup.showAllTables()
    print("Database setup done.")

if __name__ == "__main__":
    main()