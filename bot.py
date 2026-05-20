import datetime
import os
import pandas as pd
import requests
from google import genai

# Configurações de chaves puxadas do repositório
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def enviar_alerta_telegram(mensagem):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Configurações do Telegram ausentes nos Secrets.")
        return

    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("🚀 Notificação enviada para o Telegram com sucesso!")
        else:
            # ISSO VAI NOS DIZER O ERRO REAL:
            print(
                f"❌ O Telegram recusou a mensagem! Código: {response.status_code}"
            )
            print(f"📝 Resposta do servidor do Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Erro de rede ao notificar Telegram: {e}")


def obter_dados_contingencia():
    return [
        {
            "numeroContrato": "214/2025",
            "nomeRazaoSocialFornecedor": "Aliança Comercial de Alimentos Eireli",
            "objeto": "Fornecimento de gêneros alimentícios para a merenda escolar de Maricá.",
            "valorInicial": "1.890.000,00",
        }
    ]


# Execução estruturada
contratos = obter_dados_contingencia()
resultados = []

enviar_alerta_telegram(
    "🔍 *AUDITOR IA MARICÁ*\nO monitoramento diário foi iniciado..."
)

for c in contratos:
    numero = c["numeroContrato"]
    fornecedor = c["nomeRazaoSocialFornecedor"]
    objeto = c["objeto"]
    valor = c["valorInicial"]

    prompt = f"Você é um auditor fiscal. Analise em 2 linhas se R$ {valor} faz sentido para o serviço '{objeto}' da empresa '{fornecedor}'. Foco em riscos."

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        analise = response.text.strip()
    except Exception as e:
        analise = f"Erro na IA: {str(e)}"

    texto_card = (
        f"📄 *Contrato nº:* {numero}\n"
        f"🏢 *Empresa:* {fornecedor}\n"
        f"💰 *Valor:* R$ {valor}\n"
        f"🤖 *Análise da IA:* {analise}"
    )
    enviar_alerta_telegram(texto_card)

    resultados.append(
        {
            "Data": datetime.date.today().strftime("%d/%m/%Y"),
            "Contrato_N": numero,
            "Fornecedor": fornecedor,
            "Valor_RS": valor,
            "Analise_IA": analise,
        }
    )

df_final = pd.DataFrame(resultados)
df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
print("🏆 Planilha gerada com sucesso!")
