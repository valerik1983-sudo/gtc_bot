from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter, Command

from database import (
    get_user, get_orders_by_sponsor, get_order_by_id,
    get_order_items_with_names, update_order_status, is_admin, get_connection, add_event
)

router = Router()


class EditOrderState(StatesGroup):
    waiting_status = State()
    waiting_tracking = State()


@router.message(F.text == "📦 Заказы клиентов")
async def show_my_orders(message: Message):
    user_id = message.from_user.id
    all_orders = get_orders_by_sponsor(user_id)
    
    # Фильтруем только активные заказы (new и processing)
    active_statuses = ["new", "processing"]
    orders = [o for o in all_orders if o['status'] in active_statuses]
    
    if not orders:
        await message.answer("📭 У вас нет активных заказов клиентов.")
        return
    
    # Показываем заказы по одному с кнопками
    for order in orders:
        status_emoji = {
            "new": "🆕",
            "processing": "🔄"
        }.get(order['status'], "📌")
        
        created_at = order.get('created_at')
        date_str = created_at[:10] if created_at else "дата неизвестна"
        
        # Получаем ФИО клиента
        client_name = order.get('client_name') or "Клиент"
        
        text = f"{status_emoji} **Заказ #{order['id']}**\n"
        text += f"👤 {client_name}\n"
        text += f"📱 {order['phone']}\n"
        text += f"📍 {order['city']}\n"
        text += f"💰 {order['total_amount']} руб.\n"
        text += f"📅 {date_str}\n"
        tracking = order.get('tracking_number')
        if tracking and not tracking.startswith('2026'):  # если это не дата
            text += f"📮 Трек: `{tracking}`\n"
        text += f"📌 Статус: {order['status']}\n"
        
        # Кнопки управления заказом
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Ответить клиенту", callback_data=f"answer_order_{order['id']}_{order['user_id']}"),
                InlineKeyboardButton(text="📮 Добавить трек", callback_data=f"add_tracking_{order['id']}_{order['user_id']}")
            ],
            [
                InlineKeyboardButton(text="🔄 В обработке", callback_data=f"order_status_processing_{order['id']}"),
                InlineKeyboardButton(text="✅ Доставлен", callback_data=f"order_status_delivered_{order['id']}")
            ],
            [
                InlineKeyboardButton(text="🎉 Завершён", callback_data=f"order_status_completed_{order['id']}"),
                InlineKeyboardButton(text="❌ Отменить", callback_data=f"order_status_cancelled_{order['id']}")
            ]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("order"))
async def start_edit_order(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = get_user(user_id)
    
    if not user or not user.get("sponsor_id"):
        if not is_admin(user_id):
            await message.answer("❌ Только наставники могут изменять статусы заказов.")
            return
    
    try:
        order_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("❌ Использование: `/order 123`", parse_mode="Markdown")
        return
    
    order = get_order_by_id(order_id)
    if not order:
        await message.answer(f"❌ Заказ #{order_id} не найден.")
        return
    
    from database import get_user as get_user_by_id
    client = get_user_by_id(order["user_id"])
    
    if client.get("sponsor_id") != user_id and not is_admin(user_id):
        await message.answer("❌ У вас нет прав на редактирование этого заказа.")
        return
    
    await state.update_data(order_id=order_id)
    
    items = get_order_items_with_names(order_id)
    items_text = "\n".join([f"• {item['product_name']} x{item['quantity']}" for item in items])
    
    status_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Новый", callback_data="status_new"),
         InlineKeyboardButton(text="✅ Подтверждён", callback_data="status_confirmed")],
        [InlineKeyboardButton(text="🚚 Отправлен", callback_data="status_shipped"),
         InlineKeyboardButton(text="📦 Доставлен", callback_data="status_delivered")],
        [InlineKeyboardButton(text="❌ Отменён", callback_data="status_cancelled")],
        [InlineKeyboardButton(text="📮 Добавить трек-номер", callback_data="add_tracking")]
    ])
    
    await message.answer(
        f"📦 **Заказ #{order_id}**\n\n"
        f"👤 Клиент: {client['fio']}\n"
        f"📞 Телефон: {client['phone']}\n"
        f"📍 Город: {order['city']}\n"
        f"🚚 Доставка: {order['delivery_method']}\n"
        f"📮 Трек: {order.get('tracking_number') or 'не указан'}\n"
        f"💰 Сумма: {order['total_amount']} руб.\n"
        f"📊 Статус: {order['status']}\n\n"
        f"**Товары:**\n{items_text}\n\n"
        f"Выберите действие:",
        reply_markup=status_keyboard,
        parse_mode="Markdown"
    )
    await state.set_state(EditOrderState.waiting_status)


