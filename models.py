from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = 'admin'
    
    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False) 
    def __repr__(self):
        return f"<Admin {self.username}>"

class Employee(db.Model):
    __tablename__ = 'employee'
    
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    email       = db.Column(db.String(150), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100))  # ✅ Add this line


    # so Visitor.employee works
    visitors    = db.relationship(
        'Visitor',
        backref='employee',
        lazy='select'      # or 'joined' if you prefer
    )

    def __repr__(self):
        return f"<Employee {self.name}>"

class Visitor(db.Model):
    __tablename__ = 'visitor'
    
    id           = db.Column(db.Integer, primary_key=True)
    name         = db.Column(db.String(100), nullable=False)
    email        = db.Column(db.String(120), nullable=True)
    phone        = db.Column(db.String(20), nullable=True)
    visit_reason = db.Column(db.Text, nullable=True)
    checkin      = db.Column(db.DateTime, default=datetime.utcnow)
    checkout     = db.Column(db.DateTime, nullable=True)
    photo        = db.Column(db.String(200), nullable=True)

    employee_id  = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)

    @property
    def checkin_str(self):
        return self.checkin.strftime('%Y-%m-%d %H:%M') if self.checkin else ''
    
    @property
    def checkout_str(self):
        return self.checkout.strftime('%Y-%m-%d %H:%M') if self.checkout else ''

    def __repr__(self):
        return f"<Visitor {self.name} @ {self.checkin}>"
