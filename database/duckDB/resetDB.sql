-- Drop tables first (in reverse order due to foreign keys)
DROP TABLE IF EXISTS Packages;
DROP TABLE IF EXISTS Qualifiers;
DROP TABLE IF EXISTS QualifierKeys;
DROP TABLE IF EXISTS QualifierValues;
DROP TABLE IF EXISTS Subpaths;
DROP TABLE IF EXISTS Versions;
DROP TABLE IF EXISTS Names;
DROP TABLE IF EXISTS Namespaces;
DROP TABLE IF EXISTS Types;

-- Drop sequences
DROP SEQUENCE IF EXISTS seq_types;
DROP SEQUENCE IF EXISTS seq_namespaces;
DROP SEQUENCE IF EXISTS seq_names;
DROP SEQUENCE IF EXISTS seq_versions;
DROP SEQUENCE IF EXISTS seq_qualifier_keys;
DROP SEQUENCE IF EXISTS seq_qualifier_values;
DROP SEQUENCE IF EXISTS seq_qualifiers;
DROP SEQUENCE IF EXISTS seq_subpaths;
DROP SEQUENCE IF EXISTS seq_packages;

-- Create sequences FIRST
CREATE SEQUENCE seq_types START 1;
CREATE SEQUENCE seq_namespaces START 1;
CREATE SEQUENCE seq_names START 1;
CREATE SEQUENCE seq_versions START 1;
CREATE SEQUENCE seq_qualifier_keys START 1;
CREATE SEQUENCE seq_qualifier_values START 1;
CREATE SEQUENCE seq_qualifiers START 1;
CREATE SEQUENCE seq_subpaths START 1;
CREATE SEQUENCE seq_packages START 1;

-- Now create tables with DEFAULT nextval()
CREATE TABLE Types (
    TypeID INTEGER PRIMARY KEY DEFAULT nextval('seq_types'), 
    Type VARCHAR NOT NULL UNIQUE
);

CREATE TABLE Namespaces (
    NamespaceID INTEGER PRIMARY KEY DEFAULT nextval('seq_namespaces'), 
    Namespace VARCHAR NOT NULL UNIQUE
);

CREATE TABLE Names (
    NameID INTEGER PRIMARY KEY DEFAULT nextval('seq_names'), 
    Name VARCHAR NOT NULL UNIQUE
);

CREATE TABLE Versions (
    VersionID INTEGER PRIMARY KEY DEFAULT nextval('seq_versions'),
    Version VARCHAR NOT NULL UNIQUE,
    Major INTEGER,
    Minor INTEGER,
    Patch VARCHAR
);

CREATE TABLE QualifierKeys (
    KeyID INTEGER PRIMARY KEY DEFAULT nextval('seq_qualifier_keys'),
    Key VARCHAR NOT NULL UNIQUE
);

CREATE TABLE QualifierValues (
    ValueID INTEGER PRIMARY KEY DEFAULT nextval('seq_qualifier_values'),
    Value VARCHAR NOT NULL UNIQUE
);

CREATE TABLE Qualifiers (
    QualifierID INTEGER PRIMARY KEY DEFAULT nextval('seq_qualifiers'),
    KeyID INTEGER NOT NULL,
    ValueID INTEGER NOT NULL,
    FOREIGN KEY (KeyID) REFERENCES QualifierKeys(KeyID),
    FOREIGN KEY (ValueID) REFERENCES QualifierValues(ValueID),
    UNIQUE(KeyID, ValueID)
);

CREATE TABLE Subpaths (
    SubpathID INTEGER PRIMARY KEY DEFAULT nextval('seq_subpaths'),
    Subpath VARCHAR NOT NULL UNIQUE
);

CREATE TABLE Packages (
    PackageID INTEGER PRIMARY KEY DEFAULT nextval('seq_packages'),
    TypeID INTEGER NOT NULL,
    NamespaceID INTEGER,
    NameID INTEGER NOT NULL,
    VersionID INTEGER,
    QualifierID INTEGER,
    SubpathID INTEGER,
    FOREIGN KEY (TypeID) REFERENCES Types(TypeID),
    FOREIGN KEY (NamespaceID) REFERENCES Namespaces(NamespaceID),
    FOREIGN KEY (NameID) REFERENCES Names(NameID), 
    FOREIGN KEY (VersionID) REFERENCES Versions(VersionID),
    FOREIGN KEY (QualifierID) REFERENCES Qualifiers(QualifierID),
    FOREIGN KEY (SubpathID) REFERENCES Subpaths(SubpathID),
    UNIQUE(TypeID, NamespaceID, NameID, VersionID, QualifierID, SubpathID)
);

-- Create indexes for better query performance
CREATE INDEX idx_packages_type ON Packages(TypeID);
CREATE INDEX idx_packages_namespace ON Packages(NamespaceID);
CREATE INDEX idx_packages_name ON Packages(NameID);
CREATE INDEX idx_packages_version ON Packages(VersionID);
CREATE INDEX idx_qualifiers_key ON Qualifiers(KeyID);
CREATE INDEX idx_qualifiers_value ON Qualifiers(ValueID);

SHOW TABLES;

-- Show row counts
SELECT 'Types' as table_name, COUNT(*) as row_count FROM Types
UNION ALL
SELECT 'Namespaces', COUNT(*) FROM Namespaces
UNION ALL
SELECT 'Names', COUNT(*) FROM Names
UNION ALL
SELECT 'Versions', COUNT(*) FROM Versions
UNION ALL
SELECT 'QualifierKeys', COUNT(*) FROM QualifierKeys
UNION ALL
SELECT 'QualifierValues', COUNT(*) FROM QualifierValues
UNION ALL
SELECT 'Qualifiers', COUNT(*) FROM Qualifiers
UNION ALL
SELECT 'Subpaths', COUNT(*) FROM Subpaths
UNION ALL
SELECT 'Packages', COUNT(*) FROM Packages;

-- Show detailed structure
DESCRIBE Packages;