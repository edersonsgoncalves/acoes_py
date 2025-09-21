# utils/database.py
from app.models import TipoOperacao, db


def carregar_dados_iniciais():
    tipos_operacao = [
        {"nome": "Compra", "descricao": "Aquisição de ativos"},
        {"nome": "Venda", "descricao": "Venda de ativos"},
        {"nome": "Dividendo", "descricao": "Recebimento de dividendos"},
        {"nome": "JCP", "descricao": "Juros sobre Capital Próprio"},
        {"nome": "Bonificação", "descricao": "Recebimento de ações bonificadas"},
        {"nome": "Desdobramento", "descricao": "Desdobramento de ações"},
        {"nome": "Grupamento", "descricao": "Grupamento de ações"},
    ]

    for tipo in tipos_operacao:
        if not TipoOperacao.query.filter_by(nome=tipo["nome"]).first():
            novo_tipo = TipoOperacao(**tipo)
            db.session.add(novo_tipo)

    db.session.commit()
