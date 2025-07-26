from app import app
from models import db, Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    pw_hash = generate_password_hash("admin@123")
    if not Admin.query.filter_by(username="admin").first():
        db.session.add(Admin(username="admin", password=pw_hash))
        db.session.commit()
        print("✅ Admin user created!")
    else:
        print("⚠️ Admin user already exists.")
