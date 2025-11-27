import duckdb

class Database:
    def __init__(self, db_path, read_only=False):
        """
        Initialize database connection
        Args:
            db_path: Path to DuckDB file
            read_only: If True, open in read-only mode for better concurrency
        """
        self.dbPath = db_path
        self.con = duckdb.connect(self.dbPath, read_only=read_only)

    def getPackageCount(self):
        """
        Efficient count using DuckDB - MUCH faster than len(getAllPackages())
        """
        query = """
        SELECT COUNT(DISTINCT PackageID) 
        FROM Packages
        """
        result = self.con.execute(query).fetchone()
        return result[0] if result else 0

    def getPackagesPaginated(self, limit=100, offset=0):
        """
        Get packages with native DuckDB pagination - avoids loading all data into memory
        This is the key optimization for concurrent reads!
        """
        query = """
        WITH RankedPackages AS (
            SELECT 
                p.PackageID,
                ROW_NUMBER() OVER (
                    PARTITION BY e.Ecosystem, ns.Namespace, n.Name 
                    ORDER BY p.PackageID
                ) AS rn
            FROM Packages p
            LEFT JOIN Ecosystems e ON p.EcosystemID = e.EcosystemID
            LEFT JOIN Namespaces ns ON p.NamespaceID = ns.NamespaceID
            LEFT JOIN Names n ON p.NameID = n.NameID
        ),
        FilteredPackages AS (
            SELECT PackageID
            FROM RankedPackages
            WHERE rn = 1
            ORDER BY PackageID
            LIMIT ? OFFSET ?
        )
        SELECT
            array_agg(DISTINCT p.PackageID) AS PackageIDs,
            pu.PURL,
            e.Ecosystem,
            ns.Namespace,
            n.Name,
            array_agg(DISTINCT v.Version) FILTER (WHERE v.Version IS NOT NULL) AS Versions,
            array_agg(DISTINCT ROW(qk.Key, qv.Value)) FILTER (WHERE qk.Key IS NOT NULL) AS Qualifiers,
            array_agg(DISTINCT sp.Subpath) FILTER (WHERE sp.Subpath IS NOT NULL) AS Subpaths,
            array_agg(DISTINCT l.License) FILTER (WHERE l.License IS NOT NULL) AS Licenses,
            ru.RepositoryURL,
            hu.HomepageURL,
            d.Description,

            -- Dependencies as an array of structs
            array_agg(DISTINCT ROW(
                e2.Ecosystem,
                ns2.Namespace,
                n2.Name,
                v2.Version,
                l2.License
            )) FILTER (WHERE dep.DependsOnPackageID IS NOT NULL) AS Dependencies

        FROM FilteredPackages fp
        JOIN Packages p ON fp.PackageID = p.PackageID
        LEFT JOIN Ecosystems e ON p.EcosystemID = e.EcosystemID
        LEFT JOIN Namespaces ns ON p.NamespaceID = ns.NamespaceID
        LEFT JOIN Names n ON p.NameID = n.NameID
        LEFT JOIN Versions v ON p.VersionID = v.VersionID
        LEFT JOIN Qualifiers q ON p.QualifierID = q.QualifierID
        LEFT JOIN QualifierKeys qk ON q.KeyID = qk.KeyID
        LEFT JOIN QualifierValues qv ON q.ValueID = qv.ValueID
        LEFT JOIN Subpaths sp ON p.SubpathID = sp.SubpathID
        LEFT JOIN Licenses l ON p.LicenseID = l.LicenseID
        LEFT JOIN PURLs pu ON p.PURLID = pu.PURLID
        LEFT JOIN RepositoryURLs ru ON p.RepositoryURLID = ru.RepositoryURLID
        LEFT JOIN HomepageURLs hu ON p.HomepageURLID = hu.HomepageURLID
        LEFT JOIN Descriptions d ON p.DescriptionID = d.DescriptionID

        LEFT JOIN Dependencies dep ON dep.DependsOnPackageID = p.PackageID
        LEFT JOIN Packages p2 ON dep.PackageID = p2.PackageID
        LEFT JOIN Ecosystems e2 ON p2.EcosystemID = e2.EcosystemID
        LEFT JOIN Namespaces ns2 ON p2.NamespaceID = ns2.NamespaceID
        LEFT JOIN Names n2 ON p2.NameID = n2.NameID
        LEFT JOIN Versions v2 ON p2.VersionID = v2.VersionID
        LEFT JOIN Licenses l2 ON p2.LicenseID = l2.LicenseID

        GROUP BY
            e.Ecosystem, ns.Namespace, n.Name,
            pu.PURL, ru.RepositoryURL, hu.HomepageURL, d.Description

        ORDER BY MIN(p.PackageID);
        """
        
        return self.con.execute(query, (limit, offset)).fetchall()
    
    def showAllTables(self):
        """Display all tables and their contents"""
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
    
    # ========== HELPER METHODS ==========
    
    def _getOrInsertId(self, table, column, value, id_column):
        """Generic method to get or insert a lookup value and return its ID"""
        # Try to get existing
        result = self.con.execute(f"SELECT {id_column} FROM {table} WHERE {column}=?", (value,)).fetchone()
        
        if result is None:
            # Insert and return the new ID
            self.con.execute(f"INSERT INTO {table} ({column}) VALUES (?)", (value,))
            result = self.con.execute(f"SELECT {id_column} FROM {table} WHERE {column}=?", (value,)).fetchone()
        
        return result[0]
    
    # ========== TYPE, NAMESPACE, NAME, SUBPATH, LICENSE ==========
    
    def getEcosystemIndex(self, ecosystem):
        """Get or create Ecosystem ID"""
        return self._getOrInsertId("Ecosystems", "Ecosystem", ecosystem, "EcosystemID")
    
    def getNamespaceIndex(self, namespace):
        """Get or create Namespace ID"""
        return self._getOrInsertId("Namespaces", "Namespace", namespace, "NamespaceID")
    
    def getNameIndex(self, name):
        """Get or create Name ID"""
        return self._getOrInsertId("Names", "Name", name, "NameID")
    
    def getSubpathIndex(self, subpath):
        """Get or create Subpath ID"""
        return self._getOrInsertId("Subpaths", "Subpath", subpath, "SubpathID")
    
    def getLicenseIndex(self, license):
        """Get or create license ID"""
        return self._getOrInsertId("Licenses", "License", license, "LicenseID")
    
    def getNormalizedLicenseIndex(self, normalized_license):
        """Get or create normalized license ID"""
        return self._getOrInsertId("NormalizedLicenses", "NormalizedLicense", normalized_license, "NormalizedLicenseID")
    
    def getPurlIndex(self, purl):
        """Get or create PURL ID"""
        return self._getOrInsertId("PURLs", "PURL", purl, "PURLID")
    
    def getRepositoryURLIndex(self, repo_url):
        """Get or create Repository URL ID"""
        return self._getOrInsertId("RepositoryURLs", "RepositoryURL", repo_url, "RepositoryURLID")
    
    def getHomepageURLIndex(self, homepage_url):
        """Get or create Homepage URL ID"""
        return self._getOrInsertId("HomepageURLs", "HomepageURL", homepage_url, "HomepageURLID")
    
    def getDescriptionIndex(self, description):
        """Get or create Description ID"""
        return self._getOrInsertId("Descriptions", "Description", description, "DescriptionID")

    # ========== VERSION ==========
    
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
    
    # ========== QUALIFIERS ==========
    
    def getQualifierIndex(self, qualifier):
        """Get or create Qualifier ID from key-value pair"""
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
    
    # ========== PACKAGES ==========
    
    def insertPackage(self, ecosystem, namespace, name, version, qualifiers, subpath):
        """Insert package WITHOUT license (legacy method for compatibility)"""
        return self.insertPackageWithLicense(ecosystem, namespace, name, version, qualifiers, subpath, None)

    def insertPackageWithLicense(self, ecosystem, namespace, name, version, qualifiers, subpath, purl=None, repository_url=None, homepage_url=None, license=None, description=None, normalized_license=None):
        """Insert package WITH license and return (success, list of PackageIDs)"""
        if not name or not ecosystem:
            print("Package name and ecosystem is required")
            return False, []
        
        # Get license index
        licenseIndex = self.getLicenseIndex(license) if license else None

        normalizedLicenseIndex = self.getNormalizedLicenseIndex(normalized_license) if normalized_license else None
        # Handle version
        if not version:
            versionIndex = None
        else:
            versionCorrect, newVersion = self.isVersionSyntaxCorrect(version)
            if not versionCorrect:
                print(f"Invalid version syntax: {version} for {ecosystem}/{name}")
                versionIndex = None
            versionIndex = self.getVersionIndex(newVersion, *self.encodeVersion(newVersion))
        
        # Get indexes for core fields
        ecosystemIndex = self.getEcosystemIndex(ecosystem)
        namespaceIndex = self.getNamespaceIndex(namespace) if namespace else None
        nameIndex = self.getNameIndex(name)
        subpathIndex = self.getSubpathIndex(subpath) if subpath else None
        purlIndex = self.getPurlIndex(purl) if purl else None
        repositoryURLIndex = self.getRepositoryURLIndex(repository_url) if repository_url else None
        homepageURLIndex = self.getHomepageURLIndex(homepage_url) if homepage_url else None
        descriptionIndex = self.getDescriptionIndex(description) if description else None
        
        # Handle qualifiers
        if not qualifiers:
            qualifiers = [(None, None)]
        
        inserted_count = 0
        packageIDs = []
        
        for qualifier in qualifiers:
            qualifierIndex, qualifierCorrect = self.getQualifierIndex(qualifier)
            
            # Check if package already exists
            exists = self.con.execute("""
                SELECT PackageID, LicenseID FROM Packages 
                WHERE EcosystemID=? AND NamespaceID IS NOT DISTINCT FROM ?
                AND NameID=? AND VersionID IS NOT DISTINCT FROM ?
                AND QualifierID IS NOT DISTINCT FROM ? AND SubpathID IS NOT DISTINCT FROM ?
            """, (ecosystemIndex, namespaceIndex, nameIndex, versionIndex, qualifierIndex, subpathIndex)).fetchone()
            
            if not exists:
                # Package doesn't exist, insert it
                result = self.con.execute("""
                    INSERT INTO Packages (EcosystemID, NamespaceID, NameID, VersionID, QualifierID, SubpathID, LicenseID, NormalizedLicenseID, PURLID, RepositoryURLID, HomepageURLID, DescriptionID) 
                    VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    RETURNING PackageID
                """, (ecosystemIndex, namespaceIndex, nameIndex, versionIndex, qualifierIndex, subpathIndex, licenseIndex, normalizedLicenseIndex, purlIndex, repositoryURLIndex, homepageURLIndex, descriptionIndex)).fetchone()

                if result:
                    packageIDs.append(result[0])
                    inserted_count += 1
            else:
                # Package exists
                existing_package_id, existing_license_id = exists
                packageIDs.append(existing_package_id)
                
                # Only update if license is different and new license is not None
                if licenseIndex and licenseIndex != existing_license_id:
                    try:
                        self.con.execute("""
                            UPDATE Packages SET LicenseID=? WHERE PackageID=?
                        """, (licenseIndex, existing_package_id))
                    except Exception as e:
                        # If update fails due to foreign key constraint, just skip it
                        # The package still exists with its old license
                        if "foreign key" in str(e).lower():
                            pass  # Silently skip foreign key issues on update
                        else:
                            raise  # Re-raise other errors
        
        if inserted_count > 0:
            return True, packageIDs
        else:
            # Return False but still return packageIDs for existing packages
            return False, packageIDs
    def getPackageID(self, ecosystem, name, version=None, namespace=None):
        """Helper to get PackageID by ecosystem, name, and optional version/namespace"""
        ecosystemIndex = self.con.execute("SELECT EcosystemID FROM Ecosystems WHERE Ecosystem=?", (ecosystem,)).fetchone()
        nameIndex = self.con.execute("SELECT NameID FROM Names WHERE Name=?", (name,)).fetchone()
        
        if not ecosystemIndex or not nameIndex:
            return None
        
        query = """
            SELECT PackageID FROM Packages 
            WHERE EcosystemID=? AND NameID=?
        """
        params = [ecosystemIndex[0], nameIndex[0]]
        
        if namespace:
            namespaceIndex = self.con.execute("SELECT NamespaceID FROM Namespaces WHERE Namespace=?", (namespace,)).fetchone()
            if namespaceIndex:
                query += " AND NamespaceID=?"
                params.append(namespaceIndex[0])
        
        if version:
            versionIndex = self.con.execute("SELECT VersionID FROM Versions WHERE Version=?", (version,)).fetchone()
            if versionIndex:
                query += " AND VersionID=?"
                params.append(versionIndex[0])
        
        query += " LIMIT 1"
        result = self.con.execute(query, params).fetchone()
        
        return result[0] if result else None
    
    def getAllPackages(self):
        """Retrieve all packages with aggregated information including licenses"""
        query = """
        SELECT
            array_agg(DISTINCT p.PackageID)                                       AS PackageIDs,
            pu.PURL,
            e.Ecosystem,
            ns.Namespace,
            n.Name,
            array_agg(DISTINCT v.Version)              FILTER (WHERE v.Version IS NOT NULL) AS Versions,
            array_agg(DISTINCT ROW(qk.Key, qv.Value)) FILTER (WHERE qk.Key IS NOT NULL) AS Qualifiers,
            array_agg(DISTINCT sp.Subpath)             FILTER (WHERE sp.Subpath IS NOT NULL) AS Subpaths,
            array_agg(DISTINCT l.License)              FILTER (WHERE l.License IS NOT NULL) AS Licenses,
            ru.RepositoryURL,
            hu.HomepageURL,
            d.Description,

            -- Dependencies as an array of structs (ROW = struct)
            array_agg(DISTINCT ROW(
                e2.Ecosystem,
                ns2.Namespace,
                n2.Name,
                v2.Version,
                l2.License
            )) FILTER (WHERE dep.DependsOnPackageID IS NOT NULL) AS Dependencies

        FROM Packages p
        LEFT JOIN Ecosystems e           ON p.EcosystemID = e.EcosystemID
        LEFT JOIN Namespaces ns     ON p.NamespaceID = ns.NamespaceID
        LEFT JOIN Names n           ON p.NameID = n.NameID
        LEFT JOIN Versions v        ON p.VersionID = v.VersionID
        LEFT JOIN Qualifiers q      ON p.QualifierID = q.QualifierID
        LEFT JOIN QualifierKeys qk  ON q.KeyID = qk.KeyID
        LEFT JOIN QualifierValues qv ON q.ValueID = qv.ValueID
        LEFT JOIN Subpaths sp       ON p.SubpathID = sp.SubpathID
        LEFT JOIN Licenses l        ON p.LicenseID = l.LicenseID
        LEFT JOIN PURLs pu          ON p.PURLID = pu.PURLID
        LEFT JOIN RepositoryURLs ru ON p.RepositoryURLID = ru.RepositoryURLID
        LEFT JOIN HomepageURLs hu   ON p.HomepageURLID = hu.HomepageURLID
        LEFT JOIN Descriptions d    ON p.DescriptionID = d.DescriptionID

        LEFT JOIN Dependencies dep  ON dep.DependsOnPackageID = p.PackageID
        LEFT JOIN Packages p2       ON dep.PackageID = p2.PackageID
        LEFT JOIN Ecosystems e2     ON p2.EcosystemID = e2.EcosystemID
        LEFT JOIN Namespaces ns2    ON p2.NamespaceID = ns2.NamespaceID
        LEFT JOIN Names n2          ON p2.NameID = n2.NameID
        LEFT JOIN Versions v2       ON p2.VersionID = v2.VersionID
        LEFT JOIN Licenses l2       ON p2.LicenseID = l2.LicenseID

        GROUP BY
            e.Ecosystem, ns.Namespace, n.Name,
            pu.PURL, ru.RepositoryURL, hu.HomepageURL, d.Description

        ORDER BY MIN(p.PackageID);
        """
        return self.con.execute(query).fetchall()
    # ========== DEPENDENCIES ==========
    
    def insertDependency(self, packageID, dependsOnPackageID):
        """Create a dependency relationship between two packages"""
        if not packageID or not dependsOnPackageID:
            print("Both PackageID and DependsOnPackageID are required")
            return False
        
        # Check if relationship already exists
        exists = self.con.execute("""
            SELECT 1 FROM Dependencies 
            WHERE PackageID=? AND DependsOnPackageID=?
        """, (packageID, dependsOnPackageID)).fetchone()
        
        if not exists:
            self.con.execute("""
                INSERT INTO Dependencies (PackageID, DependsOnPackageID) 
                VALUES(?, ?)
            """, (packageID, dependsOnPackageID))
            return True
        return False
    
    def getDependencies(self, packageID):
        """Get all packages that a given package depends on"""
        query = """
        SELECT 
            d.DependsOnPackageID,
            pu.PURLs,
            e.Ecosystem,
            ns.Namespace,
            n.Name,
            v.Version,
            l.License,
            de.Descriptions
        FROM Dependencies d
        JOIN Packages p ON d.DependsOnPackageID = p.PackageID
        JOIN Ecosystems e ON p.EcosystemID = e.EcosystemID
        JOIN Names n ON p.NameID = n.NameID
        LEFT JOIN Namespaces ns ON p.NamespaceID = ns.NamespaceID
        LEFT JOIN Versions v ON p.VersionID = v.VersionID
        LEFT JOIN Licenses l ON p.LicenseID = l.LicenseID
        LEFT JOIN PURLs pu ON p.PURLID = pu.PURLID
        LEFT JOIN Descriptions de ON p.DescriptionID = de.DescriptionID
        WHERE d.PackageID = ?
        """
        return self.con.execute(query, (packageID,)).fetchall()
    
    def getDependents(self, packageID):
        """Get all packages that depend on a given package"""
        query = """
        SELECT 
            d.PackageID,
            pu.PURLs,
            e.Ecosystem,
            ns.Namespace,
            n.Name,
            v.Version,
            l.License,
            de.Descriptions
        FROM Dependencies d
        JOIN Packages p ON d.PackageID = p.PackageID
        JOIN Ecosystems e ON p.EcosystemID = e.EcosystemID
        JOIN Names n ON p.NameID = n.NameID
        LEFT JOIN Namespaces ns ON p.NamespaceID = ns.NamespaceID
        LEFT JOIN Versions v ON p.VersionID = v.VersionID
        LEFT JOIN Licenses l ON p.LicenseID = l.LicenseID
        LEFT JOIN PURLs pu ON p.PURLID = pu.PURLID
        LEFT JOIN Descriptions de ON p.DescriptionID = de.DescriptionID
        WHERE d.DependsOnPackageID = ?
        """
        return self.con.execute(query, (packageID,)).fetchall()
    
    # ========== LICENSE QUERIES ==========
    
    def getLicenseDistribution(self):
        """Get count of packages per license"""
        query = """
        SELECT 
            COALESCE(l.License, 'No License') as License,
            COUNT(*) as PackageCount
        FROM Packages p
        LEFT JOIN Licenses l ON p.LicenseID = l.LicenseID
        GROUP BY l.License
        ORDER BY PackageCount DESC
        """
        self.con.query(query).show()
        return self.con.execute(query).fetchall()
    
    def getPackagesByLicense(self, license):
        """Get all packages with a specific license"""
        query = """
        SELECT 
            p.PackageID,
            pu.PURLs,
            e.Ecosystem,
            ns.Namespace,
            n.Name,
            v.Version,
            de.Descriptions
        FROM Packages p
        JOIN Ecosystems e ON p.EcosystemID = e.EcosystemID
        JOIN Names n ON p.NameID = n.NameID
        LEFT JOIN Namespaces ns ON p.NamespaceID = ns.NamespaceID
        LEFT JOIN Versions v ON p.VersionID = v.VersionID
        LEFT JOIN PURLs pu ON p.PURLID = pu.PURLID
        LEFT JOIN Descriptions de ON p.DescriptionID = de.DescriptionID
        JOIN Licenses l ON p.LicenseID = l.LicenseID
        WHERE l.License = ?
        ORDER BY t.Ecosystem, n.Name
        """
        return self.con.execute(query, (license,)).fetchall()
    
    def getDependentTreeWithLicenses(self, packageID):
        """Get full DEPENDENT tree with licenses (packages that depend on this package)"""
        query = """
        WITH RECURSIVE dep_tree AS (
            -- Base case: the starting package
            SELECT 
                p.PackageID,
                pu.PURLs,
                e.Ecosystem,
                n.Name,
                v.Version,
                l.License,
                de.Descriptions,
                CAST(p.PackageID AS VARCHAR) as PackageIDPath,
                CAST(n.Name AS VARCHAR) as Path,
                CAST(NULL AS INTEGER) as ParentPackageID  -- Track immediate parent
            FROM Packages p
            JOIN Ecosystems e ON p.EcosystemID = e.EcosystemID
            JOIN Names n ON p.NameID = n.NameID
            LEFT JOIN Versions v ON p.VersionID = v.VersionID
            LEFT JOIN Licenses l ON p.LicenseID = l.LicenseID
            LEFT JOIN PURLs pu ON p.PURLID = pu.PURLID
            LEFT JOIN Descriptions de ON p.DescriptionID = de.DescriptionID
            WHERE p.PackageID = ?
            
            UNION ALL
            
            -- Recursive case: get packages that depend on this one
            SELECT 
                p.PackageID,
                pu.PURLs,
                e.Ecosystem,
                n.Name,
                v.Version,
                l.License,
                de.Descriptions,
                dt.PackageIDPath || '->' || CAST(p.PackageID AS VARCHAR),
                dt.Path || ' -> ' || n.Name,
                dt.PackageID as ParentPackageID  -- Store the parent PackageID
            FROM dep_tree dt
            JOIN Dependencies d ON dt.PackageID = d.DependsOnPackageID
            JOIN Packages p ON d.PackageID = p.PackageID
            JOIN Ecosystems e ON p.EcosystemID = e.EcosystemID
            JOIN Names n ON p.NameID = n.NameID
            LEFT JOIN Versions v ON p.VersionID = v.VersionID
            LEFT JOIN Licenses l ON p.LicenseID = l.LicenseID
            LEFT JOIN PURLs pu ON p.PURLID = pu.PURLID
            LEFT JOIN Descriptions de ON p.DescriptionID = de.DescriptionID
            WHERE INSTR(dt.PackageIDPath, CAST(p.PackageID AS VARCHAR)) = 0
        )
        SELECT 
            PackageID,
            Ecosystem,
            Name,
            Version,
            License,
            Path,
            ParentPackageID
        FROM dep_tree
        ORDER BY Name
        """
        return self.con.execute(query, (packageID,)).fetchall()
    
    # ========== UTILITY ==========
    
    def close(self):
        """Close database connection"""
        self.con.close()
    
    def commit(self):
        """Commit changes (DuckDB auto-commits, but this is here for compatibility)"""
        self.con.commit()