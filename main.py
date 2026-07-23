import asyncio
import qrcode
import os
from logger import logger
from dotenv import load_dotenv



logger.info("Бот запущен")

from handlers.menu import router as menu_router
from handlers.consultation_simple import router as consultation_router
from handlers.products import router as products_router
from handlers.complaints import router as complaints_router
from handlers.sponsor_edit import router as sponsor_edit_router
from handlers.referrals import router as referrals_router
from handlers.admin_products import router as admin_products_router
from handlers.orders import router as orders_router
from handlers.cart import router as cart_router
from handlers.cities_admin import router as cities_admin_router
from handlers.diagnostics import router as diagnostics_router
from handlers.registration import router as registration_router


from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.income import router as income_router

from aiogram.types import FSInputFile
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from keyboards import get_main_menu
from inline_keyboards import sponsor_keyboard
from states import Registration, Consultation, MentorMessage, ClientReply, CustomSource
from inline_keyboards import reply_to_mentor_keyboard, people_keyboard, person_card_keyboard
from keyboards import my_people_keyboard, consultations_menu_keyboard
from database import get_user_by_id, update_user_status, update_last_contact, get_events, is_admin, get_admins, add_event, get_connection, get_my_people, get_my_people_count, get_people_count_by_status, get_funnel_stats

from database import (
    init_db, add_user, get_user, get_sponsor, create_consultation,
    get_last_consultation, get_admins, update_consultation_status,
    get_consultation, get_active_consultation, get_my_people, get_user_by_id,
    get_my_people_count, get_people_count_by_status, get_user_by_telegram_id,
    get_funnel_stats, get_referrals_count, get_referrals, get_users_need_attention,
    get_consultation_stats, get_consultations_by_status,
    get_temp_refs_count, get_temp_refs_users,
    save_temp_sponsor,   # 👈 добавить
    clear_temp_sponsor,
    get_temp_sponsor
)

from config import ADMIN_ID, MAIN_BOT_USERNAME # 👈 ДОБАВЛЯЕМ
from handlers.quiz import router as quiz_router

from handlers.invite_generator import router as invite_generator_router


load_dotenv()  # Загружаем .env

TOKEN = os.getenv('MAIN_BOT_TOKEN')
if not TOKEN:
    raise ValueError("MAIN_BOT_TOKEN не найден в .env файле!")
bot = Bot(token=TOKEN)    
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ==================== ПОДКЛЮЧЕНИЕ РОУТЕРОВ ====================


dp.include_router(menu_router)
dp.include_router(products_router)
dp.include_router(consultation_router)
dp.include_router(cart_router)
dp.include_router(orders_router)
dp.include_router(income_router)
dp.include_router(referrals_router)
dp.include_router(cities_admin_router)
dp.include_router(sponsor_edit_router)
dp.include_router(complaints_router)
dp.include_router(admin_products_router)
dp.include_router(quiz_router)
dp.include_router(invite_generator_router)
dp.include_router(diagnostics_router) 
dp.include_router(registration_router)






# ==================== ОБРАБОТЧИКИ MAIN.PY ====================

