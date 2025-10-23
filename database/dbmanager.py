import duckdb

class DBManager:
    def __init__(self):
        self.con = duckdb.connect("database/dbjson.db")
        self.con.execute("CREATE TABLE IF NOT EXISTS purls (purl JSON);")

    def insert_purl(self, purl_json):
        self.con.execute("INSERT INTO purls (purl) VALUES (?)", (purl_json,))
