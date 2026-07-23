from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter, Command
from consult_bot import update_consult_status

from database import (
    is_admin, 
    get_all_users, 
    get_system_stats,
    get_old_consultations,
    get_all_partners,
    get_user,
    update_sponsor,
    get_office_cities,
    sync_products_from_file,
    get_all_products_from_db,
    get_product_by_id,
    get_product_price,
    set_product_price,
    update_product_in_db,
    delete_product_from_db,
    add_new_product,
    # Добавляем для историй и программ
    get_story_by_id,
    get_all_stories,
    add_story,
    update_story,
    delete_story,
    get_program_by_id,
    get_all_programs,
    add_program,
    update_program,
    delete_program
)
from keyboards import admin_menu
from states import Broadcast

router = Router()

print("🔴🔴🔴 admin.py ЗАГРУЖЕН 🔴🔴🔴")


@router.message(F.text.in_([
    "👑 Админка", "📊 Статистика системы", "⚠️ Жалобы", "⏰ Клиенты без ответа",
    "👥 Все партнеры", "📢 Сообщение всем", "🔄 Сменить спонсора",
    "🛍 Управление товарами", "🏢 Города офисов"
]))
async def admin_commands_handler(message: Message, state: FSMContext):
    print(f"🔵🔵🔵 АДМИНКА ПЕРЕХВАТИЛА: {message.text}")
    
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    if message.text == "👑 Админка":
        await message.answer("👑 Панель администратора", reply_markup=admin_menu)
    
    elif message.text == "📊 Статистика системы":
        stats = get_system_stats()
        await message.answer(
            f"📊 Система\n\n👥 Пользователей: {stats['users']}\n📅 Консультаций: {stats['consultations']}"
        )
       
    elif message.text == "⏰ Клиенты без ответа":
        consultations = get_old_consultations()
        if not consultations:
            await message.answer("Все заявки обработаны ✅")
            return
        text = "⚠️ Необработанные заявки\n\n"
        for consult in consultations:
            text += f"#{consult['id']}\n{consult['phone']}\n{consult['topic']}\n\n"
        await message.answer(text)
    
    elif message.text == "📢 Сообщение всем":
        await state.set_state(Broadcast.waiting_message)
        await message.answer(
            "Отправьте сообщение для рассылки.\n\n"
            "Можно отправить:\n• текст\n• фото\n• видео\n• документ"
        )
    
    elif message.text == "🔄 Сменить спонсора":
        await state.set_state("waiting_user_id")
        await message.answer("Введите Telegram ID пользователя, которому нужно сменить спонсора:")
    
    elif message.text == "🛍 Управление товарами":
        products = get_all_products_from_db()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Синхронизировать из файла", callback_data="sync_products")],
            [InlineKeyboardButton(text="📋 Список товаров", callback_data="list_products")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
        ])
        await message.answer(
            "🛍 **Управление товарами**\n\nВыберите действие:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    
    elif message.text == "🏢 Города офисов":
        cities = get_office_cities()
        cities_text = "\n".join([f"• {city}" for city in cities]) if cities else "Список пуст"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
            [InlineKeyboardButton(text="🗑 Удалить город", callback_data="remove_city")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
        ])
        await message.answer(
            f"🏙️ **Города с офисами**\n\n{cities_text}\n\nВсего: {len(cities)}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


@router.message(Broadcast.waiting_message)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    users = get_all_users()
    success = 0
    failed = 0

    for user in users:
        telegram_id = user["telegram_id"]
        try:
            await bot.copy_message(
                chat_id=telegram_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )
            success += 1
        except Exception:
            failed += 1

    await message.answer(f"📢 Рассылка завершена\n\n✅ Отправлено: {success}\n❌ Ошибок: {failed}")
    await state.clear()


@router.message(StateFilter("waiting_user_id"))
async def change_sponsor_get_user(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный Telegram ID (только цифры)")
        return
    
    user = get_user(user_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID {user_id} не найден")
        await state.clear()
        return
    
    await state.update_data(target_user_id=user_id)
    await message.answer(f"👤 Пользователь: {user['fio']}\n\nВведите Telegram ID нового спонсора:")
    await state.set_state("waiting_sponsor_id")


@router.message(StateFilter("waiting_sponsor_id"))
async def change_sponsor_set(message: Message, state: FSMContext):
    try:
        sponsor_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный Telegram ID (только цифры)")
        return
    
    data = await state.get_data()
    user_id = data.get("target_user_id")
    
    sponsor = get_user(sponsor_id)
    if not sponsor:
        await message.answer(f"❌ Спонсор с ID {sponsor_id} не найден")
        return
    
    update_sponsor(user_id, sponsor_id)
    await message.answer(f"✅ Спонсор для пользователя {user_id} изменён на {sponsor['fio']}")
    await state.clear()


@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("👑 Панель администратора", reply_markup=admin_menu)
    await callback.answer()


@router.callback_query(F.data == "sync_products")
async def sync_products_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    sync_products_from_file()
    await callback.message.answer("✅ Товары синхронизированы из файла в БД!")
    await callback.answer()


@router.callback_query(F.data == "list_products")
async def list_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    products = get_all_products_from_db()
    if not products:
        await callback.message.answer("📭 Товаров пока нет.")
        return
    
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(text=f"✏️ {product['name']}", callback_data=f"edit_product_{product['id']}")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")])
    
    await callback.message.edit_text(
        "📋 **Список товаров**\n\nВыберите товар для редактирования:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

# ==================== УПРАВЛЕНИЕ ИСТОРИЯМИ ====================

@router.message(F.text == "📖 Управление историями")
async def manage_stories(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить историю", callback_data="add_story")],
        [InlineKeyboardButton(text="📋 Список историй", callback_data="list_stories")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
    ])
    
    await message.answer(
        "📖 **Управление историями клиентов**\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "add_story")
async def add_story_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("add_story_title")
    await callback.message.answer("✏️ Введите заголовок истории:")
    await callback.answer()


@router.message(StateFilter("add_story_title"))
async def add_story_title(message: Message, state: FSMContext):
    await state.update_data(story_title=message.text)
    await state.set_state("add_story_content")
    await message.answer("📄 Введите текст истории:")


@router.message(StateFilter("add_story_content"))
async def add_story_content(message: Message, state: FSMContext):
    await state.update_data(story_content=message.text)
    await state.set_state("add_story_product")
    await message.answer("📦 Введите название товара (или отправьте 'пропустить'):")


@router.message(StateFilter("add_story_product"))
async def add_story_product(message: Message, state: FSMContext):
    product_name = None if message.text.lower() == "пропустить" else message.text
    await state.update_data(story_product=product_name)
    
    data = await state.get_data()
    
    from database import add_story
    add_story(
        title=data["story_title"],
        content=data["story_content"],
        product_name=data["story_product"]
    )
    
    await message.answer("✅ История добавлена!")
    await state.clear()
    
    await manage_stories(message)


@router.callback_query(F.data == "list_stories")
async def list_stories(callback: CallbackQuery):
    from database import get_all_stories
    stories = get_all_stories()
    
    if not stories:
        await callback.message.answer("📭 Историй пока нет.")
        await callback.answer()
        return
    
    keyboard = []
    for story in stories:
        keyboard.append([InlineKeyboardButton(
            text=f"✏️ {story['title'][:30]}", 
            callback_data=f"edit_story_{story['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_stories")])
    
    await callback.message.edit_text(
        "📋 **Список историй**\n\nВыберите историю для редактирования:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_story_"))
async def edit_story_form(callback: CallbackQuery, state: FSMContext):
    story_id = int(callback.data.split("_")[2])
    await state.update_data(edit_story_id=story_id)
    
    from database import get_story_by_id
    story = get_story_by_id(story_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить заголовок", callback_data="edit_story_title")],
        [InlineKeyboardButton(text="📄 Изменить текст", callback_data="edit_story_content")],
        [InlineKeyboardButton(text="📦 Изменить товар", callback_data="edit_story_product")],
        [InlineKeyboardButton(text="🗑 Удалить историю", callback_data="delete_story")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="list_stories")]
    ])
    
    text = f"**{story['title']}**\n\n{story['content'][:200]}...\n\n📦 Товар: {story['product_name'] or 'не указан'}"
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "edit_story_title")
async def edit_story_title_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("edit_story_title")
    await callback.message.answer("✏️ Введите новый заголовок:")
    await callback.answer()


@router.message(StateFilter("edit_story_title"))
async def edit_story_title_save(message: Message, state: FSMContext):
    data = await state.get_data()
    story_id = data.get("edit_story_id")
    
    from database import update_story
    update_story(story_id, title=message.text)
    
    await message.answer("✅ Заголовок обновлён!")
    await state.clear()
    
    from types import SimpleNamespace
    fake_callback = SimpleNamespace(
        message=message,
        data=f"edit_story_{story_id}",
        from_user=message.from_user,
        answer=lambda: None
    )
    await edit_story_form(fake_callback, state)


@router.callback_query(F.data == "edit_story_content")
async def edit_story_content_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("edit_story_content")
    await callback.message.answer("✏️ Введите новый текст истории:")
    await callback.answer()


@router.message(StateFilter("edit_story_content"))
async def edit_story_content_save(message: Message, state: FSMContext):
    data = await state.get_data()
    story_id = data.get("edit_story_id")
    
    from database import update_story
    update_story(story_id, content=message.text)
    
    await message.answer("✅ Текст истории обновлён!")
    await state.clear()
    
    from types import SimpleNamespace
    fake_callback = SimpleNamespace(
        message=message,
        data=f"edit_story_{story_id}",
        from_user=message.from_user,
        answer=lambda: None
    )
    await edit_story_form(fake_callback, state)


@router.callback_query(F.data == "edit_story_product")
async def edit_story_product_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("edit_story_product")
    await callback.message.answer("📦 Введите название товара (или 'пропустить'):")
    await callback.answer()


@router.message(StateFilter("edit_story_product"))
async def edit_story_product_save(message: Message, state: FSMContext):
    product_name = None if message.text.lower() == "пропустить" else message.text
    
    data = await state.get_data()
    story_id = data.get("edit_story_id")
    
    from database import update_story
    update_story(story_id, product_name=product_name)
    
    await message.answer("✅ Товар обновлён!")
    await state.clear()
    
    from types import SimpleNamespace
    fake_callback = SimpleNamespace(
        message=message,
        data=f"edit_story_{story_id}",
        from_user=message.from_user,
        answer=lambda: None
    )
    await edit_story_form(fake_callback, state)


@router.callback_query(F.data == "delete_story")
async def delete_story(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    story_id = data.get("edit_story_id")
    
    from database import delete_story
    delete_story(story_id)
    
    await callback.message.answer("✅ История удалена!")
    await state.clear()
    await callback.answer()
    
    await list_stories(callback)


@router.callback_query(F.data == "back_to_stories")
async def back_to_stories(callback: CallbackQuery):
    await manage_stories(callback.message)
    await callback.answer()


# ==================== УПРАВЛЕНИЕ ПРОГРАММАМИ ====================

@router.message(F.text == "🎁 Управление программами")
async def manage_programs(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить программу", callback_data="add_program")],
        [InlineKeyboardButton(text="📋 Список программ", callback_data="list_programs")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
    ])
    
    await message.answer(
        "🎁 **Управление программами**\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "add_program")
async def add_program_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("add_program_name")
    await callback.message.answer("✏️ Введите название программы:")
    await callback.answer()


@router.message(StateFilter("add_program_name"))
async def add_program_name(message: Message, state: FSMContext):
    await state.update_data(program_name=message.text)
    await state.set_state("add_program_description")
    await message.answer("📄 Введите описание программы:")


@router.message(StateFilter("add_program_description"))
async def add_program_description(message: Message, state: FSMContext):
    await state.update_data(program_description=message.text)
    await state.set_state("add_program_products")
    await message.answer("📦 Введите список товаров через запятую:")


@router.message(StateFilter("add_program_products"))
async def add_program_products(message: Message, state: FSMContext):
    data = await state.get_data()
    
    from database import add_program
    add_program(
        name=data["program_name"],
        description=data["program_description"],
        products=message.text
    )
    
    await message.answer("✅ Программа добавлена!")
    await state.clear()
    
    await manage_programs(message)


@router.callback_query(F.data == "list_programs")
async def list_programs(callback: CallbackQuery):
    from database import get_all_programs
    programs = get_all_programs()
    
    if not programs:
        await callback.message.answer("📭 Программ пока нет.")
        await callback.answer()
        return
    
    keyboard = []
    for program in programs:
        keyboard.append([InlineKeyboardButton(
            text=f"✏️ {program['name'][:30]}", 
            callback_data=f"edit_program_{program['id']}"
        )])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_programs")])
    
    await callback.message.edit_text(
        "🎁 **Список программ**\n\nВыберите программу для редактирования:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_program_"))
async def edit_program_form(callback: CallbackQuery, state: FSMContext):
    program_id = int(callback.data.split("_")[2])
    await state.update_data(edit_program_id=program_id)
    
    from database import get_program_by_id
    program = get_program_by_id(program_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="edit_program_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="edit_program_description")],
        [InlineKeyboardButton(text="📦 Изменить товары", callback_data="edit_program_products")],
        [InlineKeyboardButton(text="🗑 Удалить программу", callback_data="delete_program")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="list_programs")]
    ])
    
    text = f"**{program['name']}**\n\n{program['description'][:200]}...\n\n📦 Товары: {program['products']}"
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "edit_program_name")
async def edit_program_name_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("edit_program_name")
    await callback.message.answer("✏️ Введите новое название:")
    await callback.answer()


