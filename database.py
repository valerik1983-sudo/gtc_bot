# ✅ ПРАВИЛЬНО:
import os
import sqlite3
import asyncio

DB_NAME = os.getenv('DB_PATH', 'crm.db')


def get_connection():

    conn = sqlite3.connect(DB_NAME)

    conn.row_factory = sqlite3.Row

    return conn


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    # Пользователи

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        telegram_id INTEGER UNIQUE,
        username TEXT,

        fio TEXT,
        birth_date TEXT,
        phone TEXT,
        city TEXT,
        gender TEXT,

        sponsor_id INTEGER,

        role TEXT DEFAULT 'lead',

        status TEXT DEFAULT 'new',

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        last_contact_at TIMESTAMP
    )
    """)

    # Консультации

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS consultations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        client_telegram_id INTEGER,
        sponsor_telegram_id INTEGER,

        topic TEXT,
        phone TEXT,
        preferred_time TEXT,

        status TEXT DEFAULT 'new',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Администраторы

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        telegram_id INTEGER UNIQUE,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    sender_id INTEGER,
    receiver_id INTEGER,

    text TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS mentor_chats (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    mentor_id INTEGER,

    client_id INTEGER,

    consultation_id INTEGER,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    #История чатов

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    telegram_id INTEGER,

    event_type TEXT,

    event_text TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    client_telegram_id INTEGER,
    sponsor_telegram_id INTEGER,

    consultation_id INTEGER,

    status TEXT DEFAULT 'new',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Товары
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,           -- название товара (как в PRODUCTS)
    title TEXT,                 -- короткое название
    description TEXT,           -- описание
    photo_path TEXT,            -- путь к фото (images/perfecto.PNG)
    story_key TEXT,             -- ключ для историй
    program_key TEXT,           -- ключ для программ
    symptoms TEXT,              -- список симптомов через запятую
    price TEXT,                 -- цена
    volume TEXT,                -- объём
    is_active INTEGER DEFAULT 1 -- активен/скрыт
    )
    """)
    # 👇 ДОБАВЬТЕ ЭТИ СТРОКИ ПОСЛЕ СОЗДАНИЯ ТАБЛИЦЫ products
    # Добавляем новые колонки (если их нет)
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN stories TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN programs TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN symptoms_text TEXT")
    except:
        pass

    #Заказы
    # Корзина
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_name TEXT,
    quantity INTEGER DEFAULT 1,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
    )
    """)

    # Заказы
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    full_name TEXT,
    phone TEXT,
    city TEXT,
    delivery_method TEXT,
    pickup_point TEXT,
    total_amount REAL,
    status TEXT DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Товары в заказе
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    product_name TEXT,
    quantity INTEGER,
    price REAL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
    )
    """)

    # Прайс-лист (цены товаров)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_prices (
    product_name TEXT PRIMARY KEY,
    price REAL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

      # Таблица городов с офисами
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS office_cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT UNIQUE NOT NULL
        )
    """)
    
    # Добавляем тестовые города
    init_office_cities()

     # Таблица рефералов (наставники)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            sponsor_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, sponsor_id)
        )
    """)

    #cursor.execute("ALTER TABLE orders ADD COLUMN admin_notified INTEGER DEFAULT 0")
    
    # Создаем индекс для быстрого поиска
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_referrals_user_id ON referrals(user_id)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_referrals_sponsor_id ON referrals(sponsor_id)
    """)

    # Таблица историй клиентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            product_name TEXT,
            category TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица программ
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            products TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица симптомов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS symptoms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            title TEXT,
            description TEXT,
            products TEXT,
            category TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)

    # В init_db() добавьте:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            answers TEXT,
            result TEXT,
            total_score INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== ВРЕМЕННЫЕ РЕФЕРАЛЬНЫЕ СВЯЗИ =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS temp_refs (
        telegram_id INTEGER PRIMARY KEY,
        sponsor_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN sort_order INTEGER DEFAULT 0")
        print("✅ Добавлена колонка sort_order")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ Колонка sort_order уже существует")
        else:
            raise

    conn.commit()
    conn.close()


# =========================
# USERS
# =========================

def add_user(
    telegram_id,
    username,
    fio,
    birth_date,
    phone,
    city,    
    gender,
    sponsor_id=None,
    role="lead"  # 👈 ДОБАВЬТЕ
):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO users
    (
        telegram_id,
        username,
        fio,
        birth_date,
        phone,
        city,
        gender,
        sponsor_id,
        role
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        telegram_id,
        username,
        fio,
        birth_date,
        phone,
        city,
        gender,
        sponsor_id,
        role
    ))

    conn.commit()
    conn.close()


def get_user(telegram_id):
    """Получить пользователя по Telegram ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Сначала получаем данные пользователя
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    # Получаем названия колонок
    columns = [description[0] for description in cursor.description]
    user = dict(zip(columns, row))
    
    # Получаем sponsor_id из таблицы referrals, если есть
    cursor.execute("SELECT sponsor_id FROM referrals WHERE user_id = ?", (telegram_id,))
    sponsor_row = cursor.fetchone()
    
    if sponsor_row:
        user['sponsor_id'] = sponsor_row[0]
    else:
        user['sponsor_id'] = None
    
    conn.close()
    return user


def get_sponsor(telegram_id):
    """Получить наставника пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Сначала проверяем таблицу referrals
    cursor.execute("SELECT sponsor_id FROM referrals WHERE user_id = ?", (telegram_id,))
    row = cursor.fetchone()
    
    if row and row['sponsor_id']:
        conn.close()
        return {"sponsor_id": row['sponsor_id']}
    
    # Если нет, проверяем поле sponsor_id в таблице users
    cursor.execute("SELECT sponsor_id FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row and row['sponsor_id']:
        return {"sponsor_id": row['sponsor_id']}
    
    return None


# =========================
# CONSULTATIONS
# =========================

def create_consultation(
    client_telegram_id,
    sponsor_telegram_id,
    topic,
    phone,
    preferred_time
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO consultations
    (
        client_telegram_id,
        sponsor_telegram_id,
        topic,
        phone,
        preferred_time
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        client_telegram_id,
        sponsor_telegram_id,
        topic,
        phone,
        preferred_time
    ))

    conn.commit()
    conn.close()


def get_consultations_by_client(
    client_telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM consultations
        WHERE client_telegram_id = ?
        ORDER BY id DESC
        """,
        (client_telegram_id,)
    )

    consultations = cursor.fetchall()

    conn.close()

    return consultations


