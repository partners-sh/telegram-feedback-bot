import os
import logging
import html
import asyncio
import re
from aiogram import Bot, Dispatcher, types  # <-- ключевой импорт!
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

# === Вспомогательные функции ===

async def handle_user_message(message: types.Message):
    """Обработка сообщений от обычных пользователей."""
    user = message.from_user
    full_name = user.full_name or "Пользователь"
    escaped_name = html.escape(full_name)

    # Формат: ID в обратных кавычках — легко парсится регуляркой
    base_info = f"📩 От: {escaped_name} (ID: `{user.id}`)"

    try:
        if message.text:
            safe_text = html.escape(message.text)
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"{base_info}\n\n{safe_text}",
                parse_mode="HTML"
            )
        elif message.photo:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            await bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=message.photo[-1].file_id,
                caption=f"{base_info}\n\n{safe_caption}",
                parse_mode="HTML"
            )
        elif message.video:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            await bot.send_video(
                chat_id=ADMIN_CHAT_ID,
                video=message.video.file_id,
                caption=f"{base_info}\n\n{safe_caption}",
                parse_mode="HTML"
            )
        elif message.animation:  # GIF
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            await bot.send_animation(
                chat_id=ADMIN_CHAT_ID,
                animation=message.animation.file_id,
                caption=f"{base_info}\n\n{safe_caption}",
                parse_mode="HTML"
            )
        elif message.document:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            await bot.send_document(
                chat_id=ADMIN_CHAT_ID,
                document=message.document.file_id,
                caption=f"{base_info}\n\n{safe_caption}",
                parse_mode="HTML"
            )
        else:
            await message.reply("❌ Поддерживаются только текст, фото, видео, GIF и документы.")
            return

        await message.reply("✅ Ваше сообщение отправлено администратору!")

    except Exception as e:
        logging.error(f"Ошибка при пересылке от пользователя: {e}")
        await message.reply("⚠️ Не удалось отправить сообщение. Попробуйте позже.")


async def handle_admin_reply(message: types.Message):
    """Обработка ответов от администратора на пересланные сообщения."""
    reply_msg = message.reply_to_message
    if not reply_msg:
        return

    # Ищем ID в тексте или подписи сообщения, которое админ цитирует
    text_to_search = (reply_msg.text or reply_msg.caption or "")
    match = re.search(r"ID:\s*`(\d+)`", text_to_search)
    if not match:
        await message.reply("⚠️ Не удалось найти ID пользователя в пересланном сообщении.")
        return

    try:
        user_id = int(match.group(1))
        # Отправляем ответ пользователю
        if message.text:
            await bot.send_message(user_id, f"📩 Ответ от администратора:\n\n{message.text}")
        elif message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
        elif message.video:
            await bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
        elif message.animation:
            await bot.send_animation(user_id, message.animation.file_id, caption=message.caption or "")
        elif message.document:
            await bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
        else:
            await message.reply("❌ Этот тип ответа пока не поддерживается.")
            return

        await message.reply("✅ Ответ отправлен пользователю!")

    except Exception as e:
        logging.error(f"Ошибка при отправке ответа: {e}")
        await message.reply("❌ Не удалось доставить ответ этому пользователю (возможно, он заблокировал бота).")


# === Обработчики ===

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Это бот обратной связи. Отправьте сообщение — оно уйдёт администратору.")


@dp.message()
async def message_router(message: types.Message):
    """Маршрутизатор: определяет, от кого сообщение — и вызывает нужный обработчик."""
    if message.from_user.id == ADMIN_CHAT_ID and message.reply_to_message:
        await handle_admin_reply(message)
    else:
        await handle_user_message(message)


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


# === Запуск ===

async def main():
    logging.info("Запуск Telegram-бота и HTTP-сервера...")

    # Запускаем HTTP-сервер в фоне
    http_task = asyncio.create_task(start_http_server())

    # Запускаем Telegram-поллинг
    await dp.start_polling(bot)

    # Ожидаем завершения сервера
    await http_task


if __name__ == "__main__":
    asyncio.run(main())
