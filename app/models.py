from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

db = SQLAlchemy()


class PosicaoAtivo(db.Model):
    __tablename__ = "posicao_ativos"
    carteira_id = db.Column(db.Integer, db.ForeignKey("carteiras.id"), primary_key=True)
    ativo_id = db.Column(db.Integer, db.ForeignKey("ativos.id"), primary_key=True)
    custodia = db.Column(db.Numeric(15, 5), default=Decimal(0))
    preco_medio = db.Column(db.Numeric(15, 5), default=Decimal(0))

    carteira = db.relationship("Carteira", back_populates="posicoes_ativos")
    ativo = db.relationship("Ativo", back_populates="posicoes_ativos")


class Carteira(db.Model):
    __tablename__ = "carteiras"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), unique=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.now)

    posicoes_ativos = db.relationship("PosicaoAtivo", back_populates="carteira")
    operacoes = db.relationship("Operacao", back_populates="carteira")


class Ativo(db.Model):
    __tablename__ = "ativos"
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(7), unique=True, nullable=False)
    nome = db.Column(db.String(50), nullable=False)
    segmento = db.Column(db.String(100))

    posicoes_ativos = db.relationship("PosicaoAtivo", back_populates="ativo")
    operacoes = db.relationship("Operacao", back_populates="ativo")


class TipoOperacao(db.Model):
    __tablename__ = "tipos_operacoes"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.String(200))

    operacoes = db.relationship("Operacao", back_populates="tipo")


class StatusOperacao(db.Model):
    __tablename__ = "status_operacao"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(30), nullable=False, unique=True)

    operacoes = db.relationship("Operacao", back_populates="status_operacao")


class Operacao(db.Model):
    __tablename__ = "operacoes"
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, default=date.today)
    tipo_id = db.Column(db.Integer, db.ForeignKey("tipos_operacoes.id"), nullable=False)
    ativo_id = db.Column(db.Integer, db.ForeignKey("ativos.id"), nullable=False)
    carteira_id = db.Column(db.Integer, db.ForeignKey("carteiras.id"), nullable=False)
    quantidade = db.Column(db.Numeric(15, 5))
    preco_unitario = db.Column(db.Numeric(15, 5))
    custos = db.Column(db.Numeric(10, 2), default=Decimal(0))
    valor_total = db.Column(db.Numeric(15, 2))
    status_id = db.Column(
        db.Integer, db.ForeignKey("status_operacao.id"), nullable=False
    )
    registro = db.Column(db.DateTime, nullable=False, default=datetime.now)

    tipo = db.relationship("TipoOperacao", back_populates="operacoes")
    ativo = db.relationship("Ativo", back_populates="operacoes")
    carteira = db.relationship("Carteira", back_populates="operacoes")
    status_operacao = db.relationship("StatusOperacao", back_populates="operacoes")

    def __init__(
        self,
        data: date,
        tipo,
        ativo,
        carteira,
        quantidade,
        status,
        preco_unitario: Optional[Decimal] = Decimal(0),
        custos: Optional[Decimal] = Decimal(0),
    ):
        self.data = data
        self.tipo = tipo
        self.ativo = ativo
        self.carteira = carteira
        self.quantidade = quantidade
        self.preco_unitario = preco_unitario
        self.custos = custos

        # Atribui o objeto status, SQLAlchemy irá extrair o ID
        self.status_operacao = status

        # Garante que o valor total seja calculado corretamente
        self.valor_total = (self.quantidade * self.preco_unitario) + self.custos

    def __str__(self):
        return f"{self.data} | {self.tipo.nome} | {self.ativo.ticker} | {self.carteira.nome} | \
        ({self.quantidade} x {self.preco_unitario:.2f}) + {self.custos:.2f} = {self.valor_total}"
