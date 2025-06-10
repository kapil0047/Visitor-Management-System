import sqlite3

conn = sqlite3.connect('database/visitors.db')
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS visitors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        employee_to_meet TEXT,
        visit_reason TEXT,
        photo TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
