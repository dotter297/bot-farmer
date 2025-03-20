from aiogram import Router, types
from aiogram.filters import Command
from database import log_action
import sqlite3
from config import ADMIN_IDS

router = Router()


# Проверка прав администратора
def is_admin(user_id):
    return user_id in ADMIN_IDS


@router.message(Command("add_admin"))
async def add_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.reply("Используйте: /add_admin user_id")
        return

    user_id = int(args[1])
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()
    await message.reply(f"Пользователь {user_id} добавлен в администраторы.")
    await log_action(f"Добавлен администратор {user_id}")


@router.message(Command("set_online_schedule"))
async def set_online_schedule(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.reply("У вас нет прав на выполнение этой команды.")
        return

    args = message.text.split()
    if len(args) < 4:
        await message.reply("Используйте: /set_online_schedule +79991234567 HH:MM HH:MM")
        return

    phone_number, start_time, end_time = args[1], args[2], args[3]
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO online_schedule (phone_number, start_time, end_time) VALUES (?, ?, ?)",
                   (phone_number, start_time, end_time))
    conn.commit()
    conn.close()
    await message.reply(f"Онлайн для {phone_number} установлен с {start_time} до {end_time}")
    await log_action(f"Установлен онлайн для {phone_number}: {start_time}-{end_time}")
