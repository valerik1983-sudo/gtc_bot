from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from states import Registration, AdminKnowledge  # <-- ДОБАВЛЕН AdminKnowledge
from datetime import datetime
from config import MAIN_BOT_TOKEN, CONSULT_BOT_USERNAME
import asyncio
from aiogram.types import ReplyKeyboardRemove

from handlers.promotions import admin_promotions_menu
from handlers.promotions import (
    admin_add_promo_start,
    admin_edit_promo,
    promo_edit_title,
    promo_edit_desc,
    promo_edit_photo,
    promo_edit_link,
    promo_edit_expires,
    promo_toggle,
    promo_delete,
    promo_confirm_delete,
    admin_back_to_promos,
    admin_back_to_admin
)
from keyboards import (
    team_submenu, profile_submenu, get_main_menu, admin_menu, 
    products_menu_keyboard
)
from database import get_user, get_referrals_count, is_admin, get_product_price, get_connection
from states import OrderCheckout

router = Router()
from database import is_admin, get_system_stats, get_all_partners, get_old_consultations, update_sponsor, get_user, get_office_cities, get_all_products_from_db, sync_products_from_file, get_product_price
from database import update_product_in_db, get_product_by_id, get_all_users
from database import get_temp_sponsor, clear_temp_sponsor
from database import (
    add_user,
    get_unprocessed_orders,
    get_order_waiting_time,
    get_admin_link_stats,
    mark_order_as_processed
)
    
from states import Broadcast
from states import PromotionEdit
from database import (
    get_all_promotions,
    get_promotion_by_id,
    add_promotion,
    update_promotion,
    delete_promotion
)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ АДМИН-ДИАЛОГОВ ==========
# (импортируем из admin_knowledge, чтобы не засорять файл)
from handlers.admin_knowledge import (
    detect_intent,
    start_admin_dialog,
    process_product_name,
    process_product_description,
    process_rule_text
)

@router.message(F.text == "📝 Регистрация")
async def start_registration(message: Message, state: FSMContext):
    print("🔴🔴🔴 НАЧАЛО РЕГИСТРАЦИИ 🔴🔴🔴")
    
    # Проверяем, не зарегистрирован ли уже пользователь
    from database import get_user
    user = get_user(message.from_user.id)
    if user:
        await message.answer("✅ Вы уже зарегистрированы!")
        return
    
    from states import Registration
    await state.set_state(Registration.fio)
    await message.answer(
        "📝 **Регистрация в системе бота помощника**\n\n"
        "Введите ваше ФИО (Имя и Фамилию):",
        parse_mode="Markdown"
    )


@router.message(StateFilter(Registration.fio))
async def get_fio(message: Message, state: FSMContext):
    fio = message.text.strip()
    if len(fio.split()) < 2:
        await message.answer("❌ Введите полное ФИО (Имя и Фамилию):")
        return
    
    from states import Registration
    await state.update_data(fio=fio)
    await state.set_state(Registration.birth_date)
    await message.answer("🎂 Введите вашу дату рождения (ДД.ММ.ГГГГ):")


@router.message(StateFilter(Registration.birth_date))
async def get_birth_date(message: Message, state: FSMContext):
    import re
    from datetime import datetime
    
    birth_date = message.text.strip()
    
    # Проверяем формат ДД.ММ.ГГГГ
    pattern = r'^\d{2}\.\d{2}\.\d{4}$'
    if not re.match(pattern, birth_date):
        await message.answer(
            "❌ Неверный формат даты!\n\n"
            "Пожалуйста, введите дату в формате: **ДД.ММ.ГГГГ**\n"
            "Например: 15.05.1990",
            parse_mode="Markdown"
        )
        return
    
    # Проверяем, что дата существует
    try:
        day, month, year = map(int, birth_date.split('.'))
        datetime(year, month, day)
    except ValueError:
        await message.answer(
            "❌ Такой даты не существует!\n\n"
            "Пожалуйста, введите корректную дату в формате **ДД.ММ.ГГГГ**",
            parse_mode="Markdown"
        )
        return
    
    # Проверяем возраст
    today = datetime.now()
    age = today.year - year - ((today.month, today.day) < (month, day))
    
    if age < 18:
        await message.answer(
            "❌ Регистрация доступна только для пользователей старше 18 лет.",
            parse_mode="Markdown"
        )
        return
    
    if age > 120:
        await message.answer(
            "❌ Проверьте дату рождения. Возможно, вы ошиблись.",
            parse_mode="Markdown"
        )
        return
    
    await state.update_data(birth_date=birth_date)
    await state.set_state(Registration.phone)
    await message.answer("📱 Введите ваш номер телефона:")


@router.message(StateFilter(Registration.phone))
async def get_phone(message: Message, state: FSMContext):
    import re
    phone = re.sub(r'[^0-9+]', '', message.text)
    if len(phone) < 10:
        await message.answer("❌ Введите корректный номер телефона:")
        return
    
    await state.update_data(phone=phone)
    await state.set_state(Registration.city)
    await message.answer("📍 Введите ваш город:")


@router.message(StateFilter(Registration.city))
async def get_city(message: Message, state: FSMContext):
    city = message.text.strip().title()
    await state.update_data(city=city)
    await state.set_state(Registration.gender)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]],
        resize_keyboard=True
    )
    await message.answer("👫 Выберите ваш пол:", reply_markup=keyboard)


