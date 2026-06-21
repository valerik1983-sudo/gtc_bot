# handlers/reminders.py
from aiogram import Bot
from datetime import datetime, timedelta
from database import get_connection, get_user, get_cart
from config import ADMIN_ID

async def check_cart_reminders(bot: Bot):
    """Напоминание пользователям, у которых есть товары в корзине более 1 часа"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Находим пользователей с товарами в корзине старше 1 часа
    cursor.execute("""
        SELECT DISTINCT c.user_id, u.fio, COUNT(c.id) as items_count
        FROM cart c
        JOIN users u ON c.user_id = u.telegram_id
        WHERE c.added_at <= datetime('now', '-1 hour')
        AND c.reminder_sent = 0
        GROUP BY c.user_id
    """)
    
    users = cursor.fetchall()
    
    for user in users:
        user_id = user['user_id']
        items_count = user['items_count']
        user_fio = user['fio']
        
        # Отправляем напоминание
        await bot.send_message(
            user_id,
            f"🛒 **У вас есть незавершённый заказ!**\n\n"
            f"{user_fio}, вы добавили {items_count} товар(ов) в корзину более часа назад.\n\n"
            f"Вы можете продолжить оформление заказа, нажав кнопку «🛒 Мой заказ» в главном меню.\n\n"
            f"Если у вас возникли вопросы, напишите вашему наставнику."
        )
        
        # Отмечаем, что напоминание отправлено
        cursor.execute("UPDATE cart SET reminder_sent = 1 WHERE user_id = ?", (user_id,))
        conn.commit()
    
    conn.close()


async def check_mentor_reminders(bot: Bot):
    """Напоминание наставникам о новых пользователях, которым не писали 3 дня"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Находим наставников и их новых пользователей
    cursor.execute("""
        SELECT u.telegram_id as user_id, u.fio as user_fio, 
               u.sponsor_id as mentor_id, u.created_at,
               m.fio as mentor_fio,
               m.telegram_id as mentor_telegram
        FROM users u
        JOIN users m ON u.sponsor_id = m.telegram_id
        WHERE u.status = 'new' 
        AND u.created_at <= datetime('now', '-3 days')
        AND (u.last_mentor_contact IS NULL OR u.last_mentor_contact < u.created_at)
    """)
    
    new_users = cursor.fetchall()
    
    # Группируем по наставникам
    mentors = {}
    for user in new_users:
        mentor_id = user['mentor_id']
        if mentor_id not in mentors:
            mentors[mentor_id] = {
                'fio': user['mentor_fio'],
                'users': []
            }
        mentors[mentor_id]['users'].append(user)
    
    for mentor_id, data in mentors.items():
        text = f"⏰ **Напоминание о новых пользователях!**\n\n"
        text += f"{data['fio']}, у вас есть пользователи, которым вы не написали уже 3 дня:\n\n"
        
        for user in data['users']:
            text += f"• {user['user_fio']} (зарегистрировался: {user['created_at'][:10]})\n"
        
        text += f"\nСвяжитесь с ними, чтобы помочь им начать работу!"
        
        await bot.send_message(mentor_id, text)
        
        # Отмечаем, что напоминание отправлено
        for user in data['users']:
            cursor.execute("UPDATE users SET last_mentor_contact = CURRENT_TIMESTAMP WHERE telegram_id = ?", (user['user_id'],))
        conn.commit()
    
    conn.close()


async def check_consultation_reminders(bot: Bot):
    """Напоминание наставникам о консультациях без ответа (6+ часов)"""
    from consult_bot import get_consult_by_id, update_consult_status
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Находим активные консультации без ответа старше 6 часов
    cursor.execute("""
        SELECT cr.*, u.fio as client_fio, u.phone as client_phone,
               m.fio as mentor_fio, m.telegram_id as mentor_id
        FROM consult_requests cr
        JOIN users u ON cr.user_id = u.telegram_id
        JOIN users m ON cr.sponsor_id = m.telegram_id
        WHERE cr.status = 'active' 
        AND cr.last_message_at IS NULL
        AND cr.reminder_count < 2
        AND datetime(cr.created_at) <= datetime('now', '-6 hours')
    """)
    
    consults = cursor.fetchall()
    
    for consult in consults:
        consult_id = consult['id']
        user_id = consult['user_id']
        mentor_id = consult['mentor_id']
        client_fio = consult['client_fio']
        mentor_fio = consult['mentor_fio']
        created_at = consult['created_at']
        
        # Уведомляем наставника
        await bot.send_message(
            mentor_id,
            f"⏰ **Напоминание о консультации!**\n\n"
            f"{mentor_fio}, пользователь {client_fio} ждёт ответа уже более 6 часов.\n\n"
            f"📅 Запрос создан: {created_at}\n\n"
            f"Пожалуйста, ответьте пользователю как можно скорее."
        )
        
        # Увеличиваем счётчик напоминаний
        cursor.execute("UPDATE consult_requests SET reminder_count = reminder_count + 1 WHERE id = ?", (consult_id,))
        conn.commit()
        
        # Если напоминаний уже 2, меняем статус на 'complaint'
        cursor.execute("SELECT reminder_count FROM consult_requests WHERE id = ?", (consult_id,))
        reminder_count = cursor.fetchone()['reminder_count']
        
        if reminder_count >= 2:
            update_consult_status(consult_id, 'complaint')
            
            # Уведомляем админа
            await bot.send_message(
                ADMIN_ID,
                f"⚠️ **Консультация без ответа!**\n\n"
                f"Пользователь: {client_fio}\n"
                f"Наставник: {mentor_fio}\n"
                f"Консультация #{consult_id}\n"
                f"Наставник не ответил после двух напоминаний.\n"
                f"Статус изменён на 'complaint'."
            )
    
    conn.close()


async def run_reminders(bot: Bot):
    """Запускает все проверки напоминаний"""
    await check_cart_reminders(bot)
    await check_mentor_reminders(bot)
    await check_consultation_reminders(bot)