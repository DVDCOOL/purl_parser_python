import duckdb

class Database:
    def __init__(self, db_path):
        self.dbPath = db_path
        self.con = duckdb.connect(self.dbPath)
    
    def showAllTables(self):
        
        # Get all table names from the database
        tables = self.con.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()
        
        for (table,) in tables:
            print(f"\n--- {table} ---")
            self.con.table(table).show()

    def insertPackage(self, type, namespace, name, version, qualifiers, subpath):
        if not name or not type:
            print("Package name and type is required")
            return False
        
        # Handle version
        if not version:
            versionIndex = None
        else:
            versionCorrect, newVersion = self.isVersionSyntaxCorrect(version)
            if not versionCorrect:
                print(f"Invalid version syntax: {version} for {type}/{name}")
                return False
            versionIndex = self.getVersionIndex(newVersion, *self.encodeVersion(newVersion))
        
        # Get indexes for core fields
        typeIndex = self.getTypeIndex(type)
        namespaceIndex = self.getNamespaceIndex(namespace) if namespace else None
        nameIndex = self.getNameIndex(name)
        subpathIndex = self.getSubpathIndex(subpath) if subpath else None
        
        # Handle qualifiers (default to empty list if None)
        if not qualifiers:
            qualifiers = [(None, None)]
        
        inserted_count = 0
        for qualifier in qualifiers:
            qualifierIndex, qualifierCorrect = self.getQualifierIndex(qualifier)
            
            # Check if package already exists
            exists = self.con.execute("""
                SELECT 1 FROM Packages 
                WHERE TypeID=? AND NamespaceID IS NOT DISTINCT FROM ?
                AND NameID=? AND VersionID IS NOT DISTINCT FROM ?
                AND QualifierID IS NOT DISTINCT FROM ? AND SubpathID IS NOT DISTINCT FROM ?
            """, (typeIndex, namespaceIndex, nameIndex, versionIndex, qualifierIndex, subpathIndex)).fetchone()
            
            if not exists:
                self.con.execute("""
                    INSERT INTO Packages (TypeID, NamespaceID, NameID, VersionID, QualifierID, SubpathID) 
                    VALUES(?, ?, ?, ?, ?, ?)
                """, (typeIndex, namespaceIndex, nameIndex, versionIndex, qualifierIndex, subpathIndex))
                inserted_count += 1
        
        if inserted_count > 0:
            return True
        else:
            print("Package already exists")
            return False

    def getTypeIndex(self, type):
        """Get or create Type ID"""
        return self._getOrInsertId("Types", "Type", type, "TypeID")
    
    def getNamespaceIndex(self, namespace):
        """Get or create Namespace ID"""
        return self._getOrInsertId("Namespaces", "Namespace", namespace, "NamespaceID")

    def getNameIndex(self, name):
        """Get or create Name ID"""
        return self._getOrInsertId("Names", "Name", name, "NameID")
    
    def getSubpathIndex(self, subpath):
        """Get or create Subpath ID"""
        return self._getOrInsertId("Subpaths", "Subpath", subpath, "SubpathID")
    
    def _getOrInsertId(self, table, column, value, id_column):
        """Generic method to get or insert a lookup value and return its ID"""
        # Try to get existing
        result = self.con.execute(f"SELECT {id_column} FROM {table} WHERE {column}=?", (value,)).fetchone()
        
        if result is None:
            # Insert and return the new ID
            self.con.execute(f"INSERT INTO {table} ({column}) VALUES (?)", (value,))
            result = self.con.execute(f"SELECT {id_column} FROM {table} WHERE {column}=?", (value,)).fetchone()
        
        return result[0]
    
    def getQualifierIndex(self, qualifier):
        if not qualifier or len(qualifier) != 2:
            return None, False
        
        key, value = qualifier
        if not key or not value:
            return None, False
        
        keyIndex = self._getOrInsertId("QualifierKeys", "Key", key, "KeyID")
        valueIndex = self._getOrInsertId("QualifierValues", "Value", value, "ValueID")
        
        # Get or create qualifier
        result = self.con.execute("""
            SELECT QualifierID FROM Qualifiers 
            WHERE KeyID=? AND ValueID=?
        """, (keyIndex, valueIndex)).fetchone()
        
        if result is None:
            self.con.execute("""
                INSERT INTO Qualifiers (KeyID, ValueID) VALUES (?, ?)
            """, (keyIndex, valueIndex))
            result = self.con.execute("""
                SELECT QualifierID FROM Qualifiers 
                WHERE KeyID=? AND ValueID=?
            """, (keyIndex, valueIndex)).fetchone()
        
        return result[0], True

    def isVersionSyntaxCorrect(self, version):
        """Validate and normalize version string"""
        versionSpecs = version.split(".")
        
        if len(versionSpecs) < 2 or len(versionSpecs) > 3:
            return False, version
        
        if len(versionSpecs) == 2:
            version = version + ".0"
        
        major, minor, patch = self.encodeVersion(version)
        
        # Extract numeric part from major
        major_numeric = ''.join(c for c in major if c.isdigit())
        if not major_numeric:
            return False, version
        
        # Extract numeric part from minor
        minor_numeric = ''.join(c for c in minor if c.isdigit())
        if not minor_numeric:
            return False, version
        
        # Reconstruct version
        normalized_version = f"{major_numeric}.{minor_numeric}.{patch}"
        return True, normalized_version

    def encodeVersion(self, version):
        """Split version string into major, minor, patch"""
        versionSpecs = version.split(".")
        return versionSpecs[0], versionSpecs[1], versionSpecs[2]

    def getVersionIndex(self, versionChar, major, minor, patch):
        """Get or create Version ID"""
        result = self.con.execute("""
            SELECT VersionID FROM Versions WHERE Version = ?
        """, (versionChar,)).fetchone()
        
        if result is None:
            self.con.execute("""
                INSERT INTO Versions (Version, Major, Minor, Patch) 
                VALUES (?, ?, ?, ?)
            """, (versionChar, int(major), int(minor), patch))
            result = self.con.execute("""
                SELECT VersionID FROM Versions WHERE Version = ?
            """, (versionChar,)).fetchone()
        
        return result[0]

    def getAllPackages(self):
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