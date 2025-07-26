from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, send_file
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from fpdf import FPDF
from sqlalchemy.orm import joinedload
import os
import base64
import datetime
import io
from PIL import Image
from io import BytesIO
from datetime import datetime

from models import db, Admin, Employee, Visitor
import pandas as pd
from flask import send_file
import io
from io import BytesIO
from flask_migrate import Migrate
# ----------------------------------------
# App Config
# ----------------------------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# PostgreSQL Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Prachi123@localhost:5432/visitor_MSdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)
# File Upload Config
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        visit_reason = request.form.get('visit_reason')
        employee_id = request.form.get('employee_id')
        webcam_data = request.form.get('webcam_image')
        image = request.files.get('image')

        filename = None

        if webcam_data:
            try:
                header, encoded = webcam_data.split(",", 1)
                image_data = base64.b64decode(encoded)
                image_pil = Image.open(BytesIO(image_data))
                filename = f"{name}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                image_pil.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except Exception as e:
                print("Webcam image error:", e)

        elif image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
        new_visitor = Visitor(
            name=name,
            email=email,
            phone=phone,
            visit_reason=visit_reason,
            employee_id=employee_id,
            image_filename=filename  # this must match your model
        )
        db.session.add(new_visitor)
        db.session.commit()
        return redirect(url_for('visitor_pass', visitor_id=new_visitor.id))
    employees = Employee.query.all()
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


@app.route('/adminlogin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.username
            return redirect(url_for('admin_dashboard'))  # update this with your dashboard route
        else:
            flash('Invalid username or password', 'error')

    return render_template('admin_login.html')



@app.route('/edit_visitor/<int:id>', methods=['GET', 'POST'])
def edit_visitor(id):
    visitor = Visitor.query.get_or_404(id)
    if request.method == 'POST':
        visitor.name = request.form['name']
        visitor.email = request.form['email']
        # ... other fields
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_visitor.html', visitor=visitor)

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if session.get('role') != 'superuser':
        return "Unauthorized", 403
    if request.method == 'POST':
        name = request.form['name']
        designation = request.form['designation']
        new_emp = Employee(name=name, designation=designation)
        db.session.add(new_emp)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_employee.html')

# Keep only this one:
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('admin_login'))

    visitors = (Visitor.query
                .options(joinedload(Visitor.employee))
                .order_by(Visitor.checkin.desc())
                .all())
    employees = Employee.query.order_by(Employee.name).all()

    return render_template(
        'admin_dashboard.html',
        visitors=visitors,
        employees=employees
    )


@app.route('/delete_visitor/<int:visitor_id>', methods=['POST'])
def delete_visitor(visitor_id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    visitor = Visitor.query.get_or_404(visitor_id)
    db.session.delete(visitor)
    db.session.commit()
    flash('Visitor deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Logged out.', 'info')
    return redirect(url_for('admin_login'))

# ----------------------------------------
# Run the App
# ----------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
