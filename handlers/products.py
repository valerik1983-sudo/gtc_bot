from aiogram import Router, F
import urllib.parse
from config import CONSULT_BOT_USERNAME
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from keyboards import (
    products_menu_keyboard,
    get_stories_keyboard,
    get_main_menu
)
from inline_keyboards import (
    product_keyboard,
    product_card_keyboard
)
from database import (
    get_all_products_from_db, 
    get_symptoms_by_category, 
    get_symptom_by_name,
    get_user,
    get_referrals_count,
    is_admin,
    get_product_price,
    get_product_by_name,
    get_product_by_id
)
from data.products import PRODUCTS
from data.stories import STORIES
from data.programs import PROGRAMS

router = Router()


# ==================== ОСНОВНЫЕ МЕНЮ ====================

@router.message(F.text == "📋 Показать все товары")
async def show_all_products(message: Message):
    products = get_all_products_from_db()
    
    keyboard = []
    row = []
    for i, product in enumerate(products):
        row.append(KeyboardButton(text=product["name"]))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([KeyboardButton(text="🔙 Назад")])
    
    await message.answer(
        "📦 Каталог продукции Global Trend\n\n "
        "🍯 Перфекто Люкс – бальзам внутрь, очищение клетки\n"
        "💪 Виталити Люкс – бальзам внутрь, питание клетки\n"
        "🧠 Смарт Люкс – бальзам внутрь, память\n"
        "✨ Luxury Day – зубная паста, отбеливание\n"
        "🌙 Luxury Night – зубная паста, защита\n"
        "🛡️ ImmunoLux – иммуномодулятор\n"
        "💧 Павлов Спринг – обмен веществ\n"
        "🌸 Delight Lux – интимное здоровье\n"
        "⚡ Energy Lux – энергия\n"
        "⚡ Wellness Lux – похудение\n"
        "💚 Harmony Lux – гормональный баланс\n"
        "🧴 Self Love – премиальный уход за волосами\n"
        "🌿 Масло May – регенерация кожи\n\n"
        "Выберите интересующий продукт:",
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )


@router.message(F.text == "🔙 Назад")
async def back_to_products(message: Message):
    await message.answer(
        "📦 Выберите действие:",
        reply_markup=products_menu_keyboard
    )


# ==================== ПОКАЗ ТОВАРОВ ====================

