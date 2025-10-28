import duckdb

class Database:
    def __init__(self, db_path):
        self.dbPath = db_path
        self.con = duckdb.connect(self.dbPath)
        
    def dropTables(self):
        # Drop in reverse order due to foreign keys
        self.con.execute("DROP TABLE IF EXISTS Packages")
        self.con.execute("DROP TABLE IF EXISTS Qualifiers")
        self.con.execute("DROP TABLE IF EXISTS QualifierKeys")
        self.con.execute("DROP TABLE IF EXISTS QualifierValues")
        self.con.execute("DROP TABLE IF EXISTS Versions") 
        self.con.execute("DROP TABLE IF EXISTS Names")
        self.con.execute("DROP TABLE IF EXISTS Types")

        # Drop all sequences
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_pack")
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_qual")
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_key")
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_value")
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_ver") 
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_names")
        self.con.execute("DROP SEQUENCE IF EXISTS sequ_types")


    def createTables(self):
        # Create Table for Package Names
        self.createSequences()
        self.con.execute("""CREATE TABLE IF NOT EXISTS Types (
                            TypeID INTEGER PRIMARY KEY DEFAULT nextval('sequ_types'), 
                            Type VARCHAR)""")
        self.con.execute("""CREATE TABLE IF NOT EXISTS Namespaces (
                            NamespaceID INTEGER PRIMARY KEY DEFAULT nextval('sequ_namespace'), 
                            Namespace VARCHAR
                        )""")
        
        self.con.execute("""CREATE TABLE IF NOT EXISTS Names (
                            NameID INTEGER PRIMARY KEY DEFAULT nextval('sequ_names'), 
                            Name VARCHAR)""")
        # Create Table for Versions
        self.con.execute("""CREATE TABLE IF NOT EXISTS Versions (
                            VersionID INTEGER PRIMARY KEY DEFAULT nextval('sequ_ver'),
                            Version VARCHAR,
                            Major INTEGER,
                            Minor INTEGER,
                            Patch VARCHAR
                        )""")

        self.con.execute("""CREATE TABLE IF NOT EXISTS QualifierKeys (
                            KeyID INTEGER PRIMARY KEY DEFAULT nextval('sequ_key'),
                            Key VARCHAR
                        )""")
        self.con.execute("""CREATE TABLE IF NOT EXISTS QualifierValues (
                            ValueID INTEGER PRIMARY KEY DEFAULT nextval('sequ_value'),
                            Value VARCHAR
                        )""")
        self.con.execute("""CREATE TABLE IF NOT EXISTS Qualifiers (
                            QualifierID INTEGER PRIMARY KEY DEFAULT nextval('sequ_qual'),
                            KeyID INTEGER,
                            ValueID INTEGER,
                            FOREIGN KEY (KeyID) REFERENCES QualifierKeys(KeyID),
                            FOREIGN KEY (ValueID) REFERENCES QualifierValues(ValueID)
                        )""")
        self.con.execute("""CREATE TABLE IF NOT EXISTS Subpaths (
                            SubpathID INTEGER PRIMARY KEY DEFAULT nextval('sequ_subpath'),
                            Subpath VARCHAR
                         )""")
        # Create Join Table
        self.con.execute("""CREATE TABLE IF NOT EXISTS Packages (
                            PackageID INTEGER PRIMARY KEY DEFAULT nextval('sequ_pack'),
                            TypeID INTEGER,
                            NamespaceID INTEGER,
                            NameID INTEGER, 
                            VersionID INTEGER,
                            QualifierID INTEGER,
                            SubpathID INTEGER,
                            FOREIGN KEY (TypeID) REFERENCES Types(TypeID),
                            FOREIGN KEY (NamespaceID) REFERENCES Namespaces(NamespaceID),
                            FOREIGN KEY (nameID) REFERENCES Names(nameID), 
                            FOREIGN KEY (versionID) REFERENCES Versions(versionID),
                            FOREIGN KEY (QualifierID) REFERENCES Qualifiers(QualifierID),
                            FOREIGN KEY (SubpathID) REFERENCES Subpaths(SubpathID)
                        )""")


    def createSequences(self):
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_types START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_namespace START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_names START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_ver START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_pack START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_qual START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_key START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_value START 1")
        self.con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_subpath START 1")
        
    def showAllTables(self):
        self.con.table("Types").show()
        self.con.table("Namespaces").show()
        self.con.table("Names").show()
        self.con.table("Versions").show()
        self.con.table("Qualifiers").show()
        self.con.table("QualifierKeys").show()
        self.con.table("QualifierValues").show()
        self.con.table("Subpaths").show()
        self.con.table("Packages").show()


    #Name as String, Version as String "1.1.1"
    def insertPackage(self, type, namespace, name, version, qualfiers, subpath):
        if not name or not type:
            print("Package name and type is required")
            return
        
        if not version:
            versionCorrect = True
            versionIndex = 0
        else:
            versionCorrect, newVersion = self.isVersionSynCorrect(version)
            if versionCorrect:
                versionIndex = self.getVersionIndex(newVersion, *self.encodeVersion(newVersion))
            else:
                print("The Version has a wrong sytax " + version + " "+ type + " " + name)
                return
        typeIndex = self.getTypeIndex(type)
        namespaceIndex = self.getNamespaceIndex(namespace) if namespace else None
        nameIndex = self.getNameIndex(name)
        subpathIndex = self.getSubpathIndex(subpath) if subpath else None
        for qualifier in qualfiers:
            qualifierIndex, qualifierCorrect = self.getQualifierIndex(qualifier)
            if qualifierCorrect:
                saved = self.con.execute("SELECT * FROM Packages WHERE TypeID=? AND NamespaceID=? AND NameID=? AND VersionID=? AND QualifierID=? AND SubpathID=?", (typeIndex, namespaceIndex, nameIndex, versionIndex, qualifierIndex, subpathIndex)).fetchone()
                if saved is None:
                    self.con.execute("INSERT INTO Packages (TypeID, NamespaceID, NameID, VersionID, QualifierID, SubpathID) VALUES(?, ?, ?, ?, ?, ?)", (typeIndex, namespaceIndex, nameIndex, versionIndex, qualifierIndex, subpathIndex))
                else:
                    print("Package already saved")

            
            

    def getTypeIndex(self, type):
        saved = self.con.execute("SELECT * FROM Types WHERE Type=?", (type,)).fetchone()
        if saved is None:
            self.con.execute("INSERT INTO Types (type) VALUES (?)", (type,))
            saved = self.con.execute("SELECT * FROM Types WHERE Type=?", (type,)).fetchone()
        return saved[0]
    
    def getNamespaceIndex(self, namespace):
        saved = self.con.execute("SELECT * FROM Namespaces WHERE Namespace=?", (namespace,)).fetchone()
        if saved is None:
            self.con.execute("INSERT INTO Namespaces (Namespace) VALUES (?)", (namespace,))
            saved = self.con.execute("SELECT * FROM Namespaces WHERE Namespace=?", (namespace,)).fetchone()
        return saved[0]

    def getNameIndex(self, name):
        saved = self.con.execute("SELECT * FROM Names WHERE Name=?", (name,)).fetchone()
        if saved is None:
            self.con.execute("INSERT INTO Names (name) VALUES (?)", (name,))
            saved = self.con.execute("SELECT * FROM Names WHERE Name=?", (name,)).fetchone()
        return saved[0]
    
    def getQualifierIndex(self, qualifier):
        key, value = qualifier
        if key and value:
            keyIndex = self.getQualifierKeyIndex(key)
            valueIndex = self.getQualifierValueIndex(value)
            
            saved = self.con.execute("SELECT * FROM Qualifiers WHERE KeyID=? AND ValueID=?", (keyIndex, valueIndex)).fetchone()
            if saved is None:
                self.con.execute("INSERT INTO Qualifiers (KeyID, ValueID) VALUES (?, ?)", (keyIndex, valueIndex))
                saved = self.con.execute("SELECT * FROM Qualifiers WHERE KeyID=? AND ValueID=?", (keyIndex, valueIndex)).fetchone()
            return saved[0], True
        else:
            return None, False

    def getQualifierKeyIndex(self, key):
        saved = self.con.execute("SELECT * FROM QualifierKeys WHERE Key=?", (key,)).fetchone()
        if saved is None:
            self.con.execute("INSERT INTO QualifierKeys (Key) VALUES (?)", (key,))
            saved = self.con.execute("SELECT * FROM QualifierKeys WHERE Key=?", (key,)).fetchone()
        return saved[0]
    
    def getQualifierValueIndex(self, value):
        saved = self.con.execute("SELECT * FROM QualifierValues WHERE Value=?", (value,)).fetchone()
        if saved is None:
            self.con.execute("INSERT INTO QualifierValues (Value) VALUES (?)", (value,))
            saved = self.con.execute("SELECT * FROM QualifierValues WHERE Value=?", (value,)).fetchone()
        return saved[0]
    
    def getSubpathIndex(self, subpath):
        saved = self.con.execute("SELECT * FROM Subpaths WHERE Subpath=?", (subpath,)).fetchone()
        if saved is None:
            self.con.execute("INSERT INTO Subpaths (Subpath) VALUES (?)", (subpath,))
            saved = self.con.execute("SELECT * FROM Subpaths WHERE Subpath=?", (subpath,)).fetchone()
        return saved[0]

    def is_string_an_integer(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def isVersionSynCorrect(self, version):
        versionSpecs = version.split(".")
        versionCorrect = True
        if len(versionSpecs) < 2 or len(versionSpecs) > 3:
            versionCorrect = False
        elif len(versionSpecs) == 2:
            version = version + ".0"
            
        major, minor, patch = self.encodeVersion(version)
        while not self.is_string_an_integer(major) and len(major) > 0:

            major = major[1:]
        if major == "":
            return False, version
        while not self.is_string_an_integer(minor) and len(minor) > 0:
            minor = minor[1:]
        if minor == "":
            return False, version    
        version= major + "." + minor + "." + patch
        return versionCorrect, version
            

    def encodeVersion(self, version):
        versionSpecs = version.split(".")
        return versionSpecs[0], versionSpecs[1], versionSpecs[2]


    def getVersionIndex(self, versionChar, major, minor, patch):
        
        saved = self.con.execute("SELECT * FROM Versions WHERE Version = ?", (versionChar,)).fetchone()
        if saved is None:

            self.con.execute("INSERT INTO Versions (Version, Major, Minor, Patch) VALUES (?, ?, ?, ?)", (versionChar, major, minor, patch))
            saved = self.con.execute("SELECT * FROM Versions WHERE Version = ?", (versionChar,)).fetchone()
        return saved[0]


    def getAllPackages(self):
        """Get all packages with versions (sorted descending) and qualifiers grouped as lists"""
        query = """
            SELECT 
                LIST(DISTINCT p.PackageID ORDER BY p.PackageID) as PackageIDs,
                t.Type,
                ns.Namespace,
                n.Name,
                LIST(DISTINCT v.Version ORDER BY v.Version DESC) FILTER (WHERE v.Version IS NOT NULL) as Versions,
                LIST(DISTINCT [qk.Key, qv.Value]) FILTER (WHERE qk.Key IS NOT NULL) as Qualifiers,
                LIST(DISTINCT sp.Subpath) FILTER (WHERE sp.Subpath IS NOT NULL) as Subpaths
            FROM Packages p
            LEFT JOIN Types t ON p.TypeID = t.TypeID
            LEFT JOIN Namespaces ns ON p.NamespaceID = ns.NamespaceID
            LEFT JOIN Names n ON p.NameID = n.NameID
            LEFT JOIN Versions v ON p.VersionID = v.VersionID
            LEFT JOIN Qualifiers q ON p.QualifierID = q.QualifierID
            LEFT JOIN QualifierKeys qk ON q.KeyID = qk.KeyID
            LEFT JOIN QualifierValues qv ON q.ValueID = qv.ValueID
            LEFT JOIN Subpaths sp ON p.SubpathID = sp.SubpathID
            GROUP BY t.Type, ns.Namespace, n.Name, sp.Subpath
            ORDER BY MIN(p.PackageID)
        """
        self.con.query(query).show()
        return self.con.execute(query).fetchall()
