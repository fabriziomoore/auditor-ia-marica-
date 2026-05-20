import datetime
import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from google import genai

# Configuração da API do Gemini puxando dos segredos do GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# CONFIGURAÇÕES DO TELEGRAM FIXADAS
TELEGRAM_BOT_TOKEN = "8653685065:AAED9cTe0NkqMKbFYdBJi_gu76tr0QLLS8M"
TELEGRAM_CHAT_ID = "1230723925"


def enviar_alerta_telegram(mensagem):
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown",
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass


def raspar_portal_marica_real():
    print("🌐 Acessando o Portal da Transparência de Maricá ao vivo...")
    url = "https://marica.rj.gov.br"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)

        # Salva o HTML bruto do site de Maricá para você inspecionar o que o robô recebeu
        with open("diagnostico_portal.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("💾 O conteúdo bruto do portal foi salvo em 'diagnostico_portal.txt'")

        if response.status_code != 200:
            raise Exception(
                f"O servidor de Maricá respondeu com erro crítico. Status: {response.status_code}"
            )

        soup = BeautifulSoup(response.text, "html.parser")

        # Procura por qualquer tabela gerada pelo e-Cidade
        tabela = soup.find("table") or soup.find(class_="table")

        if not tabela:
            raise Exception(
                "O site carregou, mas a tabela de contratos não foi encontrada na estrutura visual. Veja o arquivo 'diagnostico_portal.txt'."
            )

        contratos_reais = []
        linhas = tabela.find_all("tr")

        for linha in lines[1:4]:
            colunas = linha.find_all("td")
            if len(colunas) >= 4:
                item = {
                    "numeroContrato": colunas.text.strip(),
                    "nomeRazaoSocialFornecedor": colunas.text.strip(),
                    "objeto": colunas.text.strip(),
                    "valorInicial": colunas.text.strip(),
                }
                contratos_reais.append(item)

        if not contratos_reais:
            raise Exception(
                "A tabela foi localizada, mas não continha linhas de contratos preenchidas."
            )

        return contratos_reais

    except Exception as e:
        erro_msg = f"❌ *INFORMAÇÃO DE COLETA*\nO robô tentou ler o site de Maricá.\n\n*Diagnóstico:* {str(e)}"
        print(erro_msg)
        enviar_alerta_telegram(erro_msg)
        raise e


# --- EXECUÇÃO DO PROCESSO ---
try:
    contratos = raspar_portal_marica_real()
    resultados = []

    enviar_alerta_telegram(
        "🔍 *AUDITOR IA MARICÁ*\nDados extraídos com sucesso. Iniciando auditoria real..."
    )

    for c in contratos:
        numero = c["numeroContrato"]
        fornecedor = c["nomeRazaoSocialFornecedor"]
        objeto = c["objeto"]
        valor = c["valorInicial"]

        prompt = f"Você é um auditor fiscal. Analise em 3 linhas os riscos do contrato real nº {numero} da empresa '{fornecedor}' no valor de R$ {valor} para o serviço '{objeto}'."

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            analise = response.text.strip()
        except Exception as e:
            analise = f"Falha na IA: {str(e)}"

        texto_card = (
            f"📄 *Contrato nº:* {numero}\n"
            f"🏢 *Empresa:* {fornecedor}\n"
            f"💰 *Valor:* R$ {valor}\n"
            f"🤖 *Análise Crítica:* {analise}"
        )
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
        time.sleep(5)

    df_final = pd.DataFrame(resultados)
    df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
    print("🏆 Planilha gerada com dados reais!")

except Exception as erro_geral:
    print(f"Execução encerrada para proteger o histórico: {erro_geral}")