@router.message(StateFilter(Registration.gender))
async def get_gender(message: Message, state: FSMContext):
    gender = message.text
    if gender not in ["Мужской", "Женский"]:
        await message.answer("❌ Выберите пол из предложенных вариантов:")
        return
    
    await state.update_data(gender=gender)
    await state.set_state(Registration.is_partner)
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да, я партнёр компании")],
            [KeyboardButton(text="❌ Нет, я новый пользователь")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "🤝 **Проверка статуса**\n\n"
        "Вы уже являетесь партнёром компании Global Trend?\n"
        "(приобрели продукт и зарегистрировались на сайте)\n\n"
        "❗ **Важно:** Если вы партнёр, регистрация в боте недоступна.\n"
        "Обратитесь к администратору для получения доступа.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.message(StateFilter(Registration.is_partner))
async def get_is_partner(message: Message, state: FSMContext):
    is_partner_text = message.text
    is_partner = "Да" in is_partner_text or "партнёр" in is_partner_text
    
    # Если пользователь уже партнёр компании - НЕ регистрируем
    if is_partner:
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📞 Связаться с администратором", url="https://t.me/gtcm_assistant_bot")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_to_main_menu")]
        ])
        
        await message.answer(
            "❌ **Регистрация недоступна для партнёров компании.**\n\n"
            "Если вы являетесь партнёром Global Trend, пожалуйста, обратитесь к администратору.\n\n"
            "Если вы ошиблись, нажмите «Главное меню» и начните регистрацию заново.",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return
    
    # Если не партнёр - продолжаем регистрацию
    data = await state.get_data()
    # ===== ВАЖНО: получаем sponsor_id из state или из temp_refs =====
    sponsor_id = data.get("sponsor_id")
    if not sponsor_id:
        from database import get_temp_sponsor
        sponsor_id = get_temp_sponsor(message.from_user.id)
        print(f"🔵🔵🔵 ВЗЯЛИ SPONSOR_ID ИЗ TEMP_REFS: {sponsor_id}")

    # ===== Сохраняем пользователя =====
    from database import add_user, clear_temp_sponsor
    add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        fio=data["fio"],
        birth_date=data["birth_date"],
        phone=data["phone"],
        city=data["city"],
        gender=data["gender"],
        sponsor_id=sponsor_id,
        role="lead"
    )

    # ===== Удаляем временную связь после регистрации =====
    if sponsor_id:
        clear_temp_sponsor(message.from_user.id)
    
    # ===== Отправляем уведомления =====
    try:
        # Уведомление наставнику (если есть)
        if sponsor_id:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="💬 Перейти в консультационный бот",
                    url=f"https://t.me/{CONSULT_BOT_USERNAME}"
                )]
            ])

            sponsor = get_user(sponsor_id)
            sponsor_is_partner = sponsor and sponsor.get('role') == 'partner' if sponsor else False

            message_text = (
                f"🆕 **Новый приглашённый!**\n\n"
                f"👤 **Имя:** {data['fio']}\n"
                f"📞 **Телефон:** {data['phone']}\n"
                f"🏙️ **Город:** {data['city']}\n"
                f"👫 **Пол:** {data['gender']}\n"
                f"🎂 **Дата рождения:** {data['birth_date']}\n\n"
                f"✅ Пользователь зарегистрировался по вашей ссылке!\n\n"
            )

            if not sponsor_is_partner:
                message_text += (
                    f"⚠️ **Внимание!** Чтобы получать вознаграждение за приглашённых, "
                    f"вам необходимо зарегистрироваться в компании (приобрести продукт).\n\n"
                )

            message_text += (
                f"💡 **Важно:** Чтобы получать уведомления о консультациях, "
                f"нажмите /start в [консультационном боте](https://t.me/{CONSULT_BOT_USERNAME})"
            )

            await message.bot.send_message(
                sponsor_id,
                message_text,
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )

        # Уведомление админу о регистрации без спонсора
        else:
            from config import ADMIN_ID
            admin_id = ADMIN_ID if ADMIN_ID else 258670125  # ваш ID, если не задан в config
            await message.bot.send_message(
                admin_id,
                f"🆕 **Новый пользователь без спонсора!**\n\n"
                f"👤 **ФИО:** {data['fio']}\n"
                f"📱 **Телефон:** {data['phone']}\n"
                f"🏙️ **Город:** {data['city']}\n"
                f"🆔 **ID:** {message.from_user.id}\n"
                f"📅 **Дата регистрации:** {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Назначьте ему спонсора через админ-панель.",
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Ошибка отправки уведомлений: {e}")

    await state.clear()

    # Отправляем приветствие
    user = get_user(message.from_user.id)
    registered = user is not None
    has_team = False
    is_admin_user = is_admin(message.from_user.id)

    await message.answer(
        f"✅ **Регистрация завершена!**\n\n"
        f"Добро пожаловать, {data['fio']}!\n\n"
        "Теперь у вас открыт полный доступ к системе.\n\n"
        f"Чтобы стать партнёром и получать вознаграждения, приобретите продукт компании.",
        reply_markup=get_main_menu(registered, has_team, is_admin_user),
        parse_mode="Markdown"
    )

# ==================== АДМИНКА ПРЯМО В MENU ====================

@router.message(F.text.in_([
    "👑 Админка", "📊 Статистика системы", "⚠️ Жалобы", "⏰ Клиенты без ответа",
    "👥 Все партнеры", "📢 Сообщение всем", "🔄 Сменить спонсора",
    "🛍 Управление товарами", "🏢 Города офисов", "👤 Без спонсора",
    "🎁 Управление акциями", "📊 Статистика переходов", "📊 Временные спонсоры"
]))
async def admin_handler(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    if message.text == "👑 Админка":
        await message.answer("👑 Панель администратора", reply_markup=admin_menu)
    
    elif message.text == "📊 Статистика системы":
        stats = get_system_stats()
        await message.answer(f"📊 Системa\n\n👥 Пользователей: {stats['users']}\n📅 Консультаций: {stats['consultations']}")
    
    elif message.text == "📊 AI Аналитика":
        from services.analytics import get_analytics_summary
        stats = get_analytics_summary()
        text = f"📊 AI Аналитика\n\n"
        text += f"Всего диалогов: {stats['total']}\n"
        text += f"Передано наставнику: {stats['forwarded']}\n\n"
        text += "Темы:\n"
        for topic, count in stats['topics']:
            text += f"  • {topic}: {count}\n"
        text += "\nПродукты:\n"
        for product, count in stats['products']:
            text += f"  • {product}: {count}\n"
        await message.answer(text, parse_mode="Markdown")


    elif message.text == "👥 Все партнеры":      
        
        from database import get_all_partners, get_connection

        partners = get_all_partners()
        if not partners:
            await message.answer("Нет партнёров в системе")
            return
        
        # Подключаемся к БД и проверяем диагностику
        conn = get_connection()
        cursor = conn.cursor()

        partners_with_diag = []
        partners_without_diag = []

        for partner in partners:
            user_id = partner['telegram_id']
            cursor.execute("SELECT COUNT(*) FROM diagnostic_results WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            if count > 0:
                partners_with_diag.append(partner)
            else:
                partners_without_diag.append(partner)

        conn.close()

        # Формируем клавиатуру
        keyboard = []

        for partner in partners_with_diag:
            keyboard.append([InlineKeyboardButton(
                text=f"🧬 {partner['fio']} (ID: {partner['telegram_id']})",
                callback_data=f"show_tree_{partner['telegram_id']}"
            )])

        for partner in partners_without_diag:
            keyboard.append([InlineKeyboardButton(
                text=f"{partner['fio']} (ID: {partner['telegram_id']})",
                callback_data=f"show_tree_{partner['telegram_id']}"
            )])

        await message.answer(
            "🌳 **Выберите партнёра для просмотра реферального дерева:**\n\n"
            "🧬 — прошёл диагностику",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    
    # ============ НЕОБРАБОТАННЫЕ ЗАКАЗЫ ============
    elif message.text == "⏰ Клиенты без ответа":
        from database import get_unprocessed_orders, get_order_waiting_time, get_user
    
        orders = get_unprocessed_orders()
    
        if not orders:
            await message.answer("✅ **Все заказы обработаны!**", parse_mode="Markdown")
            return
    
        text = "⏰ **Необработанные заказы**\n\n"
        keyboard = []
    
        for order in orders[:10]:  # Показываем первые 10
            waiting_time = get_order_waiting_time(order['id'])
        
            # Товары
            items_text = ", ".join([f"{item['name']} (x{item['quantity']})" for item in order['items']]) if order['items'] else "Нет товаров"
        
            # Эмодзи статуса
            status_emoji = "🟠"  # по умолчанию
            if waiting_time:
                if "ч" in waiting_time:
                    hours = int(waiting_time.split("ч")[0])
                    if hours >= 24:
                        status_emoji = "🚨"
                    elif hours >= 6:
                        status_emoji = "🔴"
                    elif hours >= 2:
                        status_emoji = "🟡"
            client = get_user(order['user_id'])
            username = client.get('username') if client else None
        
            text += (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"{status_emoji} **Заказ #{order['id']}**\n"
                f"👤 **Клиент:** {order['client_name']}\n"
                f"📱 **Телефон:** {order['phone']}\n"
                f"📍 **Город:** {order['city']}\n"
                f"📦 **Товары:**\n"
                f"  {items_text[:60]}...\n"
                f"💰 **Сумма:** {order['total_amount']} руб.\n"                
                f"🚚 **Доставка:** {order['delivery_text']}\n"                
                f"👨‍🏫 **Наставник:** {order['sponsor_fio']}\n"
                f"🆔 **ID наставника:** {order['sponsor_telegram_id'] or 'не указан'}\n"                
                f"⏱ **Ожидает:** {waiting_time or 'неизвестно'}\n"
                f"📅 **Создан:** {order['created_at']}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            )
        
            # Кнопки для заказа
            buttons = []
        
            # Кнопка "Написать клиенту"
            buttons.append(
                InlineKeyboardButton(
                    text=f"💬 Написать клиенту #{order['id']}",
                    callback_data=f"admin_answer_order_{order['id']}_{order['user_id']}"
                )
            )

            # Кнопка для связи
            if username:
                # Если есть username - кнопка с переходом в диалог
                keyboard.append([
                    InlineKeyboardButton(
                        text=f"💬 Написать клиенту #{order['id']}",
                        url=f"https://t.me/{username}"
                    )
                ])
            else:
                # Если нет username - показываем ID и телефон
                text += f"🆔 Telegram ID: {order['user_id']}\n"
                text += f"📱 Или по телефону: {order['phone']}\n"
        
            # Кнопка "Написать наставнику"
            if order['sponsor_telegram_id']:
                buttons.append(
                    InlineKeyboardButton(
                        text=f"👨‍🏫 Написать наставнику",
                        callback_data=f"admin_answer_order_{order['id']}_{order['sponsor_telegram_id']}"
                    )
                )
        
            # Кнопка "Отметить как обработанный"
            buttons.append(
                InlineKeyboardButton(
                    text=f"✅ Отметить заказ #{order['id']}",
                    callback_data=f"mark_order_processed_{order['id']}"
                )
            )
        
            # Добавляем кнопки в keyboard
            for btn in buttons:
                keyboard.append([btn])
    
        # Кнопка обновления
        keyboard.append([
            InlineKeyboardButton(
                text="🔄 Обновить список",
                callback_data="refresh_unprocessed_orders"
            )
        ])
    
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
    
    # ============ ОСТАЛЬНЫЕ КОМАНДЫ ============
    elif message.text == "📢 Сообщение всем":
        await state.set_state("broadcast_waiting")
        await message.answer("Отправьте сообщение для рассылки.\n\nМожно отправить:\n• текст\n• фото\n• видео\n• документ")
    
    elif message.text == "🔄 Сменить спонсора":
        await state.set_state("change_sponsor_waiting_user")
        await message.answer("Введите Telegram ID пользователя, которому нужно сменить спонсора:")
    
    elif message.text == "🛍 Управление товарами":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список товаров", callback_data="admin_list_products")],
            [InlineKeyboardButton(text="➕ Добавить новый товар", callback_data="admin_add_product")],
            [InlineKeyboardButton(text="📊 Порядок товаров", callback_data="admin_reorder_products")],
        ])
        await message.answer("🛍 **Управление товарами**", reply_markup=keyboard, parse_mode="Markdown")
    
    elif message.text == "🏢 Города офисов":
        cities = get_office_cities()
        cities_text = "\n".join([f"• {city}" for city in cities]) if cities else "Список пуст"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить город", callback_data="admin_add_city")],
            [InlineKeyboardButton(text="🗑 Удалить город", callback_data="admin_remove_city")],
        ])
        await message.answer(f"🏙️ **Города с офисами**\n\n{cities_text}\n\nВсего: {len(cities)}", reply_markup=keyboard, parse_mode="Markdown")
    
    elif message.text == "👤 Без спонсора":
        from database import get_users_without_sponsor
        users = get_users_without_sponsor()
        
        if not users:
            await message.answer("✅ Все пользователи имеют спонсора!")
            return
        
        text = "👤 **Пользователи без спонсора:**\n\n"
        for user in users:
            text += f"• {user['fio']} (ID: {user['telegram_id']})\n"
            text += f"  📱 {user['phone']}\n"
            text += f"  📅 {user['created_at']}\n\n"
        
        await message.answer(text, parse_mode="Markdown")
    elif message.text == "🎁 Управление акциями":
        await admin_promotions_menu(message)
        
    elif message.text == "📊 Статистика переходов":
        from database import get_admin_link_stats
        stats = get_admin_link_stats()
        if not stats:
            await message.answer("Нет данных о переходах.")
            return
        text = "📊 **Общая статистика переходов**\n\n"
        for row in stats:
            text += f"👤 **{row['fio']}** (ID: {row['sponsor_id']})\n"
            text += f"   Всего переходов: {row['total']}\n"
            text += f"   Регистраций: {row['registered']}\n"
            conv = round(row['registered'] / row['total'] * 100, 1) if row['total'] > 0 else 0
            text += f"   Конверсия: {conv}%\n"
            if row.get('sources'):
                text += "   📌 По источникам:\n"
                for src in row['sources']:
                    text += f"      • {src['source']}: {src['count']} переходов\n"
            text += "\n"
        await message.answer(text, parse_mode="Markdown")    
    elif message.text == "📊 Временные спонсоры":
        from database import get_temp_refs_full
        rows = get_temp_refs_full()
        if not rows:
            await message.answer("Нет записей в temp_refs.")
            return
        text = "📊 **Временные спонсоры**\n\n"
        for row in rows[:20]:
            status = "✅ зарегистрирован" if row['registered'] else "⏳ не зарегистрирован"
            text += f"🆔 {row['telegram_id']} → спонсор: {row['sponsor_fio'] or row['sponsor_id']} (источник: {row['source']})\n"
            text += f"   {status}, {row['created_at']}\n\n"
        if len(rows) > 20:
            text += f"\n... и ещё {len(rows)-20} записей."
        await message.answer(text, parse_mode="Markdown")    

# ============ КОЛБЭКИ ДЛЯ НЕОБРАБОТАННЫХ ЗАКАЗОВ ============
# Эти обработчики должны быть ВНЕ функции admin_handler

@router.callback_query(F.data.startswith("mark_order_processed_"))
async def mark_order_processed(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    order_id = int(callback.data.split("_")[3])
    from database import mark_order_as_processed
    
    mark_order_as_processed(order_id)
    
    await callback.message.edit_text(f"✅ Заказ #{order_id} отмечен как обработанный!")
    await callback.answer()


@router.callback_query(F.data == "refresh_unprocessed_orders")
async def refresh_unprocessed_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    # Создаём фейковое сообщение, чтобы вызвать admin_handler
    from types import SimpleNamespace
    fake_message = SimpleNamespace(
        text="⏰ Клиенты без ответа",
        from_user=callback.from_user,
        answer=lambda text, **kwargs: callback.message.answer(text, **kwargs)
    )
    
    from handlers.menu import admin_handler
    await admin_handler(fake_message, None)
    await callback.answer("Список обновлён ✅")

@router.callback_query(F.data.startswith("admin_answer_order_"))
async def admin_answer_order(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[3])
    user_id = int(parts[4])
    
    await state.update_data(
        admin_order_id=order_id,
        admin_answer_user_id=user_id
    )
    await state.set_state("admin_waiting_order_answer")
    
    await callback.message.answer(f"✏️ Введите ответ для пользователя (по заказу #{order_id}):")
    await callback.answer()


@router.message(StateFilter("admin_waiting_order_answer"))
async def admin_send_order_answer(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    order_id = data.get("admin_order_id")
    user_id = data.get("admin_answer_user_id")
    
    if not user_id:
        await message.answer("❌ Ошибка: пользователь не найден")
        await state.clear()
        return
    
    # Отправляем ответ пользователю
    await bot.send_message(
        user_id,
        f"📩 **Ответ администратора по заказу #{order_id}:**\n\n{message.text}\n\n"
        f"По всем вопросам обращайтесь к вашему наставнику."
    )
    
    # Логируем в events
    from database import add_event
    add_event(user_id, "order_reply", f"Администратор ответил по заказу #{order_id}")
    
    await message.answer(f"✅ Ответ отправлен пользователю по заказу #{order_id}!")
    await state.clear()


@router.callback_query(F.data.startswith("mark_order_processed_"))
async def mark_order_processed(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    order_id = int(callback.data.split("_")[3])
    from database import mark_order_as_processed
    
    mark_order_as_processed(order_id)
    
    # Уведомляем клиента
    from database import get_order_by_id, get_user
    order = get_order_by_id(order_id)
    if order:
        client = get_user(order['user_id'])
        if client:
            try:
                await callback.bot.send_message(
                    client['telegram_id'],
                    f"✅ **Ваш заказ #{order_id} отмечен как обработанный!**\n\n"
                    f"Спасибо за покупку! Если у вас есть вопросы, обращайтесь к наставнику."
                )
            except:
                pass
    
    await callback.message.edit_text(f"✅ **Заказ #{order_id} отмечен как обработанный!**\n\nКлиент уведомлён.")
    await callback.answer()


@router.callback_query(F.data == "refresh_unprocessed_orders")
async def refresh_unprocessed_orders(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    # Создаём фейковое сообщение для вызова admin_handler
    from types import SimpleNamespace
    fake_message = SimpleNamespace(
        text="⏰ Клиенты без ответа",
        from_user=callback.from_user,
        answer=callback.message.answer
    )
    
    await admin_handler(fake_message, None)
    await callback.answer("Список обновлён ✅")    

@router.message(StateFilter("broadcast_waiting"))
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    users = get_all_users()
    success = 0
    failed = 0
    for user in users:
        try:
            await bot.copy_message(
                chat_id=user["telegram_id"],
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            success += 1
        except:
            failed += 1
    await message.answer(f"📢 Рассылка завершена\n\n✅ Отправлено: {success}\n❌ Ошибок: {failed}")
    await state.clear()


@router.message(StateFilter("change_sponsor_waiting_user"))
async def change_sponsor_get_user(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный Telegram ID")
        return
    user = get_user(user_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID {user_id} не найден")
        await state.clear()
        return
    await state.update_data(target_user_id=user_id)
    await message.answer(f"👤 Пользователь: {user['fio']}\n\nВведите Telegram ID нового спонсора:")
    await state.set_state("change_sponsor_waiting_sponsor")


@router.message(StateFilter("change_sponsor_waiting_sponsor"))
async def change_sponsor_set(message: Message, state: FSMContext):
    try:
        sponsor_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный Telegram ID")
        return
    data = await state.get_data()
    user_id = data.get("target_user_id")
    sponsor = get_user(sponsor_id)
    if not sponsor:
        await message.answer(f"❌ Спонсор с ID {sponsor_id} не найден")
        return
    update_sponsor(user_id, sponsor_id)
    await message.answer(f"✅ Спонсор изменён на {sponsor['fio']}")
    await state.clear()


@router.callback_query(F.data == "admin_sync_products")
async def admin_sync_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    #sync_products_from_file()
    await callback.message.answer("✅ Товары синхронизированы!")
    await callback.answer()

# ==================== ДОБАВЛЕНИЕ НОВОГО ТОВАРА ====================

@router.callback_query(F.data == "admin_add_product")
async def admin_add_product_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    await state.set_state("admin_add_waiting_name")
    await callback.message.answer("✏️ Введите название нового товара:")
    await callback.answer()


@router.message(StateFilter("admin_add_waiting_name"))
async def admin_add_product_name(message: Message, state: FSMContext):
    await state.update_data(new_product_name=message.text)
    await state.set_state("admin_add_waiting_description")
    await message.answer("📄 Введите описание товара:")


@router.message(StateFilter("admin_add_waiting_description"))
async def admin_add_product_description(message: Message, state: FSMContext):
    await state.update_data(new_product_description=message.text)
    await state.set_state("admin_add_waiting_price")
    await message.answer("💰 Введите цену товара (только число):")


@router.message(StateFilter("admin_add_waiting_price"))
async def admin_add_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число")
        return
    
    await state.update_data(new_product_price=price)
    await state.set_state("admin_add_waiting_photo")
    await message.answer("🖼 Отправьте фото товара (или отправьте 'пропустить'):")


@router.message(StateFilter("admin_add_waiting_photo"))
async def admin_add_product_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    product_name = data.get("new_product_name")
    product_description = data.get("new_product_description")
    price = data.get("new_product_price")
    
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id
    elif message.text and message.text.lower() == "пропустить":
        photo_file_id = None
    else:
        await message.answer("❌ Отправьте фото или напишите 'пропустить'")
        return
    
    from database import add_new_product, set_product_price, update_product_in_db
    product_id = add_new_product(product_name, product_description, photo_file_id)
    if product_id:
        if photo_file_id:
            update_product_in_db(product_id, photo_path=photo_file_id)
        set_product_price(product_name, price)
        await message.answer(f"✅ Товар **{product_name}** добавлен!\n💰 Цена: {price} руб.\n🖼 Фото: {'есть' if photo_file_id else 'нет'}")
    else:
        await message.answer("❌ Ошибка при добавлении товара")
    
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Синхронизировать из файла", callback_data="admin_sync_products")],
        [InlineKeyboardButton(text="📋 Список товаров", callback_data="admin_list_products")],
        [InlineKeyboardButton(text="➕ Добавить новый товар", callback_data="admin_add_product")],
    ])
    await message.answer("🛍 **Управление товарами**\n\nВыберите действие:", reply_markup=keyboard, parse_mode="Markdown")


@router.callback_query(F.data == "admin_edit_photo")
async def admin_edit_photo_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_photo")
    await callback.message.answer("🖼 Отправьте новое фото для товара (или 'удалить' чтобы убрать фото):")
    await callback.answer()


@router.message(StateFilter("admin_waiting_photo"))
async def admin_edit_photo_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("editing_product_id")

    from database import get_product_by_id, update_product_in_db, get_product_price
    product = get_product_by_id(product_id)
    
    if not product:
        await message.answer("❌ Товар не найден. Пожалуйста, вернитесь в список товаров.")
        await state.clear()
        return
    
    if message.photo:
        photo_file_id = message.photo[-1].file_id
        print(f"🔵 Сохраняем file_id: {photo_file_id}")  # Диагностика
        
        from database import update_product_in_db
        update_product_in_db(product_id, photo_path=photo_file_id)
        
        await message.answer(f"✅ Фото товара обновлено! File_id: {photo_file_id[:20]}...")
    elif message.text and message.text.lower() == "удалить":
        from database import update_product_in_db
        update_product_in_db(product_id, photo_path="")
        await message.answer("✅ Фото товара удалено!")
    else:
        await message.answer("❌ Отправьте фото или напишите 'удалить'")
        return
    
    await state.clear()
    
    # Отправляем новое сообщение с формой редактирования вместо редактирования старого
    product = get_product_by_id(product_id)
    price = get_product_price(product['name'])
    price_display = f"{price} руб." if price and price > 0 else "не указана"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
    ])
    
    text = f"**{product['name']}**\n\n"
    text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
    text += f"💰 Цена: {price_display}\n"
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "admin_list_products")
async def admin_list_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    products = get_all_products_from_db()
    if not products:
        await callback.message.answer("📭 Товаров пока нет.")
        return
    
    # Формируем кнопки по 3 в ряд
    keyboard = []
    row = []
    for i, product in enumerate(products):
        row.append(InlineKeyboardButton(
            text=f"✏️ {product['name'][:20]}", 
            callback_data=f"admin_edit_product_{product['id']}"
        ))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_products")])
    
    text = "📋 **Список товаров:**\n\n"
    for product in products:
        price = get_product_price(product['name'])
        text += f"• **{product['name']}** — {price} руб.\n"
    text += f"\nВсего: {len(products)} товаров"
    
    # Отправляем НОВОЕ сообщение, не пытаемся редактировать старое
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), parse_mode="Markdown")
    
    # Удаляем старое сообщение, если оно было фото
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.answer()

# ==================== РЕДАКТИРОВАНИЕ ТОВАРОВ ====================

@router.callback_query(F.data.startswith("admin_edit_product_"))
async def admin_edit_product_form(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    product_id = int(callback.data.split("_")[3])
    await state.update_data(editing_product_id=product_id)
    
    from database import get_product_by_id, get_product_price
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer("❌ Товар не найден")
        await callback.answer()
        return
    
    price = get_product_price(product['name'])
    price_display = f"{price} руб." if price and price > 0 else "не указана"

    symptoms = product['symptoms'] if product['symptoms'] else 'не указаны'
    stories = product['stories'] if product['stories'] else 'не указаны'
    programs = product['programs'] if product['programs'] else 'не указаны'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
        [InlineKeyboardButton(text="🎬 Добавить видео", callback_data="admin_edit_video")],
        [InlineKeyboardButton(text="🩺 Изменить симптомы", callback_data="admin_edit_symptoms")],
        [InlineKeyboardButton(text="📖 Изменить истории", callback_data="admin_edit_stories")],
        [InlineKeyboardButton(text="🎁 Изменить программы", callback_data="admin_edit_programs")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
    ])
    
    text = f"**{product['name']}**\n\n"
    text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
    text += f"💰 Цена: {price_display}\n\n"
    text += f"🩺 Симптомы: {product['symptoms'] or 'не указаны'}\n"
    text += f"📖 Истории: {product['stories'] or 'не указаны'}\n"
    text += f"🎁 Программы: {product['programs'] or 'не указаны'}"
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()
    
    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass
    
    # Проверяем, есть ли фото
    photo_path = product['photo_path'] if product['photo_path'] else None
    
    if photo_path and photo_path.startswith('AgAC'):
        # Отправляем фото с подписью и кнопками
        await callback.message.answer_photo(
            photo=photo_path,
            caption=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        # Если фото нет, отправляем только текст
        await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await callback.answer()


@router.callback_query(F.data == "admin_edit_name")
async def admin_edit_name_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_name")
    await callback.message.answer("✏️ Введите новое название товара:")
    await callback.answer()


@router.message(StateFilter("admin_waiting_name"))
async def admin_edit_name_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    if not product_id:
        await message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return
    
    from database import update_product_in_db, get_product_by_id
    update_product_in_db(product_id, name=message.text)
    
    await message.answer(f"✅ Название изменено на: {message.text}")
    
    # Обновляем форму редактирования
    product = get_product_by_id(product_id)
    price = get_product_price(product['name'])
    price_display = f"{price} руб." if price and price > 0 else "не указана"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
    ])
    
    text = f"**{product['name']}**\n\n"
    text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
    text += f"💰 Цена: {price_display}\n"
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data == "admin_edit_desc")
async def admin_edit_desc_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_description")
    await callback.message.answer("✏️ Введите новое описание товара:")
    await callback.answer()


