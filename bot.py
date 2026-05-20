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


def buscar_contratos_reais_marica():
    print("🔄 Conectando ao endpoint geral do PNCP...")
    
    # Endpoint público de listagem geral por data de publicação
    url = "https://pncp.gov.br/api/consulta/v1/contratos"
    
    # Define um intervalo de busca recente baseado no histórico verídico
    params = {
        "dataInicial": "20250101",
        "dataFinal": "20250110",
        "pagina": 1
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=25)
        
        if response.status_code != 200:
            raise Exception(f"Erro na API Federal do PNCP. Código: {response.status_code}")
            
        dados = response.json()
        itens_contrato = dados.get("data", dados.get("resultado", []))

        contratos_filtrados = []
        
        # Filtra na listagem nacional apenas o que pertence ao município de Maricá
        for c in itens_contrato:
            orgao = c.get("orgaoEntidade", {})
            nome_orgao = orgao.get("razaoSocial", "").upper()
            objeto_texto = c.get("objeto", "").upper()
            
            if "MARICA" in nome_orgao or "MARICÁ" in nome_orgao:
                contratos_filtrados.append({
                    "numeroContrato": str(c.get("numeroContrato", "S/N")),
                    "nomeRazaoSocialFornecedor": str(c.get("nomeRazaoSocialFornecedor", "Não informado")),
                    "objeto": str(c.get("objeto", "Não informado")),
                    "valorInicial": str(c.get("valorInicial", "0"))
                })
                
        # Caso a busca por data estrita retorne zerada devido ao balanceamento da API federal, 
        # o script avisa no Telegram o status real em vez de gerar dados fictícios.
        if not contratos_filtrados:
            raise Exception("Nenhum contrato ativo foi retornado pela API federal na janela de checagem atual.")

        print(f"✅ {len(contratos_filtrados)} contratos reais localizados!")
        return contratos_filtrados[:2] # Limita a 2 itens para evitar travamento de cota

    except Exception as e:
        erro_msg = f"⚠️ *STATUS DO MONITORAMENTO*\nA API federal conectou com sucesso.\n\n*Informação técnica:* {str(e)}"
        print(erro_msg)
        enviar_alerta_telegram(erro_msg)
        raise e


# --- EXECUÇÃO DO PROCESSO 100% AUDITÁVEL ---
try:
    contratos = buscar_contratos_reais_marica()
    resultados = []

    enviar_alerta_telegram(
        "🔍 *AUDITOR IA MARICÁ*\nContratos identificados na base nacional. Processando auditoria fiscal..."
    )

    for c in contratos:
        numero = c["numeroContrato"]
        fornecedor = c["nomeRazaoSocialFornecedor"]
        objeto = c["objeto"]
        valor = c["valorInicial"]

        prompt = f"""
        Você é um auditor fiscal. Analise criticamente os dados deste contrato real extraído da prefeitura de Maricá:
        - Fornecedor: {fornecedor}
        - Objeto: {objeto}
        - Valor: R$ {valor}
        Responda em até 3 linhas indicando se o valor condiz com o serviço e aponte o risco de auditoria.
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            analise = response.text.strip()
        except Exception as e:
            analise = f"Gargalo temporário na API da IA: {str(e)}"

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
        })
        time.sleep(5)

    df_final = pd.DataFrame(resultados)
    df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
    print("🏆 Arquivo físico 'relatorio_diario_marica.csv' gerado na aba Code!")

except Exception as f:
    print(f"Execução encerrada sem alteração de arquivos: {f}")
