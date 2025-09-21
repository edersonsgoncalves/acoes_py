from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
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
                status_operacao=status_obj,
            )

            db.session.add(nova_operacao)
            db.session.commit()

            mensagem = f'Operação registrada com sucesso! <a href="{url_for('operacoes.exibir_operacoes')}">\
                Voltar para listagem de ativos</a>'
            flash(mensagem, "success")

            return redirect(url_for("operacoes.adicionar_operacao"))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar a operação: {e}", "danger")

    # Se o formulário não for válido ou se a requisição for GET,
    # renderiza o template com o formulário
    return render_template("operacoes_adicionar.html", formulario=formulario)


@bp_operacoes.route("/exibir/<int:operacao_id>", methods=["GET"])
def mostrar_operacao(operacao_id):
    operacao_especifica = db.session.get(Operacao, operacao_id)

    if not operacao_especifica:
        abort(404)

    return render_template("operacoes_exibir.html", dados=operacao_especifica)


@bp_operacoes.route("/editar/<int:operacao_id>", methods=["GET", "POST"])
def editar_operacao(operacao_id):
    operacao_para_editar = db.session.get(Operacao, operacao_id)

    if not operacao_para_editar:
        flash("Operação não encontrada.", "danger")
        return redirect(url_for("operacoes.listar_operacoes"))

    # Primeiro, popula os SelectFields com os dados do banco
    tipos_operacao = db.session.execute(db.select(TipoOperacao)).scalars().all()
    carteiras = db.session.execute(db.select(Carteira)).scalars().all()
    ativos = db.session.execute(db.select(Ativo)).scalars().all()

    # Cria o formulário já com as choices
    form = OperacaoForm()
    form.tipo.choices = [(tipo.id, tipo.nome) for tipo in tipos_operacao]
    form.carteira.choices = [(c.id, c.nome) for c in carteiras]
    form.ativo.choices = [(a.id, a.ticker) for a in ativos]

    # Agora sim, carrega os dados do objeto do banco
    if request.method == "GET":
        form.data_operacao.data = operacao_para_editar.data
        form.tipo.data = str(
            operacao_para_editar.tipo_id
        )  # Converta para string se necessário
        form.ativo.data = str(operacao_para_editar.ativo_id)
        form.carteira.data = str(operacao_para_editar.carteira_id)
        form.quantidade.data = operacao_para_editar.quantidade
        form.preco_unitario.data = operacao_para_editar.preco_unitario
        form.custos.data = operacao_para_editar.custos

    if form.validate_on_submit():
        # Lógica para atualizar a operação
        operacao_para_editar.data = form.data_operacao.data
        operacao_para_editar.tipo_id = int(form.tipo.data)
        operacao_para_editar.ativo_id = int(form.ativo.data)
        operacao_para_editar.carteira_id = int(form.carteira.data)
        operacao_para_editar.quantidade = form.quantidade.data
        operacao_para_editar.preco_unitario = form.preco_unitario.data
        operacao_para_editar.custos = form.custos.data
        operacao_para_editar.calcular_valor_total()

        db.session.commit()
        flash("Operação atualizada com sucesso!", "success")
        return redirect(url_for("operacoes.editar_operacao", operacao_id=operacao_id))

    return render_template(
        "operacoes_editar.html", formulario=form, operacao=operacao_para_editar
    )


@bp_operacoes.route("/deletar/<int:operacao_id>", methods=["POST"])
def deletar_operacao(operacao_id):
    operacao = db.session.get(Operacao, operacao_id)
    if not operacao:
        flash("Operação não encontrada.", "danger")
        return redirect(url_for("operacoes.exibir_operacoes"))

    try:
        db.session.delete(operacao)
        db.session.commit()
        flash("Operação excluída com sucesso.", "success")
        return redirect(url_for("operacoes.exibir_operacoes"))
    except Exception as e:
        db.session.rollback()
        flash(f"Não foi possível remover a operação selecionada: {e}", "danger")
        return redirect(url_for("operacoes.exibir_operacoes"))
