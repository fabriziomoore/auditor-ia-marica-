import os
import requests

# Puxa o token injetado pelo GitHub Actions
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


def descobrir_chat_id_real():
    print("🕵️‍♂️ Iniciando varredura para capturar seu ID de chat...")

    if not TELEGRAM_BOT_TOKEN:
        print("❌ Erro interno: O TOKEN não foi encontrado no ambiente.")
        return

    # CORREÇÃO: Link montado de forma segura usando parâmetros limpos
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/getUpdates"

    try:
        response = requests.get(url, timeout=15)
        dados = response.json()

        if response.status_code == 200 and dados.get("result"):
            # Varre as interações recebidas pelo robô
            for update in dados["result"]:
                message = update.get("message", {})
                chat = message.get("chat", {})
                user_id = chat.get("id")
                nome = chat.get("first_name", "Usuário")

                if user_id:
                    print("\n🎯 CAPTURADO COM SUCESSO!")
                    print(f"👤 Nome do dono da conta: {nome}")
                    print(f"🆔 O número do seu TELEGRAM_CHAT_ID real é: {user_id}")
                    print(
                        "👉 Copie este número acima e salve nos Secrets do GitHub!\n"
                    )
                    return

            print(
                "⚠️ O robô respondeu, mas não encontrou mensagens de texto recentes."
            )
        else:
            print(
                f"⚠️ Resposta do Telegram (Status {response.status_code}), mas sem histórico de mensagens."
            )
            print(
                "💡 SOLUÇÃO OBRIGATÓRIA: Abra o Telegram no celular, entre no seu @Auditor_maricabot e envie um 'Oi' para ele agora mesmo."
            )

    except Exception as e:
        print(f"❌ Erro ao decodificar dados do Telegram: {e}")


# Executa o localizador corrigido
descobrir_chat_id_real()
