from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("Установите BOT_TOKEN и ADMIN_ID в Environment Variables")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

@app.route("/webhook", methods=["POST"])
def telegram_webhook():
    try:
        data = request.get_json()
        if not data or "message" not in data:
            return jsonify({"ok": True})

        message = data["message"]
        user_id = message["from"]["id"]
        text = message.get("text", "📎 Сообщение без текста")

        # Если пишет админ — отвечаем пользователю
        if str(user_id) == ADMIN_ID:
            if "reply_to_message" in message and "text" in message["reply_to_message"]:
                replied_text = message["reply_to_message"]["text"]
                if replied_text.startswith("📩 От "):
                    try:
                        target_user = replied_text.split()[2]
                        reply_text = message.get("text", "Сообщение без текста")
                        requests.post(f"{TELEGRAM_API}/sendMessage", json={
                            "chat_id": target_user,
                            "text": reply_text
                        })
                    except Exception as e:
                        print("Ошибка при отправке ответа:", e)
            return jsonify({"ok": True})

        # Иначе — пересылаем админу
        requests.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": ADMIN_ID,
            "text": f"📩 От {user_id}\n{text}",
            "reply_markup": {"force_reply": True}
        })

    except Exception as e:
        print("❌ Ошибка в webhook:", e)

    return jsonify({"ok": True})


@app.route("/", methods=["GET"])
def home():
    return "✅ Telegram Feedback Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))