@router.callback_query(EditOrderState.waiting_status, F.data.startswith("status_"))
async def update_status(callback: CallbackQuery, state: FSMContext):
    status = callback.data.replace("status_", "")
    
    data = await state.get_data()
    order_id = data["order_id"]
    
    update_order_status(order_id, status)
    
    order = get_order_by_id(order_id)
    if order:
        from database import get_user as get_user_by_id
        client = get_user_by_id(order["user_id"])
        
        status_text = {
            "new": "🆕 создан",
            "confirmed": "✅ подтверждён",
            "shipped": "🚚 отправлен",
            "delivered": "📦 доставлен",
            "cancelled": "❌ отменен"
        }.get(status, status)
        
        try:
            await callback.bot.send_message(
                client["telegram_id"],
                f"📦 **Статус вашего заказа #{order_id} изменён!**\n\n"
                f"Новый статус: {status_text}\n\n"
                f"По вопросам заказа обращайтесь к наставнику.",
                parse_mode="Markdown"
            )
        except:
            pass
    
    await callback.answer(f"✅ Статус изменён на {status}")
    await state.clear()


@router.callback_query(EditOrderState.waiting_status, F.data == "add_tracking")
async def start_add_tracking(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditOrderState.waiting_tracking)
    await callback.message.edit_text("📮 Введите трек-номер для заказа:")
    await callback.answer()


@router.message(EditOrderState.waiting_tracking)
async def save_tracking(message: Message, state: FSMContext):
    tracking_number = message.text.strip()
    
    data = await state.get_data()
    order_id = data["order_id"]
    
    update_order_status(order_id, tracking_number=tracking_number)
    
    order = get_order_by_id(order_id)
    if order:
        from database import get_user as get_user_by_id
        client = get_user_by_id(order["user_id"])
        
        try:
            await message.bot.send_message(
                client["telegram_id"],
                f"📮 **Трек-номер заказа #{order_id}**\n\n"
                f"Отслеживать отправление можно по номеру:\n"
                f"`{tracking_number}`\n\n"
                f"Ссылка для отслеживания: https://www.cdek.ru/tracking?code={tracking_number}",
                parse_mode="Markdown"
            )
        except:
            pass
    
    await message.answer(f"✅ Трек-номер `{tracking_number}` добавлен к заказу #{order_id}",
                        parse_mode="Markdown")
    await state.clear()


@router.callback_query(F.data.startswith("admin_answer_order_"))
async def admin_answer_order(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[3])
    await state.update_data(admin_order_id=order_id)
    await state.set_state("admin_waiting_order_answer")
    await callback.message.answer("✏️ Введите ответ для клиента:")
    await callback.answer()


@router.message(StateFilter("admin_waiting_order_answer"))
async def admin_send_order_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data.get("admin_order_id")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM orders WHERE id = ?", (order_id,))
    result = cursor.fetchone()
    
    if result:
        user_id = result[0]
        
        await message.bot.send_message(
            user_id,
            f"📩 **Ответ администратора по заказу #{order_id}:**\n\n{message.text}"
        )
        
        cursor.execute("UPDATE orders SET status = 'admin_answered' WHERE id = ?", (order_id,))
        conn.commit()
        
        add_event(user_id, "order", f"Администратор ответил на заказ #{order_id}")
        
        await message.answer(f"✅ Ответ отправлен клиенту по заказу #{order_id}!")
    else:
        await message.answer("❌ Заказ не найден")
    
    conn.close()
    await state.clear()

@router.callback_query(lambda c: c.data.startswith("order_status_"))
async def update_order_status_from_list(callback: CallbackQuery):
    # Формат: order_status_processing_123
    parts = callback.data.split("_")
    status = parts[2]  # processing, delivered, completed, cancelled
    order_id = int(parts[3])
    
    from database import update_order_status, get_order_by_id, get_user
    
    # Обновляем статус
    update_order_status(order_id, status=status)
    
    # Получаем заказ и клиента
    order = get_order_by_id(order_id)
    if order:
        client = get_user(order['user_id'])
        if client:
            status_text = {
                "processing": "🔄 в обработке",
                "delivered": "✅ доставлен",
                "completed": "🎉 завершён",
                "cancelled": "❌ отменён"
            }.get(status, status)
            
            try:
                await callback.bot.send_message(
                    client['telegram_id'],
                    f"📦 **Статус вашего заказа #{order_id} изменён!**\n\n"
                    f"Новый статус: {status_text}\n\n"
                    f"По вопросам заказа обращайтесь к наставнику.",
                    parse_mode="Markdown"
                )
            except:
                pass
    
    await callback.message.edit_text(
        f"✅ Статус заказа #{order_id} изменён на {status}",
        reply_markup=None
    )
    await callback.answer()  

@router.callback_query(lambda c: c.data.startswith("answer_order_"))
async def answer_order_from_list(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    order_id = int(parts[2])
    user_id = int(parts[3])
    
    await state.update_data(answer_order_id=order_id, answer_user_id=user_id)
    await state.set_state("waiting_order_answer")
    
    await callback.message.answer("✏️ Введите ответ для клиента:")
    await callback.answer()    