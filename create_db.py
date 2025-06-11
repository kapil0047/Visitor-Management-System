import sqlite3
import os

# Ensure directory exists
os.makedirs("database", exist_ok=True)

conn = sqlite3.connect("database/visitors.db")
c = conn.cursor()

# Visitors table
c.execute('''
CREATE TABLE IF NOT EXISTS visitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    employee_id INTEGER,
    visit_reason TEXT,
    photo TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Employees table
c.execute('''
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    designation TEXT NOT NULL
)
''')

# Insert sample employees
c.execute("INSERT INTO employees (name, designation) VALUES ('Amit Sharma', 'HR')")
c.execute("INSERT INTO employees (name, designation) VALUES ('Neha Patel', 'IT Head')")
c.execute("INSERT INTO employees (name, designation) VALUES ('Raj Meena', 'Admin Officer')")

conn.commit()
conn.close()
