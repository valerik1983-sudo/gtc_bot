# consult_bot.py
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import sqlite3

# Добавляем путь к основной папке
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Импорты из основного проекта
from config import ADMIN_ID, MAIN_BOT_USERNAME, MAIN_BOT_TOKEN
from database import get_user, get_sponsor, add_event

# Токен из конфига
load_dotenv()

TOKEN = os.getenv('CONSULT_BOT_TOKEN')
if not TOKEN:
    raise ValueError("CONSULT_BOT_TOKEN не найден в .env файле!")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ==================== СОСТОЯНИЯ ====================
class ReplyState(StatesGroup):
    waiting_for_reply = State()
    waiting_user_reply = State()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def safe_get(row, key, default=None):
    """Безопасное получение значения из sqlite3.Row или dict"""
    if row is None:
        return default
    if hasattr(row, 'keys') and key in row.keys():
        return row[key]
    if isinstance(row, dict) and key in row:
        return row[key]
    return default


# ==================== БАЗА ДАННЫХ КОНСУЛЬТАЦИЙ ====================
def init_consult_db():
    conn = sqlite3.connect("consultations.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consult_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sponsor_id INTEGER,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_message_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_consult_request(user_id, sponsor_id):
    conn = sqlite3.connect("consultations.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO consult_requests (user_id, sponsor_id, status) VALUES (?, ?, 'active')",
        (user_id, sponsor_id)
    )
    consult_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return consult_id


def get_active_consult(user_id):
    conn = sqlite3.connect("consultations.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM consult_requests WHERE user_id = ? AND status = 'active'",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result


def get_consult_by_id(consult_id):
    conn = sqlite3.connect("consultations.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM consult_requests WHERE id = ?",
        (consult_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return result


def update_consult_status(consult_id, status):
    conn = sqlite3.connect("consultations.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE consult_requests SET status = ? WHERE id = ?",
        (status, consult_id)
    )
    conn.commit()
    conn.close()


def update_last_message(consult_id):
    conn = sqlite3.connect("consultations.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE consult_requests SET last_message_at = CURRENT_TIMESTAMP WHERE id = ?",
        (consult_id,)
    )
    conn.commit()
    conn.close()


# ==================== КЛАВИАТУРЫ ====================
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📞 Задать вопрос наставнику")],
        [KeyboardButton(text="🔙 Главное меню")],
        [KeyboardButton(text="❌ Завершить консультацию")]
    ],
    resize_keyboard=True
)


def reply_keyboard(user_id, consult_id):
    """Клавиатура для НАСТАВНИКА при уведомлении о новом запросе"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Ответить пользователю",
                    callback_data=f"reply_consult_{consult_id}_{user_id}"
                )
            ]
            # Убрали кнопку "Пожаловаться" - она не нужна наставнику
        ]
    )


def user_reply_keyboard(consult_id, mentor_id):
    """Клавиатура для пользователя, чтобы ответить наставнику"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Ответить наставнику",
                    callback_data=f"user_reply_{consult_id}_{mentor_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Завершить консультацию",
                    callback_data=f"user_end_consult_{consult_id}"
                )
            ]
        ]
    )