@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    args = message.text.split()
       
    if len(args) > 1:
        param = args[1]
        sponsor_id = None
        source = None

        # Проверяем, не число ли это (старый формат)
        if param.isdigit():
            sponsor_id = int(param)
            source = 'direct'
        else:
            # Парсим параметры вида sponsor_123_source_flyer
            parts = param.split('_')
            for i, part in enumerate(parts):
                if part == 'sponsor' and i+1 < len(parts):
                    try:
                        sponsor_id = int(parts[i+1])
                    except:
                        pass
                elif part == 'source' and i+1 < len(parts):
                    source = parts[i+1]
            if not source:
                source = 'direct'

        if sponsor_id:
            print(f"🔵🔵🔵 ПОЛУЧЕН СПОНСОР: {sponsor_id}, ИСТОЧНИК: {source}")
            save_temp_sponsor(message.from_user.id, sponsor_id, source)
            await state.update_data(sponsor_id=sponsor_id)
        else:
            print(f"❌ Ошибка парсинга: {param}")
    
    user = get_user(message.from_user.id)
    registered = user is not None
    is_admin_user = is_admin(message.from_user.id)
    team_count = get_referrals_count(message.from_user.id)
    has_team = team_count > 0
    
    # 👇 ОПРЕДЕЛЯЕМ ИМЯ ДЛЯ ПРИВЕТСТВИЯ
    if registered:
        # Зарегистрированный - имя из базы (ФИО)
        user_name = user.get('fio', '') if user else ''
    else:
        # Незарегистрированный - имя из Telegram
        user_name = message.from_user.first_name or ''
    
    # 👇 ФОРМИРУЕМ ПРИВЕТСТВИЕ С ИМЕНЕМ
    if user_name:
        greeting = f"Добро пожаловать, {user_name}!"
    else:
        greeting = "Добро пожаловать!"
    
    is_partner = user.get('role') == 'partner' if user else False
    show_consultation = registered and not is_admin_user and not is_partner

    # 👇 ОТПРАВЛЯЕМ ПРИВЕТСТВИЕ С ИМЕНЕМ
    await message.answer(
        greeting,
        reply_markup=get_main_menu(registered, has_team, is_admin_user)
    )
    
    # Уведомление для незарегистрированных
    if not registered:
        await message.answer(
            f"🌿 Добро пожаловать, {message.from_user.first_name}!\n\n"
            "Здесь вы сможете понять, как повысить уровень энергии и улучшить самочувствие с помощью простых шагов и натуральных решений.\n\n"
            "🔬 **Начните с диагностики**\n"
            "Ответьте на несколько вопросов — получите ваш персональный индекс энергии и рекомендации.\n\n"
            "👉 Нажмите «🔬 Пройти диагностику» в меню\n\n"
            "После диагностики вы сможете:\n"
            "• узнать персональные рекомендации\n"
            "• посмотреть подходящие решения\n"
            "• при желании открыть доступ ко всем возможностям (заказ, партнёрство, доход)\n\n"
            "💚 Всё начинается с диагностики.",
            parse_mode="Markdown"
        )
    # Кнопка консультации только для зарегистрированных, не админов и не партнёров
    elif show_consultation:
        from keyboards import get_inline_consultation_button
        await message.answer(
            "💬 Нужна консультация специалиста?\n\n"
            "Нажмите на кнопку ниже, чтобы задать вопрос вашему наставнику.",
            reply_markup=get_inline_consultation_button()
        )


