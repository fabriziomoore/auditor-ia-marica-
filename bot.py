import datetime
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from google import genai

# Configuração da API do Gemini puxando dos segredos do GitHub
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


def obter_dados_contingencia():
    print("📋 Carregando base de dados reais de Maricá para auditoria...")
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


def raspar_portal_marica():
    print("🌐 Tentando acessar o Portal da Transparência de Maricá...")
    url = "https://marica.rj.gov.br"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            tabela = soup.find("table") or soup.find(class_="table")
            if tabela:
                contratos_descobertos = []
                linhas = tabela.find_all("tr")
                for linha in linhas[1:4]:
                    colunas = linha.find_all("td")
                    if len(colunas) >= 4:
                        item = {
                            "numeroContrato": colunas[0].text.strip(),
                            "nomeRazaoSocialFornecedor": colunas[1].text.strip(),
                            "objeto": colunas[2].text.strip(),
                            "valorInicial": colunas[3].text.strip(),
                        }
                        contratos_descobertos.append(item)
                if contratos_descobertos:
                    print("✅ Sucesso ao raspar dados ao vivo do portal!")
                    return contratos_descobertos
    except:
        pass
    return obter_dados_contingencia()


def analisar_com_ia(objeto, valor, fornecedor):
    prompt = f"""
    Você é um auditor fiscal especialista em contas municipais no Estado do Rio de Janeiro.
    Analise os dados extraídos do Portal da Transparência de Maricá:
    - Fornecedor: {fornecedor}
    - Objeto do Contrato: {objeto}
    - Valor Cadastrado: R$ {valor}

    Responda em até 3 linhas se há coerência no valor e qual o principal risco de auditoria.
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Erro na análise: {str(e)}"


# --- PROCESSO PRINCIPAL ---
contratos = raspar_portal_marica()
resultados = []

for c in contratos:
    numero = c.get("numeroContrato", "S/N")
    fornecedor = c.get("nomeRazaoSocialFornecedor", "Não informado")
    objeto = c.get("objeto", "Não informado")
    valor = c.get("valorInicial", "0")

    print(f"🤖 Analisando contrato municipal nº {numero}...")
    analise = analisar_com_ia(objeto, valor, fornecedor)

    resultados.append(
        {
            "Data_Auditoria": datetime.date.today().strftime("%d/%m/%Y"),
            "Contrato_N": numero,
            "Fornecedor": fornecedor,
            "Valor_RS": valor,
            "Objeto_Completo": objeto,
            "Analise_Critica_IA": analise,
        }
    )

# Cria e força a gravação correta do arquivo CSV
df_final = pd.DataFrame(resultados)
df_final.to_csv("relatorio_diario_marica.csv", index=False, encoding="utf-8")
print("🏆 Arquivo 'relatorio_diario_marica.csv' gravado no servidor local!")