def get_last_consultation(
    client_telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM consultations
        WHERE client_telegram_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (client_telegram_id,)
    )

    consultation = cursor.fetchone()

    conn.close()

    return consultation

def update_consultation_status(
    consultation_id,
    status
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE consultations
        SET status = ?
        WHERE id = ?
        """,
        (
            status,
            consultation_id
        )
    )

    conn.commit()
    conn.close()

def get_consultation(
    consultation_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM consultations
        WHERE id = ?
        """,
        (consultation_id,)
    )

    consultation = cursor.fetchone()

    conn.close()

    return consultation

def get_active_consultation(
    client_telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM consultations
        WHERE client_telegram_id = ?
        AND is_active = 1
        ORDER BY id DESC
        LIMIT 1
        """,
        (client_telegram_id,)
    )

    consultation = cursor.fetchone()

    conn.close()

    return consultation    

# =========================
# ADMINS
# =========================

def add_admin(
    telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO admins
        (
            telegram_id
        )
        VALUES (?)
        """,
        (telegram_id,)
    )

    conn.commit()
    conn.close()


def get_admins():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM admins
        """
    )

    admins = cursor.fetchall()

    conn.close()

    return admins

def get_my_people(
    sponsor_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE sponsor_id = ?
        ORDER BY id DESC
        """,
        (sponsor_id,)
    )

    users = cursor.fetchall()

    conn.close()

    return users

