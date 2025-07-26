import os
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey')
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Prachi@123@localhost/visitor_MSdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    PDF_FOLDER = os.path.join('static', 'passes')
