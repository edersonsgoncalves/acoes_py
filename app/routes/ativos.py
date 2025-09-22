from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    flash,
    abort,
    jsonify,
    current_app,
    request,
)
from models import db, Ativo
from forms import FormularioAtivo
from sqlalchemy.exc import IntegrityError


bp_ativos = Blueprint("ativos", __name__, url_prefix="/ativo")


@bp_ativos.route("/", methods=["GET", "POST"])
@bp_ativos.route("/<int:page>")
def exibir_ativos(page=1):
    PER_PAGE = 10
    query = db.select(Ativo)
    query = query.order_by(Ativo.nome.asc())
    ativos_paginados = db.paginate(query, page=page, per_page=PER_PAGE)
    return render_template(
        "ativos_listar.html",
        ativos=ativos_paginados.items,
        paginacao=ativos_paginados,
    )


@bp_ativos.route("/adicionar", methods=["GET", "POST"])
def adicionar_ativo():
    formulario = FormularioAtivo()

    if formulario.validate_on_submit():
        try:
            novo_ativo = Ativo(
                ticker=formulario.ativo_ticker.data,
                nome=formulario.nome.data,
                segmento=formulario.segmento.data,
            )
            db.session.add(novo_ativo)
            db.session.commit()

            mensagem = f'Ativo cadastrado com sucesso! <a href="{url_for('ativos.exibir_ativos')}">\
                Voltar para listagem de ativos</a>'
            flash(mensagem, "success")

            return redirect(url_for("ativos.adicionar_ativo"))

        except IntegrityError:
            db.session.rollback()  # Importante: faz rollback da transação
            flash("Erro: Ativo já está cadastrado!", "danger")
            return redirect(url_for("ativos.adicionar_ativo"))

        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao salvar o ativo: {e}", "danger")

    # Se o formulário não for válido ou se a requisição for GET,
    # renderiza o template com o formulário
    return render_template("ativos_adicionar.html", formulario=formulario)


@bp_ativos.route("/consultar_ticker/<string:ticker>", methods=["GET"])
def consultar_ticker(ticker):
    ticker = ticker.strip().upper()

    print(f"🔍 Consultando: {ticker}")

    api_key = current_app.config.get("SERPAPI_API_KEY")

    try:
        # Remove qualquer sufixo existente e adiciona :BVMF
        ticker_clean = (
            ticker.replace(".SAO", "").replace(".SA", "").replace(".BVMF", "")
        )
        ticker_query = f"{ticker_clean}:BVMF"

        print(f"📊 Query formatada: {ticker_query}")

        # Usa a biblioteca serpapi como você sugeriu
        from serpapi import GoogleSearch

        params = {
            "api_key": api_key,
            "engine": "google_finance",
            "q": ticker_query,
            "hl": "pt-br",
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        print(f"📋 Estrutura da resposta: {list(results.keys())}")

        # VERIFICA SE EXISTE SUMMARY
        if "summary" in results:
            summary = results["summary"]
            print(f"📊 Dados do summary: {summary}")

            nome = summary.get("title", "Não Encontrado")
            # Para segmento, podemos usar exchange + currency
            segmento = ""

            print(f"✅ Encontrado: {nome} - {segmento}")

            return jsonify(nome=nome, segmento=segmento)
        else:
            print("❌ Summary não encontrado na resposta")
            return jsonify(nome="Não Encontrado", segmento="Ticker inválido")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback

        traceback.print_exc()
        return jsonify(nome="Erro na consulta", segmento="Tente novamente")


@bp_ativos.route("/exibir/<int:ativo_id>", methods=["GET"])
def mostrar_ativo(ativo_id):
    ativo_especifico = db.session.get(Ativo, ativo_id)

    if not ativo_especifico:
        abort(404)

    return render_template("ativos_exibir.html", dados=ativo_especifico)


@bp_ativos.route("/editar/<int:ativo_id>", methods=["GET", "POST"])
def editar_ativo(ativo_id):
    ativo_para_editar = db.session.get(Ativo, ativo_id)

    if not ativo_para_editar:
        flash("Ativo não encontrado.", "danger")
        return redirect(url_for("ativos.exibir_ativos"))

    # Cria o formulário já com as choices
    formulario_ativo = FormularioAtivo()
    # ativo_ticker
    # nome
    # segmento

    # Agora sim, carrega os dados do objeto do banco
    if request.method == "GET":
        formulario_ativo.ativo_ticker.data = ativo_para_editar.ticker
        formulario_ativo.nome.data = ativo_para_editar.nome
        formulario_ativo.segmento.data = ativo_para_editar.segmento

    if formulario_ativo.validate_on_submit():
        # Lógica para atualizar a operação
        ativo_para_editar.ticker = formulario_ativo.ativo_ticker.data
        ativo_para_editar.nome = formulario_ativo.nome.data
        ativo_para_editar.segmento = formulario_ativo.segmento.data

        db.session.commit()
        flash("Operação atualizada com sucesso!", "success")
        return redirect(url_for("ativos.editar_ativo", ativo_id=ativo_id))

    return render_template(
        "ativos_editar.html", formulario=formulario_ativo, ativo=ativo_para_editar
    )


@bp_ativos.route("/deletar/<int:ativo_id>", methods=["POST"])
def deletar_ativo(ativo_id):
    ativo = db.session.get(Ativo, ativo_id)
    if not ativo:
        flash("Operação não encontrada.", "danger")
        return redirect(url_for("ativos.exibir_ativos"))

    try:
        db.session.delete(ativo)
        db.session.commit()
        flash("Ativo excluído com sucesso.", "success")
        return redirect(url_for("ativos.exibir_ativos"))
    except Exception as e:
        db.session.rollback()
        flash(f"Não foi possível remover o ativo selecionado: {e}", "danger")
        return redirect(url_for("ativos.exibir_ativos"))
