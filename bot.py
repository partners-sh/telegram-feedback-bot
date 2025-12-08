import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Получаем токен и ID администратора из переменных окружения
API_TOKEN = os.getenv("API_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not API_TOKEN or not ADMIN_CHAT_ID:
    raise ValueError("Необходимо указать API_TOKEN и ADMIN_CHAT_ID в переменных окружения.")

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Это бот обратной связи. Просто отправьте мне сообщение, и оно будет переслано администратору.")

@dp.message()
async def handle_message(message: types.Message):
    user = message.from_user

    # Формируем HTML-ссылку на пользователя
    if user.username:
        user_link = f'<a href="https://t.me/{user.username}">{user.first_name}</a>'
    else:
        user_link = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'

    base_caption = f"📩 Новое сообщение от {user_link} (ID: {user.id})"

    try:
        if message.text:
            await bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"{base_caption}\n\n{message.text}",
                parse_mode="HTML"
            )
        elif message.photo:
            await bot.send_photo(
                chat_id=ADMIN_CHAT_ID,
                photo=message.photo[-1].file_id,
                caption=f"{base_caption}\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
        elif message.video:
            await bot.send_video(
                chat_id=ADMIN_CHAT_ID,
                video=message.video.file_id,
                caption=f"{base_caption}\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
        elif message.animation:  # GIF
            await bot.send_animation(
                chat_id=ADMIN_CHAT_ID,
                animation=message.animation.file_id,
                caption=f"{base_caption}\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
        elif message.document:
            await bot.send_document(
                chat_id=ADMIN_CHAT_ID,
                document=message.document.file_id,
                caption=f"{base_caption}\n\n{message.caption or ''}",
                parse_mode="HTML"
            )
        else:
            await message.reply("Извините, я поддерживаю только текст, фото, видео, GIF и документы.")
            return

        # Подтверждение пользователю
        await message.reply("✅ Ваше сообщение отправлено администратору!")

    except Exception as e:
        logging.error(f"Ошибка при пересылке сообщения: {e}")
        await message.reply("❌ Не удалось отправить сообщение. Попробуйте позже.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