def get_user_by_id(user_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    conn.close()

    return user    

def update_user_status(
    telegram_id,
    status
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET status = ?
        WHERE telegram_id = ?
        """,
        (
            status,
            telegram_id
        )
    )

    conn.commit()
    conn.close()    

def get_user_by_telegram_id(
    telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,)
    )

    user = cursor.fetchone()

    conn.close()

    return user    
  
def get_my_people_count(
    sponsor_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE sponsor_id = ?
        """,
        (sponsor_id,)
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count  

def get_people_count_by_status(
    sponsor_id,
    status
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE sponsor_id = ?
        AND status = ?
        """,
        (
            sponsor_id,
            status
        )
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count    

def get_funnel_stats(
    sponsor_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT status, COUNT(*)
        FROM users
        WHERE sponsor_id = ?
        GROUP BY status
        """,
        (sponsor_id,)
    )

    stats = cursor.fetchall()

    conn.close()

    return stats    

def add_event(
    telegram_id,
    event_type,
    event_text
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO events
        (
            telegram_id,
            event_type,
            event_text
        )
        VALUES (?, ?, ?)
        """,
        (
            telegram_id,
            event_type,
            event_text
        )
    )

    conn.commit()
    conn.close()

def get_events(
    telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM events
        WHERE telegram_id = ?
        ORDER BY id DESC
        LIMIT 20
        """,
        (telegram_id,)
    )

    events = cursor.fetchall()

    conn.close()

    return events

def update_last_contact(
    telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET last_contact_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
        """,
        (telegram_id,)
    )

    conn.commit()
    conn.close()

def get_stale_leads():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE status IN ('new', 'work')
        AND (
            last_contact_at IS NULL
            OR
            datetime(last_contact_at)
            <= datetime('now', '-3 day')
        )
        """
    )

    users = cursor.fetchall()

    conn.close()

    return users   

def is_admin(
    telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM admins
        WHERE telegram_id = ?
        """,
        (telegram_id,)
    )

    admin = cursor.fetchone()

    conn.close()

    return admin is not None    

def get_referrals_count(
    sponsor_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE sponsor_id = ?
        """,
        (sponsor_id,)
    )

    count = cursor.fetchone()[0]

    conn.close()

    return count

def get_referrals(
    sponsor_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE sponsor_id = ?
        ORDER BY id DESC
        """,
        (sponsor_id,)
    )

    users = cursor.fetchall()

    conn.close()

    return users

def get_funnel_stats(
    sponsor_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT status,
               COUNT(*) as count
        FROM users
        WHERE sponsor_id = ?
        GROUP BY status
        """,
        (sponsor_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    result = {
        "new": 0,
        "work": 0,
        "client": 0,
        "partner": 0
    }

    for row in rows:

        result[row["status"]] = row["count"]

    return result    

def get_users_need_attention(
    sponsor_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE sponsor_id = ?
        AND status IN ('new', 'work')
        ORDER BY last_contact_at ASC
        """,
        (sponsor_id,)
    )

    users = cursor.fetchall()

    conn.close()

    return users    

def get_consultations_by_sponsor(
    sponsor_telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM consultations
        WHERE sponsor_telegram_id = ?
        ORDER BY id DESC
        """,
        (sponsor_telegram_id,)
    )

    consultations = cursor.fetchall()

    conn.close()

    return consultations

def get_consultation_stats(
    sponsor_telegram_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT status,
               COUNT(*) as count
        FROM consultations
        WHERE sponsor_telegram_id = ?
        GROUP BY status
        """,
        (sponsor_telegram_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    result = {
         "new": 0,
        "work": 0,
        "client": 0,
        "partner": 0,
        "failed": 0
    }

    for row in rows:

        result[row["status"]] = row["count"]

    return result        

def get_consultations_by_status(
    sponsor_telegram_id,
    status
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM consultations
        WHERE sponsor_telegram_id = ?
        AND status = ?
        ORDER BY id DESC
        """,
        (
            sponsor_telegram_id,
            status
        )
    )

    consultations = cursor.fetchall()

    conn.close()

    return consultations    

def get_system_stats():

    conn = sqlite3.connect(
        "crm.db"
    )

    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )
    users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM consultations"
    )
    consultations = cursor.fetchone()[0]

    conn.close()

    return {
        "users": users,
        "consultations": consultations
    }    

def get_all_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT telegram_id
    FROM users
    """)

    users = cursor.fetchall()

    conn.close()

    return users    

def get_all_partners():
    """Получить всех пользователей, у которых есть приглашённые (спонсоров)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Находим всех пользователей, у которых есть приглашённые
    cursor.execute("""
        SELECT DISTINCT u.telegram_id, u.fio
        FROM users u
        WHERE EXISTS (SELECT 1 FROM users WHERE sponsor_id = u.telegram_id)
        ORDER BY u.fio
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return rows

def create_complaint(
    client_id,
    sponsor_id,
    consultation_id
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO complaints (
            client_telegram_id,
            sponsor_telegram_id,
            consultation_id
        )
        VALUES (?, ?, ?)
        """,
        (
            client_id,
            sponsor_id,
            consultation_id
        )
    )

    conn.commit()
    conn.close()   

def get_complaints():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM complaints
    WHERE status='new'
    ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows    

def get_old_consultations():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM consultations
    WHERE status='new'
    """)

    result = cursor.fetchall()

    conn.close()

    return result    

def get_sponsor_chain(telegram_id):
    """Возвращает цепочку спонсоров выше (список от верхнего до прямого)"""
    chain = []
    current_id = telegram_id
    
    while True:
        user = get_user(current_id)
        if not user or not user["sponsor_id"]:
            break
        sponsor = get_user(user["sponsor_id"])
        if not sponsor:
            break
        chain.append(sponsor)
        current_id = sponsor["telegram_id"]
    
    return chain


def get_full_hierarchy(telegram_id, max_depth=10):
    """Возвращает всю структуру ниже (кого пригласил пользователь)"""
    def build_tree(sponsor_id, depth=0):
        if depth > max_depth:
            return []
        
        referrals = get_referrals(sponsor_id)
        tree = []
        for user in referrals:
            tree.append({
                "user": user,
                "children": build_tree(user["telegram_id"], depth + 1)
            })
        return tree
    
    return build_tree(telegram_id)


def get_available_sponsors(telegram_id):
    """
    Возвращает список пользователей, которые могут стать спонсором
    (все, кроме самого себя и своих нижестоящих)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем всех пользователей, исключая:
    # 1. самого себя
    # 2. своих рефералов (нельзя назначить спонсора тому, кто ниже)
    
    # Собираем ID всех рефералов (всех уровней)
    exclude_ids = {telegram_id}
    
    def collect_descendants(sponsor_id):
        referrals = get_referrals(sponsor_id)
        for ref in referrals:
            exclude_ids.add(ref["telegram_id"])
            collect_descendants(ref["telegram_id"])
    
    collect_descendants(telegram_id)
    
    # Формируем запрос
    placeholders = ",".join("?" for _ in exclude_ids)
    cursor.execute(f"""
        SELECT telegram_id, fio, username
        FROM users
        WHERE telegram_id NOT IN ({placeholders})
        ORDER BY fio
    """, tuple(exclude_ids))
    
    users = cursor.fetchall()
    conn.close()
    return users


def update_sponsor(telegram_id, new_sponsor_id):
    """Обновляет спонсора пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users
        SET sponsor_id = ?
        WHERE telegram_id = ?
    """, (new_sponsor_id, telegram_id))
    
    conn.commit()
    conn.close()
    
    # Логируем событие
    add_event(telegram_id, "sponsor_change", f"Спонсор изменён на {new_sponsor_id}")    

def get_total_referrals_count(telegram_id):
    """Возвращает общее количество рефералов (всех уровней) без рекурсии"""
    total = 0
    stack = [telegram_id]
    
    while stack:
        current_id = stack.pop()
        referrals = get_referrals(current_id)
        
        for ref in referrals:
            total += 1
            stack.append(ref["telegram_id"])
    
    return total   

def get_unanswered_consultations():
    """Возвращает консультации, на которые не ответили более 3 часов (только в дневное время)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем все консультации со статусом 'new', созданные более 3 часов назад
    # и на которые ещё не отправляли напоминание
    cursor.execute("""
        SELECT c.*, u.fio, u.username
        FROM consultations c
        JOIN users u ON u.telegram_id = c.client_telegram_id
        WHERE c.status = 'new' 
        AND c.created_at <= datetime('now', '-3 hours')
        AND (c.reminder_sent IS NULL OR c.reminder_sent = 0)
        AND c.is_active = 1
    """)
    
    return cursor.fetchall()


def mark_reminder_sent(consultation_id):
    """Отмечаем, что напоминание отправлено"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE consultations
        SET reminder_sent = 1
        WHERE id = ?
    """, (consultation_id,))
    
    conn.commit()
    conn.close()


def add_complaint_button_shown(client_telegram_id, consultation_id):
    """Добавляем отметку, что кнопка жалобы показана клиенту"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE consultations
        SET complaint_button_shown = 1
        WHERE client_telegram_id = ? AND id = ?
    """, (client_telegram_id, consultation_id))
    
    conn.commit()
    conn.close()    
    

def get_all_products_from_db():
    """Получить все товары из БД"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY name")
    products = cursor.fetchall()
    conn.close()
    print(f"🔍 Найдено товаров: {len(products)}") 
    return products


def get_product_by_name(name):
    """Получить товар по названию"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name = ?", (name,))
    product = cursor.fetchone()
    conn.close()
    return product

 
def delete_product_from_db(product_id):
    """Удалить товар (скрыть)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()    