@router.message(StateFilter("admin_waiting_description"))
async def admin_edit_desc_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    if not product_id:
        await message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return
    
    from database import update_product_in_db, get_product_by_id
    update_product_in_db(product_id, description=message.text)
    
    await message.answer("✅ Описание товара обновлено!")
    
    # Обновляем форму редактирования
    product = get_product_by_id(product_id)
    price = get_product_price(product['name'])
    price_display = f"{price} руб." if price and price > 0 else "не указана"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
    ])
    
    text = f"**{product['name']}**\n\n"
    text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
    text += f"💰 Цена: {price_display}\n"
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data == "admin_edit_price")
async def admin_edit_price_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_price")
    await callback.message.answer("💰 Введите новую цену товара (только число):")
    await callback.answer()


@router.message(StateFilter("admin_waiting_price"))
async def admin_edit_price_save(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректное число")
        return
    
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    if not product_id:
        await message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return
    
    from database import get_product_by_id, set_product_price
    product = get_product_by_id(product_id)
    if product:
        set_product_price(product['name'], price)
        await message.answer(f"✅ Цена изменена на {price} руб.")
    else:
        await message.answer("❌ Товар не найден")
    
    # Обновляем форму редактирования
    if product:
        price_display = f"{price} руб."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
            [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
            [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
            [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
        ])
        
        text = f"**{product['name']}**\n\n"
        text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
        text += f"💰 Цена: {price_display}\n"
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    
    await state.clear()


@router.callback_query(F.data == "admin_edit_photo")
async def admin_edit_photo_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_photo")
    await callback.message.answer("🖼 Отправьте новое фото для товара:")
    await callback.answer()


@router.message(StateFilter("admin_waiting_photo"))
async def admin_edit_photo_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    if not product_id:
        await message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return
    
    if not message.photo:
        await message.answer("❌ Отправьте фото!")
        return
    
    photo_file_id = message.photo[-1].file_id
    
    from database import update_product_in_db, get_product_by_id
    update_product_in_db(product_id, photo_path=photo_file_id)
    
    await message.answer("✅ Фото товара обновлено!")
    
    # Обновляем форму редактирования
    product = get_product_by_id(product_id)
    price = get_product_price(product['name'])
    price_display = f"{price} руб." if price and price > 0 else "не указана"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
    ])
    
    text = f"**{product['name']}**\n\n"
    text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
    text += f"💰 Цена: {price_display}\n"
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.clear()

