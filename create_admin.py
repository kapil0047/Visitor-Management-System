from db import app
from models import db, Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    if Admin.query.filter_by(username='admin').first() is None:
        admin = Admin(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print('✅ Admin created')
    else:
        print('⚠️ Admin already exists')
