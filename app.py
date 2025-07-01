from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
import os
import time
import smtplib
from email.message import EmailMessage
from datetime import datetime
from fpdf import FPDF

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Folder paths
UPLOAD_FOLDER = 'static/uploads'
PDF_FOLDER = 'static/passes'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

# Email configuration
SENDER_EMAIL = 'menariaprachi0@gmail.com'
APP_PASSWORD = 'abgn tmln amyj eqnf'

def send_email(to_email, visitor_name):
    msg = EmailMessage()
    msg['Subject'] = 'Visitor Check-In Notification'
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg.set_content(f"Hello,\n\n{visitor_name} has arrived to meet you.\n\n- Pyrotech Visitor System")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(SENDER_EMAIL, APP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print("Email sending failed:", e)

def generate_visitor_pass(name, checkin_time, photo_path, employee_name):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, "PYROTECH VISITOR PASS", ln=True, align='C')

    pdf.set_draw_color(80, 80, 80)
    pdf.rect(10, 25, 190, 100)

    image_path = os.path.join('static', photo_path)
    if os.path.exists(image_path):
        pdf.image(image_path, x=15, y=35, w=40, h=40)

    pdf.set_xy(60, 35)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 10, "Name:")
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, name, ln=True)

    pdf.set_x(60)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, "Check-in Time:")
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, checkin_time, ln=True)

    pdf.set_x(60)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, "Employee to Meet:")
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, employee_name, ln=True)

    pdf.set_x(60)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(50, 10, "Status:")
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, "Approved", ln=True)

    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Thank you for visiting Pyrotech!", ln=True, align='C')

    filename = f"Visitor_Pass_{int(time.time())}.pdf"
    filepath = os.path.join(PDF_FOLDER, filename)
    pdf.output(filepath)

    return filename

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

    db_photo_path = os.path.join('uploads', unique_filename).replace("\\", "/")
    photo_url = url_for('static', filename=db_photo_path)
    checkin_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect('database/visitors.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        INSERT INTO visitors (name, email, phone, employee_id, visit_reason, photo, checkin_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, email, phone, employee_id, visit_reason, db_photo_path, checkin_time))
    conn.commit()

    # Get employee name for PDF
    c.execute("SELECT name, email FROM employees WHERE id = ?", (employee_id,))
    emp = c.fetchone()
    employee_name = emp['name'] if emp else "N/A"
    employee_email = emp['email'] if emp and 'email' in emp.keys() else None
    conn.close()

    if employee_email:
        send_email(employee_email, name)

    pdf_filename = generate_visitor_pass(name, checkin_time, db_photo_path, employee_name)

    return render_template("success.html", name=name, checkin_time=checkin_time, photo_url=photo_url, pdf_filename=pdf_filename)

@app.route('/download/<filename>')
def download_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename, as_attachment=True)

@app.route('/success')
def success():
    return render_template('success.html')

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

    # fetch distinct employee names for filter dropdown
    c.execute("SELECT DISTINCT name FROM employees")
    employees = [row[0] for row in c.fetchall()]
    conn.close()

    return render_template('admin.html', visitors=visitors, employees=employees)



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

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

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
        flash("Password updated successfully." if updated else "Username not found.")
        return redirect(url_for('login'))
    return render_template('reset_password.html')

if __name__ == '__main__':
    app.run(debug=True)
