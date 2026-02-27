import sqlite3
import json

try:
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user")
    rows = cursor.fetchall()
    users = [dict(r) for r in rows]
    print("USERS:", json.dumps(users, indent=2))
except Exception as e:
    print(f"Error: {e}")
