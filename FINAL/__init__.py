from flask import Flask
from models import db
from migrations_runtime import update_numero_marchand_length()

def create_app():
    app = Flask(__name__)

    # config
    app.config.from_object("config.Config")

    # init extensions
    db.init_app(app)

    with app.app_context():
        update_numero_marchand_length()

    return app
