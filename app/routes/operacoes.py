from flask import Blueprint, render_template, url_for, redirect, flash
from models import db, Operacao, TipoOperacao, Carteira, Ativo, StatusOperacao
from forms import OperacaoForm
from datetime import date


bp_operacoes = Blueprint("operacoes", __name__, url_prefix="/operacao")


@bp_operacoes.route("/", methods=["GET", "POST"])
def exibir_operacoes():
    operacoes = (
        db.session.execute(db.select(Operacao).order_by(Operacao.data)).scalars().all()
    )
    return render_template("operacoes_listar.html", operacoes=operacoes)


@bp_operacoes.route("/adicionar", methods=["GET", "POST"])
def adicionar_operacao():
    formulario = OperacaoForm()

    # Populando os campos SelectField
    tipos_operacao = db.session.execute(db.select(TipoOperacao)).scalars().all()
    formulario.tipo.choices = [(tipo.id, tipo.nome) for tipo in tipos_operacao]

    carteiras = db.session.execute(db.select(Carteira)).scalars().all()
    formulario.carteira.choices = [
        (carteira.id, carteira.nome) for carteira in carteiras
    ]

    ativos = db.session.execute(db.select(Ativo)).scalars().all()
    formulario.ativo.choices = [(ativo.id, ativo.ticker) for ativo in ativos]

    if formulario.validate_on_submit():
        try:
            # Pega os objetos completos com base nos IDs do formulário
            tipo_operacao_obj = db.session.get(TipoOperacao, formulario.tipo.data)
            ativo_obj = db.session.get(Ativo, formulario.ativo.data)
            carteira_obj = db.session.get(Carteira, formulario.carteira.data)

            # Pega a data do formulário
            if formulario.data_operacao.data is None:
                # Você pode escolher como tratar: usar data atual ou retornar erro
                data_operacao = date.today()  # Usa data atual se não for informada
                # Ou retornar um erro para o usuário:
                # formulario.data_operacao.errors.append('Data é obrigatória')
                # return render_template("operacoes_adicionar.html", formulario=formulario)
            else:
                data_operacao = formulario.data_operacao.data
            # Cria a nova operação com os dados do formulário

            # Lógica para definir o status dinamicamente, sem usar IDs fixos
            if data_operacao <= date.today():
                status_obj = db.session.execute(
                    db.select(StatusOperacao).filter_by(nome="Efetivada")
                ).scalar_one_or_none()
            else:
                status_obj = db.session.execute(
                    db.select(StatusOperacao).filter_by(nome="Agendada")
                ).scalar_one_or_none()

            if not status_obj:
                # Trata o caso de o status não existir no banco
                flash("Erro: Status de operação não encontrado.", "danger")
                return render_template(
                    "operacoes_adicionar.html", formulario=formulario
                )

            # Cria a nova operação com os dados do formulário
            nova_operacao = Operacao(
                data=data_operacao,
                tipo=tipo_operacao_obj,
                ativo=ativo_obj,
                carteira=carteira_obj,
                quantidade=formulario.quantidade.data,
                preco_unitario=formulario.preco_unitario.data,
                custos=formulario.custos.data,
                status=status_obj,
            )

            db.session.add(nova_operacao)
            db.session.commit()

            flash("Operação registrada com sucesso!", "success")

            return redirect(url_for("operacoes.adicionar_operacao"))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar a operação: {e}", "danger")

    # Se o formulário não for válido ou se a requisição for GET,
    # renderiza o template com o formulário
    return render_template("operacoes_adicionar.html", formulario=formulario)
