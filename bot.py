import os
import requests

# Puxa o token que você configurou no GitHub Secrets
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


def descobrir_chat_id():
    print("🕵️‍♂️ Iniciando busca pelo seu ID real do Telegram...")

    if not TELEGRAM_BOT_TOKEN:
        print("❌ Erro: O TELEGRAM_BOT_TOKEN não foi encontrado nos Secrets.")
        return

    # Consulta as últimas mensagens recebidas pelo seu robô
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/getUpdates"

    try:
        response = requests.get(url, timeout=10)
        dados = response.json()

        if response.status_code == 200 and dados.get("result"):
            # Varre as interações que o robô recebeu
            for update in dados["result"]:
                message = update.get("message", {})
                chat = message.get("chat", {})
                user_id = chat.get("id")
                first_name = chat.get("first_name", "Usuário")

                if user_id:
                    print("\n🎯 ENCONTRADO!")
                    print(
                        f"👤 Nome do Usuário que ativou o robô: {first_name}"
                    )
                    print(f"🆔 Seu ID correto é: {user_id}")
                    print(
                        "👉 Copie esse número acima e substitua no seu TELEGRAM_CHAT_ID do GitHub.\n"
                    )
                    return

            print(
                "⚠️ O robô respondeu, mas não encontrou nenhuma mensagem recente."
            )
        else:
            print(
                "⚠️ Nenhuma mensagem encontrada no histórico do robô pelo método getUpdates."
            )
            print(
                "💡 MOTIVO: Você precisa abrir o robô no celular e enviar um 'Oi' para ele primeiro."
            )

    except Exception as e:
        print(f"❌ Erro ao conectar na API do Telegram: {e}")


# Executa o espião
descobrir_chat_id()
