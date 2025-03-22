# reg sesion, main menu, fsm
import logging
from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from telethon import TelegramClient
from database import save_api_keys, get_api_keys, get_all_accounts, delete_account
from handlers.broadcast_handler import handle_broadcast_menu
from handlers.subscription_handler import handle_subscription_menu

# Настроим логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем состояния FSM
class AuthStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_api_keys = State()
    waiting_for_code = State()
    waiting_for_delete = State()

auth_clients = {}  # Временное хранилище

def register_auth_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_sessions, Text(equals="📂 Сессии"), state=None)
    dp.register_message_handler(handle_add_account, Text(equals="📲 Добавить аккаунт"), state=None)
    dp.register_message_handler(process_phone, state=AuthStates.waiting_for_phone)
    dp.register_message_handler(handle_set_api, Text(equals="🔑 Ввести API ключи"), state=None)
    dp.register_message_handler(process_api_keys, state=AuthStates.waiting_for_api_keys)
    dp.register_message_handler(handle_confirm_code, Text(equals="✅ Подтвердить вход"), state=None)
    dp.register_message_handler(process_confirmation_code, state=AuthStates.waiting_for_code)
    dp.register_message_handler(handle_delete_account, Text(equals="🗑 Удалить аккаунт"), state=None)
    dp.register_message_handler(process_delete_account, state=AuthStates.waiting_for_delete)
    dp.register_message_handler(handle_account_statistics, Text(equals="📊 Статистика аккаунтов"), state=None)
    dp.register_message_handler(handle_back, Text(equals="⬅ Назад"), state="*")  # ✅ Добавлено!
    dp.register_message_handler(handle_broadcast_menu, Text(equals="📢 Рассылка"), state=None)
    dp.register_message_handler(handle_subscription_menu, Text(equals="📢 Подписки"), state=None)

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📂 Сессии"))
    keyboard.add(KeyboardButton("📢 Рассылка"))
    keyboard.add(KeyboardButton("📢 Подписки"))
    return keyboard


def get_sessions_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("📲 Добавить аккаунт"))
    keyboard.add(KeyboardButton("🔑 Ввести API ключи"))
    keyboard.add(KeyboardButton("✅ Подтвердить вход"))
    keyboard.add(KeyboardButton("🗑 Удалить аккаунт"))
    keyboard.add(KeyboardButton("📊 Статистика аккаунтов"))
    keyboard.add(KeyboardButton("⬅ Назад"))
    return keyboard

# Обработка кнопки "Сессии"
async def handle_sessions(message: types.Message):
    accounts = get_all_accounts()
    count = len(accounts)
    response = f"📊 Подключенные аккаунты: {count}\n"
    if count > 0:
        for acc in accounts:
            response += f"📌 {acc[1]} - Статус: {acc[4]}\n"
    else:
        response += "⚠ Нет активных аккаунтов."

    await message.reply(response, reply_markup=get_sessions_keyboard())

#  Обработка кнопки "🗑 Удалить аккаунт"
async def handle_delete_account(message: types.Message):
    await message.reply("Введите номер телефона аккаунта, который хотите удалить:")
    await AuthStates.waiting_for_delete.set()

#  Удаление аккаунта
async def process_delete_account(message: types.Message, state: FSMContext):
    phone_number = message.text.strip()
    try:
        delete_account(phone_number)
        logger.info(f"Аккаунт {phone_number} удален.")  # Логирование успешного удаления
        await message.reply(f"✅ Аккаунт {phone_number} удален.", reply_markup=get_sessions_keyboard())
    except Exception as e:
        logger.error(f"Ошибка при удалении аккаунта {phone_number}: {e}")  # Логирование ошибки
        await message.reply(f"❌ Ошибка при удалении аккаунта {phone_number}.", reply_markup=get_sessions_keyboard())
    await state.finish()

# Подробная статистика аккаунтов
async def handle_account_statistics(message: types.Message):
    accounts = get_all_accounts()
    count = len(accounts)
    response = f"📊 Статистика аккаунтов:\n📌 Всего подключено: {count}\n"
    if count > 0:
        for acc in accounts:
            response += f"📌 {acc[1]} - Статус: {acc[4]}\n"
    else:
        response += "⚠ Нет активных аккаунтов."
    await message.reply(response, reply_markup=get_sessions_keyboard())