@dp.message(lambda m: m.text == "🔗 Моя ссылка")
async def my_link(message: Message):
    from database import get_temp_refs_count, get_temp_refs_users
    import qrcode
    import os
    from aiogram.types import FSInputFile
    
    bot_username = "gtcm_assistant_bot"
    link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    qr = qrcode.make(link)
    file_name = f"qr_{message.from_user.id}.png"
    qr.save(file_name)

    # Получаем статистику переходов
    clicks_count = get_temp_refs_count(message.from_user.id)
    clicks_users = get_temp_refs_users(message.from_user.id)
    
    # Считаем зарегистрированных
    registered = sum(1 for c in clicks_users if c.get("registered", False))
    unregistered = clicks_count - registered
    
    text = (
        f"🔗 **Ваша пригласительная ссылка в бот**\n\n"
        f"Делитесь этой ссылкой с друзьями!\n"
        f"Каждый, кто перейдёт по вашей ссылке и зарегистрируется, станет вашим партнёром или клиентом.\n\n"
        f"[👉 Нажмите, чтобы скопировать ссылку]({link})\n\n"  # 👈 КЛИКАБЕЛЬНАЯ ССЫЛКА
        f"Или скопируйте текст ниже:\n"
        f"`{link}`\n\n"
        f"📊 **Статистика ссылки:**\n"
        f"👆 Всего переходов: **{clicks_count}**\n"
        f"✅ Зарегистрировались: **{registered}**\n"
        f"⏳ Ожидают регистрации: **{unregistered}**\n"
    )
    
    # Показываем последние 5 переходов
    if clicks_users:
        text += f"\n📋 **Последние переходы:**\n"
        for i, click in enumerate(clicks_users[:5]):
            icon = "✅" if click.get("registered", False) else "⏳"
            name = click.get("fio") or f"ID: {click['telegram_id']} (не зарегистрирован)"
            date = click.get("created_at", "")[:16] if click.get("created_at") else ""
            text += f"{i+1}. {icon} {name} — {date}\n"
    
    # ===== СТАТИСТИКА ПО ИСТОЧНИКАМ =====
    from database import get_user_link_stats
    stats = get_user_link_stats(message.from_user.id)
    if stats:
        text += "\n📊 **Статистика по источникам:**\n"
        for stat in stats:
            conv = round(stat['registered'] / stat['total'] * 100, 1) if stat['total'] > 0 else 0
            text += f"• {stat['source']}: {stat['total']} переходов, {stat['registered']} регистраций ({conv}%)\n"
    else:
        text += "\n📊 Пока нет переходов по вашей ссылке."
    
    # 👇 ОТПРАВЛЯЕМ ТЕКСТ СО СТАТИСТИКОЙ
    await message.answer(text, parse_mode="Markdown")
    
    # 👇 ОТПРАВЛЯЕМ QR-КОД
    await message.answer_photo(FSInputFile(file_name), caption=f"📱 QR-код вашей ссылки\n\nСсылка: {link}")
    
    if os.path.exists(file_name):
        os.remove(file_name)


@dp.message(lambda m: m.text == "👤 Мой наставник")
async def my_sponsor(message: Message):
    sponsor = get_sponsor(message.from_user.id)
    if not sponsor or not sponsor["sponsor_id"]:
        await message.answer("У вас нет наставника.")
        return
    sponsor_user = get_user(int(sponsor["sponsor_id"]))
    if not sponsor_user:
        await message.answer("Наставник не найден.")
        return
    username = sponsor_user.get("username")
    if username:
        await message.answer(
            f"Ваш наставник:\n\n{sponsor_user['fio']}\n@{username}",
            reply_markup=sponsor_keyboard(username)
        )
    else:
        await message.answer(f"Ваш наставник:\n\n{sponsor_user['fio']}")

@dp.message(lambda m: m.text == "🔗 Ссылка с источником")
async def custom_source_link_start(message: Message, state: FSMContext):
    await state.set_state(CustomSource.waiting_source)
    await message.answer(
        "✏️ Введите название источника (например, `reklama_yandex` или `post_vk`).\n\n"
        "Используйте буквы, цифры и нижнее подчёркивание. Без пробелов.",
        parse_mode="Markdown"
    )


@dp.message(StateFilter(CustomSource.waiting_source))
async def custom_source_link_generate(message: Message, state: FSMContext):
    source_text = message.text.strip()
    
    # Проверяем, что строка допустима (только буквы, цифры, подчёркивание)
    import re
    if not re.match(r'^[a-zA-Z0-9_]+$', source_text):
        await message.answer(
            "❌ Недопустимые символы. Используйте только латинские буквы, цифры и нижнее подчёркивание.\n"
            "Попробуйте снова:"
        )
        return
    
    user_id = message.from_user.id
    link = f"https://t.me/{MAIN_BOT_USERNAME}?start=sponsor_{user_id}_source_{source_text}"
    
    # Генерируем QR-код
    import qrcode
    import os
    from aiogram.types import FSInputFile
    
    qr = qrcode.make(link)
    file_name = f"qr_{user_id}_{source_text}.png"
    qr.save(file_name)
    
    await message.answer(
        f"✅ **Ссылка с источником `{source_text}` готова:**\n\n"
        f"`{link}`\n\n"
        f"📊 Все переходы по этой ссылке будут отображаться в статистике с источником `{source_text}`.",
        parse_mode="Markdown"
    )
    
    await message.answer_photo(
        FSInputFile(file_name),
        caption=f"📱 QR-код для источника `{source_text}`"
    )
    
    if os.path.exists(file_name):
        os.remove(file_name)
    
    await state.clear()        
        

