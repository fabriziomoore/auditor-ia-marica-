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

    # CNPJ Oficial da Prefeitura de Maricá
    CNPJ_MARICA = "29131075000193"

    # Buscando o ano consolidado de 2024 para auditar dados verídicos e homologados
    ano_busca = 2024

    url = f"https://pncp.gov.br{CNPJ_MARICA}/contratos/{ano_busca}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, params={"pagina": 1}, headers=headers, timeout=20)

        if response.status_code != 200:
            raise Exception(
                f"Servidor Federal instável. Status: {response.status_code}"
            )

        dados = response.json()
        # Captura os contratos reais validados de dentro da resposta da API
        contratos_api = dados.get("resultado", dados.get("data", []))

        if not contratos_api:
            raise Exception(
                f"Conexão realizada, mas nenhum contrato foi retornado para o ano {ano_busca}."
            )

        contratos_limpos = []
        # Seleciona apenas os 2 primeiros contratos de Maricá para auditar via IA
        for c in contratos_api[:2]:
            item = {
                "numeroContrato": c.get("numeroContrato", "S/N"),
                "nomeRazaoSocialFornecedor": c.get(
                    "nomeRazaoSocialFornecedor", "Não informado"
                ),
                "objeto": c.get("objeto", "Não informado"),
                "valorInicial": f"{c.get('valorInicial', 0):,.2f}".replace(
                    ",", "v"
                )
                .replace(".", ",")
                .replace("v", "."),
            }
            contratos_limpos.append(item)

        print(f"✅ Sucesso! {len(contratos_limpos)} contratos reais importados.")
        return contratos_limpos

    except Exception as e:
        erro_msg = f"❌ *FALHA DE CONEXÃO REAL*\nNão foi possível obter dados do PNCP.\n\n*Motivo:* {str(e)}"
        print(erro_msg)
        enviar_alerta_telegram(erro_msg)
        raise e


# --- EXECUÇÃO DO FLUXO OFICIAL ---
try:
    contratos = buscar_contratos_pncp_reais()
    resultados = []

    enviar_alerta_telegram(
        "🔍 *AUDITOR IA MARICÁ*\nDados oficiais recuperados. Iniciando análise crítica..."
    )

    for c in contratos:
        numero = c["numeroContrato"]
        fornecedor = c["nomeRazaoSocialFornecedor"]
        objeto = c["objeto"]
        valor = c["valorInicial"]

        print(f"🤖 Solicitando auditoria para o contrato real nº {numero}...")

        prompt = f"""
        Você é um auditor fiscal especialista em contas municipais.
        Analise de forma extremamente crítica os dados deste contrato REAL da prefeitura de Maricá:
        - Fornecedor: {fornecedor}
        - Objeto do Contrato: {objeto}
        - Valor Cadastrado: R$ {valor}

        Responda em até 3 linhas se há coerência aparente no valor e aponte o principal risco de auditoria.
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            analise = response.text.strip()
        except Exception as e:
            analise = f"Limitação temporária na API da IA: {str(e)}"

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

    # Gravação física do arquivo no repositório público
    df_final = pd.DataFrame(resultados)
    df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
    print("🏆 Planilha gerada com dados 100% verídicos da base federal!")

except Exception as erro_geral:
    print(f"Execução encerrada para proteção do histórico: {erro_geral}")
