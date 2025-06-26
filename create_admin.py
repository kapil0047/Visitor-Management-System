import sqlite3
from werkzeug.security import generate_password_hash

# Connect to the database
conn = sqlite3.connect('database/visitors.db')
c = conn.cursor()

# Create the admins table
c.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

# Insert admin with hashed password
username = 'admin'
raw_password = 'admin123'  # Change this to your secure password
hashed_password = generate_password_hash(raw_password)

try:
    c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, hashed_password))
    conn.commit()
    print("✅ Admin added successfully.")
except sqlite3.IntegrityError:
    print("⚠️ Admin already exists.")

conn.close()
