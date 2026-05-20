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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            raise Exception(f"O servidor de Maricá respondeu com erro crítico. Código de Status: {response.status_code}")
            
        soup = BeautifulSoup(response.text, "html.parser")
        tabela = soup.find("table") or soup.find(class_="table")
        
        if not tabela:
            raise Exception("O site de Maricá carregou, mas a tabela de contratos (e-Cidade) não foi encontrada ou mudou de estrutura.")

        contratos_reais = []
        linhas = tabela.find_all("tr")
        
        # Pega as primeiras linhas de dados reais contidas na tabela do site público
        for linha in lines[1:4]:
            colunas = linha.find_all("td")
            if len(colunas) >= 4:
                item = {
                    "numeroContrato": colunas[0].text.strip(),
                    "nomeRazaoSocialFornecedor": colunas[1].text.strip(),
                    "objeto": colunas[2].text.strip(),
                    "valorInicial": colunas[3].text.strip(),
                }
                contratos_reais.append(item)
                
        if not contratos_reais:
            raise Exception("A tabela foi localizada, mas não continha nenhuma linha de contrato válida preenchida.")
            
        print(f"✅ Sucesso absoluto! Capturados {len(contratos_reais)} contratos reais direto do portal.")
        return contratos_reais

    except Exception as e:
        erro_msg = f"❌ *FALHA NA COLETA REAL*\nO robô não conseguiu ler o Portal de Maricá hoje.\n\n*Motivo técnico:* {str(e)}"
        print(erro_msg)
        enviar_alerta_telegram(erro_msg)
        # Força o encerramento do script sem gerar dados falsos
        raise e


# --- EXECUÇÃO DO PROCESSO 100% REAL ---
try:
    contratos = raspar_portal_marica_real()
    resultados = []

    enviar_alerta_telegram(
        "🔍 *AUDITOR IA MARICÁ*\nConexão com o portal municipal estabelecida. Iniciando análise dos dados reais..."
    )

    for c in contratos:
        numero = c["numeroContrato"]
        fornecedor = c["nomeRazaoSocialFornecedor"]
        objeto = c["objeto"]
        valor = c["valorInicial"]

        print(f"🤖 Solicitando análise de auditoria para o contrato real nº {numero}...")

        prompt = f"""
        Você é um auditor fiscal especialista em contas municipais no Estado do Rio de Janeiro.
        Analise de forma estritamente técnica os dados deste contrato real extraído da prefeitura de Maricá:
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
            analise = f"Falha na API do Gemini ao analisar este item: {str(e)}"

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

        # Respeita o intervalo do plano de uso do Gemini
        time.sleep(5)

    # Grava e consolida as informações válidas
    df_final = pd.DataFrame(resultados)
    df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
    print("🏆 Planilha gerada com dados 100% verídicos!")

except Exception as erro_geral:
    print(f"Execução interrompida para evitar contaminação do relatório: {erro_geral}")
