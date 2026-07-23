from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter 
from datetime import datetime
from database import get_office_cities
from database import get_gift_claim, redeem_gift_claim
import re

from database import (
    get_user, update_user, create_order, clear_cart, 
    add_event, get_cart, get_cart_count, add_to_cart,
    get_product_price, get_last_order, get_order_items,
    get_admins, get_connection, remove_from_cart
)
from states import OrderCheckout
from keyboards import products_menu_keyboard

router = Router()


def get_product_price_from_db(product_name):
    """Получить цену товара из БД"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM product_prices WHERE product_name = ?", (product_name,))
    result = cursor.fetchone()
    conn.close()
    return result["price"] if result else 0


@router.callback_query(lambda c: c.data.startswith("add_to_cart_"))
async def add_to_cart_handler(callback: CallbackQuery):
    import urllib.parse
    
    # Получаем данные из callback
    encoded = callback.data.replace("add_to_cart_", "")
    
    # Пробуем получить товар по ID
    try:
        product_id = int(encoded)
        from database import get_product_by_id
        product = get_product_by_id(product_id)
        if product:
            product_name = product['name']
        else:
            await callback.answer("❌ Товар не найден")
            return
    except ValueError:
        # Если не число - это название, декодируем
        product_name = urllib.parse.unquote(encoded)
    
    user_id = callback.from_user.id
    
    # Добавляем в корзину
    from database import add_to_cart, get_cart, get_cart_count, get_product_price as get_price
    add_to_cart(user_id, product_name)
    cart_count = get_cart_count(user_id)
    
    cart = get_cart(user_id)
    cart_items_text = ""
    total = 0
    
    for item in cart:
        price = get_price(item['product_name'])
        item_total = price * item['quantity']
        cart_items_text += f"• {item['product_name']} x{item['quantity']} = {item_total} руб.\n"
        total += item_total
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Продолжить покупки", callback_data="continue_shopping")],
        [InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")]
    ])
    
    await callback.message.answer(
        f"✅ **{product_name}** добавлен в корзину!\n\n"
        f"📦 **Содержимое корзины:**\n{cart_items_text}\n"
        f"💰 **Итого:** {total} руб.\n\n"
        f"В корзине {cart_count} товар(ов).",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "continue_shopping")
async def continue_shopping_handler(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "📦 Выберите категорию или товар:",
        reply_markup=products_menu_keyboard
    )
    await callback.answer()


@router.message(F.text == "🛒 Мой заказ")
async def show_cart(message: Message):
    user_id = message.from_user.id
    cart = get_cart(user_id)
    
    if not cart:
        await message.answer("🛒 Ваша корзина пуста.\n\nДобавьте товары через карточку товара.")
        return
    
    items_text = ""
    total = 0
    
    for item in cart:
        price = get_product_price_from_db(item["product_name"])
        item_total = price * item["quantity"]
        items_text += f"• {item['product_name']} x{item['quantity']} = {item_total} руб.\n"
        total += item_total
    
    keyboard = []
    for item in cart:
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ Удалить {item['product_name']}", 
                callback_data=f"cart_remove_{item['product_name']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="clear_cart")])
    keyboard.append([InlineKeyboardButton(text="🔄 Повторить прошлый заказ", callback_data="repeat_last_order")])
    
    await message.answer(
        f"🛒 **Ваша корзина:**\n\n{items_text}\n"
        f"💰 **Общая сумма:** {total} руб.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "clear_cart")
async def clear_cart_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    clear_cart(user_id)
    await callback.message.edit_text("🛒 Корзина очищена.")
    await callback.answer()


@router.callback_query(F.data == "repeat_last_order")
async def repeat_last_order(callback: CallbackQuery):
    user_id = callback.from_user.id
    last_order = get_last_order(user_id)
    
    if not last_order:
        await callback.answer("У вас нет прошлых заказов")
        return
    
    items = get_order_items(last_order["id"])
    
    for item in items:
        add_to_cart(user_id, item["product_name"], item["quantity"])
    
    await callback.message.answer("✅ Прошлый заказ добавлен в корзину!")
    await show_cart(callback.message)
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("cart_remove_"))
async def remove_from_cart_handler(callback: CallbackQuery):
    product_name = callback.data.replace("cart_remove_", "")
    user_id = callback.from_user.id
    remove_from_cart(user_id, product_name)
    await show_cart(callback.message)
    await callback.answer()


@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = get_user(user_id)
    
    cart = get_cart(user_id)
    if not cart:
        await callback.answer("Корзина пуста")
        return
    
    await state.update_data(user_id=user_id, items=cart)
    
    if user and user.get("fio") and user.get("phone"):
        await state.update_data(full_name=user["fio"], phone=user["phone"])
        
        # Добавляем город в отображение
        city_text = f"\nГород: {user.get('city', 'Не указан')}" if user.get('city') else ""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="confirm_data_yes")],
            [InlineKeyboardButton(text="✏️ Изменить", callback_data="confirm_data_edit")]
        ])
        
        await callback.message.edit_text(
            f"📝 **Проверьте ваши данные:**\n\n"
            f"ФИО: {user['fio']}\n"
            f"Телефон: {user['phone']}{city_text}\n\n"
            f"Всё верно?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        await state.set_state(OrderCheckout.confirm_data)
    else:
        await state.set_state(OrderCheckout.confirm_data)
        await callback.message.edit_text("Введите ваше ФИО:")
    
    await callback.answer()


@router.callback_query(OrderCheckout.confirm_data, F.data == "confirm_data_yes")
async def confirm_data_yes(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user = get_user(user_id)
    city = user.get("city") if user else None
    
    if city:
        await state.update_data(city=city)
        await state.set_state(OrderCheckout.city)
        await process_city(callback.message, state, city)
    else:
        await state.set_state(OrderCheckout.city)
        await callback.message.answer("📍 Введите ваш город:")
    
    await callback.answer()

async def process_city(message: Message, state: FSMContext, city: str):
    """Обработка города и выбор доставки"""
    from database import get_office_cities
    office_cities = get_office_cities()
    
    if city in office_cities:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Самовывоз", callback_data="delivery_pickup"),
             InlineKeyboardButton(text="🚚 СДЭК", callback_data="delivery_cdek")]
        ])
        await state.set_state(OrderCheckout.delivery_method)
        await message.answer(
            f"📍 {city}\n\nВыберите способ получения:",
            reply_markup=keyboard
        )
    else:
        await state.update_data(delivery_method="cdek")
        await state.set_state(OrderCheckout.pickup_point)
        print(f"🔵🔵🔵 Установлено состояние pickup_point") 
        await message.answer(
            f"📍 {city}\n\nВ вашем городе нет офиса компании.\n"
            f"Доступна только доставка СДЭК.\n\n"
            f"📦 Введите адрес или номер пункта выдачи СДЭК:"
        )

@router.callback_query(OrderCheckout.confirm_data, F.data == "confirm_data_edit")
async def confirm_data_edit(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите ваше ФИО:")
    await callback.answer()


@router.message(OrderCheckout.confirm_data)
async def get_full_name(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text.split()) < 2:
        await message.answer("Введите полное ФИО (Имя и Фамилию):")
        return
    
    user_id = message.from_user.id
    update_user(user_id, fio=text)
    await state.update_data(full_name=text)
    await message.answer("📱 Введите ваш телефон:")


@router.message(OrderCheckout.confirm_data)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("full_name"):
        return
    if data.get("phone"):
        return
    
    phone = re.sub(r'[^0-9+]', '', message.text)
    if len(phone) < 10:
        await message.answer("Введите корректный номер телефона:")
        return
    
    user_id = message.from_user.id
    update_user(user_id, phone=phone)
    await state.update_data(phone=phone)
    await state.set_state(OrderCheckout.city)
    await message.answer("📍 Введите ваш город:")


@router.message(StateFilter(OrderCheckout.city))
async def get_city(message: Message, state: FSMContext):
    city = message.text.strip().title()
    user_id = message.from_user.id
    
    # Сохраняем в БД
    update_user(user_id, city=city)
    # Сохраняем в состояние
    await state.update_data(city=city)
    
    # Проверяем, есть ли офис в городе
    cities_with_office = get_office_cities()
    
    if city in cities_with_office:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Самовывоз", callback_data="delivery_pickup"),
             InlineKeyboardButton(text="🚚 СДЭК", callback_data="delivery_cdek")]
        ])
        await state.set_state(OrderCheckout.delivery_method)
        await message.answer(
            f"📍 {city}\n\nВыберите способ получения:",
            reply_markup=keyboard
        )
    else:
        await state.update_data(delivery_method="cdek")
        await state.set_state(OrderCheckout.pickup_point)
        await message.answer(
            f"📍 {city}\n\nВ вашем городе нет офиса компании.\n"
            f"Доступна только доставка СДЭК.\n\n"
            f"📦 Введите адрес или номер пункта выдачи СДЭК:"
        )


@router.callback_query(OrderCheckout.delivery_method)
async def get_delivery_method(callback: CallbackQuery, state: FSMContext):
    method = callback.data.replace("delivery_", "")
    
    if method == "pickup":
        await state.update_data(delivery_method="pickup", pickup_point="Самовывоз из офиса")
        await show_final_confirmation(callback.message, state)
    else:
        await state.update_data(delivery_method="cdek")
        await state.set_state(OrderCheckout.pickup_point)
        await callback.message.edit_text("📦 Введите адрес или номер пункта выдачи СДЭК:")
    
    await callback.answer()


@router.message(OrderCheckout.pickup_point)
async def get_pickup_point(message: Message, state: FSMContext):
    print(f"🔵🔵🔵 get_pickup_point ВЫЗВАН, текст: {message.text}")  # Диагностика
    await state.update_data(pickup_point=message.text.strip())
    await show_final_confirmation(message, state)


async def show_final_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    
    if not items:
        await message.answer("🛒 Корзина пуста!")
        return
    
    items_text = "\n".join([f"• {item['product_name']} x{item['quantity']}" for item in items])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="final_confirm")],
        [InlineKeyboardButton(text="✏️ Изменить", callback_data="final_edit")]
    ])
    
    await state.set_state(OrderCheckout.final_confirm)
    
    await message.answer(
        f"🛒 **Проверьте заказ**\n\n"
        f"ФИО: {data.get('full_name', 'Не указано')}\n"
        f"Телефон: {data.get('phone', 'Не указан')}\n"
        f"Город: {data.get('city', 'Не указан')}\n"
        f"Получение: {'Самовывоз' if data.get('delivery_method') == 'pickup' else 'СДЭК'}\n"
        f"ПВЗ: {data.get('pickup_point', 'не указан')}\n\n"
        f"**Товары:**\n{items_text}\n\n"
        f"Всё верно?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(OrderCheckout.final_confirm, F.data == "final_confirm")
async def final_confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user_id = callback.from_user.id
    
    order_id = create_order(
        user_id=user_id,
        full_name=data["full_name"],
        phone=data["phone"],
        city=data["city"],
        delivery_method=data["delivery_method"],
        pickup_point=data["pickup_point"],
        items=data["items"]
    )
    
    # Проверяем подарок
    gift_claim = get_gift_claim(user_id)
    if gift_claim:
        # Отмечаем подарок как использованный
        redeem_gift_claim(user_id)
        # Добавляем пометку в заказ (можно сохранить в БД, если нужно)
        # Например, если есть поле gift_applied в orders, обновить:
        # cursor.execute("UPDATE orders SET gift_applied = 1 WHERE id = ?", (order_id,))
        # Добавляем информацию в order_text для наставника
        gift_marker = "\n\n🎁 **Подарок за диагностику активирован!**"
    else:
        gift_marker = ""
    
    user = get_user(user_id)
    sponsor_id = user.get("sponsor_id") if user else None
    
    items_text = "\n".join([f"• {item['product_name']} x{item['quantity']}" for item in data["items"]])
    
    order_text = (
        f"🛒 **Новый заказ #{order_id}**\n\n"
        f"**Клиент:** {data['full_name']}\n"
        f"**Телефон:** {data['phone']}\n"
        f"**Город:** {data['city']}\n"
        f"**Получение:** {'Самовывоз' if data['delivery_method'] == 'pickup' else 'СДЭК'}\n"
        f"**ПВЗ:** {data['pickup_point']}\n\n"
        f"**Заказ:**\n{items_text}"
        f"{gift_marker}"
    )
    
    # Отправляем уведомление наставнику
    if sponsor_id:
        try:
            client = get_user(user_id)
            client_username = client.get("username") if client else None
            
            # Добавляем ссылку на клиента, если есть username
            final_order_text = order_text
            if client_username:
                final_order_text += f"\n\n📌 Связаться с клиентом:\n[👤 Написать клиенту](https://t.me/{client_username})"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Ответить клиенту", callback_data=f"answer_order_{order_id}_{user_id}")],
                [InlineKeyboardButton(text="📮 Добавить трек-номер", callback_data=f"add_tracking_{order_id}_{user_id}")]
            ])
            
            await bot.send_message(
                sponsor_id, 
                final_order_text, 
                reply_markup=keyboard,
                parse_mode="Markdown",
                disable_web_page_preview=True
            )
            
            # Проверяем статус наставника (не партнёр)
            sponsor = get_user(sponsor_id)
            if sponsor and sponsor.get('role') != 'partner':
                await bot.send_message(
                    sponsor_id,
                    f"⚠️ **Внимание!**\n\n"
                    f"Ваш приглашённый {data['full_name']} оформил заказ #{order_id}.\n\n"
                    f"Вам необходимо зарегистрироваться в компании (приобрести продукт),\n"
                    f"чтобы не потерять вознаграждение за этого клиента.\n\n"
                    f"По вопросам обращайтесь к администратору или своему наставнику."
                )
        except Exception as e:
            print(f"Ошибка отправки уведомления наставнику: {e}")
    
    clear_cart(user_id)
    add_event(user_id, "order", f"Создан заказ #{order_id}")
    
    await callback.message.edit_text(
        f"✅ **Заказ #{order_id} отправлен!**\n\n"
        f"Наш специалист свяжется с вами для подтверждения.\n\n"
        f"Спасибо за покупку! 💚"
    )
    
    await state.clear()
    await callback.answer()


@router.callback_query(OrderCheckout.final_confirm, F.data == "final_edit")
async def final_edit_order(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить ФИО", callback_data="edit_fio")],
        [InlineKeyboardButton(text="📱 Изменить телефон", callback_data="edit_phone")],
        [InlineKeyboardButton(text="📍 Изменить город", callback_data="edit_city")],
        [InlineKeyboardButton(text="🔄 Начать заново", callback_data="restart_checkout")],
        [InlineKeyboardButton(text="🔙 Назад к заказу", callback_data="back_to_final")]
    ])
    
    await callback.message.edit_text("✏️ Что вы хотите изменить?", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "edit_fio")
async def edit_fio_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("waiting_fio")
    await callback.message.edit_text("Введите новое ФИО (Имя и Фамилию):")
    await callback.answer()


@router.message(StateFilter("waiting_fio"))
async def edit_fio_save(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text.split()) < 2:
        await message.answer("Введите полное ФИО (Имя и Фамилию):")
        return
    
    user_id = message.from_user.id
    update_user(user_id, fio=text)
    await state.update_data(full_name=text)
    
    await message.answer(f"✅ ФИО изменено на: {text}")
    await state.set_state(OrderCheckout.final_confirm)
    await show_final_confirmation(message, state)


@router.callback_query(F.data == "edit_phone")
async def edit_phone_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("waiting_phone")
    await callback.message.edit_text("📱 Введите новый номер телефона:")
    await callback.answer()


@router.message(StateFilter("waiting_phone"))
async def edit_phone_save(message: Message, state: FSMContext):
    phone = re.sub(r'[^0-9+]', '', message.text)
    if len(phone) < 10:
        await message.answer("Введите корректный номер телефона:")
        return
    
    user_id = message.from_user.id
    update_user(user_id, phone=phone)
    await state.update_data(phone=phone)
    
    await message.answer(f"✅ Телефон изменён на: {phone}")
    await state.set_state(OrderCheckout.final_confirm)
    await show_final_confirmation(message, state)


@router.callback_query(F.data == "edit_city")
async def edit_city_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("waiting_city")
    await callback.message.edit_text("📍 Введите новый город:")
    await callback.answer()


@router.message(StateFilter("waiting_city"))
async def edit_city_save(message: Message, state: FSMContext):
    city = message.text.strip().title()
    user_id = message.from_user.id
    update_user(user_id, city=city)
    await state.update_data(city=city)
    
    await message.answer(f"✅ Город изменён на: {city}")
    await state.set_state(OrderCheckout.final_confirm)
    await show_final_confirmation(message, state)


@router.callback_query(F.data == "back_to_final")
async def back_to_final(callback: CallbackQuery, state: FSMContext):
    await show_final_confirmation(callback.message, state)
    await state.set_state(OrderCheckout.final_confirm)
    await callback.answer()


@router.callback_query(F.data == "restart_checkout")
async def restart_checkout(callback: CallbackQuery, state: FSMContext):
    await start_checkout(callback, state)


async def answer_order_to_client(callback: CallbackQuery, state: FSMContext):
    print(f"🔴🔴🔴 answer_order_to_client ВЫЗВАН, data={callback.data}")  # Диагностика
    
    parts = callback.data.split("_")
    print(f"🔴🔴🔴 parts={parts}")  # Диагностика
    
    order_id = int(parts[2])
    user_id = int(parts[3])
    
    print(f"🔴🔴🔴 order_id={order_id}, user_id={user_id}")  # Диагностика
    
    await state.update_data(answer_order_id=order_id, answer_user_id=user_id)
    await state.set_state("waiting_order_answer")
    
    await callback.message.answer("✏️ Введите ответ для клиента:")
    await callback.answer()



async def send_order_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("answer_order_id")
    user_id = data.get("answer_user_id")
    mentor_id = message.from_user.id
    
    if not order_id or not user_id:
        await message.answer("❌ Ошибка: не найден заказ или пользователь")
        await state.clear()
        return
    
    from database import get_user
    mentor = get_user(mentor_id)
    mentor_username = mentor.get("username") if mentor else None
    
    response_text = f"📩 **Ответ по заказу #{order_id}:**\n\n{message.text}"
    
    # Добавляем ссылку только если есть username
    if mentor_username:
        response_text += f"\n\n📌 По вопросам заказа вы можете написать вашему наставнику:\n[👨‍🏫 Связаться с наставником](https://t.me/{mentor_username})"
    else:
        response_text += f"\n\n📌 По вопросам заказа обращайтесь к вашему наставнику."
    
    await message.bot.send_message(
        user_id,
        response_text,
        parse_mode="Markdown"
    )
    
    await message.answer("✅ Ответ отправлен клиенту!")
    await state.clear()


async def add_tracking_start(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    order_id = int(parts[2])
    user_id = int(parts[3])
    
    await state.update_data(tracking_order_id=order_id, tracking_user_id=user_id)
    await state.set_state("waiting_tracking_number")
    
    await callback.message.answer("📮 Введите трек-номер для отправления:")
    await callback.answer()



async def save_tracking_number(message: Message, state: FSMContext):
    from database import update_order_status, add_event, get_user
    
    data = await state.get_data()
    order_id = data.get("tracking_order_id")
    user_id = data.get("tracking_user_id")
    mentor_id = message.from_user.id
    tracking_number = message.text.strip()
    
    if not order_id or not user_id:
        await message.answer("❌ Ошибка: не найден заказ или пользователь")
        await state.clear()
        return
    
    update_order_status(order_id, status="delivered", tracking_number=tracking_number)
    
    mentor = get_user(mentor_id)
    mentor_username = mentor.get("username") if mentor else None
    
    response_text = (
        f"📮 **Трек-номер заказа #{order_id}**\n\n"
        f"Ваше отправление можно отслеживать по номеру:\n"
        f"`{tracking_number}`\n\n"
        f"Ссылка для отслеживания (СДЭК):\n"
        f"https://www.cdek.ru/tracking?code={tracking_number}"
    )
    
    if mentor_username:
        response_text += f"\n\n📌 По вопросам заказа вы можете написать вашему наставнику:\n[👨‍🏫 Связаться с наставником](https://t.me/{mentor_username})"
    else:
        response_text += f"\n\n📌 По вопросам заказа обращайтесь к вашему наставнику."
    
    await message.bot.send_message(
        user_id,
        response_text,
        parse_mode="Markdown"
    )
    
    add_event(user_id, "order", f"Наставник добавил трек-номер {tracking_number} к заказу #{order_id}")
    
    await message.answer(f"✅ Трек-номер `{tracking_number}` добавлен к заказу #{order_id} и отправлен клиенту!")
    await state.clear()