def add_new_product(name, description, photo_path=None):
    """Добавить новый товар в БД с автоматическим порядком"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем максимальный sort_order
    cursor.execute("SELECT MAX(sort_order) FROM products")
    result = cursor.fetchone()
    max_order = result[0] if result and result[0] is not None else -1
    new_order = max_order + 1
    
    try:
        cursor.execute("""
            INSERT INTO products (name, title, description, photo_path, sort_order, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (name, name, description, photo_path, new_order))
        conn.commit()
        product_id = cursor.lastrowid
        print(f"✅ Товар {name} добавлен с порядком {new_order}")
        return product_id
    except Exception as e:
        print(f"❌ Ошибка добавления товара: {e}")
        return None
    finally:
        conn.close()

# ==================== РЕДАКТИРОВАНИЕ ТОВАРОВ ====================

def update_product_in_db(product_id, **kwargs):
    """Обновить товар в БД"""
    conn = get_connection()
    cursor = conn.cursor()

    # Разрешенные поля для обновления
    allowed_fields = ['name', 'title', 'description', 'photo_path', 'story_key', 'program_key', 'price', 'volume', 'is_active']
    
    for key, value in kwargs.items():
        if value is not None:
            cursor.execute(f"UPDATE products SET {key} = ? WHERE id = ?", (value, product_id))
    
    conn.commit()
    conn.close()    

def sync_products_from_file():
    """Синхронизирует товары из файла в БД"""
    from data.products import PRODUCTS
    
    print(f"📦 Загружено продуктов из файла: {len(PRODUCTS)}")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for name, product in PRODUCTS.items():
        print(f"  ➕ Синхронизация: {name}")
        cursor.execute("""
            INSERT OR REPLACE INTO products 
            (name, title, description, photo_path, story_key, program_key, price, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            product.get("title", name),
            product.get("text", ""),
            product.get("photo", ""),
            product.get("story", ""),
            product.get("program", ""),
            product.get("price", ""),
            product.get("volume", "")
        ))
    
    conn.commit()
    conn.close()
    print("✅ Товары синхронизированы из файла в БД")    

def get_product_by_id(product_id):
    """Получить товар по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product     

# Функции для работы с симптомами
def get_symptoms_by_category(category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM symptoms WHERE category = ? AND is_active = 1", (category,))
    symptoms = cursor.fetchall()
    conn.close()
    return symptoms

def get_symptom_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM symptoms WHERE name = ?", (name,))
    symptom = cursor.fetchone()
    conn.close()
    return symptom

def add_symptom(name, title, description, products, category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO symptoms (name, title, description, products, category)
        VALUES (?, ?, ?, ?, ?)
    """, (name, title, description, products, category))
    conn.commit()
    conn.close()    

# ==================== КОРЗИНА ====================

def add_to_cart(user_id, product_name, quantity=1):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже такой товар в корзине
    cursor.execute("SELECT * FROM cart WHERE user_id = ? AND product_name = ?", (user_id, product_name))
    existing = cursor.fetchone()
    
    if existing:
        cursor.execute("UPDATE cart SET quantity = quantity + ? WHERE user_id = ? AND product_name = ?",
                      (quantity, user_id, product_name))
    else:
        cursor.execute("INSERT INTO cart (user_id, product_name, quantity) VALUES (?, ?, ?)",
                      (user_id, product_name, quantity))
    
    conn.commit()
    conn.close()


def get_cart(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, quantity FROM cart WHERE user_id = ?", (user_id,))
    cart = cursor.fetchall()
    conn.close()
    return cart


def clear_cart(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def remove_from_cart(user_id, product_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_name = ?", (user_id, product_name))
    conn.commit()
    conn.close()


def get_cart_count(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(quantity) as count FROM cart WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result["count"] or 0


# ==================== ЦЕНЫ ====================

def get_product_price(product_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT price FROM product_prices WHERE product_name = ?", (product_name,))
    result = cursor.fetchone()
    conn.close()
    return result["price"] if result else 0


def set_product_price(product_name, price):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO product_prices (product_name, price)
        VALUES (?, ?)
    """, (product_name, price))
    conn.commit()
    conn.close()


# ==================== ЗАКАЗЫ ====================

def create_order(user_id, full_name, phone, city, delivery_method, pickup_point, items):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Считаем сумму
    total = 0
    for item in items:
        price = get_product_price(item["product_name"])
        total += price * item["quantity"]

    utc_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')    
    
    cursor.execute("""
        INSERT INTO orders (user_id, full_name, phone, city, delivery_method, pickup_point, total_amount)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, full_name, phone, city, delivery_method, pickup_point, total))
    
    order_id = cursor.lastrowid
    
    for item in items:
        price = get_product_price(item["product_name"])
        cursor.execute("""
            INSERT INTO order_items (order_id, product_name, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (order_id, item["product_name"], item["quantity"], price))
    
    conn.commit()
    conn.close()
    return order_id


def get_user_orders(user_id, limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM orders 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (user_id, limit))
    orders = cursor.fetchall()
    conn.close()
    return orders


def get_order_items(order_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_name, quantity, price FROM order_items WHERE order_id = ?", (order_id,))
    items = cursor.fetchall()
    conn.close()
    return items


def get_last_order(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM orders 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (user_id,))
    order = cursor.fetchone()
    conn.close()
    return order    

# database.py - добавьте эту функцию
def update_user(telegram_id, **kwargs):
    """Обновление данных пользователя в БД"""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    for key, value in kwargs.items():
        if value is not None:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if not updates:
        return False
    
    values.append(telegram_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE telegram_id = ?"
    
    try:
        cursor.execute(query, values)
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка обновления пользователя: {e}")
        return False
    finally:
        conn.close()

# database.py - добавьте эти функции

def get_orders_by_sponsor(sponsor_id):
    """Получить все заказы клиентов наставника"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT o.*, u.fio as client_name 
        FROM orders o
        JOIN users u ON o.user_id = u.telegram_id
        WHERE u.sponsor_id = ?
        ORDER BY o.created_at DESC
    """, (sponsor_id,))
    
    orders = []
    for row in cursor.fetchall():
        # Используем row как словарь, а не по индексам
        orders.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "full_name": row["full_name"],
            "phone": row["phone"],
            "city": row["city"],
            "delivery_method": row["delivery_method"],
            "pickup_point": row["pickup_point"],
            "total_amount": row["total_amount"],
            "status": row["status"],
            "tracking_number": row["tracking_number"] if row["tracking_number"] else None,
            "created_at": row["created_at"],
            "client_name": row["client_name"] or row["full_name"] or "Клиент"  # берем из users или из заказа
        })
    
    conn.close()
    return orders


def get_order_by_id(order_id):
    """Получить заказ по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    
    if row:
        order = {
            "id": row[0],
            "user_id": row[1],
            "full_name": row[2],
            "phone": row[3],
            "city": row[4],
            "delivery_method": row[5],
            "pickup_point": row[6],
            "total_amount": row[7],
            "status": row[8],
            "tracking_number": row[9],
            "created_at": row[10]
        }
        conn.close()
        return order
    
    conn.close()
    return None


def get_order_items_with_names(order_id):
    """Получить товары заказа с названиями"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT oi.*, p.name as product_name 
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,))
    
    items = []
    for row in cursor.fetchall():
        items.append({
            "id": row[0],
            "order_id": row[1],
            "product_id": row[2],
            "product_name": row[3],
            "quantity": row[4],
            "price": row[5]
        })
    
    conn.close()
    return items


