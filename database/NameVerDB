import duckdb

# !!! Put file location here
con = duckdb.connect("duckDBtest/packages.db")

#### SETUP: (TODO: Organize better later on)
#To create tables run createTables()

def createTables():
    # Create Table for Package Names
    con.execute("CREATE TABLE IF NOT EXISTS Names (nameID INTEGER PRIMARY KEY, name VARCHAR)")
    # Create Table for Versions
    con.execute("CREATE TABLE IF NOT EXISTS Versions (versionID INTEGER PRIMARY KEY, verMajor INTEGER, verMinor INTEGER, verPatch INTEGER)")
    # Create Join Table
    con.execute("CREATE TABLE IF NOT EXISTS Packages (nameID INTEGER, versionID INTEGER, FOREIGN KEY (nameID) REFERENCES Names(nameID), FOREIGN KEY (versionID) REFERENCES Versions(versionID))")
    createSequences()

def createSequences():
    con.execute("CREATE SEQUENCE IF NOT EXISTS sequ_names START 1")


#####

def showAllTables():
	con.table("Names").show()
	con.table("Packages").show()
	con.table("Versions").show()

#Name as String, Version as String "1.1.1"
def insertPackage(name, version):
	versionList = version.split(".")
	versionIndex = getVersionIndex(versionList)
	nameIndex = getNameIndex(name)
	
	saved = con.execute("SELECT * FROM Packages WHERE nameID=? AND versionID=?", (nameIndex, versionIndex)).fetchone()
	if saved is None:
		con.execute("INSERT INTO Packages VALUES(?, ?)", (nameIndex, versionIndex))
	else:
		print("Package already saved")
	con.table("Packages").show()

def getNameIndex(name):
	saved = con.execute("SELECT * FROM Names WHERE name=?", (name,)).fetchone()
	if saved is None:
		con.execute("INSERT INTO Names VALUES (nextval('sequ_names'), ?)", (name,))
	return con.execute("SELECT nameID FROM Names WHERE name=?", (name,)).fetchone()[0]

#version = Version as List
#TODO check datatype of version
def getVersionIndex(version):
	vMaj = int(version[0])
	vMin = int(version[1])
	vPat = int(version[2])
	versionID = vMaj * 1000000 + vMin * 1000 + int(version[2])
	
	saved = con.execute("SELECT * FROM Versions WHERE versionID=?", (versionID,)).fetchone()
	if saved is None:
		con.execute("INSERT INTO Versions VALUES (?, ?, ?, ?)", (versionID, vMaj, vMin, vPat))
	
	return versionID

# "Pregenerated" Version table makes comparison easy - Versions are ordered, versionID corresponds with the lateness of the version:
def compareVersions(versionID1, versionID2):
	if versionID1 > versionID2:
		return versionID1
	if versionID2 > versionID1:
		return versionID2
	else:
		print("same Version!")
