-- Drop tables first (in reverse order due to foreign keys)
DROP TABLE IF EXISTS Dependencies;
DROP TABLE IF EXISTS Packages;
DROP TABLE IF EXISTS Qualifiers;
DROP TABLE IF EXISTS QualifierKeys;
DROP TABLE IF EXISTS QualifierValues;
DROP TABLE IF EXISTS Subpaths;
DROP TABLE IF EXISTS Versions;
DROP TABLE IF EXISTS Names;
DROP TABLE IF EXISTS Namespaces;
DROP TABLE IF EXISTS Types;
DROP TABLE IF EXISTS PURLs;
DROP TABLE IF EXISTS Licenses;
DROP TABLE IF EXISTS NormalizedLicenses;
DROP TABLE IF EXISTS RepositoryURLs;
DROP TABLE IF EXISTS HomepageURLs;
DROP TABLE IF EXISTS Descriptions;
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
DROP SEQUENCE IF EXISTS seq_dependencies;
DROP SEQUENCE IF EXISTS seq_licenses;
DROP SEQUENCE IF EXISTS seq_purls;
DROP SEQUENCE IF EXISTS seq_repository_urls;
DROP SEQUENCE IF EXISTS seq_homepage_urls;
DROP SEQUENCE IF EXISTS seq_descriptions;
DROP SEQUENCE IF EXISTS seq_normalized_licenses;

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
CREATE SEQUENCE seq_dependencies START 1;
CREATE SEQUENCE seq_licenses START 1;
CREATE SEQUENCE seq_purls START 1;
CREATE SEQUENCE seq_repository_urls START 1;
CREATE SEQUENCE seq_homepage_urls START 1;
CREATE SEQUENCE seq_descriptions START 1;
CREATE SEQUENCE seq_normalized_licenses START 1;

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

-- Create Licenses table


CREATE TABLE Licenses (
    LicenseID INTEGER PRIMARY KEY DEFAULT nextval('seq_licenses'),
    License VARCHAR NOT NULL UNIQUE  -- Can store SPDX identifiers or compound licenses
);

CREATE TABLE NormalizedLicenses (
    NormalizedLicenseID INTEGER PRIMARY KEY DEFAULT nextval('seq_licenses'),
    NormalizedLicense VARCHAR NOT NULL UNIQUE  -- Can store normalized license expressions
);

CREATE TABLE PURLs (
    PURLID INTEGER PRIMARY KEY DEFAULT nextval('seq_purls'),
    PURL VARCHAR NOT NULL UNIQUE  -- Can store the PURL (Package URL)
);

CREATE TABLE RepositoryURLs (
    RepositoryURLID INTEGER PRIMARY KEY DEFAULT nextval('seq_purls'),
    RepositoryURL VARCHAR NOT NULL UNIQUE  -- Can store the Repository URL
);

CREATE TABLE HomepageURLs (
    HomepageURLID INTEGER PRIMARY KEY DEFAULT nextval('seq_homepage_urls'),
    HomepageURL VARCHAR NOT NULL UNIQUE  -- Can store the Homepage URL
);

CREATE TABLE Descriptions (
    DescriptionID INTEGER PRIMARY KEY DEFAULT nextval('seq_descriptions'),
    Description TEXT NOT NULL UNIQUE  -- Can store the Description
);
-- Create Dependencies relationship table (many-to-many)



CREATE TABLE Packages (
    PackageID INTEGER PRIMARY KEY DEFAULT nextval('seq_packages'),
    TypeID INTEGER NOT NULL,
    NamespaceID INTEGER,
    NameID INTEGER NOT NULL,
    VersionID INTEGER,
    QualifierID INTEGER,
    SubpathID INTEGER,
    LicenseID INTEGER,
    NormalizedLicenseID INTEGER,
    PURLID INTEGER,
    RepositoryURLID INTEGER,
    HomepageURLID INTEGER,
    DescriptionID INTEGER,
    FOREIGN KEY (LicenseID) REFERENCES Licenses(LicenseID),
    FOREIGN KEY (NormalizedLicenseID) REFERENCES NormalizedLicenses(NormalizedLicenseID),
    FOREIGN KEY (TypeID) REFERENCES Types(TypeID),
    FOREIGN KEY (NamespaceID) REFERENCES Namespaces(NamespaceID),
    FOREIGN KEY (NameID) REFERENCES Names(NameID), 
    FOREIGN KEY (VersionID) REFERENCES Versions(VersionID),
    FOREIGN KEY (QualifierID) REFERENCES Qualifiers(QualifierID),
    FOREIGN KEY (SubpathID) REFERENCES Subpaths(SubpathID),
    FOREIGN KEY (PURLID) REFERENCES PURLs(PURLID),
    FOREIGN KEY (RepositoryURLID) REFERENCES RepositoryURLs(RepositoryURLID),
    FOREIGN KEY (HomepageURLID) REFERENCES HomepageURLs(HomepageURLID),
    FOREIGN KEY (DescriptionID) REFERENCES Descriptions(DescriptionID),
    UNIQUE(TypeID, NamespaceID, NameID, VersionID, QualifierID, SubpathID)
);

CREATE TABLE Dependencies (
    DependencyID INTEGER PRIMARY KEY DEFAULT nextval('seq_dependencies'),
    PackageID INTEGER NOT NULL,           -- The dependent package
    DependsOnPackageID INTEGER NOT NULL,  -- The package it depends on
    FOREIGN KEY (PackageID) REFERENCES Packages(PackageID),
    FOREIGN KEY (DependsOnPackageID) REFERENCES Packages(PackageID),
    UNIQUE(PackageID, DependsOnPackageID)
);


-- Create indexes for better query performance
CREATE INDEX idx_packages_type ON Packages(TypeID);
CREATE INDEX idx_packages_namespace ON Packages(NamespaceID);
CREATE INDEX idx_packages_name ON Packages(NameID);
CREATE INDEX idx_packages_version ON Packages(VersionID);
CREATE INDEX idx_qualifiers_key ON Qualifiers(KeyID);
CREATE INDEX idx_qualifiers_value ON Qualifiers(ValueID);
CREATE INDEX idx_packages_license ON Packages(LicenseID);
CREATE INDEX idx_packages_normalized_license ON Packages(NormalizedLicenseID);
CREATE INDEX idx_dependencies_package ON Dependencies(PackageID);
CREATE INDEX idx_dependencies_depends_on ON Dependencies(DependsOnPackageID);
CREATE INDEX idx_packages_repository_url ON Packages(RepositoryURLID);
CREATE INDEX idx_packages_homepage_url ON Packages(HomepageURLID);
CREATE INDEX idx_packages_purl ON Packages(PURLID);
CREATE INDEX idx_packages_description ON Packages(DescriptionID);

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
SELECT 'Packages', COUNT(*) FROM Packages
UNION ALL
SELECT 'PURLs', COUNT(*) FROM PURLs;

-- Show detailed structure
DESCRIBE Packages;