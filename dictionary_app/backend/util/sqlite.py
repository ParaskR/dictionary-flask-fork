import sqlite3


class Database:

    def __init__(self, db):
        try:
            self.conn = sqlite3.connect(db)
            self.conn.execute("PRAGMA foreign_keys = 1")

        except Exception as e:
            print(e)

    def post_query(self, query, values):
        cur = self.conn.cursor()
        try:
            if len(values) > 0:
                cur.execute(query, values)
            else:
                cur.execute(query)
            self.conn.commit()
        except Exception as e:
            print("ERROR: ", str(e))

    def selection_query(self, query):
        cur = self.conn.cursor()
        data = []
        try:
            cur.execute(query)
            data = cur.fetchall()
            self.conn.commit()
        except Exception as e:
            print("ERROR: ", str(e))
        return data
