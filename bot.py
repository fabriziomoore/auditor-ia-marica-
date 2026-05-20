import datetime
import os
import time
import pandas as pd
import requests
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


def buscar_contratos_pncp_reais():
    print("🔄 Conectando ao banco de dados nacional do PNCP...")
    CNPJ_MARICA = "29131075000193"
    
    # Mantendo o ano consolidado de 2024 para capturar dados homologados
    ano_busca = 2024
    
    url = f"https://pncp.gov.br/api/consulta/v1/orgaos/{CNPJ_MARICA}/contratos/{ano_busca}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, params={"pagina": 1}, headers=headers, timeout=20)
        
        if response.status_code != 200:
            raise Exception(f"Servidor Federal recusou a requisição. Código: {response.status_code}")
            
        dados = response.json()
        
        # CORREÇÃO: Varre as duas palavras-chave usadas pelo governo para garantir a captura
        contratos_api = []
        if isinstance(dados, dict):
            contratos_api = dados.get("data", dados.get("resultado", []))
        elif isinstance(dados, list):
            contratos_api = dados

        if not contratos_api:
            raise Exception(f"A API do governo respondeu com sucesso, mas a lista de contratos de Maricá para {ano_busca} retornou vazia.")

        contratos_limpos = []
        # Captura os 2 primeiros contratos verídicos retornados pelo Governo Federal
        for c in contratos_api[:2]:
            contratos_limpos.append({
                "numeroContrato": str(c.get("numeroContrato", "S/N")),
                "nomeRazaoSocialFornecedor": str(c.get("nomeRazaoSocialFornecedor", "Não informado")),
                "objeto": str(c.get("objeto", "Não informado")),
                "valorInicial": str(c.get("valorInicial", "0"))
            })
            
        print(f"✅ Sucesso absoluto! {len(contratos_limpos)} contratos reais importados.")
        return contratos_limpos

    except Exception as e:
        erro_msg = f"❌ *FALHA DE CONEXÃO REAL*\nNão foi possível obter dados oficiais.\n\n*Motivo técnico:* {str(e)}"
        print(erro_msg)
        enviar_alerta_telegram(erro_msg)
        raise e


# --- EXECUÇÃO DO FLUXO OFICIAL ---
try:
    contratos = buscar_contratos_pncp_reais()
    resultados = []

    enviar_alerta_telegram(
        "🔍 *AUDITOR IA MARICÁ*\nConexão com a base federal estabelecida. Analisando contratos reais de Maricá..."
    )

    for c in contratos:
        numero = c["numeroContrato"]
        fornecedor = c["nomeRazaoSocialFornecedor"]
        objeto = c["objeto"]
        valor = c["valorInicial"]

        print(f"🤖 Solicitando auditoria para o contrato real nº {numero}...")

        prompt = f"""
        Você é um auditor fiscal especialista em contas municipais.
        Analise de forma crítica os dados deste contrato real extraído da prefeitura de Maricá:
        - Fornecedor: {fornecedor}
        - Objeto do Contrato: {objeto}
        - Valor Cadastrado: R$ {valor}

        Responda em até 3 linhas se há coerência no valor e aponte o principal risco de auditoria.
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            analise = response.text.strip()
        except Exception as e:
            analise = f"Falha na API da IA: {str(e)}"

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
        
        # Pausa de cota inteligente para o plano do Gemini
        time.sleep(5)

    df_final = pd.DataFrame(resultados)
    df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
    print("🏆 Planilha gerada com dados 100% verídicos da base federal!")

except Exception as erro_geral:
    print(f"Execução interrompida para evitar contaminação do relatório: {erro_geral}")
