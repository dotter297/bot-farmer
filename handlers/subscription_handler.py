# подписка
import asyncio
import logging
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from telethon import TelegramClient
from database import get_all_accounts
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.channels import LeaveChannelRequest

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Определяем состояния FSM
class SubscriptionStates(StatesGroup):
    waiting_for_channel = State()
    waiting_for_action = State()
    waiting_for_delay = State()
    waiting_for_account_count = State()


# Главное меню подписки
async def handle_subscription_menu(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("➕ Подписаться"))
    keyboard.add(KeyboardButton("➖ Отписаться"))
    keyboard.add(KeyboardButton("⬅ Назад"))
    await message.reply("Выберите действие:", reply_markup=keyboard)


# Выбор канала для подписки
async def handle_choose_channel(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("⬅ Назад"))
    await message.reply("Введите @юзернейм или ссылку на канал:", reply_markup=keyboard)
    await SubscriptionStates.waiting_for_channel.set()


# Получение канала и выбор действия
async def process_channel(message: types.Message, state: FSMContext):
    if message.text.strip() == "⬅ Назад":
        await state.finish()
        await handle_subscription_menu(message)
        return

    await state.update_data(channel=message.text.strip())
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Подписаться"))
    keyboard.add(KeyboardButton("Отписаться"))
    keyboard.add(KeyboardButton("⬅ Назад"))
    await message.reply("Выберите действие:", reply_markup=keyboard)
    await SubscriptionStates.waiting_for_action.set()


# Получение типа действия (подписка/отписка)
async def process_action(message: types.Message, state: FSMContext):
    if message.text.strip() == "⬅ Назад":
        await state.finish()
        await handle_subscription_menu(message)
        return

    action = message.text.strip()
    if action not in ["Подписаться", "Отписаться"]:
        await message.reply("Выберите действие из предложенных.")
        return
    await state.update_data(action=action)
    await message.reply("Введите задержку между действиями (в секундах, например 5):")
    await SubscriptionStates.waiting_for_delay.set()


# Получение задержки
async def process_delay(message: types.Message, state: FSMContext):
    if message.text.strip() == "⬅ Назад":
        await state.finish()
        await handle_subscription_menu(message)
        return

    try:
        delay = int(message.text.strip())
        await state.update_data(delay=delay)
        await message.reply("Введите количество аккаунтов для выполнения действия:")
        await SubscriptionStates.waiting_for_account_count.set()
    except ValueError:
        await message.reply("Введите число секунд (например, 5):")


# Получение количества аккаунтов
async def process_account_count(message: types.Message, state: FSMContext):
    if message.text.strip() == "⬅ Назад":
        await state.finish()
        await handle_subscription_menu(message)
        return

    try:
        account_count = int(message.text.strip())
        data = await state.get_data()
        channel = data['channel']
        action = data['action']
        delay = data['delay']

        accounts = get_all_accounts()[:account_count]  # Берем нужное количество аккаунтов
        if not accounts:
            await message.reply("Нет доступных аккаунтов.")
            await state.finish()
            return

        await message.reply(f"Начинаю {'подписку' if action == 'Подписаться' else 'отписку'} на {channel}...")
        await process_subscription(accounts, channel, action, delay, message)
        await state.finish()
    except ValueError:
        await message.reply("Введите корректное число аккаунтов.")


# Функция подписки/отписки
async def process_subscription(accounts, channel, action, delay, message):
    for account in accounts:
        phone, session_name, api_id, api_hash = account[1], account[2], account[3], account[4]
        client = TelegramClient(session_name, api_id, api_hash)

        try:
            await client.connect()
            if action == "Подписаться":
                await client(JoinChannelRequest(channel))
                await message.reply(f"✅ {phone} подписан на {channel}")
            else:
                await client(LeaveChannelRequest(channel))
                await message.reply(f"❌ {phone} отписан от {channel}")
        except Exception as e:
            await message.reply(f"⚠ Ошибка с аккаунтом {phone}: {e}")
        finally:
            await client.disconnect()

        await asyncio.sleep(delay)  # Задержка


# Регистрация обработчиков
def register_subscription_handlers(dp: Dispatcher):
    dp.register_message_handler(handle_subscription_menu, Text(equals="📢 Подписка/Отписка"), state=None)
    dp.register_message_handler(handle_choose_channel, Text(equals="➕ Подписаться"), state=None)
    dp.register_message_handler(handle_choose_channel, Text(equals="➖ Отписаться"), state=None)
    dp.register_message_handler(handle_back, Text(equals="⬅ Назад"), state="*")
    dp.register_message_handler(process_channel, state=SubscriptionStates.waiting_for_channel)
    dp.register_message_handler(process_action, state=SubscriptionStates.waiting_for_action)
    dp.register_message_handler(process_delay, state=SubscriptionStates.waiting_for_delay)
    dp.register_message_handler(process_account_count, state=SubscriptionStates.waiting_for_account_count)

async def handle_back(message: types.Message, state: FSMContext):
    from handlers.auth_handler import get_main_keyboard
    logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню .")
    await message.reply("❌ Подписка отменена.", reply_markup=get_main_keyboard())
    await state.finish()