# ==================== РЕДАКТИРОВАНИЕ СИМПТОМОВ ====================
# ==================== РЕДАКТИРОВАНИЕ СИМПТОМОВ ====================
@router.callback_query(F.data == "admin_edit_symptoms")
async def admin_edit_symptoms_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_edit_symptoms")
    await callback.message.answer(
        "🩺 Введите симптомы для этого товара через запятую.\n\n"
        "Пример: усталость, сонливость, низкая энергия\n\n"
        "Или отправьте 'пропустить' чтобы оставить пустым:"
    )
    await callback.answer()


@router.message(StateFilter("admin_edit_symptoms"))
async def admin_edit_symptoms_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    symptoms = None if message.text.lower() == "пропустить" else message.text
    
    from database import update_product_in_db, get_product_by_id, get_product_price
    update_product_in_db(product_id, symptoms=symptoms)
    
    await message.answer("✅ Симптомы сохранены!")
    
    # Получаем обновлённый товар
    product = get_product_by_id(product_id)
    
    # 👇 ДОБАВЬТЕ ПРОВЕРКУ
    if not product:
        await message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return
    
    price = get_product_price(product['name'])
    price_display = f"{price} руб." if price and price > 0 else "не указана"
    
    symptoms_display = product['symptoms'] if product['symptoms'] else 'не указаны'
    stories_display = product['stories'] if product['stories'] else 'не указаны'
    programs_display = product['programs'] if product['programs'] else 'не указаны'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
        [InlineKeyboardButton(text="🩺 Изменить симптомы", callback_data="admin_edit_symptoms")],
        [InlineKeyboardButton(text="📖 Изменить истории", callback_data="admin_edit_stories")],
        [InlineKeyboardButton(text="🎁 Изменить программы", callback_data="admin_edit_programs")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
    ])
    
    text = f"**{product['name']}**\n\n"
    text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
    text += f"💰 Цена: {price_display}\n\n"
    text += f"🩺 Симптомы: {symptoms_display}\n"
    text += f"📖 Истории: {stories_display}\n"
    text += f"🎁 Программы: {programs_display}"
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.clear()


# ==================== РЕДАКТИРОВАНИЕ ИСТОРИЙ ====================
# ==================== РЕДАКТИРОВАНИЕ ИСТОРИЙ ====================
@router.callback_query(F.data == "admin_edit_stories")
async def admin_edit_stories_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_edit_stories")
    await callback.message.answer(
        "📖 Введите историю (или несколько историй, разделяя знаком | )\n\n"
        "Формат: Заголовок: Текст истории\n\n"
        "Пример: История 1: Описание истории... | История 2: Описание другой истории...\n\n"
        "Или отправьте 'пропустить' чтобы оставить пустым:"
    )
    await callback.answer()


@router.message(StateFilter("admin_edit_stories"))
async def admin_edit_stories_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    stories = None if message.text.lower() == "пропустить" else message.text
    
    from database import update_product_in_db, get_product_by_id, get_product_price
    update_product_in_db(product_id, stories=stories)
    
    await message.answer("✅ Истории сохранены!")
    
    product = get_product_by_id(product_id)
    # 👇 ДОБАВЬТЕ ПРОВЕРКУ
    if not product:
        await message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return
    price = get_product_price(product['name'])
    price_display = f"{price} руб." if price and price > 0 else "не указана"
    
    symptoms_display = product['symptoms'] if product['symptoms'] else 'не указаны'
    stories_display = product['stories'] if product['stories'] else 'не указаны'
    programs_display = product['programs'] if product['programs'] else 'не указаны'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
        [InlineKeyboardButton(text="🩺 Изменить симптомы", callback_data="admin_edit_symptoms")],
        [InlineKeyboardButton(text="📖 Изменить истории", callback_data="admin_edit_stories")],
        [InlineKeyboardButton(text="🎁 Изменить программы", callback_data="admin_edit_programs")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
    ])
    
    text = f"**{product['name']}**\n\n"
    text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
    text += f"💰 Цена: {price_display}\n\n"
    text += f"🩺 Симптомы: {symptoms_display}\n"
    text += f"📖 Истории: {stories_display}\n"
    text += f"🎁 Программы: {programs_display}"
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.clear()


# ==================== РЕДАКТИРОВАНИЕ ПРОГРАММ ====================
# ==================== РЕДАКТИРОВАНИЕ ПРОГРАММ ====================
@router.callback_query(F.data == "admin_edit_programs")
async def admin_edit_programs_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_edit_programs")
    await callback.message.answer(
        "🎁 Введите программу (или несколько программ, разделяя знаком | )\n\n"
        "Формат: Название программы: Описание программы\n\n"
        "Пример: Детокс: Очищение организма... | Энергия: Повышение тонуса...\n\n"
        "Или отправьте 'пропустить' чтобы оставить пустым:"
    )
    await callback.answer()


@router.message(StateFilter("admin_edit_programs"))
async def admin_edit_programs_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    programs = None if message.text.lower() == "пропустить" else message.text
    
    from database import update_product_in_db, get_product_by_id, get_product_price
    update_product_in_db(product_id, programs=programs)
    
    await message.answer("✅ Программы сохранены!")
    
    # Получаем обновлённый товар
    product = get_product_by_id(product_id)
    # 👇 ДОБАВЬТЕ ПРОВЕРКУ
    if not product:
        await message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return
    price = get_product_price(product['name'])
    price_display = f"{price} руб." if price and price > 0 else "не указана"
    
    symptoms_display = product['symptoms'] if product['symptoms'] else 'не указаны'
    stories_display = product['stories'] if product['stories'] else 'не указаны'
    programs_display = product['programs'] if product['programs'] else 'не указаны'
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
        [InlineKeyboardButton(text="🩺 Изменить симптомы", callback_data="admin_edit_symptoms")],
        [InlineKeyboardButton(text="📖 Изменить истории", callback_data="admin_edit_stories")],
        [InlineKeyboardButton(text="🎁 Изменить программы", callback_data="admin_edit_programs")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
    ])
    
    text = f"**{product['name']}**\n\n"
    text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
    text += f"💰 Цена: {price_display}\n\n"
    text += f"🩺 Симптомы: {symptoms_display}\n"
    text += f"📖 Истории: {stories_display}\n"
    text += f"🎁 Программы: {programs_display}"
    
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.clear() 

@router.callback_query(F.data == "admin_edit_video")
async def admin_edit_video_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_video")
    await callback.message.answer(
        "🎬 Введите ссылку на видео (YouTube, Vimeo или любой другой хостинг):\n\n"
        "Пример: https://www.youtube.com/watch?v=XXXXX"
    )
    await callback.answer()    

@router.message(StateFilter("admin_waiting_video"))
async def admin_edit_video_save(message: Message, state: FSMContext):
    video_url = message.text.strip()
    if not video_url.startswith(('http://', 'https://')):
        await message.answer("❌ Введите корректную ссылку (начинается с http:// или https://):")
        return

    data = await state.get_data()
    product_id = data.get("editing_product_id")
    if not product_id:
        await message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return

    from database import update_product_in_db, get_product_by_id, get_product_price
    update_product_in_db(product_id, video_url=video_url)

    await message.answer("✅ Видео сохранено!")

    # Возвращаемся к форме редактирования
    product = get_product_by_id(product_id)
    if product:
        product = dict(product)  # преобразуем в словарь, чтобы использовать .get()
        price = get_product_price(product['name'])
        price_display = f"{price} руб." if price and price > 0 else "не указана"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
            [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
            [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
            [InlineKeyboardButton(text="🎬 Добавить видео", callback_data="admin_edit_video")],
            [InlineKeyboardButton(text="🩺 Изменить симптомы", callback_data="admin_edit_symptoms")],
            [InlineKeyboardButton(text="📖 Изменить истории", callback_data="admin_edit_stories")],
            [InlineKeyboardButton(text="🎁 Изменить программы", callback_data="admin_edit_programs")],
            [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
        ])

        text = f"**{product['name']}**\n\n"
        text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
        text += f"💰 {price_display}\n"
        text += f"🎬 Видео: {'есть' if product.get('video_url') else 'нет'}\n"

        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer("❌ Товар не найден")

    await state.clear()    
    

@router.callback_query(F.data == "admin_delete_product")
async def admin_delete_product(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    data = await state.get_data()
    product_id = data.get("editing_product_id")
    
    if not product_id:
        await callback.message.answer("❌ Ошибка: товар не найден")
        await callback.answer()
        return
    
    from database import delete_product_from_db
    delete_product_from_db(product_id)
    
    await callback.message.answer("✅ Товар удалён!")
    await state.clear()
    await callback.answer()
    
    # Показываем список товаров
    await admin_list_products(callback)


@router.callback_query(F.data == "admin_back_to_products")
async def admin_back_to_products(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Синхронизировать из файла", callback_data="admin_sync_products")],
        [InlineKeyboardButton(text="📋 Список товаров", callback_data="admin_list_products")],
        [InlineKeyboardButton(text="➕ Добавить новый товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="📊 Порядок товаров", callback_data="admin_reorder_products")],
    ])
    await callback.message.edit_text(
        "🛍 **Управление товарами**\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


# ==================== РЕДАКТИРОВАНИЕ ГОРОДОВ ====================

@router.callback_query(F.data == "admin_add_city")
async def admin_add_city_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("admin_waiting_city")
    await callback.message.answer("🏙️ Введите название города для добавления:")
    await callback.answer()


@router.message(StateFilter("admin_waiting_city"))
async def admin_add_city_save(message: Message, state: FSMContext):
    from database import add_office_city
    city_name = message.text.strip().title()
    add_office_city(city_name)
    await message.answer(f"✅ Город {city_name} добавлен!")
    await state.clear()
    await admin_back_to_cities(message)


@router.callback_query(F.data == "admin_remove_city")
async def admin_remove_city_start(callback: CallbackQuery):
    from database import get_office_cities
    cities = get_office_cities()
    if not cities:
        await callback.answer("Список городов пуст")
        return
    
    keyboard = []
    for city in cities:
        keyboard.append([InlineKeyboardButton(text=f"🗑 {city}", callback_data=f"admin_remove_city_{city}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_cities")])
    
    await callback.message.edit_text(
        "🏙️ **Выберите город для удаления:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_remove_city_"))
async def admin_remove_city_save(callback: CallbackQuery):
    from database import remove_office_city, get_office_cities
    city_name = callback.data.replace("admin_remove_city_", "")
    remove_office_city(city_name)
    
    cities = get_office_cities()
    cities_text = "\n".join([f"• {city}" for city in cities]) if cities else "Список пуст"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="admin_add_city")],
        [InlineKeyboardButton(text="🗑 Удалить город", callback_data="admin_remove_city")],
    ])
    await callback.message.edit_text(
        f"✅ Город **{city_name}** удалён!\n\n🏙️ **Города с офисами**\n\n{cities_text}\n\nВсего: {len(cities)}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "admin_back_to_cities")
async def admin_back_to_cities(callback: CallbackQuery):
    from database import get_office_cities
    cities = get_office_cities()
    cities_text = "\n".join([f"• {city}" for city in cities]) if cities else "Список пуст"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="admin_add_city")],
        [InlineKeyboardButton(text="🗑 Удалить город", callback_data="admin_remove_city")],
    ])
    await callback.message.edit_text(
        f"🏙️ **Города с офисами**\n\n{cities_text}\n\nВсего: {len(cities)}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()
    
# ==================== АКЦИИ И ПОДАРКИ ====================

# ----- ПОЛЬЗОВАТЕЛЬСКАЯ ЧАСТЬ -----
@router.message(F.text == "🎁 Акции и подарки")
async def show_promotions(message: Message):
    promotions = get_all_promotions(active_only=True)

    if not promotions:
        await message.answer(
            "🎁 **Акции и подарки**\n\n"
            "На данный момент активных акций нет.\n"
            "Следите за обновлениями!",
            parse_mode="Markdown"
        )
        return

    for promo in promotions:
        text = f"🎁 **{promo['title']}**\n\n{promo['description']}"
        if promo.get('link'):
            text += f"\n\n🔗 [Подробнее]({promo['link']})"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Перейти по ссылке", url=promo['link'])]
        ]) if promo.get('link') else None

        if promo.get('photo_id'):
            await message.answer_photo(
                photo=promo['photo_id'],
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )


