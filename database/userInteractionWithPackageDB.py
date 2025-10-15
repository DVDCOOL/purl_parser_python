import duckdb

# !!! Put file location here

dbPath = "database/duckDB/packages.db"

con = duckdb.connect(dbPath)


def showAllTables():
	con.table("Names").show()
	con.table("Packages").show()
	con.table("Versions").show()


#Name as String, Version as String "1.1.1"
def insertPackage(packages):
	for package in packages:
		versionCorrect, newVersion = isVersionSynCorrect(package[1])
		if versionCorrect:
			versionIndex = getVersionIndex(newVersion, *encodeVersion(newVersion))
			nameIndex = getNameIndex(package[0])
			
			saved = con.execute("SELECT * FROM Packages WHERE NameID=? AND VersionID=?", (nameIndex, versionIndex)).fetchone()
			if saved is None:
				con.execute("INSERT INTO Packages (NameID, VersionID) VALUES(?, ?)", (nameIndex, versionIndex))
			else:
				print("Package already saved")
		else:
			print("The Version has a wrong sytax")


def getNameIndex(name):
	saved = con.execute("SELECT * FROM Names WHERE Name=?", (name,)).fetchone()
	if saved is None:
		con.execute("INSERT INTO Names (name) VALUES (?)", (name,))
		saved = con.execute("SELECT * FROM Names WHERE Name=?", (name,)).fetchone()
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


def getVersionIndex(versionChar, major, minor, patch):

	saved = con.execute("SELECT * FROM Versions WHERE Version = ?", (versionChar,)).fetchone()
	if saved is None:

		con.execute("INSERT INTO Versions (Version, Major, Minor, Patch) VALUES (?, ?, ?, ?)", (versionChar, major, minor, patch))
		saved = con.execute("SELECT * FROM Versions WHERE Version = ?", (versionChar,)).fetchone()
	return saved[0]


def showAllPackages():
	con.sql("""SELECT Packages.PackageID, Names.Name, Versions.Version
            	FROM ((Packages 
            	INNER JOIN Names ON Packages.NameID = Names.NameID)
              	INNER JOIN Versions ON Packages.VersionID = Versions.VersionID)""").show()


def findVersionsOfPackage(package):
	con.sql(f"""SELECT Packages.PackageID, Names.Name, Versions.Version
            	FROM ((Packages 
            	INNER JOIN Names ON Packages.NameID = Names.NameID)
              	INNER JOIN Versions ON Packages.VersionID = Versions.VersionID)
            	WHERE Names.Name = '{package}'""").show()


def findPackageOfVersion(version):
	con.sql(f"""SELECT Packages.PackageID, Names.Name, Versions.Version
            	FROM ((Packages 
            	INNER JOIN Names ON Packages.NameID = Names.NameID)
              	INNER JOIN Versions ON Packages.VersionID = Versions.VersionID)
            	WHERE Versions.Version = '{version}'""").show()


def findLatestVersionOfPackage(packageList):
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

	con.sql(query).show()

 
def getConsoleInput():
	print("""
---------  PACKAGE DATABASE  ---------
Press the corresponding number for your need
1 - Print all the packages
2 - Find all versions available of a certain npm package
3 - Find all npm packages with version 1.0.0
4 - Find the last version of a number of npm packages
e - Exit
""")

	comand = ""
	comand = input("Command: ")
	while comand != "e":

		if comand == "1":
			showAllPackages()
		elif comand == "2":
			package = input("Package: ")
			findVersionsOfPackage(package)
		elif comand == "3":
			findPackageOfVersion("1.0.0")
		elif comand == "4":
			listOfPackages = input("Packages (separated by , and no spaces): ")
			findLatestVersionOfPackage(listOfPackages)
			
		else:
			print("Not command called: " + comand)
		comand = input("Command: ")
		

def main():
	getConsoleInput()


main()