def update_order_status(order_id, status=None, tracking_number=None):
    """Обновить статус заказа и/или трек-номер"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if status and tracking_number:
        cursor.execute("""
            UPDATE orders 
            SET status = ?, tracking_number = ? 
            WHERE id = ?
        """, (status, tracking_number, order_id))
    elif status:
        cursor.execute("""
            UPDATE orders 
            SET status = ? 
            WHERE id = ?
        """, (status, order_id))
    elif tracking_number:
        cursor.execute("""
            UPDATE orders 
            SET tracking_number = ? 
            WHERE id = ?
        """, (tracking_number, order_id))
    
    conn.commit()
    conn.close()


def get_office_cities():
    """Получить список городов, где есть офисы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT city FROM office_cities")
    cities = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return cities        

def get_user(telegram_id):
    """Получить пользователя по Telegram ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
    
    columns = [description[0] for description in cursor.description]
    user = dict(zip(columns, row))
    
    # Если в таблице users уже есть sponsor_id, используем его
    if user.get('sponsor_id'):
        conn.close()
        return user
    
    # Если нет, ищем в referrals
    cursor.execute("SELECT sponsor_id FROM referrals WHERE user_id = ?", (telegram_id,))
    sponsor_row = cursor.fetchone()
    
    if sponsor_row:
        user['sponsor_id'] = sponsor_row[0]
    else:
        user['sponsor_id'] = None
    
    conn.close()
    return user

# database.py - добавьте эти функции (без создания таблиц)

def get_order_by_id(order_id):
    """Получить заказ по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
    row = cursor.fetchone()
    
    if row:
        order = {
            "id": row[0],
            "user_id": row[1],
            "full_name": row[2],
            "phone": row[3],
            "city": row[4],
            "delivery_method": row[5],
            "pickup_point": row[6],
            "total_amount": row[7],
            "status": row[8],
            "tracking_number": row[9],
            "created_at": row[10]
        }
        conn.close()
        return order
    
    conn.close()
    return None


def get_order_items_with_names(order_id):
    """Получить товары заказа с названиями"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT oi.*, p.name as product_name 
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    """, (order_id,))
    
    items = []
    for row in cursor.fetchall():
        items.append({
            "id": row[0],
            "order_id": row[1],
            "product_id": row[2],
            "product_name": row[3],
            "quantity": row[4],
            "price": row[5]
        })
    
    conn.close()
    return items


def update_order_status(order_id, status=None, tracking_number=None):
    """Обновить статус заказа и/или трек-номер"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if status and tracking_number:
        cursor.execute("""
            UPDATE orders 
            SET status = ?, tracking_number = ? 
            WHERE id = ?
        """, (status, tracking_number, order_id))
    elif status:
        cursor.execute("""
            UPDATE orders 
            SET status = ? 
            WHERE id = ?
        """, (status, order_id))
    elif tracking_number:
        cursor.execute("""
            UPDATE orders 
            SET tracking_number = ? 
            WHERE id = ?
        """, (tracking_number, order_id))
    
    conn.commit()
    conn.close()


def get_office_cities():
    """Получить список городов, где есть офисы (из существующей таблицы)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT city FROM office_cities")
    cities = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return cities


def update_user(telegram_id, **kwargs):
    """Обновление данных пользователя (ФИО, телефон, город)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    # Разрешенные поля для обновления
    allowed_fields = ['fio', 'phone', 'city']
    
    for key, value in kwargs.items():
        if key in allowed_fields and value is not None:
            updates.append(f"{key} = ?")
            values.append(value)
    
    if not updates:
        conn.close()
        return False
    
    values.append(telegram_id)
    query = f"UPDATE users SET {', '.join(updates)} WHERE telegram_id = ?"
    
    try:
        cursor.execute(query, values)
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Ошибка update_user: {e}")
        return False
    finally:
        conn.close()    

# database.py - добавьте эти функции

def add_office_city(city):
    """Добавить город в список офисов"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO office_cities (city) VALUES (?)", (city,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка добавления города: {e}")
        return False
    finally:
        conn.close()



def remove_office_city(city):
    """Удалить город из списка офисов"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM office_cities WHERE city = ?", (city,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка удаления города: {e}")
        return False
    finally:
        conn.close()


def get_office_cities():
    """Получить список городов, где есть офисы"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT city FROM office_cities ORDER BY city")
    cities = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return cities        

