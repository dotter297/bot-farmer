# start bot
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage  # Добавляем FSM-хранилище
from config import API_TOKEN
from handlers.auth_handler import register_auth_handlers, get_main_keyboard  # Исправил повторный импорт
from aiogram.utils import executor  # Добавляем запуск
from handlers.broadcast_handler import register_broadcast_handlers
from handlers.subscription_handler import register_subscription_handlers

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()  # Создаем временное хранилище FSM
dp = Dispatcher(bot, storage=storage)  # Передаем storage в Dispatcher

# Регистрируем обработчики рассылки и авторизации
register_broadcast_handlers(dp)
register_auth_handlers(dp)  # Регистрируем обработчики
register_subscription_handlers(dp)

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    await message.reply("Добро пожаловать! Я бот, который может управлять множеством аккаунтов! Выберите действие:", reply_markup=get_main_keyboard())

if __name__ == "__main__":
    print("🚀 Бот успешно запущен!")  # Проверяем запуск
    executor.start_polling(dp, skip_updates=True)
