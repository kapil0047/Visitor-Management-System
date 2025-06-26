from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import sqlite3
import os
import time
import smtplib
from email.message import EmailMessage
from datetime import datetime
from werkzeug.security import generate_password_hash
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for sessions

# Upload folder setup
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Email configuration
SENDER_EMAIL = 'menariaprachi0@gmail.com'
APP_PASSWORD = 'abgn tmln amyj eqnf'

def send_email(to_email, visitor_name):
    msg = EmailMessage()
    msg['Subject'] = 'Visitor Check-In Notification'
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg.set_content(f"Hello,\n\n{visitor_name} has arrived to meet you.\n\n- Pyrotech Visitor System")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SENDER_EMAIL, APP_PASSWORD)
        smtp.send_message(msg)

# Welcome page
@app.route('/')
def welcome():
    return render_template('welcome.html')

# Visitor form
@app.route('/visitor')
def visitor_form():
    conn = sqlite3.connect('database/visitors.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM employees")
    employees = c.fetchall()
    conn.close()
    return render_template('index.html', employees=employees)

# Check-in route
@app.route('/checkin', methods=['POST'])
def checkin():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    employee_id = request.form['employee_id']
    visit_reason = request.form['visit_reason']
    photo_file = request.files['photo']

    filename = secure_filename(photo_file.filename)
    unique_filename = f"{int(time.time())}_{filename}"
    photo_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    photo_file.save(photo_path)

    # Save for HTML usage
    photo = os.path.join('uploads', unique_filename).replace("\\", "/")
    photo_url = url_for('static', filename=photo)
    print("Photo to save in DB:", photo)

    checkin_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Save to DB
    conn = sqlite3.connect('database/visitors.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        INSERT INTO visitors (name, email, phone, employee_id, visit_reason, photo)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (name, email, phone, employee_id, visit_reason, photo))
    conn.commit()

    # Notify employee
    c.execute("SELECT email FROM employees WHERE id = ?", (employee_id,))
    result = c.fetchone()
    conn.close()

    if result and result['email']:
        send_email(result['email'], name)

    return render_template("success.html", name=name, checkin_time=checkin_time, photo_url=photo_url)

# 🔐 Admin login with secure password hash check
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database/visitors.db')
        c = conn.cursor()
        c.execute("SELECT password FROM admins WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()

        if result and check_password_hash(result[0], password):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash("Invalid credentials.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/success')
def success():
    return render_template('success.html')


# Admin dashboard
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database/visitors.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT v.*, e.name AS employee_name, e.designation 
        FROM visitors v 
        LEFT JOIN employees e ON v.employee_id = e.id
    """)
    visitors = c.fetchall()
    conn.close()
    return render_template('admin.html', visitors=visitors)

@app.route('/admin/visitors')
def visitor_log():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database/visitors.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT v.*, e.name AS employee_name, e.designation 
        FROM visitors v 
        LEFT JOIN employees e ON v.employee_id = e.id
        ORDER BY v.id DESC
    """)
    visitors = c.fetchall()
    conn.close()

    return render_template('visitor_log.html', visitors=visitors)


# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

from werkzeug.security import generate_password_hash

@app.route('/register', methods=['GET', 'POST'])
def register_admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect('database/visitors.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
            flash("✅ New admin registered!")
        except sqlite3.IntegrityError:
            flash("⚠️ Username already exists.")
        conn.close()
        return redirect(url_for('register_admin'))

    return render_template('register.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for('reset_password'))

        hashed_password = generate_password_hash(new_password)

        conn = sqlite3.connect('database/visitors.db')
        c = conn.cursor()
        c.execute("UPDATE admins SET password = ? WHERE username = ?", (hashed_password, username))
        conn.commit()
        updated = c.rowcount
        conn.close()

        if updated:
            flash("Password updated successfully.")
        else:
            flash("Username not found.")

        return redirect(url_for('login'))

    return render_template('reset_password.html')

# Run app
if __name__ == '__main__':
    app.run(debug=True)