async def show_product_card(message: Message):
    product_name = message.text
    from database import get_product_by_name, get_product_price
    product = get_product_by_name(product_name)
    
    if not product:
        await message.answer("❌ Товар не найден")
        return
    
    price = get_product_price(product_name)
    price_display = f"{price} руб." if price and price > 0 else "Цена не указана"
    
    text = f"**{product['name']}**\n\n"
    text += f"💰 {price_display}\n\n"
    text += f"📄 {product['description']}\n\n" if product['description'] else ""
    
    #symptoms = product['symptoms'] if product['symptoms'] else None
    #if symptoms:
    #    text += f"🩺 **Помогает при:**\n{symptoms}\n\n"

    text += "Для заказа добавьте товар в корзину через кнопку ниже 👇"
    
    keyboard_buttons = [
        [InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_to_cart_{product_name}")]
    ]
    
    stories = product['stories'] if product['stories'] else None
    if stories:
        keyboard_buttons.append([InlineKeyboardButton(text="📖 Истории клиентов", callback_data=f"product_stories_{product['id']}")])
    
    keyboard_buttons.append([InlineKeyboardButton(text="💬 Нужна консультация", url="https://t.me/gtcm_consult_bot")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    photo_path = product['photo_path'] if product['photo_path'] else None
    
    if photo_path and photo_path.startswith('AgAC'):
        try:
            await message.answer_photo(
                photo=photo_path,
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка отправки фото: {e}")
            await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


# ==================== КОЛБЭКИ ====================

@router.callback_query(lambda c: c.data.startswith("symptom_"))
async def show_symptom_recommendation(callback: CallbackQuery):
    symptom_name = callback.data.replace("symptom_", "")
    symptom = get_symptom_by_name(symptom_name)
    
    if not symptom:
        await callback.answer("Симптом не найден")
        return
    
    products = symptom["products"].split(",")
    text = symptom["description"]
    
    buttons = []
    for p in products:
        p = p.strip()
        buttons.append([InlineKeyboardButton(text=f"📦 {p}", callback_data=f"product_{p}")])
    buttons.append([InlineKeyboardButton(text="💬 Консультация", callback_data=f"consult_{symptom_name}")])
    
    await callback.message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("product_"))
async def show_product_from_callback(callback: CallbackQuery):
    product_name = callback.data.replace("product_", "")
    
    product = PRODUCTS.get(product_name)
    if not product:
        await callback.answer("Товар не найден")
        return
    
    price = get_product_price(product_name)
    price_text = f"\n\n💰 Цена: {price} руб." if price and price > 0 else ""
    
    photo = FSInputFile(product["photo"])
    
    await callback.message.answer_photo(
        photo=photo,
        caption=f"**{product['title']}**\n\n{product['text']}{price_text}",
        reply_markup=product_card_keyboard(product_name),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "need_consultation")
async def product_consultation(callback: CallbackQuery):
    await callback.message.answer("Напишите ваш вопрос и специалист свяжется с вами.")
    await callback.answer()


@router.callback_query(lambda c: c.data == "how_to_order")
async def how_to_order(callback: CallbackQuery):
    await callback.message.answer(
        "🛒 Как заказать\n\nДля оформления заказа напишите наставнику."
    )
    await callback.answer()


# ==================== ИСТОРИИ ====================

async def show_product_stories(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[2])
    
    from database import get_product_by_id
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer("❌ Товар не найден")
        await callback.answer()
        return
    
    stories = product['stories'] if product['stories'] else None
    if not stories:
        await callback.message.answer("📭 Историй для этого товара пока нет.")
        await callback.answer()
        return
    
    stories_list = stories.split('|')
    for story in stories_list:
        parts = story.strip().split(':', 1)
        if len(parts) == 2:
            title = parts[0].strip()
            content = parts[1].strip()
            text = f"📖 **{title}**\n\n{content}"
        else:
            text = f"📖 {story.strip()}"
        await callback.message.answer(text, parse_mode="Markdown")
    
    await callback.answer()


# ==================== ПОДБОР ПО СИМПТОМАМ ====================

@router.message(F.text == "🔍 Подобрать по показаниям")
async def show_all_symptoms(message: Message):
    from database import get_all_products_from_db

    # Добавляем описание
    await message.answer(
        "🩺 **Подбор по показаниям**\n\n"
        "Выберите ваш симптом, и мы покажем продукты, которые могут помочь.\n\n"
        "Если не нашли нужный симптом – обратитесь к наставнику.",
        parse_mode="Markdown"
    )
    
    products = get_all_products_from_db()
    
    # Собираем все симптомы из товаров
    all_symptoms = set()
    for product in products:
        if product['symptoms']:
            symptoms_list = [s.strip() for s in product['symptoms'].split(',')]
            for symptom in symptoms_list:
                all_symptoms.add(symptom)
    
    if not all_symptoms:
        await message.answer("📭 Пока нет добавленных симптомов в товарах.")
        return
    
    keyboard = []
    row = []
    for i, symptom in enumerate(sorted(all_symptoms)):
        # Используем хеш как ID для callback
        symptom_id = hash(symptom) % 1000000
        row.append(InlineKeyboardButton(
            text=f"🩺 {symptom}", 
            callback_data=f"symptom_select_{symptom_id}"
        ))
        if (i + 1) % 3 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton(text="💬 Связаться с наставником", url="https://t.me/gtcm_consult_bot")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_products")])
    
    await message.answer(
        "🔍 **Выберите симптом:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data.startswith("symptom_select_"))
async def show_products_by_symptom(callback: CallbackQuery):
    symptom_id = int(callback.data.replace("symptom_select_", ""))
    
    from database import get_all_products_from_db, get_product_price
    
    products = get_all_products_from_db()
    
    # Восстанавливаем симптом по ID (хешу)
    all_symptoms = {}
    for product in products:
        if product['symptoms']:
            symptoms_list = [s.strip() for s in product['symptoms'].split(',')]
            for symptom in symptoms_list:
                symptom_hash = hash(symptom) % 1000000
                all_symptoms[symptom_hash] = symptom
    
    symptom = all_symptoms.get(symptom_id)
    if not symptom:
        await callback.message.answer("❌ Симптом не найден")
        await callback.answer()
        return
    
    matching_products = []
    for product in products:
        if product['symptoms']:
            symptoms_list = [s.strip() for s in product['symptoms'].split(',')]
            if symptom in symptoms_list:
                matching_products.append(product)
    
    if not matching_products:
        await callback.message.answer(f"📭 Нет товаров при симптоме '{symptom}'.")
        await callback.answer()
        return
    
    text = f"🩺 **Товары при симптоме '{symptom}':**\n\n"
    
    keyboard = []
    for product in matching_products:
        price = get_product_price(product['name'])
        text += f"• **{product['name']}** — {price} руб.\n"
        # Используем ID товара
        keyboard.append([InlineKeyboardButton(
            text=f"🛒 Добавить {product['name']}", 
            callback_data=f"add_to_cart_{product['id']}"
        )])
    
    keyboard.append([InlineKeyboardButton(text="💬 Связаться с наставником", url="https://t.me/gtcm_consult_bot")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_symptoms")])
    
    await callback.message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_symptoms")
async def back_to_symptoms(callback: CallbackQuery):
    await show_all_symptoms(callback.message)
    await callback.answer()

# ==================== ГОТОВЫЕ ПРОГРАММЫ ====================

@router.message(F.text == "🎁 Готовые программы")
async def show_all_programs_from_products(message: Message):
    from database import get_all_products_from_db
   
    
    products = get_all_products_from_db()
    
    all_programs = set()
    for product in products:
        if product['programs']:
            programs_list = [p.strip() for p in product['programs'].split(',')]
            for program in programs_list:
                if program:
                    all_programs.add(program)
    
    if not all_programs:
        await message.answer("📭 Пока нет готовых программ.")
        return
    
    keyboard = []
    row = []
    for program in sorted(all_programs):
        row.append(InlineKeyboardButton(text=f"🎁 {program}", callback_data=f"prog_{program}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton(text="💬 Связаться с наставником", url="https://t.me/gtcm_consult_bot")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_products")])
    
    await message.answer(
        "🎁 **Готовые программы**\n\n"
        "Это готовые наборы продуктов для решения конкретных задач: здоровье, энергия, иммунитет и т.д.\n\n"
        "Выберите программу:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data.startswith("prog_"))
async def show_products_by_program(callback: CallbackQuery):
    program_name = callback.data.replace("prog_", "")
    
    from database import get_all_products_from_db, get_product_price
    
    products = get_all_products_from_db()
    
    matching_products = []
    for product in products:
        if product['programs']:
            programs_list = [p.strip() for p in product['programs'].split(',')]
            if program_name in programs_list:
                matching_products.append(product)
    
    if not matching_products:
        await callback.message.answer(f"📭 Нет товаров в программе '{program_name}'.")
        await callback.answer()
        return
    
    text = f"🎁 **Программа '{program_name}':**\n\n"
    
    keyboard = []
    for product in matching_products:
        price = get_product_price(product['name'])
        text += f"• **{product['name']}** — {price} руб.\n"
        keyboard.append([InlineKeyboardButton(
            text=f"🛒 Добавить {product['name']}", 
            callback_data=f"add_to_cart_{product['name']}"
        )])
    keyboard.append([InlineKeyboardButton(text="💬 Связаться с наставником", url="https://t.me/gtcm_consult_bot")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_programs_menu")])
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_programs_menu")
async def back_to_programs_menu(callback: CallbackQuery):
    await show_all_programs_from_products(callback.message)
    await callback.answer()


# ==================== ГЛАВНОЕ МЕНЮ ====================

@router.message(F.text == "🏠 Главное меню")
async def back_to_main_menu(message: Message):
    user = get_user(message.from_user.id)
    registered = user is not None
    has_team = get_referrals_count(message.from_user.id) > 0 if registered else False
    is_admin_user = is_admin(message.from_user.id)
    
    await message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu(registered, has_team, is_admin_user)
    )