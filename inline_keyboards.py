from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton


def sponsor_keyboard(username):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📞 Связаться с наставником",
                    url=f"https://t.me/{username}"
                )
            ]
        ]
    )

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


def reply_to_mentor_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✍️ Ответить наставнику",
                    callback_data="reply_to_mentor"
                )
            ]
        ]
    )    

def people_keyboard(users):
    """Клавиатура для списка людей с кнопкой "Написать" """
    keyboard = []
    for user in users:
        username = user.get('username')
        if username:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"👤 {user['fio']}",
                    callback_data=f"person_{user['id']}"
                ),
                InlineKeyboardButton(
                    text="💬 Написать",
                    url=f"https://t.me/{username}"
                )
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(
                    text=f"👤 {user['fio']}",
                    callback_data=f"person_{user['id']}"
                )
            ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)  

def person_card_keyboard(
    telegram_id
):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="💬 Написать",
                    callback_data=f"chat_{telegram_id}"
                )
            ],

            [
                 InlineKeyboardButton(
                    text="📋 История",
                    callback_data=f"history_{telegram_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🟡 В работу",
                    callback_data=f"status_work_{telegram_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🟢 Клиент",
                    callback_data=f"status_client_{telegram_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="💎 Партнер",
                    callback_data=f"status_partner_{telegram_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🔴 Не отвечает",
                    callback_data=f"status_failed_{telegram_id}"
                )
            ]
        ]
    )    

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

def complaint_keyboard(
    client_id
):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📩 Написать клиенту",
                    callback_data=f"complaint_msg_{client_id}"
                )
            ],
            [     
                InlineKeyboardButton(
                    text="⚠️ Жалобы",
                    callback_data="admin_complaints"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔄 Сменить наставника",
                    callback_data=f"change_mentor_{client_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Закрыть жалобу",
                    callback_data=f"complaint_close_{client_id}"
                )
            ]
        ]
    )    

from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

def product_keyboard(
    topic
):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Получить консультацию",
                    callback_data=f"product_consult_{topic}"
                )
            ]
        ]
    )    



from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

def product_card_keyboard(product):
    code = PRODUCT_CODES.get(product, "unknown")
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📖 История клиента", callback_data=f"story_{code}"),
                InlineKeyboardButton(text="📦 Готовая программа", callback_data=f"program_{code}")
            ],
            [
                InlineKeyboardButton(text="🛒 Добавить в заказ", callback_data=f"add_to_cart_{product}")
            ]
        ]
    )

def energy_program_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 История клиента",
                    callback_data="story_energy"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛒 Заказать",
                    callback_data="buy_energy"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💬 Консультация",
                    callback_data="consult_energy"
                )
            ]
        ]
    )    

PRODUCT_CODES = {
    "Перфекто Люкс": "perfecto",
    "Виталити Люкс": "vitality",
    "Смарт Люкс": "smart",
    "Энергия Люкс": "energy",
    "ImmunoLux": "immuno",
    "Павлов Спринг": "pavlov",
}

def product_card_keyboard(product):
    code = PRODUCT_CODES.get(product, "unknown")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 История клиента",
                    callback_data=f"story_{code}"
                ),
                InlineKeyboardButton(
                    text="📦 Готовая программа",
                    callback_data=f"program_{code}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛒 Добавить в заказ",
                    callback_data=f"add_to_cart_{product}"
                )
            ]
        ]
    )

def income_info_keyboard():
    """Клавиатура для разворачивающегося текста о доходе"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📖 Развернуть информацию",
                    callback_data="expand_income_info"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤝 Как рекомендовать?",
                    callback_data="how_to_refer"
                )
            ]
        ]
    )


def collapse_keyboard():
    """Клавиатура для сворачивания"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬆️ Свернуть",
                    callback_data="collapse_income_info"
                )
            ]
        ]
    )    

def search_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Поиск по имени", callback_data="search_by_name")],
            [InlineKeyboardButton(text="📱 Поиск по телефону", callback_data="search_by_phone")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_people")]
        ]
    )    

def complaint_button_keyboard(consultation_id):
    """Кнопка для жалобы (появляется через 3 часа)"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❗ Мне не ответили",
                    callback_data=f"complaint_timeout_{consultation_id}"
                )
            ]
        ]
    )    

def confirm_not_registered_keyboard():
    """Клавиатура для подтверждения, что пользователь не зарегистрирован в компании"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтверждаю, что НЕ зарегистрирован",
                    callback_data="confirm_not_registered"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Я уже зарегистрирован в компании",
                    callback_data="already_registered"
                )
            ]
        ]
    )    

def product_recommendation_keyboard(products, symptom):
    """Клавиатура с рекомендованными товарами"""
    buttons = []
    for product in products:
        buttons.append([InlineKeyboardButton(text=f"📦 {product}", callback_data=f"product_{product}")])
    buttons.append([InlineKeyboardButton(text="💬 Получить консультацию", callback_data=f"consult_{symptom}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)    