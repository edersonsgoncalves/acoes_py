# routes/main.py
from flask import Blueprint, jsonify, render_template
from models import Carteira

bp_inicio = Blueprint("main", __name__)


@bp_inicio.route("/")
def home():
    return render_template("index.html")


# "<p>Sistema de Gestão de Ativos</p><br/><a href='/operacao/adicionar'>Inserir Operações</a>"


@bp_inicio.route("/carteiras")
def listar_carteiras():
    carteiras = Carteira.query.all()
    return jsonify(
        [
            {"id": c.id, "nome": c.nome, "data_criacao": c.data_criacao.isoformat()}
            for c in carteiras
        ]
    )
