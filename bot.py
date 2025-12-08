import os
import logging
import html
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# HTTP-сервер для Render
from fastapi import FastAPI
from uvicorn import Config, Server

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Переменные окружения
API_TOKEN = os.getenv("API_TOKEN")
try:
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
except (TypeError, ValueError):
    raise ValueError("ADMIN_CHAT_ID должен быть целым числом (ID чата или пользователя).")

if not API_TOKEN:
    raise ValueError("API_TOKEN не задан в переменных окружения.")

# Инициализация бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# === Обработчики Telegram ===

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Это бот обратной связи. Отправьте сообщение — оно уйдёт администратору.")

@dp.message()
async def handle_message(message: types.Message):
    user = message.from_user

    # Безопасная HTML-ссылка на пользователя
    escaped_name = html.escape(user.first_name or "Пользователь")
    if user.username:
        user_link = f'<a href="https://t.me/{user.username}">{escaped_name}</a>'
    else:
        user_link = f'<a href="tg://user?id={user.id}">{escaped_name}</a>'

    base_caption = f"📩 Новое сообщение от {user_link} (ID: {user.id})"

    try:
        if message.text:
            safe_text = html.escape(message.text)
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"{base_caption}\n\n{safe_text}",
                parse_mode="HTML"
            )
        elif message.photo:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            await bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=message.photo[-1].file_id,
                caption=f"{base_caption}\n\n{safe_caption}",
                parse_mode="HTML"
            )
        elif message.video:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            await bot.send_video(
                chat_id=ADMIN_CHAT_ID,
                video=message.video.file_id,
                caption=f"{base_caption}\n\n{safe_caption}",
                parse_mode="HTML"
            )
        elif message.animation:  # GIF
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            await bot.send_animation(
                chat_id=ADMIN_CHAT_ID,
                animation=message.animation.file_id,
                caption=f"{base_caption}\n\n{safe_caption}",
                parse_mode="HTML"
            )
        elif message.document:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            await bot.send_document(
                chat_id=ADMIN_CHAT_ID,
                document=message.document.file_id,
                caption=f"{base_caption}\n\n{safe_caption}",
                parse_mode="HTML"
            )
        else:
            await message.reply("❌ Поддерживаются только текст, фото, видео, GIF и документы.")
            return

        await message.reply("✅ Ваше сообщение отправлено администратору!")

    except Exception as e:
        logging.error(f"Ошибка при пересылке сообщения: {e}")
        await message.reply("⚠️ Не удалось отправить сообщение. Попробуйте позже.")

# === HTTP-сервер для Render ===

app = FastAPI()

@app.get("/")
async def health_check():
    """Endpoint для проверки работоспособности (Render требует открытый порт)."""
    return {"status": "ok", "service": "telegram-feedback-bot"}

async def start_http_server():
    """Запускает HTTP-сервер на порту, указанном Render в переменной PORT."""
    port = int(os.getenv("PORT", 8000))
    config = Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = Server(config)
    await server.serve()

# === Основная функция ===

async def main():
    logging.info("Запуск Telegram-бота и HTTP-сервера...")

    # Запускаем HTTP-сервер в фоне
    http_task = asyncio.create_task(start_http_server())

    # Запускаем Telegram-поллинг
    await dp.start_polling(bot)

    # Ожидаем завершения сервера (на случай graceful shutdown)
    await http_task

if __name__ == "__main__":
    asyncio.run(main())
