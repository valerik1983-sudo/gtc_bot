# handlers/order_timeout.py
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from database import get_connection, get_user, add_event
from config import ADMIN_ID

router = Router()


async def check_unprocessed_orders(bot: Bot):
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN admin_notified INTEGER DEFAULT 0")
        conn.commit()
    except:
        pass
    
    cursor.execute("""
        SELECT o.*, u.fio as client_name, u.phone as client_phone, 
               u2.fio as sponsor_name
        FROM orders o
        JOIN users u ON o.user_id = u.telegram_id
        LEFT JOIN users u2 ON u.sponsor_id = u2.telegram_id
        WHERE o.status = 'new' 
        AND datetime(o.created_at) <= datetime('now', '-6 hours')
        AND o.admin_notified = 0
    """)
    
    orders = cursor.fetchall()
    
    for order in orders:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Ответить клиенту", callback_data=f"admin_answer_order_{order['id']}")]
        ])
        
        await bot.send_message(
            ADMIN_ID,
            f"⚠️ **Просроченный заказ!**\n\n"
            f"📦 **Заказ #{order['id']}**\n"
            f"👤 Клиент: {order['client_name']}\n"
            f"📞 Телефон: {order['client_phone']}\n"
            f"👨‍🏫 Наставник: {order['sponsor_name'] or 'Не назначен'}\n"
            f"📅 Создан: {order['created_at']}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        
        cursor.execute("UPDATE orders SET admin_notified = 1 WHERE id = ?", (order['id'],))
        conn.commit()
    
    conn.close()


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