# ----- АДМИНСКАЯ ЧАСТЬ -----
async def admin_promotions_menu(message: Message):
    """Меню управления акциями (вызывается из admin_handler)"""
    if not is_admin(message.from_user.id):
        return

    promotions = get_all_promotions()

    if not promotions:
        await message.answer(
            "🎁 Управление акциями\n\n"
            "Акций пока нет. Нажмите «➕ Добавить акцию», чтобы создать первую.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить акцию", callback_data="admin_add_promo")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_admin")]
            ])
        )
        return

    keyboard = []
    for promo in promotions:
        status_icon = "✅" if promo['is_active'] else "❌"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_icon} {promo['title'][:30]}",
                callback_data=f"admin_edit_promo_{promo['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="➕ Добавить акцию", callback_data="admin_add_promo")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_admin")])

    await message.answer(
        "🎁 **Управление акциями**\n\n"
        "Выберите акцию для редактирования или добавьте новую.\n"
        "✅ — активна, ❌ — неактивна.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )


# ---------- ДОБАВЛЕНИЕ АКЦИИ С КНОПКОЙ ОТМЕНЫ ----------

@router.callback_query(F.data == "admin_add_promo")
async def admin_add_promo_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(PromotionEdit.waiting_title)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_promo")]
    ])
    await callback.message.answer("✏️ Введите заголовок акции:", reply_markup=keyboard)
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_title))
async def admin_add_promo_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(PromotionEdit.waiting_description)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_promo")]
    ])
    await message.answer("📄 Введите описание акции (можно с форматированием Markdown):", reply_markup=keyboard)


@router.message(StateFilter(PromotionEdit.waiting_description))
async def admin_add_promo_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(PromotionEdit.waiting_photo)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_promo")]
    ])
    await message.answer(
        "🖼 Отправьте фото для акции (или отправьте 'пропустить'):\n\n"
        "Фото будет отображаться в карточке акции.",
        reply_markup=keyboard
    )


@router.message(StateFilter(PromotionEdit.waiting_photo))
async def admin_add_promo_photo(message: Message, state: FSMContext):
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.lower() == "пропустить":
        photo_id = None
    else:
        # Оставляем клавиатуру с отменой
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_promo")]
        ])
        await message.answer("❌ Отправьте фото или напишите 'пропустить'", reply_markup=keyboard)
        return

    await state.update_data(photo_id=photo_id)
    await state.set_state(PromotionEdit.waiting_link)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_promo")]
    ])
    await message.answer(
        "🔗 Введите ссылку для перехода (например, https://... ) или отправьте 'пропустить':",
        reply_markup=keyboard
    )


@router.message(StateFilter(PromotionEdit.waiting_link))
async def admin_add_promo_link(message: Message, state: FSMContext):
    link = None
    if message.text and message.text.lower() != "пропустить":
        if not message.text.startswith(('http://', 'https://')):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_promo")]
            ])
            await message.answer("❌ Ссылка должна начинаться с http:// или https://. Попробуйте снова:", reply_markup=keyboard)
            return
        link = message.text
    await state.update_data(link=link)
    await state.set_state(PromotionEdit.waiting_expires)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_promo")]
    ])
    await message.answer(
        "📅 Введите дату истечения акции (необязательно) в формате ДД.ММ.ГГГГ\n"
        "или отправьте 'пропустить', если акция бессрочная:",
        reply_markup=keyboard
    )


@router.message(StateFilter(PromotionEdit.waiting_expires))
async def admin_add_promo_expires(message: Message, state: FSMContext):
    expires_at = None
    if message.text and message.text.lower() != "пропустить":
        try:
            from datetime import datetime
            expires_at = datetime.strptime(message.text, "%d.%m.%Y").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_promo")]
            ])
            await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ или 'пропустить':", reply_markup=keyboard)
            return

    data = await state.get_data()
    promo_id = add_promotion(
        title=data['title'],
        description=data['description'],
        photo_id=data.get('photo_id'),
        link=data.get('link'),
        expires_at=expires_at
    )

    await message.answer(f"✅ Акция **{data['title']}** успешно добавлена! (ID: {promo_id})")
    await state.clear()
    await admin_promotions_menu(message)


# ---------- КНОПКА ОТМЕНЫ ----------
@router.callback_query(F.data == "admin_cancel_promo")
async def admin_cancel_promo(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Создание акции отменено.")
    await admin_promotions_menu(callback.message)
    await callback.answer()


# ---------- РЕДАКТИРОВАНИЕ АКЦИЙ ----------
@router.callback_query(F.data.startswith("admin_edit_promo_"))
async def admin_edit_promo(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    promo_id = int(callback.data.split("_")[3])
    promo = get_promotion_by_id(promo_id)
    if not promo:
        await callback.message.answer("❌ Акция не найдена")
        await callback.answer()
        return

    await state.update_data(edit_promo_id=promo_id)

    status_text = "🟢 Активна" if promo['is_active'] else "🔴 Неактивна"
    text = (
        f"🎁 **{promo['title']}**\n\n"
        f"{promo['description']}\n\n"
        f"📅 Создана: {promo['created_at']}\n"
        f"⏳ Истекает: {promo['expires_at'] or 'бессрочно'}\n"
        f"📊 Статус: {status_text}\n"
        f"🔗 Ссылка: {promo['link'] or 'нет'}\n"
        f"🖼 Фото: {'есть' if promo['photo_id'] else 'нет'}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить заголовок", callback_data="promo_edit_title")],
        [InlineKeyboardButton(text="✏️ Изменить описание", callback_data="promo_edit_desc")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="promo_edit_photo")],
        [InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data="promo_edit_link")],
        [InlineKeyboardButton(text="📅 Изменить срок", callback_data="promo_edit_expires")],
        [InlineKeyboardButton(text="🔄 Переключить статус", callback_data=f"promo_toggle_{promo_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"promo_delete_{promo_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_promos")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


# ---------- РЕДАКТИРОВАНИЕ ПОЛЕЙ ----------
@router.callback_query(F.data == "promo_edit_title")
async def promo_edit_title(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_title)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="promo_cancel_edit")]
    ])
    await callback.message.answer("✏️ Введите новый заголовок:", reply_markup=keyboard)
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_title))
async def promo_save_title(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return
    update_promotion(promo_id, title=message.text)
    await message.answer("✅ Заголовок обновлён!")
    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data == "promo_edit_desc")
async def promo_edit_desc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_description)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="promo_cancel_edit")]
    ])
    await callback.message.answer("✏️ Введите новое описание:", reply_markup=keyboard)
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_description))
async def promo_save_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return
    update_promotion(promo_id, description=message.text)
    await message.answer("✅ Описание обновлено!")
    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data == "promo_edit_photo")
async def promo_edit_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_photo)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="promo_cancel_edit")]
    ])
    await callback.message.answer("🖼 Отправьте новое фото (или 'удалить' чтобы убрать):", reply_markup=keyboard)
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_photo))
async def promo_save_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return

    if message.photo:
        photo_id = message.photo[-1].file_id
        update_promotion(promo_id, photo_id=photo_id)
        await message.answer("✅ Фото обновлено!")
    elif message.text and message.text.lower() == "удалить":
        update_promotion(promo_id, photo_id=None)
        await message.answer("✅ Фото удалено!")
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="promo_cancel_edit")]
        ])
        await message.answer("❌ Отправьте фото или напишите 'удалить'", reply_markup=keyboard)
        return

    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data == "promo_edit_link")
async def promo_edit_link(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_link)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="promo_cancel_edit")]
    ])
    await callback.message.answer("🔗 Введите новую ссылку (или 'удалить' чтобы убрать):", reply_markup=keyboard)
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_link))
async def promo_save_link(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return

    if message.text.lower() == "удалить":
        update_promotion(promo_id, link=None)
        await message.answer("✅ Ссылка удалена!")
    else:
        if not message.text.startswith(('http://', 'https://')):
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="promo_cancel_edit")]
            ])
            await message.answer("❌ Ссылка должна начинаться с http:// или https://. Попробуйте снова:", reply_markup=keyboard)
            return
        update_promotion(promo_id, link=message.text)
        await message.answer("✅ Ссылка обновлена!")

    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data == "promo_edit_expires")
async def promo_edit_expires(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_expires)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="promo_cancel_edit")]
    ])
    await callback.message.answer("📅 Введите новую дату истечения (ДД.ММ.ГГГГ) или 'удалить' чтобы сделать бессрочной:", reply_markup=keyboard)
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_expires))
async def promo_save_expires(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return

    if message.text.lower() == "удалить":
        update_promotion(promo_id, expires_at=None)
        await message.answer("✅ Срок истечения убран (бессрочная акция)")
    else:
        try:
            from datetime import datetime
            expires_at = datetime.strptime(message.text, "%d.%m.%Y").strftime("%Y-%m-%d %H:%M:%S")
            update_promotion(promo_id, expires_at=expires_at)
            await message.answer(f"✅ Дата истечения установлена на {message.text}")
        except ValueError:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="promo_cancel_edit")]
            ])
            await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ или 'удалить'", reply_markup=keyboard)
            return

    await state.clear()
    await admin_promotions_menu(message)


# ---------- ОТМЕНА РЕДАКТИРОВАНИЯ ----------
@router.callback_query(F.data == "promo_cancel_edit")
async def promo_cancel_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Редактирование отменено.")
    await admin_promotions_menu(callback.message)
    await callback.answer()


# ---------- ПЕРЕКЛЮЧЕНИЕ СТАТУСА ----------
@router.callback_query(F.data.startswith("promo_toggle_"))
async def promo_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    promo_id = int(callback.data.split("_")[2])
    promo = get_promotion_by_id(promo_id)
    if not promo:
        await callback.message.answer("❌ Акция не найдена")
        await callback.answer()
        return
    new_status = 0 if promo['is_active'] else 1
    update_promotion(promo_id, is_active=new_status)
    status_text = "активирована" if new_status else "деактивирована"
    await callback.message.answer(f"✅ Акция {status_text}!")
    await callback.answer()
    await admin_promotions_menu(callback.message)