# database.py - добавьте функцию для инициализации городов
def init_office_cities():
    """Инициализация списка городов (если таблица пуста)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Проверяем, есть ли города
    cursor.execute("SELECT COUNT(*) FROM office_cities")
    count = cursor.fetchone()[0]
    
    if count == 0:
        default_cities = [
            "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург",
            "Казань", "Нижний Новгород", "Красноярск", "Самара",
            "Ростов-на-Дону", "Уфа", "Краснодар", "Пермь", "Сочи", "Томск"
        ]
        
        for city in default_cities:
            cursor.execute("INSERT INTO office_cities (city) VALUES (?)", (city,))
        
        conn.commit()
        print(f"✅ Добавлено {len(default_cities)} городов в office_cities")
    
    conn.close()    

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
            last_message_at TIMESTAMP,
            admin_notified INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()    

# ==================== ИСТОРИИ КЛИЕНТОВ ====================
def get_all_stories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stories WHERE is_active = 1 ORDER BY created_at DESC")
    stories = cursor.fetchall()
    conn.close()
    return stories

def get_stories_by_product(product_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stories WHERE product_name = ? AND is_active = 1", (product_name,))
    stories = cursor.fetchall()
    conn.close()
    return stories

def add_story(title, content, product_name=None, category=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stories (title, content, product_name, category)
        VALUES (?, ?, ?, ?)
    """, (title, content, product_name, category))
    conn.commit()
    conn.close()

