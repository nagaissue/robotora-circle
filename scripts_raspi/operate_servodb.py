import os
import sqlite3

class DatabaseManager:
    # データベースの初期化
    def __init__(self, axis_number=5):
        base_dir = os.path.dirname(__file__)
        self.axis_number = axis_number
        db_name = "arm_data"+ str(self.axis_number) +".db"
        self.database = os.path.join(base_dir, db_name)
        conn = self.connect_db()
        cur = conn.cursor()
        colmuns = []
        for i in range(self.axis_number):
            colmuns.append("axis" + str(i+1) + " INTEGER check(axis" + str(i+1) + " >= -360 AND axis" + str(i+1) + " <= 360)")
        self.sql_table = "CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY AUTOINCREMENT, "+ ", ".join(colmuns) + ");"

        # 設定値テーブル(min/max)
        cur.execute(self.sql_table)
        conn.commit()
        conn.close()

    # データベース接続関数
    def connect_db(self):
        return sqlite3.connect(self.database)
    
    # データ挿入関数
    def insert_data(self, axis_angle):
        conn = self.connect_db()
        cur = conn.cursor()
        if self.count_data() == 0:
            cur.execute("drop table if exists data;")
            cur.execute(self.sql_table)
            conn.commit()
        colmuns = []
        for i in range(self.axis_number):
            colmuns.append("axis" + str(i+1))
        sql_insert = "INSERT INTO data ("+ ", ".join(colmuns) + ") VALUES (" + ", ".join(["?"] * len(colmuns)) + ");"
        cur.execute(sql_insert, axis_angle)
        conn.commit()
        conn.close()

    # データ更新関数
    def update_data(self, data_id=None, axis_angle=None):
        conn = self.connect_db()
        cur = conn.cursor()
        colmuns = []
        for i in range(self.axis_number):
            colmuns.append("axis" + str(i+1) + " = ?")
        sql_update = "UPDATE data SET " + ", ".join(colmuns) + " WHERE id = ?;"
        status = axis_angle + (data_id,)
        cur.execute(sql_update, status)
        conn.commit()
        conn.close()

    # データ削除関数
    def delete_data(self, data_id):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM data WHERE id = ?;", (data_id,))
        conn.commit()
        conn.close()

    # データ全件削除関数
    def delete_all_data(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM data;")
        conn.commit()
        conn.close()

    # データID検索関数
    def select_data_by_id(self, data_id):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM data WHERE id = ?;", (data_id,))
        row = cur.fetchone()
        conn.close()
        return row

    # データ全件取得関数
    def select_all_data(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM data;")
        rows = cur.fetchall()
        conn.close()
        return rows
    
    # データ件数取得関数
    def count_data(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM data;")
        count = cur.fetchone()[0]
        conn.close()
        return count

    def control_command(self):
        db = sqlite3.connect(self.database)
        cursor = db.cursor()
        while True:
            try:
                sql = input("SQL> ")
                if "exit" in sql or "quit" in sql:
                    db.close()
                    break
                cursor.execute(sql)
                if "select" in sql:
                    rows = cursor.fetchall()
                    for row in rows:
                        print(row)
                elif "exit" in sql or "quit" in sql:
                    db.close()
                    break
                db.commit()
            except Exception as e:
                print(f"Error: {e}")
                continue
