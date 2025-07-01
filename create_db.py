import sqlite3
import os
from werkzeug.security import generate_password_hash

# Ensure the database directory exists
os.makedirs("database", exist_ok=True)

# Connect to DB
conn = sqlite3.connect("database/visitors.db")
c = conn.cursor()

# Create visitors table with checkin_time
c.execute('''
CREATE TABLE IF NOT EXISTS visitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    employee_id INTEGER,
    visit_reason TEXT,
    photo TEXT,
    checkin_time TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Create employees table
c.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    designation TEXT NOT NULL,
    email TEXT NOT NULL
)
''')

# Insert sample employees
c.execute("INSERT INTO employees (name, designation, email) VALUES ('Amit Sharma', 'HR', 'amit@pyrotech.com')")
c.execute("INSERT INTO employees (name, designation, email) VALUES ('Neha Patel', 'IT Head', 'neha@pyrotech.com')")
c.execute("INSERT INTO employees (name, designation, email) VALUES ('Raj Meena', 'Admin Officer', 'raj@pyrotech.com')")

# Create admins table
c.execute('''
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# Insert default admin
hashed_password = generate_password_hash('admin123')
try:
    c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', hashed_password))
except sqlite3.IntegrityError:
    print("Admin already exists.")

# Finalize
conn.commit()
conn.close()

print("✅ Database created with all required tables.")
