import os
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import shutil

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

# Create required directories
os.makedirs('instance', exist_ok=True)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs('static/translations', exist_ok=True)  # Ensure translations directory exists

# Set proper permissions for database directory
db_path = os.path.join('instance', 'viral_content.db')
if os.path.exists(db_path):
    os.chmod(db_path, 0o666)
    os.chmod('instance', 0o777)

# Cleanup function for temporary files
def cleanup_old_files():
    """Clean up files older than 24 hours"""
    uploads_dir = app.config["UPLOAD_FOLDER"]
    if os.path.exists(uploads_dir):
        current_time = time.time()
        for filename in os.listdir(uploads_dir):
            filepath = os.path.join(uploads_dir, filename)
            # If file is older than 24 hours, remove it
            if os.path.isfile(filepath):
                if os.stat(filepath).st_mtime < (current_time - 86400):
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass

# Initialize extensions
db.init_app(app)

with app.app_context():
    import models
    db.create_all()
    cleanup_old_files()  # Clean up old files on startup
