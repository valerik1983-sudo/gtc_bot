from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


# ==================== ГЛАВНОЕ МЕНЮ ====================

def get_main_menu(registered=False, has_team=False, is_admin=False):
    keyboard = []
    keyboard.append([KeyboardButton(text="🔬 Пройти диагностику")])
    # 1. Продукты и доход
    if registered:
        keyboard.append([KeyboardButton(text="📦 Продукты и доход")])

    # 2. FAQ и Мой заказ
    row = [KeyboardButton(text="❓ FAQ")]
    if registered:
        row.append(KeyboardButton(text="🛒 Мой заказ"))
    else:
        row.append(KeyboardButton(text="📝 Регистрация"))
    keyboard.append(row)

    # 3. Команда и Профиль (только для зарегистрированных)
    row = []
    if has_team or is_admin:
        row.append(KeyboardButton(text="👥 Команда"))
    if registered:
        row.append(KeyboardButton(text="🔗 Профиль"))
    if row:
        keyboard.append(row)
    from database import has_active_promotions
    if has_active_promotions():
        keyboard.append([KeyboardButton(text="🎁 Акции и подарки")])
    # 4. Админка
    if is_admin:
        keyboard.append([KeyboardButton(text="👑 Админка")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_inline_consultation_button():
    """Инлайн-кнопка для перехода к консультации (отправляется отдельно)"""
    from config import CONSULT_BOT_USERNAME
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🤖 Перейти к консультации",
                    url=f"https://t.me/{CONSULT_BOT_USERNAME}"
                )
            ]
        ]
    )

# ==================== ПОДМЕНЮ "ПРОДУКТЫ И ДОХОД" (ЕДИНОЕ) ====================

products_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Подобрать по показаниям"), KeyboardButton(text="📋 Показать все товары")],
        [KeyboardButton(text="🎁 Готовые программы"), KeyboardButton(text="💰 Узнать о доходе")],
        [KeyboardButton(text="🏠 Главное меню")]
    ],
    resize_keyboard=True
)


# ==================== ПОДМЕНЮ "КОМАНДА" ====================

team_submenu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👥 Мои люди"), KeyboardButton(text="📈 Воронка")],
        [KeyboardButton(text="📦 Заказы клиентов"), KeyboardButton(text="📝 Генератор приглашений")],
        [KeyboardButton(text="🏠 Главное меню")]
    ],
    resize_keyboard=True
)


# ==================== ПОДМЕНЮ "ПРОФИЛЬ" ====================

profile_submenu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="👤 Мой наставник"), KeyboardButton(text="🔗 Моя ссылка")],
        [KeyboardButton(text="🔗 Ссылка с источником"), KeyboardButton(text="📝 Мои данные")],
        [KeyboardButton(text="🏠 Главное меню")]
    ],
    resize_keyboard=True
)


# ==================== ОСТАЛЬНЫЕ КЛАВИАТУРЫ ====================

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Статистика системы"), KeyboardButton(text="⚠️ Жалобы")],
        [KeyboardButton(text="⏰ Клиенты без ответа"), KeyboardButton(text="👥 Все партнеры")],
        [KeyboardButton(text="📢 Сообщение всем"), KeyboardButton(text="🔄 Сменить спонсора")],
        [KeyboardButton(text="🛍 Управление товарами"), KeyboardButton(text="🏢 Города офисов")],
        [KeyboardButton(text="👤 Без спонсора"), KeyboardButton(text="🎁 Управление акциями")],
        [KeyboardButton(text="📊 Статистика переходов"), KeyboardButton(text="📊 AI Аналитика")],  # новая кнопка
        [KeyboardButton(text="📊 Временные спонсоры"), KeyboardButton(text="🏠 Главное меню")]
    ],
    resize_keyboard=True
)



def all_products_keyboard():
    from database import get_all_products_from_db
    products = get_all_products_from_db()
    
    keyboard = []
    row = []
    for product in products:
        row.append(KeyboardButton(text=product["name"]))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([KeyboardButton(text="🔙 Назад")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)




def consultations_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🆕 Новые", callback_data="consults_new"),
             InlineKeyboardButton(text="🔥 В работе", callback_data="consults_work")],
            [InlineKeyboardButton(text="🎉 Клиенты", callback_data="consults_client"),
             InlineKeyboardButton(text="🤝 Партнеры", callback_data="consults_partner")],
            [InlineKeyboardButton(text="❌ Не отвечают", callback_data="consults_failed")]
        ]
    )


gender_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Мужской"), KeyboardButton(text="Женский")]],
    resize_keyboard=True
)


contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📱 Отправить телефон", request_contact=True)],
        [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)


def my_people_keyboard(users):
    buttons = []
    for user in users:
        buttons.append([InlineKeyboardButton(text=user["fio"], callback_data=f"person_{user['id']}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_stories_keyboard():
    return stories_keyboard


def get_programs_keyboard():
    return programs_keyboard

consultation_submenu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🤖 Перейти к консультации", url="https://t.me/gtcm_consult_bot")],
        [KeyboardButton(text="🔙 Главное меню")]
    ],
    resize_keyboard=True
)    

from config import CONSULT_BOT_USERNAME
from database import get_all_stories, get_all_programs

def get_products_menu_keyboard():
    """Динамическое меню товаров из базы"""
    from database import get_all_products_from_db
    
    keyboard = []
    
    # Кнопки фильтрации
    keyboard.append([KeyboardButton(text="🔍 Подобрать по показаниям"), KeyboardButton(text="📋 Показать все товары")])
    keyboard.append([KeyboardButton(text="🎁 Готовые программы")]) 
    # Динамические кнопки для программ
    programs = get_all_programs()
    if programs:
        programs_row = []
        for program in programs:
            programs_row.append(KeyboardButton(text=f"🎁 {program['name']}"))
            if len(programs_row) == 2:
                keyboard.append(programs_row)
                programs_row = []
        if programs_row:
            keyboard.append(programs_row)
    
    # Динамические кнопки для историй
    stories = get_all_stories()
    if stories:
        stories_row = []
        for story in stories:
            stories_row.append(KeyboardButton(text=f"📖 {story['title']}"))
            if len(stories_row) == 2:
                keyboard.append(stories_row)
                stories_row = []
        if stories_row:
            keyboard.append(stories_row)
    
    # Кнопка дохода и консультации
    keyboard.append([KeyboardButton(text="💰 Узнать о доходе")])
    keyboard.append([KeyboardButton(text="🏠 Главное меню")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


products_menu_keyboard = get_products_menu_keyboard()

