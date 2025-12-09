import os
import logging
import html
import asyncio
import re
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Хранилище: {admin_message_id: (user_id, user_message_id)}
REPLY_MAP = {}

# Переменные окружения
API_TOKEN = os.getenv("API_TOKEN")
try:
    ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
except (TypeError, ValueError):
    raise ValueError("ADMIN_CHAT_ID должен быть целым числом.")

if not API_TOKEN:
    raise ValueError("API_TOKEN не задан.")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()


async def handle_user_message(message: types.Message):
    user = message.from_user
    full_name = user.full_name or "Пользователь"
    escaped_name = html.escape(full_name)

    if user.username:
        user_link = f'<a href="https://t.me/{user.username}">{escaped_name}</a>'
    else:
        user_link = f'<a href="tg://user?id={user.id}">{escaped_name}</a>'

    base_info = f"📩 От: {user_link} (ID: `{user.id}`)"

    # Проверяем, отвечает ли пользователь на сообщение бота
    reply_to_admin_msg_id = None
    if message.reply_to_message:
        original_user_msg_id = message.reply_to_message.message_id
        # Ищем в REPLY_MAP связку: (user_id, original_user_msg_id) → admin_msg_id
        for admin_id, (u_id, u_msg_id) in REPLY_MAP.items():
            if u_id == user.id and u_msg_id == original_user_msg_id:
                reply_to_admin_msg_id = admin_id
                break

    try:
        if message.text:
            safe_text = html.escape(message.text)
            admin_msg = await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"{base_info}\n\n{safe_text}",
                parse_mode="HTML",
                reply_to_message_id=reply_to_admin_msg_id
            )
        elif message.photo:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            admin_msg = await bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=message.photo[-1].file_id,
                caption=f"{base_info}\n\n{safe_caption}",
                parse_mode="HTML",
                reply_to_message_id=reply_to_admin_msg_id
            )
        elif message.video:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            admin_msg = await bot.send_video(
                chat_id=ADMIN_CHAT_ID,
                video=message.video.file_id,
                caption=f"{base_info}\n\n{safe_caption}",
                parse_mode="HTML",
                reply_to_message_id=reply_to_admin_msg_id
            )
        elif message.animation:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            admin_msg = await bot.send_animation(
                chat_id=ADMIN_CHAT_ID,
                animation=message.animation.file_id,
                caption=f"{base_info}\n\n{safe_caption}",
                parse_mode="HTML",
                reply_to_message_id=reply_to_admin_msg_id
            )
        elif message.document:
            safe_caption = html.escape(message.caption or '') if message.caption else ''
            admin_msg = await bot.send_document(
                chat_id=ADMIN_CHAT_ID,
                document=message.document.file_id,
                caption=f"{base_info}\n\n{safe_caption}",
                parse_mode="HTML",
                reply_to_message_id=reply_to_admin_msg_id
            )
        else:
            await message.reply("❌ Поддерживаются только текст, фото, видео, GIF и документы.")
            return

        # Сохраняем связку для ответа админа
        REPLY_MAP[admin_msg.message_id] = (user.id, message.message_id)
        await message.reply("✅ Ваше сообщение отправлено администратору!")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.reply("⚠️ Не удалось отправить сообщение.")


async def handle_admin_reply(message: types.Message):
    reply_to = message.reply_to_message
    if not reply_to:
        return

    if reply_to.message_id not in REPLY_MAP:
        await message.reply("⚠️ Не найдено исходное сообщение для ответа.")
        return

    user_id, user_message_id = REPLY_MAP[reply_to.message_id]

    try:
        if message.text:
            await bot.send_message(
                user_id,
                f"📩 Ответ от администратора:\n\n{message.text}",
                reply_to_message_id=user_message_id
            )
        elif message.photo:
            await bot.send_photo(
                user_id,
                message.photo[-1].file_id,
                caption=message.caption or "",
                reply_to_message_id=user_message_id
            )
        elif message.video:
            await bot.send_video(
                user_id,
                message.video.file_id,
                caption=message.caption or "",
                reply_to_message_id=user_message_id
            )
        elif message.animation:
            await bot.send_animation(
                user_id,
                message.animation.file_id,
                caption=message.caption or "",
                reply_to_message_id=user_message_id
            )
        elif message.document:
            await bot.send_document(
                user_id,
                message.document.file_id,
                caption=message.caption or "",
                reply_to_message_id=user_message_id
            )
        else:
            await message.reply("❌ Этот тип ответа не поддерживается.")
            return

        await message.reply("✅ Ответ отправлен с цитированием!")

    except Exception as e:
        logging.error(f"Ошибка отправки ответа: {e}")
        await message.reply("❌ Не удалось доставить ответ.")


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Это бот обратной связи. Отправьте сообщение — оно уйдёт администратору.")


@dp.message()
async def message_router(message: types.Message):
    if message.from_user.id == ADMIN_CHAT_ID and message.reply_to_message:
        await handle_admin_reply(message)
    else:
        await handle_user_message(message)


async def main():
    logging.info("Запуск бота с двусторонним цитированием...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
