from flask import Flask
import os
from dotenv import load_dotenv
from models import db
from routes.operacoes import bp_operacoes
from routes.ativos import bp_ativos
from routes.main import bp_inicio

from flask_migrate import Migrate


load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DB_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
    BRAPI_API_KEY = os.getenv("BRAPI_API_KEY")
    BRAPI_API_BASE_URL = "https://brapi.dev/api/quote/"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Registra seus Blueprints
    app.register_blueprint(bp_operacoes)
    app.register_blueprint(bp_ativos)
    app.register_blueprint(bp_inicio)

    Migrate(app, db)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
