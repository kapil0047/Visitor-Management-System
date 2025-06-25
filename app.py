from flask import Flask, render_template, request, url_for
from werkzeug.utils import secure_filename
import sqlite3
import os
import time
import smtplib
from email.message import EmailMessage
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/visitor')
def visitor_form():
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
    photo_file = request.files['photo']

    filename = secure_filename(photo_file.filename)
    unique_filename = f"{int(time.time())}_{filename}"
    photo_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    photo_file.save(photo_path)

    # Save for HTML usage
    photo = os.path.join('uploads', unique_filename).replace("\\", "/")
    photo_url = url_for('static', filename=photo)

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

@app.route('/admin')
def admin():
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

if __name__ == '__main__':
    app.run(debug=True)
