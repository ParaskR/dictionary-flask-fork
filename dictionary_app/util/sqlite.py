import sqlite3


class Database:

    def __init__(self):
        try:
            self.conn = sqlite3.connect("util/dictionary.db")
            self.conn.execute("PRAGMA foreign_keys = 1")
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            print(e)

    def post_query(self, query):
        cur = self.conn.cursor()
        try:
            cur.execute(query)
            self.conn.commit()
            self.conn.close()
            return True
        except Exception as e:
            print("ERROR: ", str(e))
            return False

    def selection_query(self, query):
        cur = self.conn.cursor()
        data = []
        try:
            cur.execute(query)
            data = cur.fetchall()
            self.conn.commit()
            self.conn.close()
        except Exception as e:
            print("ERROR: ", str(e))
        return data
