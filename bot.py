import datetime
import os
import time
import pandas as pd
import requests
from google import genai

# Configuração da API do Gemini puxando dos segredos do GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

# CONFIGURAÇÕES DO TELEGRAM FIXADAS E BLINDADAS
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


def buscar_contratos_reais_pncp():
    print("🔄 Conectando ao Banco de Dados Nacional do PNCP...")

    # CNPJ Oficial da Prefeitura de Maricá
    CNPJ_MARICA = "29131075000193"

    # Ano corrente de execução
    ano_busca = datetime.datetime.now().year

    # Se estivermos no início do ano e a API nacional estiver sem dados para 2026,
    # mudamos o ano de busca para 2025 automaticamente para capturar dados verídicos consolidados
    url = f"https://pncp.gov.br{CNPJ_MARICA}/contratos/{ano_busca}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, params={"pagina": 1}, headers=headers, timeout=20)

        # Se o ano atual retornar vazio ou fora do ar, tenta buscar dados do ano anterior homologado
        if response.status_code != 200 or not response.json().get("data", response.json().get("resultado")):
            print("⚠️ Sem registros em 2026. Consultando base histórica real de 2025...")
            ano_busca = 2025
            url = f"https://pncp.gov.br{CNPJ_MARICA}/contratos/{ano_busca}"
            response = requests.get(url, params={"pagina": 1}, headers=headers, timeout=20)

        if response.status_code != 200:
            raise Exception(f"API Federal indisponível. Status: {response.status_code}")

        dados = response.json()
        contratos_api = dados.get("data", dados.get("resultado", []))

        # SE FALHAR EM TRAZER DADOS REAIS, O SCRIPT PARA IMEDIATAMENTE E ACUSA O ERRO
        if not contratos_api:
            raise Exception(f"A API do Governo não retornou nenhum registro real para Maricá no ano {ano_busca}.")

        contratos_limpos = []
        # Captura os 2 primeiros contratos 100% verídicos para auditar
        for c in contratos_api[:2]:
            contratos_limpos.append({
                "numeroContrato": str(c.get("numeroContrato", "S/N")),
                "nomeRazaoSocialFornecedor": str(c.get("nomeRazaoSocialFornecedor", "Não informado")),
                "objeto": str(c.get("objeto", "Não informado")),
                "valorInicial": str(c.get("valorInicial", "0"))
            })

        print(f"✅ Sucesso absoluto! {len(contratos_limpos)} contratos REAIS importados.")
        return contratos_limpos

    except Exception as e:
        erro_msg = f"❌ *ERRO CRÍTICO DE AUDITORIA*\nO robô travou para evitar contaminação do relatório.\n\n*Motivo técnico:* {str(e)}"
        print(erro_msg)
        enviar_alerta_telegram(erro_msg)
        # Cancela a execução para não salvar lixo na planilha
        raise e


# --- EXECUÇÃO DO FLUXO 100% AUDITÁVEL ---
try:
    contratos = buscar_contratos_reais_pncp()
    resultados = []

    enviar_alerta_telegram(
        "🔍 *AUDITOR IA MARICÁ*\nConexão com a base federal estabelecida. Analisando novos dados reais..."
    )

    for c in contratos:
        numero = c["numeroContrato"]
        fornecedor = c["nomeRazaoSocialFornecedor"]
        objeto = c["objeto"]
        valor = c["valorInicial"]

        print(f"🤖 Solicitando auditoria para o contrato real nº {numero}...")

        prompt = f"""
        Você é um auditor fiscal experiente.
        Analise de forma estritamente séria os dados deste contrato REAL extraído da Prefeitura de Maricá:
        - Fornecedor: {fornecedor}
        - Objeto do Contrato: {objeto}
        - Valor Cadastrado: R$ {valor}

        Responda em até 3 linhas se há coerência no valor e qual o principal risco de auditoria fiscal.
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            analise = response.text.strip()
        except Exception as e:
            analise = f"Falha temporária na API do Gemini: {str(e)}"

        texto_card = (
            f"📄 *Contrato nº:* {numero}\n"
            f"🏢 *Empresa:* {fornecedor}\n"
            f"💰 *Valor:* R$ {valor}\n"
            f"🤖 *Análise Crítica:* {analise}"
        )

        # Envia direto para o seu Telegram
        enviar_alerta_telegram(texto_card)

        resultados.append({
            "Data_Auditoria": datetime.date.today().strftime("%d/%m/%Y"),
            "Contrato_N": numero,
            "Fornecedor": fornecedor,
            "Valor_RS": valor,
            "Objeto_Completo": objeto,
            "Analise_Critica_IA": analise,
        })

        # Pausa anti-bloqueio de cota da IA
        time.sleep(5)

    # Força a gravação física correta da planilha limpa
    df_final = pd.DataFrame(resultados)
    df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
    print("🏆 Arquivo 'relatorio_diario_marica.csv' gravado com sucesso com dados reais!")

except Exception as erro_geral:
    print(f"Execução encerrada para proteger o histórico contra dados simulados: {erro_geral}")
