from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route('/')
def home():
    # Fetch employees from DB to show in dropdown
    conn = sqlite3.connect('database/visitors.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM employees")
    employees = c.fetchall()
    conn.close()
    return render_template('index.html', employees=employees)

@app.route('/checkin', methods=['POST'])
def checkin():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    employee_id = request.form['employee_id']
    visit_reason = request.form['visit_reason']
    photo = request.form['photo']

    conn = sqlite3.connect('database/visitors.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO visitors (name, email, phone, employee_id, visit_reason, photo)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (name, email, phone, employee_id, visit_reason, photo))
    conn.commit()
    conn.close()

    return render_template("success.html", name=name)

@app.route('/admin')
def admin():
    conn = sqlite3.connect('database/visitors.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT v.*, e.name AS employee_name, e.designation 
        FROM visitors v 
        LEFT JOIN employees e ON v.employee_id = e.id""")
    visitors = c.fetchall()
    conn.close()
    return render_template('admin.html', visitors=visitors)

if __name__ == '__main__':
    app.run(debug=True)
