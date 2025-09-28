# routes/main.py
from flask import Blueprint, jsonify, render_template
from models import Carteira, PosicaoAtivo, TipoAtivo
from collections import defaultdict
from decimal import Decimal
from services.api_service import buscar_cotacao_atual

bp_inicio = Blueprint("main", __name__)


@bp_inicio.route("/")
def dashboard():
    posicoes = PosicaoAtivo.query.all()

    dados_dashboard = []

    total_investido = 0
    total_valor_atual = 0
    total_valor_mercado = Decimal("0")  # NOVO TOTAL
    carteira_valor_atual = 0

    # Dicionários para dados dos gráficos
    distribuicao_por_tipo = defaultdict(float)
    distribuicao_por_segmento = defaultdict(float)

    for posicao in posicoes:
        if posicao.custodia == 0:
            continue

        valor_investido_posicao = posicao.custodia * posicao.preco_medio
        total_investido += valor_investido_posicao

        # 2. BUSCA COTAÇÃO ATUAL
        preco_atual = buscar_cotacao_atual(posicao.ativo.ticker)

        # 3. CÁLCULO DE VALORIZAÇÃO
        valor_mercado_posicao = posicao.custodia * preco_atual
        total_valor_mercado += valor_mercado_posicao

        lucro_prejuizo_posicao = valor_mercado_posicao - valor_investido_posicao

        # Evita divisão por zero se o valor investido for 0
        if valor_investido_posicao == 0:
            percentual_valorizacao = Decimal("0")
        else:
            percentual_valorizacao = (
                lucro_prejuizo_posicao / valor_investido_posicao
            ) * Decimal("100")

        # O valor atual será o valor investido por enquanto
        valor_atual_posicao = valor_investido_posicao
        total_valor_atual += valor_atual_posicao

        # Adiciona o valor investido para o tipo e segmento correspondentes
        tipo_ativo = TipoAtivo.query.get(posicao.ativo.tipo_id)
        segmento_ativo = posicao.ativo.segmento

        # 4. AGRUPAMENTO PARA GRÁFICOS
        distribuicao_por_tipo[tipo_ativo] += float(
            valor_mercado_posicao
        )  # Use float para o gráfico, mas mantenha Decimal no resto
        distribuicao_por_segmento[segmento_ativo] += float(valor_investido_posicao)

        # 5. ADICIONA OS DADOS À LISTA
        dados_dashboard.append(
            {
                "ticker": posicao.ativo.ticker,
                "nome": posicao.ativo.nome,
                "custodia": posicao.custodia,
                "preco_medio": posicao.preco_medio,
                "preco_atual": preco_atual,  # NOVO
                "valor_investido": valor_investido_posicao,
                "valor_mercado": valor_mercado_posicao,  # NOVO
                "lucro_prejuizo": lucro_prejuizo_posicao,  # NOVO
                "percentual_valorizacao": percentual_valorizacao,  # NOVO
                "tipo": tipo_ativo,
            }
        )
    lucro_prejuizo_total = total_valor_mercado - total_investido

    print(dados_dashboard)
    print()

    lucro_prejuizo = total_valor_atual - total_investido

    print(total_investido, lucro_prejuizo)
    # Renderize o template, passando os NOVOS dados
    return render_template(
        "index.html",
        total_valor_mercado=total_valor_mercado,
        lucro_prejuizo=lucro_prejuizo_total,
        dados=dados_dashboard,
        total_investido=total_investido,
        # Dados para os gráficos
        distribuicao_por_tipo=distribuicao_por_tipo,
        distribuicao_por_segmento=distribuicao_por_segmento,
        carteira_valor_atual=carteira_valor_atual,
    )


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
