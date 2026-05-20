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
        requests.post(url, json=payload, timeout=10)
    except:
        pass


def buscar_compras_reais_marica():
    print("🔄 Consultando API oficial de compras públicas de Maricá...")

    # Código oficial do município de Maricá-RJ no sistema integrado de gestão (SIASG/ComprasGov)
    codigo_municipio_marica = "984337"
    
    # URL oficial de contratações diretas, dispensas e contratos integrados
    url = f"https://dados.gov.br{codigo_municipio_marica}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            raise Exception(f"Servidor de dados governamentais instável. Status: {response.status_code}")
            
        dados = response.json()
        
        # Estrutura padrão de retorno do barramento de dados do governo federal (_embedded)
        compras = dados.get("_embedded", {}).get("dispensasInexigibilidades", [])

        if not compras:
            raise Exception("Nenhuma contratação recente foi listada no painel do barramento federal para o código de Maricá.")

        contratos_reais = []
        
        # Extrai os dados legítimos das primeiras contratações públicas válidas encontradas
        for c in compras[:2]:
            contratos_reais.append({
                "numeroContrato": str(c.get("id", "S/N")),
                "nomeRazaoSocialFornecedor": "Fornecedor registrado no processo",
                "objeto": str(c.get("objeto", "Não especificado")),
                "valorInicial": str(c.get("valor_estimado", "0"))
            })
            
        print(f"✅ {len(contratos_reais)} registros reais encontrados!")
        return contratos_reais

    except Exception as e:
        erro_msg = f"❌ *FALHA TÉCNICA REAL*\nA API do governo não retornou dados públicos hoje.\n\n*Motivo:* {str(e)}"
        print(erro_msg)
        enviar_alerta_telegram(erro_msg)
        raise e


# --- EXECUÇÃO DO PROCESSO PRINCIPAL REAL ---
try:
    contratos = buscar_compras_reais_marica()
    resultados = []

    enviar_alerta_telegram(
        "🔍 *AUDITOR IA MARICÁ*\nDados extraídos com sucesso. Iniciando auditoria real de processos públicos..."
    )

    for c in contratos:
        numero = c["numeroContrato"]
        fornecedor = c["nomeRazaoSocialFornecedor"]
        objeto = c["objeto"]
        valor = c["valorInicial"]

        prompt = f"""
        Você é um auditor fiscal especialista. Analise se há coerência no objeto deste processo de compra real de Maricá:
        - Identificação/Número: {numero}
        - Descrição do Objeto: {objeto}
        - Valor Estimado: R$ {valor}
        Responda estritamente em até 3 linhas indicando o foco principal que uma auditoria fiscal deve ter sobre esse gasto.
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            analise = response.text.strip()
        except Exception as e:
            analise = f"Gargalo na chamada da inteligência artificial: {str(e)}"

        texto_card = (
            f"📄 *Processo ID:* {numero}\n"
            f"💰 *Valor Estimado:* R$ {valor}\n"
            f"📦 *Objeto:* {objeto}\n"
            f"🤖 *Auditoria IA:* {analise}"
        )
        
        enviar_alerta_telegram(texto_card)

        resultados.append({
            "Data_Verificacao": datetime.date.today().strftime("%d/%m/%Y"),
            "Processo_ID": numero,
            "Valor_Estimado": valor,
            "Objeto_Completo": objeto,
            "Analise_IA": analise
        })
        time.sleep(5)

    # Gravação forçada do arquivo no repositório
    df_final = pd.DataFrame(resultados)
    df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
    print("🏆 O arquivo 'relatorio_diario_marica.csv' foi gravado e salvo com dados públicos!")

except Exception as erro:
    print(f"Execução encerrada para proteger seu histórico de relatórios: {erro}")
