from flask_wtf import FlaskForm
from wtforms import DecimalField, DateField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange
from wtforms.widgets import NumberInput
from decimal import Decimal


class OperacaoForm(FlaskForm):
    # Campo para a data da operação
    data_operacao = DateField("Data da Operação", validators=[DataRequired()])

    # Campo para o ticker do ativo
    ativo = SelectField("Ticker do Ativo", validators=[DataRequired()])

    # Campo para o tipo de operação (compra, venda, etc.)
    tipo = SelectField("Tipo de Operação", validators=[DataRequired()])

    # Campo para a carteira
    carteira = SelectField("Nome da Carteira", validators=[DataRequired()])

    # Campo para a quantidade de ativos
    quantidade = DecimalField(
        "Quantidade",
        validators=[DataRequired(), NumberRange(min=0)],
        widget=NumberInput(step=1),
    )

    # Campo para o preço unitário
    preco_unitario = DecimalField(
        "Preço Unitário",
        validators=[DataRequired(), NumberRange(min=0)],
        widget=NumberInput(step=0.01),
    )

    # Campo para os custos (emolumentos, etc.)
    custos = DecimalField(
        "Custos",
        validators=[NumberRange(min=0)],
        default=Decimal(0),
        widget=NumberInput(step=0.01),
    )

    # Botão de envio do formulário
    submit = SubmitField("Registrar Operação")
