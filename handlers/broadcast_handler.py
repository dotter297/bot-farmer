# рассыока
import logging
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from telethon import TelegramClient
from database import get_all_accounts


# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Определяем состояния FSM
class BroadcastStates(StatesGroup):
    waiting_for_chat_id = State()
    waiting_for_message = State()
    waiting_for_account_selection = State()
    waiting_for_message_count = State()  # Новое состояние для выбора количества сообщений


broadcast_data = {}  # Временное хранилище


def register_broadcast_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_broadcast_menu, Text(equals="📢 Рассылка"), state=None)
    dp.register_message_handler(start_broadcast, Text(equals="📢 Новая рассылка"), state=None)
    dp.register_message_handler(handle_back, Text(equals="⬅ Назад"), state="*")
    dp.register_message_handler(process_chat_id, state=BroadcastStates.waiting_for_chat_id)
    dp.register_message_handler(process_message, state=BroadcastStates.waiting_for_message)
    dp.register_message_handler(process_account_selection, state=BroadcastStates.waiting_for_account_selection)
    dp.register_message_handler(process_message_count, state=BroadcastStates.waiting_for_message_count)  # Новая обработка


def get_broadcast_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📢 Новая рассылка"))
    keyboard.add(KeyboardButton("⬅ Назад"))
    return keyboard


def get_cancel_keyboard():
    """Клавиатура с кнопкой отмены"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("⬅ Отмена"))
    return keyboard


# 1️⃣ Меню рассылки
async def handle_broadcast_menu(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} открыл меню рассылки.")
    await message.reply("📢 Меню рассылки. Выберите действие:", reply_markup=get_broadcast_keyboard())


# 2️⃣ Начало рассылки
async def start_broadcast(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} начал новую рассылку.")
    await message.reply("Введите ID чата, куда отправлять сообщения:")
    await BroadcastStates.waiting_for_chat_id.set()


# 3️⃣ Получение ID чата
async def process_chat_id(message: types.Message, state: FSMContext):
    chat_id = message.text.strip()
    broadcast_data[message.chat.id] = {"chat_id": chat_id}

    logger.info(f"Пользователь {message.from_user.id} ввел ID чата: {chat_id}")
    await message.reply("Теперь отправьте сообщение, которое хотите разослать:", reply_markup=get_cancel_keyboard())
    await BroadcastStates.waiting_for_message.set()


# 4️⃣ Получение сообщения
async def process_message(message: types.Message, state: FSMContext):
    if message.chat.id not in broadcast_data:
        logger.warning(f"Ошибка: отсутствуют данные для {message.chat.id}. Завершаем процесс.")
        await message.reply("⚠ Произошла ошибка. Попробуйте начать рассылку заново.", reply_markup=get_broadcast_keyboard())
        await state.finish()
        return

    broadcast_data[message.chat.id]["message"] = message.text
    logger.info(f"Пользователь {message.from_user.id} отправил сообщение для рассылки: {message.text}")

    accounts = get_all_accounts()
    if not accounts:
        logger.warning("Нет доступных аккаунтов для рассылки.")
        await message.reply("⚠ Нет доступных аккаунтов для рассылки.", reply_markup=get_broadcast_keyboard())
        await state.finish()
        return

    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Все аккаунты"))
    for acc in accounts:
        keyboard.add(KeyboardButton(acc[1]))
    keyboard.add(KeyboardButton("⬅ Отмена"))

    await message.reply("Выберите аккаунты для рассылки:", reply_markup=keyboard)
    await BroadcastStates.waiting_for_account_selection.set()


# 5️⃣ Выбор аккаунтов для рассылки
async def process_account_selection(message: types.Message, state: FSMContext):
    if message.chat.id not in broadcast_data:
        logger.warning(f"Ошибка: отсутствуют данные для {message.chat.id}. Завершаем процесс.")
        await message.reply("⚠ Произошла ошибка. Попробуйте начать рассылку заново.", reply_markup=get_broadcast_keyboard())
        await state.finish()
        return

    if message.text == "⬅ Отмена":
        logger.info(f"Пользователь {message.from_user.id} отменил рассылку.")
        await message.reply("❌ Рассылка отменена.", reply_markup=get_broadcast_keyboard())
        await state.finish()
        return

    selected_accounts = []
    accounts = get_all_accounts()
    account_numbers = [acc[1] for acc in accounts]

    if message.text == "Все аккаунты":
        selected_accounts = account_numbers
    elif message.text in account_numbers:
        selected_accounts.append(message.text)
    else:
        logger.warning(f"Пользователь {message.from_user.id} ввел неверный аккаунт: {message.text}")
        await message.reply("⚠ Неверный выбор. Выберите аккаунт из списка.")
        return

    broadcast_data[message.chat.id]["accounts"] = selected_accounts
    chat_id = broadcast_data[message.chat.id]["chat_id"]
    message_text = broadcast_data[message.chat.id]["message"]

    # Переходим к выбору количества сообщений
    await message.reply("Сколько раз вы хотите отправить это сообщение? Введите количество:", reply_markup=get_cancel_keyboard())
    await BroadcastStates.waiting_for_message_count.set()


# 6️⃣ Получение количества сообщений
async def process_message_count(message: types.Message, state: FSMContext):
    if message.chat.id not in broadcast_data:
        logger.warning(f"Ошибка: отсутствуют данные для {message.chat.id}. Завершаем процесс.")
        await message.reply("⚠ Произошла ошибка. Попробуйте начать рассылку заново.", reply_markup=get_broadcast_keyboard())
        await state.finish()
        return

    if message.text == "⬅ Отмена":
        logger.info(f"Пользователь {message.from_user.id} отменил рассылку.")
        await message.reply("❌ Рассылка отменена.", reply_markup=get_broadcast_keyboard())
        await state.finish()
        return

    try:
        message_count = int(message.text)
        if message_count < 1:
            raise ValueError("Количество должно быть положительным числом.")
    except ValueError:
        await message.reply("⚠ Введите корректное количество сообщений (целое положительное число).")
        return

    broadcast_data[message.chat.id]["message_count"] = message_count
    selected_accounts = broadcast_data[message.chat.id]["accounts"]
    chat_id = broadcast_data[message.chat.id]["chat_id"]
    message_text = broadcast_data[message.chat.id]["message"]

    logger.info(f"Пользователь {message.from_user.id} выбрал количество сообщений: {message_count}")
    await message.reply(f"📢 Начинаю рассылку {message_count} раз в {chat_id} с {len(selected_accounts)} аккаунтов...")

    accounts = get_all_accounts()
    for acc in accounts:
        if acc[1] in selected_accounts:
            session_name = f"session_{acc[1]}"
            client = TelegramClient(session_name, acc[3], acc[4])
            await client.connect()
            try:
                for _ in range(message_count):
                    await client.send_message(chat_id, message_text)
                    await message.reply(f"✅ Сообщение отправлено с {acc[1]}")
                    logger.info(f"Сообщение успешно отправлено с {acc[1]} в {chat_id}")
            except Exception as e:
                await message.reply(f"❌ Ошибка отправки с {acc[1]}: {e}")
                logger.error(f"Ошибка при отправке с {acc[1]}: {e}")
            await client.disconnect()

    await state.finish()
    logger.info(f"Рассылка в {chat_id} завершена.")


# 7️⃣ Обработчик кнопки "⬅ Назад"
async def handle_back(message: types.Message, state: FSMContext):
    from handlers.auth_handler import get_main_keyboard
    logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню рассылки.")
    await message.reply("❌ Рассылка отменена.", reply_markup=get_main_keyboard())
    await state.finish()