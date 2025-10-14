# nameVerDoc Documentation

Creates a database that saves and manages npm package names and versions. Here, a duckdb database is used.

## createTables()

Creates new Tables for Names, Versions and for the Join Table Packages.

## createSequences()

Creates Sequences for the Primary Keys of Names and Packages.

## showAllTables()

Prints the contents of all tables on the console

## insertPackage(name, version)
name        -> str
version     -> str

Inserts the name and version (semantic versioning) in their respective tables and saves their corresponding IDs together in Packages. Does nothing if the given name-version combination is already saved. Shows all the tables after.

## getNameIndex(name)
name        -> str

returns     -> int

Returns the nameID of the Parameter. If the name is not yet saved in the Names table, the name will be added to Names and that ID will be returned.

## getVersionIndex(version)
version     -> list[int]

returns     -> int

Returns a unique versionID that is calculated using the versions' components. If the version is not yet saved, the version and its calculated versionID will be added to the Versions table.

## compareVersions(versionID1, versionID2)
versionID1  -> int
versionID2  -> int

Compares two versions by their versionIDs and returns the latest one.