@router.message(StateFilter("edit_program_name"))
async def edit_program_name_save(message: Message, state: FSMContext):
    data = await state.get_data()
    program_id = data.get("edit_program_id")
    
    from database import update_program
    update_program(program_id, name=message.text)
    
    await message.answer("✅ Название обновлено!")
    await state.clear()
    
    from types import SimpleNamespace
    fake_callback = SimpleNamespace(
        message=message,
        data=f"edit_program_{program_id}",
        from_user=message.from_user,
        answer=lambda: None
    )
    await edit_program_form(fake_callback, state)


@router.callback_query(F.data == "edit_program_description")
async def edit_program_description_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("edit_program_description")
    await callback.message.answer("✏️ Введите новое описание:")
    await callback.answer()


@router.message(StateFilter("edit_program_description"))
async def edit_program_description_save(message: Message, state: FSMContext):
    data = await state.get_data()
    program_id = data.get("edit_program_id")
    
    from database import update_program
    update_program(program_id, description=message.text)
    
    await message.answer("✅ Описание обновлено!")
    await state.clear()
    
    from types import SimpleNamespace
    fake_callback = SimpleNamespace(
        message=message,
        data=f"edit_program_{program_id}",
        from_user=message.from_user,
        answer=lambda: None
    )
    await edit_program_form(fake_callback, state)


