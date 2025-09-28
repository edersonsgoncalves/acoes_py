from decimal import Decimal
from models import db, PosicaoAtivo, Operacao


def recalcular_posicao(operacao: Operacao):
    """
    Recalcula a custódia e o preço médio de um ativo para uma carteira específica
    após a realização de uma nova operação (que deve estar salva no DB).
    """

    # Use 'with_for_update()' se você estiver em um ambiente concorrido para travar a linha
    # Mas vamos manter o básico por enquanto para evitar Deadlocks.
    posicao = PosicaoAtivo.query.filter_by(
        ativo_id=operacao.ativo_id, carteira_id=operacao.carteira_id
    ).first()

    # -----------------------------------------------------
    # GARANTINDO TIPOS DE DADOS
    # -----------------------------------------------------

    # É fundamental garantir que todos os cálculos usem o tipo Decimal
    quantidade_operacao = operacao.quantidade
    valor_operacao = operacao.valor_total

    # Se não houver posição, cria uma nova
    if not posicao:
        posicao = PosicaoAtivo(
            ativo_id=operacao.ativo_id,
            carteira_id=operacao.carteira_id,
            custodia=Decimal("0"),
            preco_medio=Decimal("0"),
        )
        db.session.add(posicao)
        # Não precisa de db.session.flush() aqui se você vai commitar no final.

    custodia_antiga = posicao.custodia
    preco_medio_antigo = posicao.preco_medio

    # Assumindo: 1 = Compra, 2 = Venda (Ajuste conforme seus IDs de TipoOperacao)
    is_compra = operacao.tipo_id == 1
    is_venda = operacao.tipo_id == 2

    # 1. CÁLCULO DA NOVA CUSTÓDIA (Quantidade)
    if is_compra:
        nova_custodia = custodia_antiga + quantidade_operacao
    elif is_venda:
        nova_custodia = custodia_antiga - quantidade_operacao
    else:
        # Se não for compra nem venda, apenas retorna (ou trate outros tipos)
        return

    # 2. CÁLCULO DO NOVO PREÇO MÉDIO
    if is_compra:
        # Investimento total anterior: (Quantidade * Preço Médio)
        valor_total_antigo = custodia_antiga * preco_medio_antigo

        # O novo preço médio é o total investido (antigo + novo) dividido pela nova custódia
        if nova_custodia > 0:
            novo_preco_medio = (valor_total_antigo + valor_operacao) / nova_custodia
            posicao.preco_medio = novo_preco_medio
        else:
            # Posição zerada, mesmo sendo compra (situação rara, mas seguro)
            posicao.preco_medio = Decimal("0")

    # 3. ATUALIZAÇÃO FINAL

    # Garante que a custódia nunca seja negativa (situação que deve ser tratada na validação,
    # mas aqui é a última linha de defesa).
    if nova_custodia <= 0:
        posicao.custodia = Decimal("0")
        posicao.preco_medio = Decimal("0")
    else:
        posicao.custodia = nova_custodia

    # Salva as alterações na sessão
    db.session.add(posicao)  # Adiciona ou atualiza a posição

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar a posição no DB: {e}")
        raise  # Levanta a exceção para que a rota possa capturar


def recalcular_posicao_historico(ativo_id: int, carteira_id: int):
    """
    Recalcula a posição de um ativo/carteira do zero, com base em todas as operações.
    É fundamental para garantir a correção após qualquer EDIÇÃO ou EXCLUSÃO de operação.
    """

    # 1. Busca TODAS as operações ordenadas por data para garantir o cálculo correto
    operacoes = (
        Operacao.query.filter_by(ativo_id=ativo_id, carteira_id=carteira_id)
        .order_by(Operacao.data.asc(), Operacao.registro.asc())
        .all()
    )

    # Inicializa variáveis
    custodia_atual = Decimal("0")
    preco_medio_atual = Decimal("0")

    # 2. Looping para recalcular o histórico do zero
    for op in operacoes:
        quantidade = op.quantidade
        valor_total = op.valor_total
        is_compra = op.tipo_id == 1  # Assumindo 1 = Compra (Verifique seus IDs!)

        if is_compra:
            # Valor investido anteriormente
            valor_total_antigo = custodia_atual * preco_medio_atual

            nova_custodia = custodia_atual + quantidade

            if nova_custodia > 0:
                # Novo Preço Médio = (Total investido antes + Valor da nova compra) / Nova Custódia
                novo_preco_medio = (valor_total_antigo + valor_total) / nova_custodia
                preco_medio_atual = novo_preco_medio
                custodia_atual = nova_custodia

        else:  # Venda ou Outro tipo
            # A venda apenas diminui a custódia. O preço médio não muda.
            nova_custodia = custodia_atual - quantidade

            if nova_custodia <= 0:
                custodia_atual = Decimal("0")
                preco_medio_atual = Decimal("0")
            else:
                custodia_atual = nova_custodia

    # 3. SALVA OU CRIA A POSIÇÃO FINAL

    posicao = PosicaoAtivo.query.filter_by(
        ativo_id=ativo_id, carteira_id=carteira_id
    ).first()

    if not posicao:
        posicao = PosicaoAtivo(ativo_id=ativo_id, carteira_id=carteira_id)
        db.session.add(posicao)

    posicao.custodia = custodia_atual
    posicao.preco_medio = preco_medio_atual

    db.session.commit()
