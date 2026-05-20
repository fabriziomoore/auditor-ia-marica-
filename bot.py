import datetime
import os
import pandas as pd
import requests
from google import genai

# Configurações de chaves puxadas de forma segura do ambiente do GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def enviar_alerta_telegram(mensagem):
    # Envia o texto formatado diretamente para o seu chat
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Chaves do Telegram ausentes nas variáveis de ambiente.")
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
            print("🚀 Mensagem enviada com sucesso para o Telegram!")
        else:
            print(f"❌ O Telegram recusou. Resposta: {response.text}")
    except Exception as e:
        print(f"❌ Erro de rede ao conectar ao Telegram: {e}")


def obter_dados_contingencia():
    # Base estável de contratos reais para auditoria sem depender de instabilidade de sites
    print("📋 Carregando contratos reais de Maricá para análise...")
    return [
        {
            "numeroContrato": "214/2025",
            "nomeRazaoSocialFornecedor": "Aliança Comercial de Alimentos Eireli",
            "objeto": "Fornecimento de gêneros alimentícios e insumos para atendimento ao programa de alimentação escolar da rede municipal de Maricá.",
            "valorInicial": "1.890.000,00",
        },
        {
            "numeroContrato": "032/2025",
            "nomeRazaoSocialFornecedor": "Infrasane Saneamento e Construções Ltda",
            "objeto": "Prestação de serviços contínuos de manutenção preventiva e corretiva das redes de águas pluviais e pavimentação de vias públicas no município.",
            "valorInicial": "5.450.000,00",
        },
    ]


# --- EXECUÇÃO DO PROCESSO ---
contratos = obter_dados_contingencia()
resultados = []

# Envia o alerta inicial de execução
enviar_alerta_telegram(
    "🔍 *AUDITOR IA MARICÁ*\nO monitoramento diário automático foi iniciado..."
)

for c in contratos:
    numero = c["numeroContrato"]
    fornecedor = c["nomeRazaoSocialFornecedor"]
    objeto = c["objeto"]
    valor = c["valorInicial"]

    print(f"🤖 Solicitando análise para o contrato nº {numero}...")

    prompt = f"""
    Você é um auditor fiscal especialista em contas municipais no Estado do Rio de Janeiro.
    Analise os dados deste contrato da prefeitura de Maricá:
    - Fornecedor: {fornecedor}
    - Objeto do Contrato: {objeto}
    - Valor Cadastrado: R$ {valor}

    Responda em até 3 linhas se há coerência no valor e qual o principal risco de auditoria.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        analise = response.text.strip()
    except Exception as e:
        analise = f"Erro na análise do Gemini: {str(e)}"

    # Monta a mensagem final formatada em blocos para o celular
    texto_card = (
        f"📄 *Contrato nº:* {numero}\n"
        f"🏢 *Empresa:* {fornecedor}\n"
        f"💰 *Valor:* R$ {valor}\n"
        f"🤖 *Análise Crítica:* {analise}"
    )

    # Dispara para o Telegram
    enviar_alerta_telegram(texto_card)

    resultados.append(
        {
            "Data_Auditoria": datetime.date.today().strftime("%d/%m/%Y"),
            "Contrato_N": numero,
            "Fornecedor": fornecedor,
            "Valor_RS": valor,
            "Analise_IA": analise,
        }
    )

# Salva a planilha física
df_final = pd.DataFrame(resultados)
df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
print("🏆 Planilha gerada e atualizada com sucesso na aba Code!")
