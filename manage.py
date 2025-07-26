from flask import Flask
from flask_migrate import Migrate
from models import db
from app import app  # importing your Flask app from app.py

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()
