from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import joinedload

import os
import io
import base64
import uuid
import pandas as pd
from datetime import datetime
from PIL import Image
from fpdf import FPDF
from io import BytesIO
from flask import render_template, make_response
from xhtml2pdf import pisa
import io
from models import db, Admin, Employee, Visitor
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
from flask import jsonify
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# ----------------------------------------
# App Config
# ----------------------------------------
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_fallback_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'static/uploads/')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
migrate = Migrate(app, db)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  
from datetime import timedelta

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
# ----------------------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def send_notification_email(to_email, visitor_name, visit_reason):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = "New Visitor at Pyrotech"

        body = f"""
        Hello,

        You have a new visitor:

        Name: {visitor_name}
        Purpose: {visit_reason}

        Please attend to them at the reception.

        Regards,
        Visitor Management System
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent to:", to_email)

    except Exception as e:
        print("❌ Email sending failed:", e)
import os
from flask import current_app

def link_callback(uri, rel):
    if uri.startswith('/static/'):
        path = os.path.join(current_app.root_path, uri[1:])  # remove leading "/"
        return path
    return uri


# Initialize DB
db.init_app(app)

# ----------------------------------------
# Create Tables + Default Data
# ----------------------------------------

with app.app_context():
    db.create_all()

    if not Admin.query.filter_by(username="admin").first():
        pw_hash = generate_password_hash("admin")
        db.session.add(Admin(username="admin", password=pw_hash))

    if not Admin.query.filter_by(username="admin1").first():
        pw_hash = generate_password_hash("admin123")
        db.session.add(Admin(username="admin1", password=pw_hash))

    if Employee.query.count() == 0:
        emp1 = Employee(name="Prachi Menaria", email="prachi@example.com", designation="Software Engineer")
        emp2 = Employee(name="Yash Mehta", email="yash@example.com", designation="HR Manager")
        db.session.add_all([emp1, emp2])
    
    db.session.commit()

# ----------------------------------------
# Routes
# ----------------------------------------

@app.route('/')
def index():
    return render_template('welcome.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

@app.route('/visitor_form', methods=['GET', 'POST'])
def visitor_form():
    employees = Employee.query.all()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        visit_reason = request.form.get('visit_reason', '').strip()
        employee_id = request.form.get('employee_id', '').strip()

        # ✅ Server-side validation
        if not name or not email or not phone or not visit_reason or not employee_id:
            flash("All fields are required.", "error")
            return redirect(url_for('visitor_form'))

        webcam_data = request.form.get('photo')  # Base64 data
        uploaded_file = request.files.get('image')  # File from input

        filename = None

        if webcam_data:
            try:
                header, encoded = webcam_data.split(",", 1)
                image_data = base64.b64decode(encoded)
                image_pil = Image.open(BytesIO(image_data))
                filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                image_pil.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                print("Webcam capture failed:", e)

        elif uploaded_file and uploaded_file.filename:
            filename = secure_filename(uploaded_file.filename)
            uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_visitor = Visitor(
            name=name,
            email=email,
            phone=phone,
            visit_reason=visit_reason,
            employee_id=employee_id,
            photo=filename
        )

        db.session.add(new_visitor)
        db.session.commit()

        # ✅ Send email to selected employee
        emp = Employee.query.get(employee_id)
        if emp and emp.email:
            send_notification_email(emp.email, name, visit_reason)

        return redirect(url_for('visitor_pass', visitor_id=new_visitor.id))

    return render_template('visitor_form.html', employees=employees)



@app.route('/success')
def success():
    return "✅ Visitor registered successfully."

@app.route('/get_employees')
def get_employees():
    employees = Employee.query.all()
    return jsonify([
        {'id': e.id, 'name': e.name, 'designation': e.designation}
        for e in employees
    ])

@app.route('/generate_pass/<int:visitor_id>')
def generate_pass(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    employee = Employee.query.get(visitor.employee_id)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Visitor Pass", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Name: {visitor.name}", ln=True)
    pdf.cell(200, 10, txt=f"Email: {visitor.email}", ln=True)
    pdf.cell(200, 10, txt=f"Phone: {visitor.phone}", ln=True)
    pdf.cell(200, 10, txt=f"Purpose: {visitor.visit_reason}", ln=True)
    pdf.cell(200, 10, txt=f"Date: {visitor.date.strftime('%d %B %Y')}", ln=True)
    pdf.cell(200, 10, txt=f"Employee to Visit: {employee.name}", ln=True)

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    return send_file(pdf_output, download_name='visitor_pass.pdf', as_attachment=True)

@app.route('/visitor_pass/<int:visitor_id>')
def visitor_pass(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    return render_template('visitor_pass.html', visitor=visitor)

@app.route('/checkout/<int:visitor_id>', methods=['POST'])
def checkout_visitor(visitor_id):
    v = Visitor.query.get_or_404(visitor_id)
    v.checkout = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('admin_dashboard'))
@app.route('/edit_visitor/<int:visitor_id>', methods=['GET', 'POST'])
def edit_visitor(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    employees = Employee.query.all()

    if request.method == 'POST':
        visitor.name = request.form.get('name')
        visitor.email = request.form.get('email')
        visitor.phone = request.form.get('phone')
        visitor.visit_reason = request.form.get('visit_reason')
        visitor.employee_id = request.form.get('employee_id')

        new_photo = request.files.get('photo')

        if new_photo and new_photo.filename:
            filename = secure_filename(new_photo.filename)
            extension = filename.rsplit('.', 1)[-1].lower()
            unique_name = f"{secure_filename(visitor.name)}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
            new_photo.save(photo_path)

            # Optional: delete old photo file from system (if needed)
            old_photo_path = os.path.join('static', visitor.photo)
            if os.path.exists(old_photo_path):
                os.remove(old_photo_path)

            # Save only relative path in DB
            visitor.photo = os.path.relpath(photo_path, start='static')

        db.session.commit()
        flash("Visitor updated successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_visitor.html', visitor=visitor, employees=employees)

@app.route('/export_excel')
def export_excel():
    rows = []
    for v in Visitor.query.options(db.joinedload(Visitor.employee)).all():
        rows.append({
          'Visitor Name':    v.name,
          'Email':           v.email,
          'Phone':           v.phone,
          'Employee Name':   v.employee.name if v.employee else '',
          'Designation':     v.employee.designation if v.employee else '',
          'Visit Reason':    v.visit_reason,
          'Check‑in Time':   v.checkin_str,
          'Check‑out Time':  v.checkout_str,
        })
    df = pd.DataFrame(rows)
    out = BytesIO()
    df.to_excel(out, index=False)
    out.seek(0)
    return send_file(out, download_name="visitor_logs.xlsx", as_attachment=True)


@app.route('/print_pdf')
def print_pdf():
    visitors = Visitor.query.options(db.joinedload(Visitor.employee)).all()
    rendered = render_template("pdf_template.html", visitors=visitors)
    
    # Convert HTML to PDF
    pdf = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.StringIO(rendered), dest=pdf)
    
    if pisa_status.err:
        return "PDF generation failed", 500
    
    pdf.seek(0)
    return send_file(pdf, download_name="visitor_logs.pdf", as_attachment=True)
from flask import make_response
from xhtml2pdf import pisa
import io

@app.route('/visitor_pass_pdf/<int:visitor_id>')
def visitor_pass_pdf(visitor_id):
    visitor = Visitor.query.get_or_404(visitor_id)
    rendered = render_template("visitorpass_pdf.html", visitor=visitor)

    # Encode HTML properly for PDF rendering
    pdf = io.BytesIO()
    pisa_status = pisa.CreatePDF(io.BytesIO(rendered.encode("utf-8")), dest=pdf)

    if pisa_status.err:
        return "PDF generation failed", 500

    pdf.seek(0)
    return send_file(pdf, download_name=f"{visitor.name}_VisitorPass.pdf", as_attachment=True)

@app.route('/adminlogin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id             # Store admin ID, not username
            session['role'] = 'admin'
            session.permanent = True

            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('admin_login.html')

from werkzeug.security import generate_password_hash
from flask import redirect, url_for, session, request, render_template, flash

@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    admin_id = session.get('admin_id')
    if not admin_id:
        flash("Please log in first.", "error")
        return redirect(url_for('admin_login'))
    current_admin = Admin.query.get(admin_id)

    if not current_admin or not current_admin.is_superadmin:
        flash("You are not authorized to create a new admin.", "error")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_super = 'is_super' in request.form

        if Admin.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        else:
            hashed_password = generate_password_hash(password)
            new_admin = Admin(
                username=username,
                password=hashed_password,
                is_superadmin=is_super
            )
            db.session.add(new_admin)
            db.session.commit()
            flash('New admin created successfully!', 'success')
            return redirect(url_for('admin_dashboard'))

    return render_template('create_admin.html')



@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        designation = request.form.get("designation")
        department = request.form.get("department")

        new_emp = Employee(
            name=name,
            email=email,
            designation=designation,
            department=department
        )
        db.session.add(new_emp)
        db.session.commit()

        # ✅ Send welcome email to the new employee
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = email
            msg['Subject'] = "Welcome to Pyrotech!"

            body = f"""
            Hello {name},

            You have been added to the Pyrotech Visitor Management System as an employee.

            Your designation: {designation}
            Department: {department or "N/A"}

            You will now receive notifications when a visitor is assigned to you.

            Regards,
            Pyrotech Visitor Management System
            """
            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
            server.quit()
            print("✅ Welcome email sent to:", email)

        except Exception as e:
            print("❌ Failed to send welcome email:", e)

        flash("Employee added successfully.", "success")
        return redirect(url_for("admin_dashboard"))  # or admin_dashboard if needed

    return render_template("add_employee.html")

@app.route('/delete_visitor/<int:visitor_id>', methods=['POST'])
def delete_visitor(visitor_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    visitor = Visitor.query.get_or_404(visitor_id)
    db.session.delete(visitor)
    db.session.commit()
    flash('Visitor deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

# Keep only this one:
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))
    current_admin = Admin.query.get(session['admin_id'])


    if not current_admin:
        return redirect(url_for('unauthorized'))

    visitors = (Visitor.query
                .options(joinedload(Visitor.employee))
                .order_by(Visitor.checkin.desc())
                .all())
    employees = Employee.query.order_by(Employee.name).all()

    return render_template(
        'admin_dashboard.html',
        visitors=visitors,
        employees=employees,
        current_admin=current_admin
    )


@app.route('/unauthorized')
def unauthorized():
    return "<h2>❌ You are not authorized to access this page.</h2>", 403
@app.route('/delete_logs', methods=['POST'])
def delete_logs():
    Visitor.query.delete()
    db.session.commit()
    return '', 204
@app.route('/delete_selected_logs', methods=['POST'])
def delete_selected_logs():
    try:
        data = request.get_json()
        ids = data.get('ids', []) if data else []

        valid_ids = []
        for visitor_id in ids:
            if visitor_id is not None and str(visitor_id).isdigit():
                valid_ids.append(int(visitor_id))

        if not valid_ids:
            return jsonify({"error": "No valid IDs provided"}), 400

        for visitor_id in valid_ids:
            visitor = db.session.get(Visitor, visitor_id)
            if visitor:
                db.session.delete(visitor)

        db.session.commit()
        return '', 204

    except Exception as e:
        print("Error in delete_selected_logs:", e)
        return jsonify({"error": "Server error"}), 500


@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    session.pop('role', None)

    flash('Logged out.', 'info')
    return redirect(url_for('admin_login'))

# ----------------------------------------
# Run the App
# ----------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
