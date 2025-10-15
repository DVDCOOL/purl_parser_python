import duckdb
import userInteractionWithPackageDB as uidb


con = duckdb.connect(uidb.dbPath)

def dropTables():
    # Drop in reverse order due to foreign keys
    con.execute("DROP TABLE IF EXISTS Packages")
    con.execute("DROP TABLE IF EXISTS Versions") 
    con.execute("DROP TABLE IF EXISTS Names")

    # Drop sequences too
    con.execute("DROP SEQUENCE IF EXISTS sequ_pack")
    con.execute("DROP SEQUENCE IF EXISTS sequ_ver") 
    con.execute("DROP SEQUENCE IF EXISTS sequ_names")


def createTables():
    # Create Table for Package Names
    createSequences()
    con.execute("""CREATE TABLE IF NOT EXISTS Names (
        				NameID INTEGER PRIMARY KEY DEFAULT nextval('sequ_names'), 
            			Name VARCHAR)""")
    # Create Table for Versions
    con.execute("""CREATE TABLE IF NOT EXISTS Versions (
        				VersionID INTEGER PRIMARY KEY DEFAULT nextval('sequ_ver'),
						Version VARCHAR,
            			Major VARCHAR,
						Minor VARCHAR,
						Patch VARCHAR
                    )""")
    # Create Join Table
    con.execute("""CREATE TABLE IF NOT EXISTS Packages (
        				PackageID INTEGER PRIMARY KEY DEFAULT nextval('sequ_pack'), 
            			NameID INTEGER, 
               			VersionID INTEGER, 
                  		FOREIGN KEY (nameID) REFERENCES Names(nameID), 
                    	FOREIGN KEY (versionID) REFERENCES Versions(versionID)
                    )""")


def createSequences():
    con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_names START 1")
    con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_ver START 1")
    con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_pack START 1")
    

    
    
dropTables()
createTables()
