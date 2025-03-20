import asyncio
from aiogram import executor
from bot import dp
from database import init_db
from handlers.broadcast_handler import register_broadcast_handlers


async def main():
    try:
        # Инициализация базы данных
        init_db()

        # Регистрируем обработчики
        register_broadcast_handlers(dp)


        # Запускаем бота
        print("Бот запущен!")
        await dp.start_polling()

    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    asyncio.run(main())