# ---------- УДАЛЕНИЕ ----------
@router.callback_query(F.data.startswith("promo_delete_"))
async def promo_delete(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    promo_id = int(callback.data.split("_")[2])
    promo = get_promotion_by_id(promo_id)
    if not promo:
        await callback.message.answer("❌ Акция не найдена")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"promo_confirm_delete_{promo_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back_to_promos")]
    ])
    await callback.message.answer(
        f"⚠️ Вы уверены, что хотите удалить акцию **{promo['title']}**?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()
    
    


@router.callback_query(F.data.startswith("promo_confirm_delete_"))
async def promo_confirm_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    promo_id = int(callback.data.split("_")[3])
    delete_promotion(promo_id)
    await callback.message.answer("✅ Акция удалена!")
    await callback.answer()
    await admin_promotions_menu(callback.message)


# ---------- НАЗАД ----------
@router.callback_query(F.data == "admin_back_to_promos")
async def admin_back_to_promos(callback: CallbackQuery):
    await admin_promotions_menu(callback.message)
    await callback.answer()


# ==================== ГЛАВНОЕ МЕНЮ ====================

@router.message(F.text == "🔬 Пройти диагностику")
async def diagnostics_button_handler(message: Message, state: FSMContext):
    """Обработка кнопки диагностики из меню"""
    from handlers.diagnostics import start_diagnostics
    await start_diagnostics(message, state)

@router.message(F.text == "📦 Продукты и доход")
async def products_category(message: Message, state: FSMContext):
    print("🔴🔴🔴 products_category ВЫЗВАН 🔴🔴🔴")
    
    user = get_user(message.from_user.id)
    
    # ===== БАЗОВЫЙ ТЕКСТ (общий) =====
    base_text = (
        "🌿 **Продукты Global Trend** – это натуральные средства для здоровья, красоты и долголетия.\n\n"
        "Вы можете:\n"
        "• 🔍 Подобрать по показаниям – найти продукт по вашим симптомам\n"
        "• 📋 Показать все товары – посмотреть весь каталог\n"
        "• 🎁 Готовые программы – готовые решения для конкретных задач\n"
        "• 💰 Узнать о доходе – как зарабатывать с нами\n\n"
        "Выберите действие:"
    )
    
    # ===== ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ ЗАРЕГИСТРИРОВАН =====
    # ===== ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ ЗАРЕГИСТРИРОВАН =====
    if not user:
        # ===== ПЫТАЕМСЯ НАЙТИ СПОНСОРА =====
        sponsor_id = None
        
        # 1. Пробуем взять из state
        state_data = await state.get_data()
        sponsor_id = state_data.get("sponsor_id")
        
        # 2. Если нет — пробуем из temp_refs
        if not sponsor_id:
            from database import get_temp_sponsor
            sponsor_id = get_temp_sponsor(message.from_user.id)
        
        # Формируем ссылку
        if sponsor_id:
            reg_link = f"https://t.me/gtcm_assistant_bot?start={sponsor_id}"
        else:
            reg_link = "https://t.me/gtcm_assistant_bot?start=registration"
        
        text = (
            "🔓 **Для доступа к полному каталогу и персонализированному подбору**\n"
            "Настоятельно рекомендуем пройти регистрацию для показа всех возможностей бота.\n\n"
            f"👉 <a href='{reg_link}'>Зарегистрироваться</a>\n\n"
            f"{base_text}"
        )
        
        await message.answer(
            text,
            reply_markup=products_menu_keyboard,
            parse_mode="HTML"
        )
        return
    
    # ===== ЕСЛИ ПОЛЬЗОВАТЕЛЬ ЗАРЕГИСТРИРОВАН =====
    birth_date = user.get('birth_date', '01.01.2000')
    try:
        day, month, year = map(int, birth_date.split('.'))
    except:
        year = 2000
    
    today = datetime.now()
    age = today.year - year - ((today.month, today.day) < (month, day))
    
    # ===== ОПРЕДЕЛЯЕМ ПОКОЛЕНИЕ =====
    if year >= 2013:
        generation = "Альфа"
        gen_greeting = "🌱 **Для самых юных — здоровье с пелёнок!**"
        gen_text = (
            "Мы создали продукты, которые помогают детям расти крепкими, умными и активными.\n"
            "• Укрепление иммунитета без химии\n"
            "• Поддержка мозга и нервной системы\n"
            "• Здоровые зубы и дёсны с детства"
        )
        gen_rec = "🌟 Рекомендуем: натуральные средства для роста и иммунитета"
    elif year >= 1997:
        generation = "Зумеры (Z)"
        gen_greeting = "⚡Энергия и драйв 24/7!**"
        gen_text = (
            "Ты живёшь на полной скорости — мы даём топливо для этого.\n"
            "• Мгновенный заряд бодрости без кофе\n"
            "• Чистая кожа и здоровый вид\n"
            "• Продукты, которые работают быстро и заметно"
        )
        gen_rec = "🌟 Рекомендуем: **Energy Lux и Wellness Lux** — твой драйв на весь день"
    elif year >= 1981:
        generation = "Миллениалы (Y)"
        gen_greeting = "Баланс и осознанность!**"
        gen_text = (
            "Ты ищешь смысл, качество и продукты, которые работают на клеточном уровне.\n"
            "• Восстановление энергии после стресса\n"
            "• Гормональный баланс и эмоциональное здоровье\n"
            "• Омоложение и защита от старения"
        )
        gen_rec = "🌟 Рекомендуем: **Harmony Lux** — баланс гормонов и эмоций"
    elif year >= 1965:
        generation = "Поколение X"
        gen_greeting = "Надёжность и результат!**"
        gen_text = (
            "Ценишь стабильность и практичность — мы даём продукты, которые реально работают.\n"
            "• Крепкий иммунитет и защита от вирусов\n"
            "• Поддержка сердца и сосудов\n"
            "• Чёткий ум и хорошая память"
        )
        gen_rec = "🌟 Рекомендуем: **Pavlov Spring** — твоя защита и опора"
    elif year >= 1946:
        generation = "Бэби-бумеры"
        gen_greeting = "Активное долголетие!**"
        gen_text = (
            "Ты в этом мире не гость — ты его создатель. Мы поможем оставаться бодрым.\n"
            "• Здоровье суставов и сосудов\n"
            "• Ясный ум и хорошая память\n"
            "• Энергия для путешествий и общения"
        )
        gen_rec = "🌟 Рекомендуем: **ImmunoLux** — здоровье сосудов, суставов и поддержка всего иммунитета"
    else:
        generation = "Старшее поколение"
        gen_greeting = "🌿 **Для активных в любом возрасте!**"
        gen_text = (
            "Ты — пример для окружающих. Мы поддержим твою энергию и бодрость.\n"
            "• Мягкая поддержка всех систем организма\n"
            "• Укрепление иммунитета и тонуса\n"
            "• Продукты, которые заботятся о тебе"
        )
        gen_rec = "🌟 Рекомендуем: **Delight Lux** — мягкая поддержка организма"
    
    # ===== ФОРМИРУЕМ ФИНАЛЬНЫЙ ТЕКСТ =====
    # Сначала персонализация, потом базовый текст с действиями
    text = (
        f"🌟 **{user['fio']}**, мы подобрали продукты специально для вас!\n\n"
        f"{gen_greeting}\n"
        f"{gen_text}\n\n"
        f"{gen_rec}\n\n"
        f"{base_text}"
    )
    
    

    await message.answer(
        text,
        reply_markup=products_menu_keyboard,
        parse_mode="Markdown"
    )

    

@router.message(F.text == "👥 Команда")
async def team_category(message: Message):
    await message.answer("👥 Управление командой:", reply_markup=team_submenu)


@router.message(F.text == "🔗 Профиль")
async def profile_category(message: Message):
    await message.answer("🔗 Ваш профиль:", reply_markup=profile_submenu)


# ==================== ПОДМЕНЮ "ПРОДУКТЫ И ДОХОД" ====================

@router.message(F.text == "🔍 Подобрать по показаниям")
async def redirect_symptoms(message: Message):
    from handlers.products import show_all_symptoms
    await show_all_symptoms(message)


@router.message(F.text == "📋 Показать все товары")
async def redirect_all_products(message: Message):
    from handlers.products import show_all_products
    await show_all_products(message)


@router.message(F.text == "🎁 Готовые программы")
async def redirect_programs(message: Message):
    from handlers.products import show_all_programs_from_products
    await show_all_programs_from_products(message)


@router.message(F.text == "📚 Истории клиентов")
async def redirect_stories(message: Message):
    from handlers.products import show_stories
    await show_stories(message)


@router.message(F.text == "💰 Узнать о доходе")
async def redirect_income(message: Message, state: FSMContext):
    from handlers.quiz import start_quiz
    await start_quiz(message, state)


@router.message(F.text == "🔙 Назад")
async def handle_back_in_products(message: Message):
    from handlers.products import back_to_products
    await back_to_products(message)


# ==================== ПОДМЕНЮ "КОМАНДА" ====================

@router.message(F.text == "👥 Мои люди")
async def redirect_my_people(message: Message):
    from handlers.referrals import my_people
    await my_people(message)


@router.message(F.text == "📈 Воронка")
async def redirect_funnel(message: Message):
    from handlers.referrals import funnel_stats
    await funnel_stats(message)


@router.message(F.text == "📅 Мои консультации")
async def redirect_consultations(message: Message):
    from handlers.consultations import my_consultations
    await my_consultations(message)


#@router.message(F.text == "⏰ Требуют внимания")
#async def redirect_attention(message: Message):
#    from handlers.referrals import need_attention
#    await need_attention(message)


@router.message(F.text == "📦 Заказы клиентов")
async def redirect_orders(message: Message):
    from handlers.orders import show_my_orders
    await show_my_orders(message)


# ==================== ПОДМЕНЮ "ПРОФИЛЬ" ====================

@router.message(F.text == "👤 Мой наставник")
async def redirect_sponsor(message: Message):
    from handlers.referrals import my_sponsor
    await my_sponsor(message)


@router.message(F.text == "🔗 Моя ссылка")
async def redirect_link(message: Message):
    from main import my_link
    await my_link(message)


@router.message(F.text == "🛒 Мой заказ")
async def redirect_cart(message: Message):
    from handlers.cart import show_cart
    await show_cart(message)


@router.message(F.text == "📝 Мои данные")
async def redirect_my_data(message: Message):
    from handlers.referrals import my_data
    await my_data(message)


# ==================== КНОПКИ В ГЛАВНОЕ МЕНЮ ====================

@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    user = get_user(message.from_user.id)
    registered = user is not None
    has_team = get_referrals_count(message.from_user.id) > 0 if registered else False
    is_admin_user = is_admin(message.from_user.id)
    await message.answer("🏠 Главное меню", reply_markup=get_main_menu(registered, has_team, is_admin_user))

@router.callback_query(lambda c: c.data.startswith("consult_request_"))
async def create_consult_request(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[2])
    from database import get_user
    user = get_user(user_id)
    if not user:
        await callback.message.answer("Пользователь не найден.")
        await callback.answer()
        return

    sponsor_id = user.get('sponsor_id')
    if sponsor_id:
        try:
            from aiogram import Bot
            from config import CONSULT_BOT_TOKEN
            consult_bot = Bot(token=CONSULT_BOT_TOKEN)
            # Получаем последний вопрос пользователя из памяти
            from services.memory import memory
            history = memory.get_history(user_id, limit=1)
            last_question = history[-1]["content"] if history else "Нет вопроса"
            await consult_bot.send_message(
                sponsor_id,
                f"🆕 Новая заявка на консультацию от пользователя {user.get('fio', 'Пользователь')} (ID: {user_id})\n"
                f"Вопрос: {last_question}\n"
                f"Телефон: {user.get('phone', 'Не указан')}\n"
                f"Город: {user.get('city', 'Не указан')}\n"
                f"Для ответа перейдите в консультационный бот."
            )
            await callback.message.answer("✅ Заявка передана вашему наставнику. Ожидайте ответа.")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления наставнику: {e}")
            await callback.message.answer("❌ Не удалось отправить заявку. Попробуйте позже.")
    else:
        await callback.message.answer("❌ У вас нет наставника. Обратитесь к администратору.")
    await callback.answer()

# ==================== ОБРАБОТКА ЧАВО ====================

@router.message(F.text == "❓ FAQ")
async def show_faq(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Как сделать заказ?", callback_data="faq_order")],
        [InlineKeyboardButton(text="🚚 Доставка", callback_data="faq_delivery")],
        [InlineKeyboardButton(text="💳 Оплата", callback_data="faq_payment")],
        [InlineKeyboardButton(text="🔄 Возврат", callback_data="faq_return")],
        [InlineKeyboardButton(text="👥 Партнерская программа", callback_data="faq_partner")],
        [InlineKeyboardButton(text="📞 Консультация", callback_data="faq_consult")]
    ])
    
    await message.answer(
        "❓ **Часто задаваемые вопросы**\n\n"
        "Выберите интересующий вас вопрос:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Обработчики для каждого вопроса
@router.callback_query(lambda c: c.data.startswith("faq_"))
async def faq_answer(callback: CallbackQuery):
    question = callback.data.replace("faq_", "")
    
    answers = {
        "order": "**📦 Как сделать заказ?**\n\n"
                 "1. Выберите товар в разделе «Продукты и доход»\n"
                 "2. Нажмите «🛒 Добавить в корзину»\n"
                 "3. Перейдите в «🛒 Мой заказ»\n"
                 "4. Подтвердите данные и выберите способ доставки\n"
                 "5. Нажмите «✅ Подтвердить заказ»",
        
        "delivery": "**🚚 Доставка**\n\n"
                    "• Самовывоз из офиса в вашем городе (бесплатно при наличии)\n"
                    "• Доставка СДЭК — стоимость рассчитывается при оформлении и оплачивается отдельно",
        
        "payment": "**💳 Оплата**\n\n"
                   "• Оплата при получении (наличные/карта)\n"
                   "• Онлайн-оплата картой на сайте(в разработке)\n"
                   "• Оплата по ссылке от наставника",
        
        "return": "**🔄 Возврат**\n\n"
                  "По закону РФ данная категория товаров возврату и обмену не подлежат.\n"
                  "Если у вас сомнения в органолептических характеристиках полученного продукта - обратитесь, пожалуйста, к наставнику",
        
        "partner": "**👥 Партнерская программа**\n\n"
                   "Приглашайте друзей по вашей ссылке и получайте вознаграждение за их покупки.\n"
                   "Ваша ссылка: нажмите «🔗 Профиль» → «🔗 Моя ссылка»",
        
        "consult": "**📞 Консультация**\n\n"
                   "Если у вас остались вопросы, нажмите «🤖 Перейти к консультации».\n"
                   "Наш специалист свяжется с вами."
    }
    
    text = answers.get(question, "Ответ не найден")

    # Добавляем кнопку только для консультации
    if question == "consult":
        from config import CONSULT_BOT_USERNAME
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Перейти к консультации", url=f"https://t.me/{CONSULT_BOT_USERNAME}")],
            [InlineKeyboardButton(text="🔙 Назад к вопросам", callback_data="back_to_faq")]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад к вопросам", callback_data="back_to_faq")]
        ])
    
      
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "back_to_faq")
async def back_to_faq(callback: CallbackQuery):
    await show_faq(callback.message)
    await callback.answer()    

