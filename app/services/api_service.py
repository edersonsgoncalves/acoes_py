import requests
from flask import current_app  # Para acessar a API_KEY da configuração
from decimal import Decimal


def buscar_cotacao_atual(ticker: str) -> Decimal:
    """Busca a cotação atual de um ativo usando a API brapi."""

    # URL da API. Use o .format para inserir o Ticker
    url = f"{current_app.config['BRAPI_API_BASE_URL']}{ticker}"

    # Parâmetros de requisição (incluindo a API Key)
    params = {"token": current_app.config["BRAPI_API_KEY"]}

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()  # Lança exceção para erros HTTP
        data = response.json()

        # Estrutura da brapi (pode variar, cheque a documentação)
        if data and "results" in data and len(data["results"]) > 0:
            # O preço atual é o campo 'regularMarketPrice'
            preco_float = data["results"][0].get("regularMarketPrice", 0)

            return Decimal(
                str(preco_float)
            )  # Converte para Decimal para precisão financeira

        # Se não encontrar dados (ex: ticker inválido)
        return Decimal("0")

    except requests.exceptions.RequestException as e:
        # Trata erros de conexão ou Timeout
        print(f"Erro ao buscar cotação para {ticker}: {e}")
        return Decimal("0")
    except Exception as e:
        # Outros erros (JSON, etc)
        print(f"Erro inesperado na API para {ticker}: {e}")
        return Decimal("0")
