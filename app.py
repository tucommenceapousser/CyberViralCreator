import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "viral-content-generator-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///viral_content.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32MB max file size
app.config["UPLOAD_FOLDER"] = "static/uploads"

# Initialize extensions
db.init_app(app)

with app.app_context():
    import models
    db.create_all()

    # Create required directories if they don't exist
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