@router.message(F.text == "📝 Генератор приглашений")
async def redirect_invite_generator(message: Message):
    from handlers.invite_generator import invite_generator
    await invite_generator(message)

# ==================== ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ====================
@router.message()
async def handle_all_messages(message: Message, state: FSMContext):
    from handlers.cart import get_city, get_pickup_point, send_order_answer, save_tracking_number
    from data.products import PRODUCTS
    from handlers.products import show_product_card as show_product
    from states import OrderCheckout
    from database import get_all_products_from_db
    from handlers.quiz import cancel_quiz
    from states import ReplyState
    
    
    current_state = await state.get_state()
    print(f"🔵🔵🔵 handle_all_messages: состояние={current_state}, текст={message.text}")

    # ---- 1. Проверка админ-команд (естественный язык) ----
    # Срабатывает только если пользователь админ и намерение распознано
    # (вызов должен быть ПЕРЕД всеми остальными проверками, кроме проверки FSM)
    if is_admin(message.from_user.id):
        # Но если мы уже в каком-то состоянии, не прерываем его
        if current_state is None:
            from handlers.admin_knowledge import detect_intent, start_admin_dialog
            intent = await detect_intent(message.text)
            if intent:
                await start_admin_dialog(message, state, intent)
                return
        # Если состояние не None, админ-команды не обрабатываем (пусть идёт по обычной логике)

    # ---- 2. Обработка состояний админ-диалогов ----
    if current_state in ["AdminKnowledge:waiting_product_name", "AdminKnowledge:waiting_product_description", "AdminKnowledge:waiting_rule_text"]:
        from handlers.admin_knowledge import process_product_name, process_product_description, process_rule_text
        if current_state == "AdminKnowledge:waiting_product_name":
            await process_product_name(message, state)
        elif current_state == "AdminKnowledge:waiting_product_description":
            await process_product_description(message, state)
        elif current_state == "AdminKnowledge:waiting_rule_text":
            await process_rule_text(message, state)
        return

    # ===== ОБРАБОТКА ВВОДА ПРОИЗВОЛЬНОГО ИСТОЧНИКА =====
    if current_state == "CustomSource:waiting_source":
        from main import custom_source_link_generate
        await custom_source_link_generate(message, state)
        return

    # ===== ПРОВЕРКА ДЛЯ РЕГИСТРАЦИИ =====
    if current_state == Registration.is_partner:
        from handlers.menu import get_is_partner
        await get_is_partner(message, state)
        return

    if current_state == "ReplyState:waiting_user_reply":
        from handlers.referrals import send_user_reply_main
        await send_user_reply_main(message, state)
        return

    # Если пользователь в квизе и хочет выйти - завершаем квиз
    if current_state and current_state.startswith("Quiz:"):
        await cancel_quiz(message, state)
        return
    
    # Пропускаем сообщения, которые должны обрабатываться другими роутерами (админка)
    admin_commands = [
        "👑 Админка", "📊 Статистика системы", "⚠️ Жалобы", "⏰ Клиенты без ответа",
        "👥 Все партнеры", "📢 Сообщение всем", "🔄 Сменить спонсора",
        "🛍 Управление товарами", "🏢 Города офисов", "📖 Управление историями",
        "🎁 Управление программами", "🩺 Управление симптомами", "❓ FAQ","📝 Генератор приглашений" 
    ]
    
    if message.text in admin_commands:
        print(f"🔵🔵🔵 Пропускаем админскую команду: {message.text}")
        return  # Не обрабатываем, пусть admin_router обрабатывает
    
    # 👇 ДОБАВЛЯЕМ ОБРАБОТКУ waiting_city
    if current_state == "waiting_city":
        from handlers.cart import edit_city_save
        await edit_city_save(message, state)
        return
    
    # 👇 ДОБАВЛЯЕМ ОБРАБОТКУ waiting_fio
    if current_state == "waiting_fio":
        from handlers.cart import edit_fio_save
        await edit_fio_save(message, state)
        return
    
    # 👇 ДОБАВЛЯЕМ ОБРАБОТКУ waiting_phone
    if current_state == "waiting_phone":
        from handlers.cart import edit_phone_save
        await edit_phone_save(message, state)
        return

    # 1. Сначала проверяем оформление заказа
    if current_state == "OrderCheckout:city":
        await get_city(message, state)
        return
    elif current_state == "OrderCheckout:pickup_point":
        await get_pickup_point(message, state)
        return
    
    # 2. Проверяем ответ наставника на заказ
    elif current_state == "waiting_order_answer":
        await send_order_answer(message, state)
        return
    
    # 3. Проверяем добавление трек-номера
    elif current_state == "waiting_tracking_number":
        await save_tracking_number(message, state)
        return

    elif current_state == "admin_waiting_complaint_reply":
        from handlers.menu import admin_send_complaint_reply
        await admin_send_complaint_reply(message, state)
        return    
    
    # 4. Если не в процессе заказа - проверяем карточки товаров
    if current_state is None:
        products_list = [p["name"] for p in get_all_products_from_db()]
        if message.text in products_list or message.text in PRODUCTS:
            await show_product(message)
            return
    
    # 5. Если ничего не подошло — пробуем AI (если включён)
    from handlers.ai_handler import handle_ai_request
    from config import AI_ENABLED

    if AI_ENABLED:
        await handle_ai_request(message, state)
    else:
        # Старое поведение: показываем меню
        user = get_user(message.from_user.id)
        registered = user is not None
        has_team = get_referrals_count(message.from_user.id) > 0 if registered else False
        is_admin_user = is_admin(message.from_user.id)

        await message.answer(
            "🤔 Я не понял ваш запрос.\n\n"
            "Пожалуйста, воспользуйтесь кнопками меню ниже, чтобы выбрать нужное действие:",
            reply_markup=get_main_menu(registered, has_team, is_admin_user)
        )
        
        print(f"🔵🔵🔵 Сообщение не обработано: {message.text}")


@router.message(lambda m: m.text == "🤖 Перейти к консультации")
async def go_to_consultation(message: Message):
    from config import CONSULT_BOT_USERNAME
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Открыть консультационного бота",
                    url=f"https://t.me/{CONSULT_BOT_USERNAME}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel_consultation"
                )
            ]
        ]
    )
    
    await message.answer(
        "🤖 Нажмите на кнопку ниже, чтобы перейти в консультационный бот.\n\n"
        "Там вы сможете задать вопрос вашему наставнику.",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "cancel_consultation")
async def cancel_consultation(callback_query: CallbackQuery):
    await callback_query.message.delete()
    await callback_query.answer("Отменено")