# Обработка кнопки "⬅ Назад"
async def handle_back(message: types.Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню рассылки.")

    # Проверяем текущее состояние, если это не отмена - просто возвращаем в меню
    current_state = await state.get_state()

    if current_state is None:
        await message.reply("Вы уже в главном меню.", reply_markup=get_broadcast_keyboard())
    else:
        await message.reply("Возвращаюсь в главное меню рассылки...", reply_markup=get_broadcast_keyboard())

    await state.finish()


#  Пользователь нажимает "📲 Добавить аккаунт"
async def handle_add_account(message: types.Message):
    await message.reply("Введите ваш номер телефона в формате: +79991234567", reply_markup=get_main_keyboard())
    await AuthStates.waiting_for_phone.set()

#  Ввод номера телефона
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.text
    auth_clients[message.chat.id] = {"phone_number": phone_number}
    logger.info(f"Номер телефона {phone_number} сохранен.")  # Логирование сохранения номера
    await message.reply("Теперь введите API ID и API HASH через пробел (например: 1234567 abcdefghijklmnopqrstuvwxyz)", reply_markup=get_main_keyboard())
    await AuthStates.waiting_for_api_keys.set()

#  Пользователь нажимает "🔑 Ввести API ключи"
async def handle_set_api(message: types.Message):
    await message.reply("Введите API ID и API HASH через пробел", reply_markup=get_main_keyboard())
    await AuthStates.waiting_for_api_keys.set()

#  Ввод API ID и API HASH
async def process_api_keys(message: types.Message, state: FSMContext):
    if message.chat.id not in auth_clients or "phone_number" not in auth_clients[message.chat.id]:
        await message.reply("Сначала введите номер телефона через \"📲 Добавить аккаунт\".", reply_markup=get_main_keyboard())
        return

    args = message.text.split()
    if len(args) != 2:
        await message.reply("Неверный формат. Введите API ID и API HASH через пробел.", reply_markup=get_main_keyboard())
        return

    api_id, api_hash = int(args[0]), args[1]
    phone_number = auth_clients[message.chat.id]["phone_number"]

    try:
        save_api_keys(phone_number, api_id, api_hash)  # Сохраняем API в базу
        logger.info(f"API ключи сохранены для {phone_number}.")  # Логирование сохранения API
        await message.reply(f"API ключи сохранены для {phone_number}. Теперь используйте ✅ Подтвердить вход.", reply_markup=get_main_keyboard())
        await state.finish()
    except Exception as e:
        logger.error(f"Ошибка при сохранении API ключей для {phone_number}: {e}")  # Логирование ошибки
        await message.reply(f"❌ Ошибка при сохранении API ключей.", reply_markup=get_main_keyboard())

#  Отправка кода подтверждения
async def handle_confirm_code(message: types.Message):
    if message.chat.id not in auth_clients or "phone_number" not in auth_clients[message.chat.id]:
        await message.reply("Сначала введите номер телефона и API-ключи.", reply_markup=get_main_keyboard())
        return

    phone_number = auth_clients[message.chat.id]["phone_number"]
    api_keys = get_api_keys(phone_number)

    if not api_keys:
        await message.reply("API-ключи не найдены. Введите их заново через \"🔑 Ввести API ключи\".", reply_markup=get_main_keyboard())
        return

    api_id, api_hash = api_keys
    session_name = f"session_{phone_number}"
    client = TelegramClient(session_name, api_id, api_hash)

    await client.connect()
    logger.info(f"📩 Отправка запроса на код для {phone_number}")

    try:
        # Отправляем новый код
        code_request = await client.send_code_request(phone_number)
        auth_clients[message.chat.id]["client"] = client
        auth_clients[message.chat.id]["phone_code_hash"] = code_request.phone_code_hash  # Обновляем hash кода
        await message.reply("Введите код подтверждения, который пришел вам в Telegram.", reply_markup=get_main_keyboard())
        await AuthStates.waiting_for_code.set()
    except Exception as e:
        logger.error(f"Ошибка при отправке кода для {phone_number}: {e}")  # Логирование ошибки
        await message.reply(f"Ошибка при отправке кода: {e}", reply_markup=get_main_keyboard())

#  Подтверждение кода
async def process_confirmation_code(message: types.Message, state: FSMContext):
    if message.chat.id not in auth_clients or "phone_number" not in auth_clients[message.chat.id]:
        await message.reply("Сначала введите номер телефона и API-ключи.", reply_markup=get_main_keyboard())
        return

    phone_number = auth_clients[message.chat.id]["phone_number"]
    client = auth_clients[message.chat.id].get("client")
    phone_code_hash = auth_clients[message.chat.id].get("phone_code_hash")

    if not client or not phone_code_hash:
        await message.reply("Ошибка: код не был запрошен. Используйте ✅ Подтвердить вход заново.", reply_markup=get_main_keyboard())
        return

    try:
        # Авторизуемся с новым кодом
        await client.sign_in(phone_number, message.text, phone_code_hash=phone_code_hash)
        logger.info(f"✅ Аккаунт {phone_number} успешно авторизован!")  # Логирование успеха
        await message.reply("✅ Аккаунт успешно авторизован!", reply_markup=get_main_keyboard())
        await state.finish()
    except Exception as e:
        if "confirmation code has expired" in str(e).lower():
            await message.reply("❌ Код подтверждения устарел! Нажмите ✅ Подтвердить вход, чтобы запросить новый код.", reply_markup=get_main_keyboard())
        else:
            logger.error(f"Ошибка при подтверждении кода для {phone_number}: {e}")  # Логирование ошибки
            await message.reply(f"❌ Ошибка при подтверждении кода: {e}", reply_markup=get_main_keyboard())

