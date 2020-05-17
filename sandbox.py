class DbCursor:
    def __enter__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()

        return c

    def __exit__(self):
        self.conn.close()


with DbCursor() as c:
    c.execute("SELECT * FROM perms WHERE key_id=?", (request_key,))
    r = c.fetchall()

    print(r)