@dp.message(lambda m: m.text == "👥 Мои люди")
async def my_people(message: Message):
    from database import get_referrals_count, get_total_referrals_count, get_referrals
    direct = get_referrals_count(message.from_user.id)
    total = get_total_referrals_count(message.from_user.id)
    
    if total == 0:
        await message.answer("У вас пока нет людей в структуре.")
        return
    
    users = get_referrals(message.from_user.id)  # прямые приглашённые
    text = f"👥 Прямых: {direct}  |  Всего в структуре: {total}\n\n"
    for user in users:
        d = get_referrals_count(user['telegram_id'])
        t = get_total_referrals_count(user['telegram_id'])
        text += f"• {user['fio']} — Статус: {user['status']}  (в команде: {d} личных, {t} всего)\n"
    await message.answer(text, reply_markup=my_people_keyboard(users))


@dp.callback_query(lambda c: c.data.startswith("person_"))
async def person_card(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    user = get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.")
        return
    await callback.message.answer(build_person_card(user), reply_markup=person_card_keyboard(user["telegram_id"]))
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("status_") and not c.data.startswith("order_status_"))
async def change_status(callback: CallbackQuery):
    parts = callback.data.split("_")
    status = parts[1]   
    telegram_id = int(parts[2])
    update_user_status(telegram_id, status)
    add_event(telegram_id, "status", f"Статус изменен на {status}")
    user = get_user_by_telegram_id(telegram_id)
    await callback.message.edit_text(build_person_card(user), reply_markup=person_card_keyboard(telegram_id))
    await callback.answer("Статус обновлен ✅")


def get_status_text(status):
    statuses = {
        "new": "⚪ Новый", "work": "🟡 В работе", "client": "🟢 Клиент",
        "partner": "💎 Партнер", "failed": "🔴 Не отвечает"
    }
    return statuses.get(status, status)


def build_person_card(user):
    from database import get_referrals_count, get_total_referrals_count
    direct = get_referrals_count(user["telegram_id"])
    total = get_total_referrals_count(user["telegram_id"])
    return (
        f"👤 {user['fio']}\n\n"
        f"🎂 Дата рождения: {user['birth_date']}\n"
        f"📱 Телефон: {user['phone']}\n"
        f"🏙️ Город: {user['city']}\n"
        f"👫 Пол: {user['gender']}\n\n"
        f"📊 Статус: {get_status_text(user['status'])}\n\n"
        f"👥 Команда: {direct} лично приглашенных, {total} всего в структуре"
    )


@dp.message(lambda m: m.text == "📊 Статистика")
async def statistics(message: Message):
    sponsor_id = message.from_user.id
    await message.answer(
        f"📊 Моя структура\n\n"
        f"👥 Всего людей: {get_my_people_count(sponsor_id)}\n"
        f"⚪ Новые: {get_people_count_by_status(sponsor_id, 'new')}\n"
        f"🟡 В работе: {get_people_count_by_status(sponsor_id, 'work')}\n"
        f"🟢 Клиенты: {get_people_count_by_status(sponsor_id, 'client')}\n"
        f"💎 Партнеры: {get_people_count_by_status(sponsor_id, 'partner')}\n"
        f"🔴 Не отвечают: {get_people_count_by_status(sponsor_id, 'failed')}"
    )


@dp.message(lambda m: m.text == "📈 Воронка")
async def funnel_stats(message: Message):
    stats = get_funnel_stats(message.from_user.id)
    data = {k: stats.get(k, 0) for k in ["new", "work", "client", "partner", "failed"]}
    total = sum(data.values())
    if total == 0:
        await message.answer("Пока нет данных.")
        return
    await message.answer(
        f"📈 Воронка\n\n👥 Всего лидов: {total}\n"
        f"⚪ Новые: {data['new']}\n🟡 В работе: {data['work']}\n"
        f"🟢 Клиенты: {data['client']}\n💎 Партнеры: {data['partner']}\n"
        f"🔴 Не отвечают: {data['failed']}\n\n"
        f"📊 Конверсия в клиента: {round(data['client'] / total * 100, 1)}%\n"
        f"📊 Конверсия в партнера: {round(data['partner'] / total * 100, 1)}%"
    )