@router.callback_query(F.data == "edit_program_products")
async def edit_program_products_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state("edit_program_products")
    await callback.message.answer("📦 Введите список товаров через запятую:")
    await callback.answer()


@router.message(StateFilter("edit_program_products"))
async def edit_program_products_save(message: Message, state: FSMContext):
    data = await state.get_data()
    program_id = data.get("edit_program_id")
    
    from database import update_program
    update_program(program_id, products=message.text)
    
    await message.answer("✅ Список товаров обновлён!")
    await state.clear()
    
    from types import SimpleNamespace
    fake_callback = SimpleNamespace(
        message=message,
        data=f"edit_program_{program_id}",
        from_user=message.from_user,
        answer=lambda: None
    )
    await edit_program_form(fake_callback, state)


@router.callback_query(F.data == "delete_program")
async def delete_program(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    program_id = data.get("edit_program_id")
    
    from database import delete_program
    delete_program(program_id)
    
    await callback.message.answer("✅ Программа удалена!")
    await state.clear()
    await callback.answer()
    
    await list_programs(callback)


@router.callback_query(F.data == "back_to_programs")
async def back_to_programs(callback: CallbackQuery):
    await manage_programs(callback.message)
    await callback.answer()    

 

@router.callback_query(lambda c: c.data.startswith("admin_reply_complaint_"))
async def admin_reply_complaint(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    consult_id = int(parts[3])
    user_id = int(parts[4])
    
    await state.update_data(
        reply_complaint_consult_id=consult_id,
        reply_complaint_user_id=user_id
    )
    await state.set_state("admin_waiting_complaint_reply")
    
    await callback.message.answer("✏️ Введите ответ для пользователя (по жалобе):")
    await callback.answer()


@router.message(StateFilter("admin_waiting_complaint_reply"))
async def admin_send_complaint_reply(message: Message, state: FSMContext):
    from database import add_event
    from consult_bot import update_consult_status
    
    data = await state.get_data()
    consult_id = data.get("reply_complaint_consult_id")
    user_id = data.get("reply_complaint_user_id")
    
    if not user_id:
        await message.answer("❌ Ошибка: пользователь не найден")
        await state.clear()
        return
    
    # Отправляем ответ пользователю (через основного бота)
    await message.bot.send_message(
        user_id,
        f"📩 **Ответ администратора по жалобе:**\n\n{message.text}\n\n"
        f"Извините за неудобства. Если у вас остались вопросы, "
        f"вы можете снова обратиться к наставнику."
    )
    
    # Обновляем статус консультации в базе консультаций
    try:
        update_consult_status(consult_id, "resolved")
    except:
        pass
    
    add_event(user_id, "complaint", f"Администратор ответил на жалобу по консультации #{consult_id}")
    
    await message.answer("✅ Ответ отправлен пользователю!")
    await state.clear()    

@router.message(F.text == "👥 Все партнеры")
async def all_partners(message: Message):
    if not is_admin(message.from_user.id):
        return

    from database import get_all_partners, get_diagnostic_history

    partners = get_all_partners()
    print(f"🔍 Найдено партнёров (админ): {len(partners)}")

    if not partners:
        await message.answer("Нет партнёров в системе")
        return

    # Разделяем на две группы
    partners_with_diag = []
    partners_without_diag = []

    for partner in partners:
        history = get_diagnostic_history(partner['telegram_id'])
        
        print(f"🔍 Партнёр {partner['fio']} (ID {partner['telegram_id']}) — диагностика: {len(history)} записей")
        if len(history) > 0:
            partners_with_diag.append(partner)
        else:
            partners_without_diag.append(partner)

    # Формируем клавиатуру: сначала с диагностикой, потом без
    keyboard = []

    for partner in partners_with_diag:
        display_text = f"🧬 {partner['fio']} (ID: {partner['telegram_id']})"
        keyboard.append([InlineKeyboardButton(
            text=display_text,
            callback_data=f"show_tree_{partner['telegram_id']}"
        )])

    for partner in partners_without_diag:
        display_text = f"{partner['fio']} (ID: {partner['telegram_id']})"
        keyboard.append([InlineKeyboardButton(
            text=display_text,
            callback_data=f"show_tree_{partner['telegram_id']}"
        )])

    await message.answer(
        "🌳 **Выберите партнёра для просмотра реферального дерева:**\n\n"
        ,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data.startswith("show_tree_"))
async def show_partner_tree(callback: CallbackQuery, state: FSMContext):
    partner_id = int(callback.data.split("_")[2])
    
    from database import get_user, get_full_referral_tree, get_status_style, get_connection

    partner = get_user(partner_id)
    if not partner:
        await callback.message.answer("❌ Партнёр не найден")
        await callback.answer()
        return

    tree = get_full_referral_tree(partner_id, level=1, max_level=5)

    # ---- Рекурсивно извлекаем незарегистрированных ----
    unregistered_nodes = []
    
    def extract_unregistered(nodes):
        for node in nodes:
            if not node.get('registered', True):
                unregistered_nodes.append(node)
            if node.get('children'):
                extract_unregistered(node['children'])
    
    extract_unregistered(tree)

    # ---- Фильтруем дерево, оставляя только зарегистрированных ----
    def filter_registered(nodes):
        filtered = []
        for node in nodes:
            if node.get('registered', True):
                new_node = node.copy()
                if node.get('children'):
                    new_node['children'] = filter_registered(node['children'])
                filtered.append(new_node)
        return filtered
    
    filtered_tree = filter_registered(tree)

    # 🔧 ВРУЧНУЮ добавляем информацию о диагностике для каждого узла (для отфильтрованного дерева)
    def enrich_with_diagnostic(nodes):
        conn = get_connection()
        cursor = conn.cursor()
        for node in nodes:
            cursor.execute("SELECT COUNT(*) FROM diagnostic_results WHERE user_id = ?", (node["id"],))
            count = cursor.fetchone()[0]
            node["has_diagnostic"] = count > 0
            if node.get("children"):
                enrich_with_diagnostic(node["children"])
        conn.close()

    if filtered_tree:
        enrich_with_diagnostic(filtered_tree)

    # Функция форматирования дерева
    def format_tree(nodes, prefix="", is_last=True):
        text = ""
        for i, node in enumerate(nodes):
            is_last_child = (i == len(nodes) - 1)
            if prefix:
                text += prefix + ("└── " if is_last_child else "├── ")
            else:
                text += "└── " if is_last_child else "├── "

            diag_icon = "🧬 " if node.get("has_diagnostic", False) else ""

            if not node.get("registered", True):
                text += f"{diag_icon}⏳ **{node['fio']}**\n"
                text += prefix + ("    " if is_last_child else "│   ") + f"   🆔 {node['id']}\n"
                text += prefix + ("    " if is_last_child else "│   ") + "   ⚠️ *Ожидает регистрации*\n"
            else:
                style = get_status_style(node["status"])
                text += f"{diag_icon}{style['emoji']} **{node['fio']}**\n"
                text += prefix + ("    " if is_last_child else "│   ") + f"   🆔 {node['id']}\n"
                if node.get("phone"):
                    text += prefix + ("    " if is_last_child else "│   ") + f"   📞 {node['phone']}\n"

            if node.get("children"):
                new_prefix = prefix + ("    " if is_last_child else "│   ")
                text += format_tree(node["children"], new_prefix, is_last_child)
        return text

    # Легенда
    legend = (
        "📊 **Легенда статусов:**\n"
        "🆕 - Новый (зарегистрировался)\n"
        "🟡 - В работе\n"
        "🟢 - Клиент\n"
        "💎 - Партнёр\n"
        "🔴 - Не отвечает\n"
        "⏳ - Ожидает регистрации (перешёл по ссылке)\n"
        "🧬 - Прошёл диагностику\n\n"
    )

    if not filtered_tree and not unregistered_nodes:
        await callback.message.answer(
            legend + f"👤 **{partner['fio']}** (ID: {partner_id})\n\nНет приглашённых пользователей.",
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    text = legend + f"🌳 **Реферальное дерево**\n\n"
    text += f"👑 **{partner['fio']}** (ID: {partner_id})\n\n"

    if filtered_tree:
        text += format_tree(filtered_tree, "", False)
    else:
        text += "Нет зарегистрированных приглашённых.\n"

    # Сохраняем список незарегистрированных в state
    await state.update_data(unregistered_list=unregistered_nodes)

    # Если есть незарегистрированные, добавляем счётчик и кнопку
    if unregistered_nodes:
        text += f"\n\n📌 **Незарегистрированных: {len(unregistered_nodes)}**"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 Показать незарегистрированных", callback_data=f"show_unreg_{partner_id}")]
        ])
    else:
        keyboard = None

    if len(text) > 4000:
        parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await callback.message.edit_text(part, reply_markup=keyboard, parse_mode="Markdown")
            else:
                await callback.message.answer(part, parse_mode="Markdown")
    else:
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")

    await callback.answer()
    
@router.callback_query(lambda c: c.data.startswith("show_unreg_"))
async def show_unregistered_list(callback: CallbackQuery, state: FSMContext):
    partner_id = int(callback.data.split("_")[2])
    
    # Заново получаем дерево для этого партнёра
    from database import get_full_referral_tree
    tree = get_full_referral_tree(partner_id, level=1, max_level=5)
    
    # Рекурсивно извлекаем незарегистрированных
    unregistered = []
    def extract_unregistered(nodes):
        for node in nodes:
            if not node.get('registered', True):
                unregistered.append(node)
            if node.get('children'):
                extract_unregistered(node['children'])
    extract_unregistered(tree)
    
    if not unregistered:
        await callback.message.answer("Нет незарегистрированных пользователей.")
        await callback.answer()
        return
    
    text = f"📋 **Незарегистрированные (приглашённые пользователем {partner_id})**\n\n"
    for i, node in enumerate(unregistered, 1):
        text += f"{i}. 🆔 {node['id']} (перешёл по ссылке, но не зарегистрировался)\n"
    text += f"\nВсего: {len(unregistered)} человек."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к дереву", callback_data=f"show_tree_{partner_id}")]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()  

@router.callback_query(F.data == "admin_reorder_products")
async def admin_reorder_products(callback: CallbackQuery):
    """Показывает кнопки для изменения порядка товаров"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    products = get_all_products_from_db()
    
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"⬆️ {product['name']}",
                callback_data=f"product_up_{product['id']}"
            ),
            InlineKeyboardButton(
                text=f"⬇️",
                callback_data=f"product_down_{product['id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_products")])
    
    await callback.message.edit_text(
        "📊 **Управление порядком товаров**\n\n"
        "⬆️ - поднять выше\n"
        "⬇️ - опустить ниже\n\n"
        "Товары отображаются сверху вниз:",
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
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем текущий порядок
    cursor.execute("SELECT sort_order FROM products WHERE id = ?", (product_id,))
    current = cursor.fetchone()
    
    if current and current[0] > 0:
        # Меняем местами с предыдущим
        new_order = current[0] - 1
        cursor.execute("UPDATE products SET sort_order = ? WHERE id = ?", (new_order, product_id))
        conn.commit()
    
    conn.close()
    
    await admin_reorder_products(callback)
    await callback.answer("✅ Порядок обновлён")


@router.callback_query(F.data.startswith("product_down_"))
async def product_down(callback: CallbackQuery):
    """Опустить товар ниже"""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    product_id = int(callback.data.split("_")[2])
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Получаем текущий порядок
    cursor.execute("SELECT sort_order FROM products WHERE id = ?", (product_id,))
    current = cursor.fetchone()
    
    if current:
        new_order = current[0] + 1
        cursor.execute("UPDATE products SET sort_order = ? WHERE id = ?", (new_order, product_id))
        conn.commit()
    
    conn.close()
    
    await admin_reorder_products(callback)
    await callback.answer("✅ Порядок обновлён")    