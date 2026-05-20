import datetime
import os
import time
import pandas as pd
import requests
from google import genai

# Configuração da API do Gemini puxando dos segredos do GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# CONFIGURAÇÕES DO TELEGRAM FIXADAS NO CÓDIGO
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
        response = requests.post(url, json=payload, timeout=12)
        if response.status_code == 200:
            print("🚀 Disparo de mensagem enviado para o Telegram.")
        else:
            print(f"❌ Falha no Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Erro de rede ao enviar Telegram: {e}")


def buscar_contratos_pncp_reais():
    print("🔄 Conectando à base de dados nacional do PNCP...")
    
    # URL oficial de consulta por data do Governo Federal
    url = "https://pncp.gov.br/api/consulta/v1/contratos"
    
    # Formato correto exigido pela API: AAAAMMDD sem hifens ou separadores
    params = {
        "dataInicial": "20250101",
        "dataFinal": "20250115",
        "pagina": 1
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=25)
        
        if response.status_code != 200:
            raise Exception(f"Erro na API Federal. Código HTTP: {response.status_code}")
            
        dados = response.json()
        itens_contrato = dados.get("data", dados.get("resultado", []))

        contratos_filtrados = []
        
        # Filtra a listagem nacional buscando registros da cidade de Maricá
        for c in itens_contrato:
            orgao = c.get("orgaoEntidade", {})
            razao_social = orgao.get("razaoSocial", "").upper()
            municipio = c.get("municipio", {}).get("nome", "").upper()
            objeto = c.get("objeto", "").upper()
            
            if "MARICA" in razao_social or "MARICÁ" in razao_social or "MARICA" in municipio:
                contratos_filtrados.append({
                    "numeroContrato": str(c.get("numeroContrato", "S/N")),
                    "nomeRazaoSocialFornecedor": str(c.get("nomeRazaoSocialFornecedor", "Não informado")),
                    "objeto": str(c.get("objeto", "Não informado")),
                    "valorInicial": str(c.get("valorInicial", "0"))
                })
                
        return contratos_filtrados

    except Exception as e:
        print(f"⚠️ Alerta de conexão: {e}")
        return []


# --- EXECUÇÃO DO FLUXO ---
contratos = buscar_contratos_pncp_reais()
resultados = []

# Envia um sinal para você saber que o robô está ativo e executando o código
enviar_alerta_telegram("🔍 *AUDITOR IA MARICÁ*\nO robô iniciou a checagem da base de dados oficial...")

if contratos:
    for c in contratos[:2]: # Limita a duas análises por cota
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
            analise = f"Gargalo temporário na IA: {str(e)}"

        texto_card = (
            f"📄 *Contrato nº:* {numero}\n"
            f"🏢 *Empresa:* {fornecedor}\n"
            f"💰 *Valor:* R$ {valor}\n"
            f"🤖 *Análise Crítica:* {analise}"
        )
        enviar_alerta_telegram(texto_card)

        resultados.append({
            "Data_Auditoria": datetime.date.today().strftime("%d/%m/%Y"),
            "Contrato_N": numero,
            "Fornecedor": fornecedor,
            "Valor_RS": valor,
            "Analise_IA": analise,
            "Status_Checagem": "Dados Processados"
        })
        time.sleep(5)
else:
    # SE NÃO HOUVER CONTRATOS, FORÇA A CRIAÇÃO DA PLANILHA INFORMANDO O STATUS REAL
    print("⚠️ Nenhum contrato encontrado na janela de datas. Criando registro de checagem em branco...")
    resultados.append({
        "Data_Auditoria": datetime.date.today().strftime("%d/%m/%Y"),
        "Contrato_N": "NENHUM NOVO",
        "Fornecedor": "Nenhum detectado",
        "Valor_RS": "0",
        "Analise_IA": "Base checada sem novos registros de contratos públicos para Maricá neste período.",
        "Status_Checagem": "Sem Novidades"
    })

# Gravação garantida do arquivo físico
df_final = pd.DataFrame(resultados)
df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
print("🏆 Planilha gerada com sucesso e salva no repositório!")
