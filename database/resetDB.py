import duckDB.functionsForDB as db
import DBConfigs as conf


def main():
    dbToReset = db.Database(conf.dbPath)
    dbToReset.dropTables()
    dbToReset.createTables()
    print("Database reset done.")
    
if __name__ == "__main__":
    main()
    
