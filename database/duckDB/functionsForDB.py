import duckdb

class Database:
    def __init__(self, db_path):
        self.dbPath = db_path
        self.con = duckdb.connect(self.dbPath)
        
    def dropTables(self):
        # Drop in reverse order due to foreign keys
        self.con.execute("DROP TABLE IF EXISTS Packages")
        self.con.execute("DROP TABLE IF EXISTS Versions") 
        self.con.execute("DROP TABLE IF EXISTS Names")

        # Drop sequences too
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_pack")
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_ver") 
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_names")


    def createTables(self):
        # Create Table for Package Names
        self.createSequences()
        self.con.execute("""CREATE TABLE IF NOT EXISTS Names (
                            NameID INTEGER PRIMARY KEY DEFAULT nextval('sequ_names'), 
                            Name VARCHAR)""")
        # Create Table for Versions
        self.con.execute("""CREATE TABLE IF NOT EXISTS Versions (
                            VersionID INTEGER PRIMARY KEY DEFAULT nextval('sequ_ver'),
                            Version VARCHAR,
                            Major VARCHAR,
                            Minor VARCHAR,
                            Patch VARCHAR
                        )""")
        # Create Join Table
        self.con.execute("""CREATE TABLE IF NOT EXISTS Packages (
                            PackageID INTEGER PRIMARY KEY DEFAULT nextval('sequ_pack'), 
                            NameID INTEGER, 
                            VersionID INTEGER, 
                            FOREIGN KEY (nameID) REFERENCES Names(nameID), 
                            FOREIGN KEY (versionID) REFERENCES Versions(versionID)
                        )""")


    def createSequences(self):
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_names START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_ver START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_pack START 1")
        
    def showAllTables(self):
        self.con.table("Names").show()
        self.con.table("Packages").show()
        self.con.table("Versions").show()


    #Name as String, Version as String "1.1.1"
    def insertPackage(self, packages):
        for package in packages:
            versionCorrect, newVersion = self.isVersionSynCorrect(package[1])
            if versionCorrect:
                versionIndex = self.getVersionIndex(newVersion, *self.encodeVersion(newVersion))
                nameIndex = self.getNameIndex(package[0])
                
                saved = self.con.execute("SELECT * FROM Packages WHERE NameID=? AND VersionID=?", (nameIndex, versionIndex)).fetchone()
                if saved is None:
                    self.con.execute("INSERT INTO Packages (NameID, VersionID) VALUES(?, ?)", (nameIndex, versionIndex))
                else:
                    print("Package already saved")
            else:
                print("The Version has a wrong sytax")


    def getNameIndex(self, name):
        saved = self.con.execute("SELECT * FROM Names WHERE Name=?", (name,)).fetchone()
        if saved is None:
            self.con.execute("INSERT INTO Names (name) VALUES (?)", (name,))
            saved = self.con.execute("SELECT * FROM Names WHERE Name=?", (name,)).fetchone()
        return saved[0]


    def isVersionSynCorrect(version):
        versionSpecs = version.split(".")
        print(len(versionSpecs))
        versionCorrect = True
        if len(versionSpecs) < 2 or len(versionSpecs) > 3:
            versionCorrect = False
        elif len(versionSpecs) == 2:
            print(version)
            version = version + ".0"
            print(version)
        return versionCorrect, version
            

    def encodeVersion(version):
        versionSpecs = version.split(".")
        return versionSpecs[0], versionSpecs[1], versionSpecs[2]


    def getVersionIndex(self, versionChar, major, minor, patch):

        saved = self.con.execute("SELECT * FROM Versions WHERE Version = ?", (versionChar,)).fetchone()
        if saved is None:

            self.con.execute("INSERT INTO Versions (Version, Major, Minor, Patch) VALUES (?, ?, ?, ?)", (versionChar, major, minor, patch))
            saved = self.con.execute("SELECT * FROM Versions WHERE Version = ?", (versionChar,)).fetchone()
        return saved[0]


    def showAllPackages(self):
        self.con.sql("""SELECT Packages.PackageID, Names.Name, Versions.Version
                    FROM ((Packages 
                    INNER JOIN Names ON Packages.NameID = Names.NameID)
                    INNER JOIN Versions ON Packages.VersionID = Versions.VersionID)""").show()


    def findVersionsOfPackage(self, package):
        self.con.sql(f"""SELECT Packages.PackageID, Names.Name, Versions.Version
                    FROM ((Packages 
                    INNER JOIN Names ON Packages.NameID = Names.NameID)
                    INNER JOIN Versions ON Packages.VersionID = Versions.VersionID)
                    WHERE Names.Name = '{package}'""").show()


    def findPackageOfVersion(self, version):
        self.con.sql(f"""SELECT Packages.PackageID, Names.Name, Versions.Version
                    FROM ((Packages 
                    INNER JOIN Names ON Packages.NameID = Names.NameID)
                    INNER JOIN Versions ON Packages.VersionID = Versions.VersionID)
                    WHERE Versions.Version = '{version}'""").show()


    def findLatestVersionOfPackage(self,packageList):
        if not packageList:
            print("No packages specified")
            return

        packageList = packageList.split(",")

        placeholders = ','.join([f"'{name}'" for name in packageList])

        query = f"""
        WITH RankedVersions AS (
            SELECT
                Packages.PackageID,
                Names.Name,
                Versions.Version,
                Versions.Major,
                Versions.Minor,
                Versions.Patch,
                ROW_NUMBER() OVER (
                    PARTITION BY Names.Name 
                    ORDER BY Versions.Major DESC, Versions.Minor DESC, Versions.Patch DESC
                ) as rn
            FROM Packages 
            INNER JOIN Names ON Packages.NameID = Names.NameID
            INNER JOIN Versions ON Packages.VersionID = Versions.VersionID
            WHERE Names.Name IN ({placeholders})
        )
        SELECT PackageID, Name, Version
        FROM RankedVersions
        WHERE rn = 1
        """
        self.con.sql(query).show()


        