@dp.callback_query(lambda c: c.data.startswith("history_"))
async def show_history(callback: CallbackQuery):
    telegram_id = int(callback.data.split("_")[1])
    events = get_events(telegram_id)
    if not events:
        await callback.message.answer("История пуста.")
        return
    text = "📋 История:\n\n" + "\n".join([f"• {e['event_text']} \n{e['created_at']}" for e in events])
    await callback.message.answer(text)
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("chat_"))
async def chat_with_user(callback: CallbackQuery):
    """Обработчик кнопки "Написать" в карточке пользователя"""
    telegram_id = int(callback.data.split("_")[1])
    
    from database import get_user_by_telegram_id
    user = get_user_by_telegram_id(telegram_id)
    
    if not user:
        await callback.answer("Пользователь не найден.")
        return
    
    # Преобразуем sqlite3.Row в словарь
    user_dict = dict(user)
    
    username = user_dict.get('username')
    fio = user_dict.get('fio', 'Пользователь')
    phone = user_dict.get('phone', 'не указан')
    user_id = user_dict.get('id')
    
    if username:
        # Если есть username - открываем диалог
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="💬 Написать в Telegram",
                        url=f"https://t.me/{username}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="🔙 Назад к карточке",
                        callback_data=f"person_{user_id}"
                    )
                ]
            ]
        )
        
        await callback.message.answer(
            f"💬 Связь с {fio}\n\n"
            f"👤 Username: @{username}\n\n"
            f"Нажмите кнопку ниже, чтобы написать сообщение:",
            reply_markup=keyboard
        )
    else:
        # Если нет username - показываем телефон и ID
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 Назад к карточке",
                        callback_data=f"person_{user_id}"
                    )
                ]
            ]
        )
        
        await callback.message.answer(
            f"💬 Связь с {fio}\n\n"
            f"❌ У пользователя нет username в Telegram.\n\n"
            f"📱 Телефон: {phone}\n"
            f"🆔 Telegram ID: {telegram_id}\n\n"
            f"Вы можете связаться с ним по телефону или найти по ID.",
            reply_markup=keyboard
        )
    
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("person_"))
async def person_card(callback: CallbackQuery):
    """Показывает карточку пользователя"""
    user_id = int(callback.data.split("_")[1])
    user = get_user_by_id(user_id)
    if not user:
        await callback.answer("Пользователь не найден.")
        return
    
    await callback.message.answer(
        build_person_card(user),
        reply_markup=person_card_keyboard(user["telegram_id"])
    )
    await callback.answer()    

def get_user_dict(telegram_id):
    """Получить пользователя как словарь"""
    user = get_user_by_telegram_id(telegram_id)
    if user:
        return dict(user)
    return None    


#@dp.message(lambda m: m.text == "⏰ Требуют внимания")
#async def need_attention(message: Message):
 #   users = get_users_need_attention(message.from_user.id)
 #   if not users:
 #       await message.answer("Сейчас нет людей, требующих внимания ✅")
 #       return
 #   text = "⏰ Требуют внимания\n\n" + "\n".join([f"👤 {u['fio']}\n📊 Статус: {u['status']}\n📱 {u['phone']}" for u in users])
 #   await message.answer(text)
@dp.message(Command("cancel"))
async def cancel_command(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активного процесса для отмены.")
        return
    await state.clear()
    await message.answer("❌ Действие отменено.")

async def main():
    print("Бот запущен")
  
    await dp.start_polling(bot)


def start_main():
    init_db()
    asyncio.run(main())


if __name__ == "__main__":
    start_main()