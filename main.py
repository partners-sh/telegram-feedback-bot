from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Получаем переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN или ADMIN_ID не установлены!")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route("/", methods=["GET"])
def home():
    return "✅ Telegram Feedback Bot is running!"

@app.route("/webhook", methods=["GET", "POST"])
def telegram_webhook():
    print("🔹 Запрос получен:", request.method)

    if request.method == "GET":
        return "Webhook endpoint is ready for POST requests.", 200

    try:
        data = request.get_json()
        if not data:
            print("❌ Пустой JSON")
            return jsonify({"ok": True})

        if "message" not in data:
            print("❌ Нет сообщения в данных")
            return jsonify({"ok": True})

        message = data["message"]
        user_id = message["from"]["id"]
        chat_id = message["chat"]["id"]

        # Если пишет админ — пытаемся ответить пользователю
        if str(user_id) == str(ADMIN_ID):
            if "reply_to_message" in message and "text" in message["reply_to_message"]:
                replied_text = message["reply_to_message"]["text"]
                if replied_text.startswith("📩 От "):
                    try:
                        target_user = replied_text.split()[2]
                        reply_text = message.get("text", "Сообщение без текста")
                        print(f"📤 Ответ пользователю {target_user}: {reply_text}")
                        requests.post(f"{TELEGRAM_API}/sendMessage", json={
                            "chat_id": target_user,
                            "text": reply_text
                        })
                    except Exception as e:
                        print("❌ Ошибка при отправке ответа:", e)
            return jsonify({"ok": True})

        # Иначе — пересылаем админу
        text = message.get("text", "📎 Медиа/нестандартное сообщение")
        print(f"📥 Сообщение от {user_id}: {text}")

        requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": ADMIN_ID,
            "text": f"📩 От {user_id}\n{text}",
            "reply_markup": {"force_reply": True}
        })

    except Exception as e:
        print("❌ Ошибка в webhook:", e)
        return jsonify({"ok": False}), 500

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
