import sqlite3
from pathlib import Path
p = Path(__file__).parent.parent / "database" / "licenses.db"
try:
    conn = sqlite3.connect(p)
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key='admin_password'")
    row = cur.fetchone()
    if row:
        print(row[0])
    else:
        print('<no admin_password setting found>')
except Exception as e:
    print('ERROR:', e)
finally:
    try:
        conn.close()
    except:
        pass