def user_waiting_keyboard(consult_id):
    """Клавиатура для ПОЛЬЗОВАТЕЛЯ, когда он ждёт ответ"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⚠️ Пожаловаться (нет ответа)",
                    callback_data=f"complaint_{consult_id}"
                )
            ]
        ]
    )    


def back_to_main_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔙 Вернуться в главный бот",
                    url=f"https://t.me/{MAIN_BOT_USERNAME}"
                )
            ]
        ]
    )


# ==================== ОБРАБОТЧИКИ ====================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в консультационный центр Global Trend!\n\n"
        "Здесь вы можете задать вопрос вашему наставнику.\n\n"
        "📞 Нажмите 'Задать вопрос наставнику', чтобы начать.",
        reply_markup=main_menu
    )


@dp.message(F.text == "🔙 Главное меню")
async def back_to_main(message: Message):
    await message.answer(
        "🔙 Возвращаем вас в главный бот.\n\n"
        "Нажмите на кнопку ниже, чтобы открыть главное меню:",
        reply_markup=back_to_main_menu_keyboard()
    )


@dp.message(F.text == "📞 Задать вопрос наставнику")
async def ask_question(message: Message):
    user_id = message.from_user.id
    
    active = get_active_consult(user_id)
    if active:
        await message.answer("⚠️ У вас уже есть активная консультация. Ожидайте ответа наставника.")
        return
    
    user = get_user(user_id)
    if not user:
        await message.answer(
            "❌ Вы не зарегистрированы в системе.\n\n"
            "Пожалуйста, сначала зарегистрируйтесь в главном боте: "
            f"https://t.me/{MAIN_BOT_USERNAME}"
        )
        return
    
    sponsor = get_sponsor(user_id)
    sponsor_id = None
    
    if sponsor and sponsor['sponsor_id']:
        sponsor_id = sponsor['sponsor_id']
        sponsor_user = get_user(int(sponsor_id))
        if sponsor_user:
            print(f"✅ Наставник найден: {sponsor_user['fio']} (ID: {sponsor_id})")
        else:
            sponsor_id = None
    else:
        print(f"⚠️ У пользователя {user_id} нет наставника")
    
    consult_id = save_consult_request(user_id, sponsor_id)
    user_phone = safe_get(user, 'phone', 'Не указан')
    user_city = safe_get(user, 'city', 'Не указан')
    
    if sponsor_id:
        try:
            await bot.send_message(
                int(sponsor_id),
                f"🆕 **Новый запрос консультации!**\n\n"
                f"👤 Пользователь: {safe_get(user, 'fio', 'Пользователь')}\n"
                f"📞 Телефон: {user_phone}\n"
                f"🏙️ Город: {user_city}\n"
                f"📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                reply_markup=reply_keyboard(user_id, consult_id),
                parse_mode="Markdown"
            )
            print(f"✅ Уведомление отправлено наставнику {sponsor_id}")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            await bot.send_message(
                ADMIN_ID,
                f"⚠️ **Новый запрос консультации (ошибка отправки наставнику)**\n\n"
                f"👤 Пользователь: {safe_get(user, 'fio', 'Пользователь')}\n"
                f"📞 Телефон: {user_phone}\n"
                f"🏙️ Город: {user_city}",
                reply_markup=reply_keyboard(user_id, consult_id),
                parse_mode="Markdown"
            )
    else:
        await bot.send_message(
            ADMIN_ID,
            f"⚠️ **Новый запрос консультации (нет наставника)**\n\n"
            f"👤 Пользователь: {safe_get(user, 'fio', 'Пользователь')}\n"
            f"📞 Телефон: {user_phone}\n"
            f"🏙️ Город: {user_city}",
            reply_markup=reply_keyboard(user_id, consult_id),
            parse_mode="Markdown"
        )
    
    await message.answer(
        "✅ Ваш запрос передан наставнику.\n\n"
        "Ожидайте ответа в этом чате.\n\n"
        "📌 Если ответа нет в течение 6 часов, нажмите на кнопку ниже.",
        reply_markup=user_waiting_keyboard(consult_id)
    )

@dp.callback_query(lambda c: c.data.startswith("user_complaint_"))
async def user_complaint(callback: CallbackQuery):
    consult_id = int(callback.data.replace("user_complaint_", ""))
    user_id = callback.from_user.id
    
    # Проверяем, что консультация существует
    consult = get_consult_by_id(consult_id)
    if not consult:
        await callback.message.answer("❌ Консультация не найдена")
        await callback.answer()
        return
    
    # Обновляем статус
    update_consult_status(consult_id, "complaint")
    
    await callback.message.answer("⚠️ Жалоба принята! Администратор рассмотрит.")
    
    from aiogram import Bot
    from config import MAIN_BOT_TOKEN, ADMIN_ID
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from database import get_user
    
    main_bot = Bot(token=MAIN_BOT_TOKEN)
    
    # Получаем данные пользователя
    user = get_user(user_id)
    user_fio = user.get('fio', 'Не указано') if user else 'Не указано'
    user_phone = user.get('phone', 'Не указан') if user else 'Не указан'
    user_city = user.get('city', 'Не указан') if user else 'Не указан'
    user_username = user.get('username', 'Нет') if user else 'Нет'
    
    # Получаем данные консультации
    consult = get_consult_by_id(consult_id)
    sponsor_id = consult[2] if consult else None
    created_at = consult[4] if consult else 'Неизвестно'
    
    # Получаем данные наставника
    sponsor_name = "Не назначен"
    sponsor_phone = "Не указан"
    sponsor_username = "Нет"
    if sponsor_id:
        sponsor = get_user(sponsor_id)
        if sponsor:
            sponsor_name = sponsor.get('fio', 'Не указано')
            sponsor_phone = sponsor.get('phone', 'Не указан')
            sponsor_username = sponsor.get('username', 'Нет')
    
    # Формируем текст уведомления
    notification_text = (
        f"⚠️ **ЖАЛОБА НА КОНСУЛЬТАЦИЮ!**\n\n"
        f"📋 **Консультация #{consult_id}**\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 **ПОЛЬЗОВАТЕЛЬ:**\n"
        f"   • ФИО: {user_fio}\n"
        f"   • ID: {user_id}\n"
        f"   • Телефон: {user_phone}\n"
        f"   • Город: {user_city}\n"
        f"   • Username: @{user_username}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👨‍🏫 **НАСТАВНИК:**\n"
        f"   • ФИО: {sponsor_name}\n"
        f"   • ID: {sponsor_id or 'Не назначен'}\n"
        f"   • Телефон: {sponsor_phone}\n"
        f"   • Username: @{sponsor_username}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 Дата создания консультации: {created_at}\n\n"
        f"Нажмите на кнопку, чтобы ответить пользователю."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✏️ Ответить на жалобу", 
            callback_data=f"admin_reply_complaint_{consult_id}_{user_id}"
        )]
    ])
    
    await main_bot.send_message(
        ADMIN_ID,
        notification_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await main_bot.session.close()
    await callback.answer()    


@dp.message(F.text == "❌ Завершить консультацию")
async def end_consultation(message: Message):
    user_id = message.from_user.id
    active = get_active_consult(user_id)
    if active:
        update_consult_status(active[0], "closed")
        await message.answer(
            "👋 Консультация завершена.\n\n"
            "Если появятся вопросы, снова нажмите '📞 Задать вопрос наставнику'.",
            reply_markup=main_menu
        )
    else:
        await message.answer("❌ У вас нет активной консультации.")


@dp.callback_query(lambda c: c.data.startswith("reply_consult_"))
async def reply_to_user(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    consult_id = int(parts[2])
    user_id = int(parts[3])
    
    update_consult_status(consult_id, "active")
    await state.update_data(reply_user_id=user_id, consult_id=consult_id)
    await state.set_state(ReplyState.waiting_for_reply)
    
    await callback.message.answer("✏️ Введите ответ для пользователя:")
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("complaint_"))
async def handle_complaint(callback: CallbackQuery):
    parts = callback.data.split("_")
    consult_id = int(parts[1])
    user_id = callback.from_user.id 
    
    update_consult_status(consult_id, "complaint")
    
    await callback.message.answer("⚠️ Жалоба принята! Администратор рассмотрит.")
    
    from aiogram import Bot
    from config import MAIN_BOT_TOKEN, ADMIN_ID
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from database import get_user, get_sponsor
    
    main_bot = Bot(token=MAIN_BOT_TOKEN)
    
    # Получаем данные пользователя
    user = get_user(user_id)
    user_fio = user.get('fio', 'Не указано') if user else 'Не указано'
    user_phone = user.get('phone', 'Не указан') if user else 'Не указан'
    user_city = user.get('city', 'Не указан') if user else 'Не указан'
    user_username = user.get('username', 'Нет') if user else 'Нет'
    
    # Получаем данные консультации (consult - это кортеж)
    consult = get_consult_by_id(consult_id)
    sponsor_id = consult[2] if consult else None
    created_at = consult[4] if consult else 'Неизвестно'
    
    # Получаем данные наставника
    sponsor_name = "Не назначен"
    sponsor_phone = "Не указан"
    sponsor_username = "Нет"
    if sponsor_id:
        sponsor = get_user(sponsor_id)
        if sponsor:
            sponsor_name = sponsor.get('fio', 'Не указано')
            sponsor_phone = sponsor.get('phone', 'Не указан')
            sponsor_username = sponsor.get('username', 'Нет')
    
    # Формируем текст уведомления
    notification_text = (
        f"⚠️ **ЖАЛОБА НА КОНСУЛЬТАЦИЮ!**\n\n"
        f"📋 **Консультация #{consult_id}**\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 **ПОЛЬЗОВАТЕЛЬ:**\n"
        f"   • ФИО: {user_fio}\n"
        f"   • ID: {user_id}\n"
        f"   • Телефон: {user_phone}\n"
        f"   • Город: {user_city}\n"
        f"   • Username: @{user_username}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👨‍🏫 **НАСТАВНИК:**\n"
        f"   • ФИО: {sponsor_name}\n"
        f"   • ID: {sponsor_id or 'Не назначен'}\n"
        f"   • Телефон: {sponsor_phone}\n"
        f"   • Username: @{sponsor_username}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 Дата создания консультации: {created_at}\n\n"
        f"Нажмите на кнопку, чтобы ответить пользователю."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✏️ Ответить на жалобу", 
            callback_data=f"admin_reply_complaint_{consult_id}_{user_id}"
        )]
    ])
    
    await main_bot.send_message(
        ADMIN_ID,
        notification_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await main_bot.session.close()
    await callback.answer()


@dp.message(StateFilter(ReplyState.waiting_for_reply))
async def send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("reply_user_id")
    consult_id = data.get("consult_id")
    
    if not target_user_id:
        await state.clear()
        await message.answer("❌ Ошибка: не найден получатель.")
        return
    
    try:
        mentor_id = message.from_user.id
        
        # Получаем имя наставника
        from database import get_user
        mentor = get_user(mentor_id)
        mentor_name = mentor.get('fio', 'Наставник') if mentor else 'Наставник'
        
        # Отправляем ответ пользователю с именем наставника
        if message.text:
            await bot.send_message(
                target_user_id,
                f"📩 **{mentor_name}:**\n\n{message.text}",
                reply_markup=user_reply_keyboard(consult_id, mentor_id),
                parse_mode="Markdown"
            )
        elif message.photo:
            await bot.send_photo(
                target_user_id,
                message.photo[-1].file_id,
                caption=f"📩 **{mentor_name}:**\n\n{message.caption or ''}",
                reply_markup=user_reply_keyboard(consult_id, mentor_id)
            )
        else:
            await message.answer("⚠️ Неподдерживаемый тип сообщения.")
            return
        
        update_last_message(consult_id)
        
        # Уведомление в основной бот
        from aiogram import Bot
        from config import MAIN_BOT_TOKEN, CONSULT_BOT_USERNAME
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        main_bot = Bot(token=MAIN_BOT_TOKEN)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💬 Перейти к ответу", 
                url=f"https://t.me/{CONSULT_BOT_USERNAME}"
            )]
        ])
        
        await main_bot.send_message(
            target_user_id,
            f"🔔 **{mentor_name} ответил вам в консультационном боте!**\n\n"
            f"Нажмите на кнопку ниже, чтобы прочитать ответ.",
            reply_markup=keyboard
        )
        
        await main_bot.session.close()
        
        await message.answer("✅ Ответ отправлен пользователю!")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()


@dp.callback_query(lambda c: c.data.startswith("user_reply_"))
async def user_reply_to_mentor(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    consult_id = int(parts[2])
    mentor_id = int(parts[3])
    
    await state.update_data(
        reply_to_mentor_id=mentor_id,
        user_consult_id=consult_id,
        user_id=callback.from_user.id
    )
    await state.set_state(ReplyState.waiting_user_reply)
    
    await callback.message.answer("✏️ Введите ваше сообщение для наставника:")
    await callback.answer()


@dp.message(StateFilter(ReplyState.waiting_user_reply))
async def send_user_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    mentor_id = data.get("reply_to_mentor_id")
    consult_id = data.get("user_consult_id")
    user_id = data.get("user_id")
    
    if not mentor_id:
        await state.clear()
        await message.answer("❌ Ошибка: не найден получатель.")
        return
    
    try:
        # Получаем имя пользователя
        from database import get_user
        user = get_user(user_id)
        user_name = user.get('fio', 'Пользователь') if user else 'Пользователь'
        
        # Отправляем ответ наставнику с именем пользователя
        if message.text:
            await bot.send_message(
                mentor_id,
                f"💬 **{user_name}:**\n\n{message.text}",
                reply_markup=reply_keyboard(user_id, consult_id),
                parse_mode="Markdown"
            )
        elif message.photo:
            await bot.send_photo(
                mentor_id,
                message.photo[-1].file_id,
                caption=f"💬 **{user_name}:**\n\n{message.caption or ''}",
                reply_markup=reply_keyboard(user_id, consult_id)
            )
        else:
            await message.answer("⚠️ Неподдерживаемый тип сообщения.")
            return
        
        update_last_message(consult_id)
        await message.answer("✅ Ваш ответ отправлен наставнику!")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()


@dp.callback_query(lambda c: c.data.startswith("user_end_consult_"))
async def user_end_consult(callback: CallbackQuery):
    parts = callback.data.split("_")
    consult_id = int(parts[3])
    
    update_consult_status(consult_id, "closed")
    await callback.message.answer(
        "👋 Консультация завершена.\n\nСпасибо за обращение!",
        reply_markup=main_menu
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("admin_reply_complaint_"))
async def admin_reply_complaint(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    consult_id = int(parts[3])
    user_id = int(parts[4])
    
    await state.update_data(
        reply_complaint_consult_id=consult_id,
        reply_complaint_user_id=user_id
    )
    await state.set_state("admin_waiting_complaint_reply")
    
    await callback.message.answer("✏️ Введите ответ для пользователя (по жалобе):")
    await callback.answer()


@dp.message(StateFilter("admin_waiting_complaint_reply"))
async def admin_send_complaint_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    consult_id = data.get("reply_complaint_consult_id")
    user_id = data.get("reply_complaint_user_id")
    
    if not user_id:
        await message.answer("❌ Ошибка: пользователь не найден")
        await state.clear()
        return
    
    try:
        # Получаем имя администратора
        from database import get_user
        admin = get_user(message.from_user.id)
        admin_name = admin.get('fio', 'Администратор') if admin else 'Администратор'
        
        # Отправляем уведомление в основной бот
        from aiogram import Bot
        from config import MAIN_BOT_TOKEN, CONSULT_BOT_USERNAME
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        main_bot = Bot(token=MAIN_BOT_TOKEN)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💬 Перейти к ответу", 
                url=f"https://t.me/{CONSULT_BOT_USERNAME}"
            )]
        ])

        await main_bot.send_message(
            user_id,
            f"🔔 **{admin_name} (администратор) ответил вам в консультационном боте!**\n\n"
            f"Нажмите на кнопку ниже, чтобы прочитать ответ:",
            reply_markup=keyboard
        )

        await main_bot.session.close()
        
        # Отправляем ответ пользователю в консультационном боте
        await bot.send_message(
            user_id,
            f"📩 **{admin_name} (администратор):**\n\n{message.text}\n\n"
            f"Извините за неудобства. Если у вас остались вопросы, "
            f"вы можете снова обратиться к наставнику."
        )
        
        update_consult_status(consult_id, "resolved")
        
        await message.answer("✅ Ответ отправлен пользователю!")
        
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    
    await state.clear()

# ==================== ЗАПУСК ====================
def start_consult_bot():
    init_consult_db()
    print("🤖 Консультационный бот запущен")
    asyncio.run(dp.start_polling(bot))


if __name__ == "__main__":
    start_consult_bot()