def update_story(story_id, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE stories SET {key} = ? WHERE id = ?", (value, story_id))
    conn.commit()
    conn.close()

def delete_story(story_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE stories SET is_active = 0 WHERE id = ?", (story_id,))
    conn.commit()
    conn.close()

# ==================== ПРОГРАММЫ ====================
def get_all_programs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM programs WHERE is_active = 1 ORDER BY created_at DESC")
    programs = cursor.fetchall()
    conn.close()
    return programs

def add_program(name, description, products):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO programs (name, description, products)
        VALUES (?, ?, ?)
    """, (name, description, products))
    conn.commit()
    conn.close()

def update_program(program_id, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE programs SET {key} = ? WHERE id = ?", (value, program_id))
    conn.commit()
    conn.close()

def delete_program(program_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE programs SET is_active = 0 WHERE id = ?", (program_id,))
    conn.commit()
    conn.close()    

# ==================== ИСТОРИИ ====================
def get_story_by_id(story_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
    story = cursor.fetchone()
    conn.close()
    return story

def get_all_stories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stories WHERE is_active = 1 ORDER BY created_at DESC")
    stories = cursor.fetchall()
    conn.close()
    return stories

def add_story(title, content, product_name=None, category=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO stories (title, content, product_name, category)
        VALUES (?, ?, ?, ?)
    """, (title, content, product_name, category))
    conn.commit()
    conn.close()

def update_story(story_id, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE stories SET {key} = ? WHERE id = ?", (value, story_id))
    conn.commit()
    conn.close()

def delete_story(story_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE stories SET is_active = 0 WHERE id = ?", (story_id,))
    conn.commit()
    conn.close()

# ==================== ПРОГРАММЫ ====================
def get_program_by_id(program_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM programs WHERE id = ?", (program_id,))
    program = cursor.fetchone()
    conn.close()
    return program

def get_all_programs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM programs WHERE is_active = 1 ORDER BY created_at DESC")
    programs = cursor.fetchall()
    conn.close()
    return programs

def add_program(name, description, products):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO programs (name, description, products)
        VALUES (?, ?, ?)
    """, (name, description, products))
    conn.commit()
    conn.close()

def update_program(program_id, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE programs SET {key} = ? WHERE id = ?", (value, program_id))
    conn.commit()
    conn.close()

def delete_program(program_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE programs SET is_active = 0 WHERE id = ?", (program_id,))
    conn.commit()
    conn.close()    

# ==================== СИМПТОМЫ ====================

def get_symptom_by_id(symptom_id):
    """Получить симптом по ID"""
    conn = get_connection()  # Исправлено: было get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, title, description, products FROM symptoms WHERE id = ? AND is_active = 1", (symptom_id,))
    symptom = cursor.fetchone()
    conn.close()
    return dict(symptom) if symptom else None

def get_all_symptoms_with_ids():
    """Получить все симптомы с ID"""
    conn = get_connection()  # Исправлено: было get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, title FROM symptoms WHERE is_active = 1 ORDER BY title")
    symptoms = cursor.fetchall()
    conn.close()
    return [dict(s) for s in symptoms]

def get_all_symptoms():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM symptoms WHERE is_active = 1 ORDER BY category, title")
    symptoms = cursor.fetchall()
    conn.close()
    return [dict(s) for s in symptoms]

def get_symptoms_by_category(category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM symptoms WHERE category = ? AND is_active = 1", (category,))
    symptoms = cursor.fetchall()
    conn.close()
    return symptoms

def get_symptom_by_name(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM symptoms WHERE name = ?", (name,))
    symptom = cursor.fetchone()
    conn.close()
    return symptom

def add_symptom(name, title, description, products, category):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO symptoms (name, title, description, products, category)
        VALUES (?, ?, ?, ?, ?)
    """, (name, title, description, products, category))
    conn.commit()
    conn.close()

def update_symptom(symptom_id, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in kwargs.items():
        if value is not None:
            cursor.execute(f"UPDATE symptoms SET {key} = ? WHERE id = ?", (value, symptom_id))
    conn.commit()
    conn.close()

def delete_symptom(symptom_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE symptoms SET is_active = 0 WHERE id = ?", (symptom_id,))
    conn.commit()
    conn.close()

def get_product_by_id(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

def update_product_in_db(product_id, **kwargs):
    conn = get_connection()
    cursor = conn.cursor()
    for key, value in kwargs.items():
        if value is not None:
            cursor.execute(f"UPDATE products SET {key} = ? WHERE id = ?", (value, product_id))
    conn.commit()
    conn.close()    

def get_users_without_sponsor():
    """Получить пользователей, у которых нет спонсора (кроме админов)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users 
        WHERE (sponsor_id IS NULL OR sponsor_id = 0)
        AND telegram_id NOT IN (SELECT telegram_id FROM admins)
        ORDER BY created_at DESC
    """)
    users = cursor.fetchall()
    conn.close()
    return users 

  

def update_consult_request_status(consult_id, status):
    """Обновить статус консультации в consultations.db"""
    import sqlite3
    conn = sqlite3.connect("consultations.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE consult_requests SET status = ? WHERE id = ?", (status, consult_id))
    conn.commit()
    conn.close()    

def get_full_referral_tree(sponsor_id, level=0, max_level=5):
    """Рекурсивно получает дерево рефералов"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT telegram_id, fio, phone, status, created_at
        FROM users 
        WHERE sponsor_id = ?
        ORDER BY created_at DESC
    """, (sponsor_id,))
    
    referrals = cursor.fetchall()
    conn.close()
    
    tree = []
    for ref in referrals:
        node = {
            "id": ref["telegram_id"],
            "fio": ref["fio"],
            "phone": ref["phone"],
            "status": ref["status"],
            "level": level,
            "children": []
        }
        if level < max_level:
            node["children"] = get_full_referral_tree(ref["telegram_id"], level + 1, max_level)
        tree.append(node)
    
    return tree


# В database.py, найдите и замените функцию format_referral_tree

def format_referral_tree(tree, prefix="", is_last=True):
    """Форматирует дерево рефералов в текст с цветовым кодированием"""
    text = ""
    for i, node in enumerate(tree):
        is_last_child = (i == len(tree) - 1)
        
        # Выбор символов для веток
        if prefix:
            if is_last_child:
                text += prefix + "└── "
            else:
                text += prefix + "├── "
        else:
            if is_last_child:
                text += "└── "
            else:
                text += "├── "
        
        # Проверяем, зарегистрирован ли пользователь
        if not node.get("registered", True):
            # Незарегистрированный пользователь
            text += f"⏳ **{node['fio']}**\n"
            text += prefix + ("    " if is_last_child else "│   ") + f"   🆔 {node['id']}\n"
            text += prefix + ("    " if is_last_child else "│   ") + "   ⚠️ *Ожидает регистрации*\n"
        else:
            # Зарегистрированный пользователь
            style = get_status_style(node["status"])
            text += f"{style['emoji']} **{node['fio']}**\n"
            text += prefix + ("    " if is_last_child else "│   ") + f"   🆔 {node['id']}\n"
            
            if node.get("phone"):
                text += prefix + ("    " if is_last_child else "│   ") + f"   📞 {node['phone']}\n"
        
        # Рекурсивно обрабатываем детей
        if node.get("children"):
            new_prefix = prefix + ("    " if is_last_child else "│   ")
            text += format_referral_tree(node["children"], new_prefix, is_last_child)
    
    return text


def get_status_style(status):
    """Возвращает цвет и эмодзи для статуса"""
    styles = {
        "new": {"color": "⚫", "name": "Новый", "emoji": "🆕"},
        "work": {"color": "🟡", "name": "В работе", "emoji": "🟡"},
        "client": {"color": "🟢", "name": "Клиент", "emoji": "🟢"},
        "partner": {"color": "🔵", "name": "Партнёр", "emoji": "💎"},
        "failed": {"color": "🔴", "name": "Не отвечает", "emoji": "🔴"},
        "unregistered": {"color": "⏳", "name": "Ожидает регистрации", "emoji": "⏳"} 
    }
    return styles.get(status, {"color": "⚪", "name": "Неизвестно", "emoji": "⚪"})    

# ==================== ВРЕМЕННЫЕ РЕФЕРАЛЬНЫЕ СВЯЗИ ====================

def save_temp_sponsor(telegram_id: int, sponsor_id: int):
    """Сохраняет временную реферальную связь"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO temp_refs (telegram_id, sponsor_id)
        VALUES (?, ?)
    """, (telegram_id, sponsor_id))
    
    conn.commit()
    conn.close()
    print(f"🔵🔵🔵 СОХРАНЁН ВРЕМЕННЫЙ СПОНСОР: {telegram_id} -> {sponsor_id}")


def get_temp_sponsor(telegram_id: int):
    """Получает временного спонсора, если есть"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT sponsor_id FROM temp_refs WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    
    conn.close()
    
    if row:
        print(f"🔵🔵🔵 НАЙДЕН ВРЕМЕННЫЙ СПОНСОР: {telegram_id} -> {row[0]}")
        return row[0]
    
    print(f"🔵🔵🔵 НЕТ ВРЕМЕННОГО СПОНСОРА ДЛЯ: {telegram_id}")
    return None


def clear_temp_sponsor(telegram_id: int):
    """Удаляет временную связь после регистрации"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM temp_refs WHERE telegram_id = ?", (telegram_id,))
    
    conn.commit()
    conn.close()
    print(f"🔵🔵🔵 УДАЛЁН ВРЕМЕННЫЙ СПОНСОР ДЛЯ: {telegram_id}")    


def get_temp_refs_count(sponsor_id: int):
    """Получить количество переходов по ссылке (из temp_refs)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) FROM temp_refs
        WHERE sponsor_id = ?
    """, (sponsor_id,))
    
    count = cursor.fetchone()[0]
    conn.close()
    return count


def get_temp_refs_users(sponsor_id: int):
    """Получить список пользователей, перешедших по ссылке (из temp_refs)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT tr.telegram_id, tr.created_at, u.fio
        FROM temp_refs tr
        LEFT JOIN users u ON tr.telegram_id = u.telegram_id
        WHERE tr.sponsor_id = ?
        ORDER BY tr.created_at DESC
    """, (sponsor_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        result.append({
            "telegram_id": row["telegram_id"],
            "created_at": row["created_at"],
            "fio": row["fio"],
            "registered": row["fio"] is not None
        })
    
    return result

def get_full_referral_tree(sponsor_id, level=0, max_level=5):
    """Рекурсивно получает дерево рефералов, включая незарегистрированных из temp_refs"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем зарегистрированных пользователей (у кого sponsor_id = sponsor_id)
    cursor.execute("""
        SELECT telegram_id, fio, phone, status, created_at
        FROM users 
        WHERE sponsor_id = ?
        ORDER BY created_at DESC
    """, (sponsor_id,))
    
    referrals = cursor.fetchall()
    
    # Получаем НЕзарегистрированных из temp_refs
    # (у кого есть запись в temp_refs, но нет в users)
    cursor.execute("""
        SELECT tr.telegram_id, tr.created_at
        FROM temp_refs tr
        LEFT JOIN users u ON tr.telegram_id = u.telegram_id
        WHERE tr.sponsor_id = ?
        AND u.telegram_id IS NULL
        ORDER BY tr.created_at DESC
    """, (sponsor_id,))
    
    unregistered = cursor.fetchall()
    conn.close()
    
    tree = []
    
    # Добавляем зарегистрированных
    for ref in referrals:
        node = {
            "id": ref["telegram_id"],
            "fio": ref["fio"],
            "phone": ref["phone"],
            "status": ref["status"],
            "registered": True,
            "level": level,
            "children": []
        }
        if level < max_level:
            node["children"] = get_full_referral_tree(ref["telegram_id"], level + 1, max_level)
        tree.append(node)
    
    # Добавляем НЕзарегистрированных
    for ref in unregistered:
        node = {
            "id": ref["telegram_id"],
            "fio": f"❌ Не зарегистрирован",
            "phone": None,
            "status": "unregistered",
            "registered": False,
            "level": level,
            "children": []
        }
        tree.append(node)
    
    return tree

def get_unprocessed_orders():
    """Получить все необработанные заказы с полной информацией"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            o.id,
            o.user_id,
            o.full_name,
            o.phone,
            o.city,
            o.total_amount,
            o.status,
            o.created_at,
            o.delivery_method,
            o.pickup_point,
            u.fio as client_fio,
            u.sponsor_id,
            s.fio as sponsor_fio,
            s.telegram_id as sponsor_telegram_id,
            -- Вычисляем разницу в минутах (все в UTC)
            (strftime('%s', 'now') - strftime('%s', o.created_at)) / 60 as waiting_minutes
        FROM orders o
        LEFT JOIN users u ON o.user_id = u.telegram_id
        LEFT JOIN users s ON u.sponsor_id = s.telegram_id
        WHERE o.status IN ('new', 'processing')
        ORDER BY o.created_at ASC
    """)
    
    orders = cursor.fetchall()
    conn.close()
    
    result = []
    for order in orders:
        # Получаем товары в заказе
        conn2 = get_connection()
        cursor2 = conn2.cursor()
        cursor2.execute("""
            SELECT product_name, quantity, price 
            FROM order_items 
            WHERE order_id = ?
        """, (order[0],))
        items = cursor2.fetchall()
        conn2.close()
        
        # order[0]=id, [1]=user_id, [2]=full_name, [3]=phone, [4]=city,
        # [5]=total_amount, [6]=status, [7]=created_at, [8]=delivery_method,
        # [9]=pickup_point, [10]=client_fio, [11]=sponsor_id, [12]=sponsor_fio,
        # [13]=sponsor_telegram_id
        
        client_name = order[10] or order[2] or "Клиент"
        
        # Определяем способ доставки текстом
        delivery_method = order[8] or "Не указан"
        if delivery_method == "pickup":
            delivery_text = f"🏢 Самовывоз ({order[9] or 'не указан'})"
        elif delivery_method == "courier":
            delivery_text = "🚚 Доставка курьером"
        elif delivery_method == "cdek":
            delivery_text = "📦 Доставка СДЭК"
        else:
            delivery_text = delivery_method
        
        result.append({
            'id': order[0],
            'user_id': order[1],
            'full_name': order[2] or client_name,
            'phone': order[3],
            'city': order[4],
            'total_amount': order[5],
            'status': order[6],
            'created_at': order[7],
            'delivery_method': order[8],
            'delivery_text': delivery_text,
            'pickup_point': order[9],
            'client_name': client_name,
            'sponsor_id': order[11],
            'sponsor_fio': order[12] or "Нет наставника",
            'sponsor_telegram_id': order[13],
            'items': [{'name': item[0], 'quantity': item[1], 'price': item[2]} for item in items]
        })
    
    return result


def mark_order_as_processed(order_id):
    """Отметить заказ как обработанный (изменить статус на 'completed')"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'completed' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()


from datetime import datetime, timezone

def get_order_waiting_time(order_id):
    """Получить время ожидания заказа (UTC)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT created_at FROM orders WHERE id = ?", (order_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return "неизвестно"
    
    created_at_str = result[0]
    
    try:
        created_at = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
        # Заменяем наивную дату на UTC
        created_at = created_at.replace(tzinfo=timezone.utc)
    except:
        return "неизвестно"
    
    # Текущее время в UTC
    now_utc = datetime.now(timezone.utc)
    
    delta = now_utc - created_at
    
    if delta.total_seconds() < 0:
        return "только что"
    if delta.total_seconds() < 60:
        return "только что"
    
    hours = delta.total_seconds() // 3600
    minutes = (delta.total_seconds() % 3600) // 60
    
    if hours > 0:
        return f"{int(hours)}ч {int(minutes)}мин"
    else:
        return f"{int(minutes)}мин"

def get_all_products_from_db():
    """Получить все товары с сортировкой по sort_order"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM products 
        WHERE is_active = 1 
        ORDER BY sort_order ASC
    """)
    products = cursor.fetchall()
    conn.close()
    return [dict(p) for p in products] 