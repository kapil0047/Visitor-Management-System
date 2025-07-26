from flask import Flask
from flask_migrate import Migrate
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

app = create_app()
migrate = Migrate(app, db)
