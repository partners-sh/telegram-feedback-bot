import re

# ... остальной код ...

async def handle_user_message(message: types.Message):
    user = message.from_user
    escaped_name = html.escape(user.full_name or "Пользователь")

    # Формат: "ID: `123456789`" — в обратных кавычках для лёгкого парсинга
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
        elif message.animation:
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
        logging.error(f"Ошибка: {e}")
        await message.reply("⚠️ Не удалось отправить сообщение.")

async def handle_admin_reply(message: types.Message):
    reply_msg = message.reply_to_message
    if not reply_msg:
        return

    # Ищем ID в тексте или подписи
    text_to_search = (reply_msg.text or reply_msg.caption or "")
    match = re.search(r"ID:\s*`(\d+)`", text_to_search)
    if not match:
        await message.reply("⚠️ Не удалось найти ID пользователя.")
        return

    try:
        user_id = int(match.group(1))
        if message.text:
            await bot.send_message(user_id, f"📩 Ответ от администратора:\n\n{message.text}")
        elif message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
        # Добавьте другие типы по желанию

        await message.reply("✅ Ответ отправлен!")
    except Exception as e:
        logging.error(f"Ошибка отправки ответа: {e}")
        await message.reply("❌ Не удалось доставить ответ.")

@dp.message()
async def router(message: types.Message):
    if message.from_user.id == ADMIN_CHAT_ID and message.reply_to_message:
        await handle_admin_reply(message)
    else:
        await handle_user_message(message)
