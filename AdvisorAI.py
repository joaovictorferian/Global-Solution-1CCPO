import requests

URL_COLAB = "https://alienable-chef-pueblo.ngrok-free.dev"

def recomendar_acao(evento_nome, categoria, severidade, atributos_afetados, opcoes_resposta):
    try:
        resposta = requests.post(
            f"{URL_COLAB}/recomendar",
            json={
                "evento_nome": evento_nome,
                "categoria": categoria,
                "severidade": severidade,
                "atributos_afetados": atributos_afetados,
                "opcoes_resposta": opcoes_resposta,
            },
            timeout=30,
        )
        if resposta.status_code == 200:
            return resposta.json()["recomendacao"]
        else:
            return "IA indisponível — servidor retornou erro."
    except requests.exceptions.ConnectionError:
        return "IA indisponível — Colab não está rodando."
    except requests.exceptions.Timeout:
        return "IA indisponível — tempo de resposta excedido."
    except Exception:
        return "IA indisponível — erro inesperado."