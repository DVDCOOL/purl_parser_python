import duckdb
import userInteractionWithPackageDB as uidb

con = duckdb.connect(uidb.dbPath)

uidb.insertPackage([
    ["test", "1.0"],
    ["test", "2.3.1"],
    ["bigPackage", "2.1.1"]])