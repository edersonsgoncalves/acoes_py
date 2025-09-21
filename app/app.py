from flask import Flask
import os
from dotenv import load_dotenv
from models import db
from routes.operacoes import bp_operacoes
from routes.main import bp_inicio
from flask_migrate import Migrate


load_dotenv()

app = Flask(__name__)

app.register_blueprint(bp_operacoes)
app.register_blueprint(bp_inicio)

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

migrate = Migrate(app, db)
db.init_app(app)

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
