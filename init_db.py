from models import db
from flask import Flask
from config import Config

def init_db():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
