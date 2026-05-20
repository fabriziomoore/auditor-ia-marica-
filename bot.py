import os
import requests

# Puxa o token que você configurou perfeitamente no GitHub Secrets
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


def descobrir_chat_id_real():
    print("🕵️‍♂️ Iniciando varredura para capturar seu ID de chat...")

    if not TELEGRAM_BOT_TOKEN:
        print("❌ Erro interno: O TOKEN não foi injetado pelo GitHub.")
        return

    # Consulta quem interagiu com o robô nas últimas horas
    url = f"https://telegram.org{TELEGRAM_BOT_TOKEN}/getUpdates"

    try:
        response = requests.get(url, timeout=10)
        dados = response.json()

        if response.status_code == 200 and dados.get("result"):
            for update in dados["result"]:
                # Procura por mensagens diretas enviadas a ele
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

            print("⚠️ O robô respondeu, mas a conversa está em branco.")
        else:
            print("⚠️ Histórico vazio no servidor do Telegram.")
            print(
                "💡 SOLUÇÃO: Abra o Telegram no celular, entre no seu @Auditor_maricabot e envie um 'Oi' para ele agora."
            )

    except Exception as e:
        print(f"❌ Erge de conexão: {e}")


# Executa o localizador
descobrir_chat_id_real()