@router.message(StateFilter("admin_waiting_complaint_reply"))
async def admin_send_complaint_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    consult_id = data.get("reply_complaint_consult_id")
    user_id = data.get("reply_complaint_user_id")
    
    if not user_id:
        await message.answer("❌ Ошибка: пользователь не найден")
        await state.clear()
        return
    
    # Отправляем ответ пользователю
    await message.bot.send_message(
        user_id,
        f"📩 **Ответ администратора по жалобе:**\n\n{message.text}\n\n"
        f"Извините за неудобства. Если у вас остались вопросы, "
        f"вы можете снова обратиться к наставнику."
    )
    
    # Обновляем статус консультации (через прямой SQL)
    import sqlite3
    try:
        conn = sqlite3.connect("consultations.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE consult_requests SET status = 'resolved' WHERE id = ?", (consult_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка обновления статуса: {e}")
    
    await message.answer("✅ Ответ отправлен пользователю!")
    await state.clear()         

@router.callback_query(F.data == "admin_reorder_products")
async def admin_reorder_products(callback: CallbackQuery):
    """Показывает кнопки для изменения порядка товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    from database import get_all_products_from_db
    products = get_all_products_from_db()
    
    if not products:
        await callback.message.answer("📭 Товаров пока нет.")
        await callback.answer()
        return
    
    keyboard = []
    for idx, product in enumerate(products):
        sort_order = product.get('sort_order', idx)
        keyboard.append([
            InlineKeyboardButton(
                text=f"⬆️ {product['name']}",
                callback_data=f"product_up_{product['id']}"
            ),
            InlineKeyboardButton(
                text="⬇️",
                callback_data=f"product_down_{product['id']}"
            ),
            InlineKeyboardButton(
                text=f"#{sort_order}",
                callback_data="ignore"
            )
        ])
    
    # Добавляем кнопку для обновления порядка
    keyboard.append([
        InlineKeyboardButton(
            text="🔄 Перенумеровать порядок",
            callback_data="renumber_products"
        )
    ])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_products")])
    
    await callback.message.edit_text(
        "📊 **Управление порядком товаров**\n\n"
        "⬆️ - поднять выше\n"
        "⬇️ - опустить ниже\n"
        "Номер показывает текущую позицию\n\n"
        "Новые товары добавляются в конец списка.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product_up_"))
async def product_up(callback: CallbackQuery):
    """Поднять товар выше"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    product_id = int(callback.data.split("_")[2])
    
    from database import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем текущий порядок товара
    cursor.execute("SELECT sort_order, name FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        await callback.answer("❌ Товар не найден")
        return
    
    current_order = result[0] or 0
    name = result[1]
    
    # Ищем товар с порядком на 1 меньше
    cursor.execute("SELECT id, name FROM products WHERE sort_order = ?", (current_order - 1,))
    prev_product = cursor.fetchone()
    
    if prev_product:
        # Меняем местами
        cursor.execute("UPDATE products SET sort_order = ? WHERE id = ?", (current_order, prev_product[0]))
        cursor.execute("UPDATE products SET sort_order = ? WHERE id = ?", (current_order - 1, product_id))
        conn.commit()
        conn.close()
        
        await admin_reorder_products(callback)
        await callback.answer(f"✅ {name} поднят выше")
    else:
        conn.close()
        await callback.answer("ℹ️ Товар уже на верхней позиции")


@router.callback_query(F.data.startswith("product_down_"))
async def product_down(callback: CallbackQuery):
    """Опустить товар ниже"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    product_id = int(callback.data.split("_")[2])
    
    from database import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем текущий порядок товара
    cursor.execute("SELECT sort_order, name FROM products WHERE id = ?", (product_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        await callback.answer("❌ Товар не найден")
        return
    
    current_order = result[0] or 0
    name = result[1]
    
    # Ищем товар с порядком на 1 больше
    cursor.execute("SELECT id, name FROM products WHERE sort_order = ?", (current_order + 1,))
    next_product = cursor.fetchone()
    
    if next_product:
        # Меняем местами
        cursor.execute("UPDATE products SET sort_order = ? WHERE id = ?", (current_order, next_product[0]))
        cursor.execute("UPDATE products SET sort_order = ? WHERE id = ?", (current_order + 1, product_id))
        conn.commit()
        conn.close()
        
        await admin_reorder_products(callback)
        await callback.answer(f"✅ {name} опущен ниже")
    else:
        conn.close()
        await callback.answer("ℹ️ Товар уже на нижней позиции")

@router.callback_query(F.data == "renumber_products")
async def renumber_products(callback: CallbackQuery):
    """Перенумеровывает порядок товаров (убирает пропуски)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    from database import get_connection, get_all_products_from_db
    
    products = get_all_products_from_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    for idx, product in enumerate(products):
        cursor.execute("UPDATE products SET sort_order = ? WHERE id = ?", (idx, product['id']))
    
    conn.commit()
    conn.close()
    
    await admin_reorder_products(callback)
    await callback.answer("✅ Порядок перенумерован")        


# ==================== КОЛБЭКИ ====================

@router.callback_query()
async def redirect_callbacks(callback: CallbackQuery, state: FSMContext):
    print(f"🔹 ПОЛУЧЕН CALLBACK: {callback.data}")
    
    # ===== ГЕНЕРАТОР ПРИГЛАШЕНИЙ =====
    if callback.data.startswith("invite_"):
        from handlers.invite_generator import invite_type_selected, invite_source_selected
        if callback.data.startswith("invite_source_"):
            await invite_source_selected(callback, state)
        else:
            await invite_type_selected(callback, state)
        return
    
    # ===== ДИАГНОСТИКА =====
    if callback.data.startswith("diag_ans_") or callback.data in [
        "diagnostics_restart", "diagnostics_compare", "diag_cancel",
        "diag_recommendations", "diag_register", "diag_to_main",
        "diag_consult", "diag_back_to_result"
    ]:
        from handlers.diagnostics import (
            answer_question, restart_diagnostics, compare_diagnostics,
            cancel_diagnostics, get_recommendations, register_after_diagnostic,
            diag_to_main, diag_consult, back_to_result
        )
        if callback.data.startswith("diag_ans_"):
            await answer_question(callback, state)
        elif callback.data == "diagnostics_restart":
            await restart_diagnostics(callback, state)
        elif callback.data == "diagnostics_compare":
            await compare_diagnostics(callback)
        elif callback.data == "diag_cancel":
            await cancel_diagnostics(callback, state)
        elif callback.data == "diag_recommendations":
            await get_recommendations(callback)
        elif callback.data == "diag_register":
            await register_after_diagnostic(callback, state)
        elif callback.data == "diag_to_main":
            await diag_to_main(callback)
        elif callback.data == "diag_consult":
            await diag_consult(callback)
        elif callback.data == "diag_back_to_result":
            await back_to_result(callback)
        elif callback.data == "diag_register_recommend":
            from handlers.diagnostics import register_from_recommend
            await register_from_recommend(callback, state)    
        return
    
        # ===== АКЦИИ (ADMIN) =====
    if callback.data == "admin_add_promo":
        await admin_add_promo_start(callback, state)
        return

    if callback.data.startswith("admin_edit_promo_"):
        await admin_edit_promo(callback, state)
        return

    if callback.data == "promo_edit_title":
        await promo_edit_title(callback, state)
        return

    if callback.data == "promo_edit_desc":
        await promo_edit_desc(callback, state)
        return

    if callback.data == "promo_edit_photo":
        await promo_edit_photo(callback, state)
        return

    if callback.data == "promo_edit_link":
        await promo_edit_link(callback, state)
        return

    if callback.data == "promo_edit_expires":
        await promo_edit_expires(callback, state)
        return

    if callback.data.startswith("promo_toggle_"):
        await promo_toggle(callback)
        return

    if callback.data.startswith("promo_delete_"):
        await promo_delete(callback, state)
        return

    if callback.data.startswith("promo_confirm_delete_"):
        await promo_confirm_delete(callback)
        return

    if callback.data == "admin_back_to_promos":
        await admin_back_to_promos(callback)
        return

    if callback.data == "admin_back_to_admin":
        await admin_back_to_admin(callback)
        return
    
    # Квиз
    if callback.data.startswith("quiz_"):
        from handlers.quiz import answer_question
        await answer_question(callback, state)
        return
        # ===== ПОКАЗ НЕЗАРЕГИСТРИРОВАННЫХ В ДЕРЕВЕ =====
    if callback.data.startswith("show_unreg_"):
        from handlers.admin import show_unregistered_list
        await show_unregistered_list(callback, state)
        return
    
    # Симптомы (подбор по показаниям)
    if callback.data.startswith("symptom_select_"):
        from handlers.products import show_products_by_symptom
        await show_products_by_symptom(callback)
        return

    # Программы (готовые программы)
    if callback.data.startswith("prog_"):
        from handlers.products import show_products_by_program
        await show_products_by_program(callback)
        return

    # Истории в карточке товара
    if callback.data.startswith("product_stories_"):
        from handlers.products import show_product_stories
        await show_product_stories(callback)
        return

    # Консультации
    if callback.data.startswith("msg_"):
        from handlers.consultations import mentor_message_start
        await mentor_message_start(callback, state)
    
    elif callback.data == "reply_to_mentor":
        from handlers.consultations import reply_to_mentor
        await reply_to_mentor(callback, state)
    
    # Продукты
    elif callback.data.startswith("product_"):
        from handlers.products import show_product_from_callback
        await show_product_from_callback(callback)
    
    elif callback.data.startswith("symptom_select_"):
        from handlers.products import show_products_by_symptom
        await show_products_by_symptom(callback)
    
    elif callback.data.startswith("program_"):
        from handlers.products import show_program
        await show_program(callback)
    
    elif callback.data.startswith("story_"):
        from handlers.products import show_story
        await show_story(callback)
    
    elif callback.data.startswith("consult_"):
        from handlers.products import product_consultation
        await product_consultation(callback)
        
    elif callback.data == "how_to_order":
        from handlers.products import how_to_order
        await how_to_order(callback)
    
    # Корзина и заказы
    elif callback.data.startswith("add_to_cart_"):
        from handlers.cart import add_to_cart_handler
        await add_to_cart_handler(callback)
    
    elif callback.data.startswith("cart_remove_"):
        from handlers.cart import remove_from_cart_handler
        await remove_from_cart_handler(callback)
    
    elif callback.data == "checkout":
        from handlers.cart import start_checkout
        await start_checkout(callback, state)
    
    elif callback.data == "clear_cart":
        from handlers.cart import clear_cart_handler
        await clear_cart_handler(callback)
    
    elif callback.data == "repeat_last_order":
        from handlers.cart import repeat_last_order
        await repeat_last_order(callback)
    
    elif callback.data == "continue_shopping":
        from handlers.cart import continue_shopping_handler
        await continue_shopping_handler(callback)
    
    elif callback.data == "view_cart":
        from handlers.cart import show_cart
        await show_cart(callback.message)
        await callback.answer()
    
    # Оформление заказа
    elif callback.data == "confirm_data_yes":
        from handlers.cart import confirm_data_yes
        await confirm_data_yes(callback, state)
    
    elif callback.data == "confirm_data_edit":
        from handlers.cart import confirm_data_edit
        await confirm_data_edit(callback, state)
    
    elif callback.data.startswith("delivery_"):
        from handlers.cart import get_delivery_method
        await get_delivery_method(callback, state)
    
    elif callback.data == "final_confirm":
        from handlers.cart import final_confirm_order
        await final_confirm_order(callback, state, callback.bot)
    
    elif callback.data == "final_edit":
        from handlers.cart import final_edit_order
        await final_edit_order(callback, state)
    
    elif callback.data == "edit_fio":
        from handlers.cart import edit_fio_start
        await edit_fio_start(callback, state)
    
    elif callback.data == "edit_phone":
        from handlers.cart import edit_phone_start
        await edit_phone_start(callback, state)
    
    elif callback.data == "edit_city":
        from handlers.cart import edit_city_start
        await edit_city_start(callback, state)
    
    elif callback.data == "back_to_final":
        from handlers.cart import back_to_final
        await back_to_final(callback, state)
    
    elif callback.data == "restart_checkout":
        from handlers.cart import restart_checkout
        await restart_checkout(callback, state)

    elif callback.data.startswith("prog_"):
        from handlers.products import show_products_by_program
        await show_products_by_program(callback)    
    
    # Доход
    elif callback.data == "expand_income_info":
        from handlers.income import expand_income
        await expand_income(callback)
    
    elif callback.data == "collapse_income_info":
        from handlers.income import collapse_income
        await collapse_income(callback)
    
    elif callback.data == "how_to_refer":
        from handlers import quiz
        await quiz.how_to_refer(callback)
    
    # Заказы клиентов (для наставников)
    elif callback.data.startswith("status_"):
        from handlers.orders import update_status
        await update_status(callback, state)
    
    elif callback.data == "add_tracking":
        from handlers.orders import start_add_tracking
        await start_add_tracking(callback, state)

    # Добавьте обработку для ответа на заказ
    elif callback.data.startswith("answer_order_"):
        from handlers.cart import answer_order_to_client
        await answer_order_to_client(callback, state)
    
    # Добавьте обработку для трек-номера
    elif callback.data.startswith("add_tracking_"):
        from handlers.cart import add_tracking_start
        await add_tracking_start(callback, state) 

    elif callback.data == "back_to_symptoms":
        from handlers.products import show_all_symptoms
        await show_all_symptoms(callback.message)
        await callback.answer()   

    elif callback.data == "back_to_programs_menu":
        from handlers.products import show_all_programs_from_products
        await show_all_programs_from_products(callback.message)
        await callback.answer()    

    elif callback.data.startswith("show_tree_"):
        from handlers.admin import show_partner_tree
        await show_partner_tree(callback, state)