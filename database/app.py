import duckDB.functionsForDB as db
import DBConfigs as conf

def main():
	uidb = db.FunctionsForDB(conf.dbPath)
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
			uidb.showAllPackages()
		elif comand == "2":
			package = input("Package: ")
			uidb.findVersionsOfPackage(package)
		elif comand == "3":
			uidb.findPackageOfVersion("1.0.0")
		elif comand == "4":
			listOfPackages = input("Packages (separated by , and no spaces): ")
			uidb.findLatestVersionOfPackage(listOfPackages)
			
		else:
			print("Not command called: " + comand)
		comand = input("Command: ")

if __name__ == "__main__":
	main()