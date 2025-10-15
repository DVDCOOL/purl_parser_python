# userInteractionWithPackageDB DOCUMENTATION

A simple interface to query the package database

## showAllTables()

Prints the contents of all tables on the console.

## insertPackage(packages)
packages    -> list[str]

Takes a package in a list[name, version] format and adds it to the Database. If the Package is already saved or has the wrong syntax, nothing will be done.

## getNameIndex(name)
name        -> str

returns     -> int

Returns the ID of the Parameter. If the name is not yet saved in the Names table, the name will be added to Names and that ID will be returned.

## isVersionSynCorrect(version)
version     -> str

returns     -> boolean, str

Returns True if the version fits the standard of 0.0.0 . If a version with no patch-number is given, a .0 will be added to the end of the version automatically. The version is returned as a string alongside the boolean.

## encodeVersion(version)
version     -> str

returns     -> str, str, str

Splits the version into its components and returns them.

## getVersionIndex(versionChar, major, minor, patch)
versionChar -> str
major       -> str
minor       -> str
patch       -> str

returns     -> int

Returns the ID of the version. If the version is not yet save in the Versions table, it will be added to the table and the corresponding ID will be returned.

## showAllPackages()

Shows an overview of all Packages saved in the Database

## findPackageOfVersion(version)
version     -> str

Finds all Packages of the given version

## findLatestVersionOfPackage(packageList)
packageList -> str

Finds the latest versions of the given package names and shows them.

## getConsoleInput()

Provides a small interface in the console to query the Database:
Command '1' -> Shows all saved packages
Command '2' -> Asks for a package and shows all Versions of it
Command '3' -> Shows all packages with the Version 1.0.0
Command '4' -> Asks for a number of packages and shows their latest versions.

