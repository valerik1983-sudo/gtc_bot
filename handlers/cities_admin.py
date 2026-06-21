from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import is_admin, get_office_cities, add_office_city, remove_office_city

router = Router()


@router.message(F.text == "🏢 Города офисов")
async def manage_cities(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    cities = get_office_cities()
    cities_text = "\n".join([f"• {city}" for city in cities]) if cities else "Список пуст"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
        [InlineKeyboardButton(text="🗑 Удалить город", callback_data="remove_city")]
        
    ])
    
    await message.answer(
        f"🏙️ **Города с офисами**\n\n{cities_text}\n\n"
        f"Всего: {len(cities)}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# Временное хранилище для тех, кто ждёт ввода города
waiting_for_city = {}


@router.callback_query(F.data == "add_city")
async def add_city_start(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    waiting_for_city[callback.from_user.id] = True
    await callback.message.edit_text(
        "🏙️ Введите название города для добавления в список офисов:\n\n"
        "Например: Сочи\n\n"
        "Или нажмите /cancel для отмены"
    )
    await callback.answer()


@router.message(F.text == "/cancel")
async def cancel_add_city(message: Message):
    user_id = message.from_user.id
    if waiting_for_city.get(user_id):
        waiting_for_city.pop(user_id, None)
        await message.answer("❌ Добавление города отменено")
        # Возвращаем в меню городов
        await manage_cities(message)


@router.message()
async def add_city_save(message: Message):
    user_id = message.from_user.id
    
    # Проверяем, ждёт ли пользователь ввод города
    if not waiting_for_city.get(user_id):
        return  # Не ждём - пропускаем сообщение для других обработчиков
    
    if not is_admin(user_id):
        waiting_for_city.pop(user_id, None)
        return
    
    city_name = message.text.strip().title()
    if len(city_name) < 2:
        await message.answer("❌ Название города слишком короткое. Попробуйте ещё раз:")
        return
    
    add_office_city(city_name)
    waiting_for_city.pop(user_id, None)
    
    cities = get_office_cities()
    cities_text = "\n".join([f"• {city}" for city in cities]) if cities else "Список пуст"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
        [InlineKeyboardButton(text="🗑 Удалить город", callback_data="remove_city")]
        
    ])
    
    await message.answer(
        f"✅ Город **{city_name}** добавлен!\n\n"
        f"🏙️ **Города с офисами**\n\n{cities_text}\n\n"
        f"Всего: {len(cities)}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "remove_city")
async def remove_city_start(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    cities = get_office_cities()
    
    if not cities:
        await callback.answer("Список городов пуст")
        return
    
    buttons = []
    for city in cities:
        buttons.append([InlineKeyboardButton(text=f"🗑 {city}", callback_data=f"remove_city_{city}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_cities")])
    
    await callback.message.edit_text(
        "🏙️ **Выберите город для удаления:**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("remove_city_"))
async def remove_city_save(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён")
        return
    
    city_name = callback.data.replace("remove_city_", "")
    remove_office_city(city_name)
    
    cities = get_office_cities()
    cities_text = "\n".join([f"• {city}" for city in cities]) if cities else "Список пуст"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
        [InlineKeyboardButton(text="🗑 Удалить город", callback_data="remove_city")]
       
    ])
    
    await callback.message.edit_text(
        f"✅ Город **{city_name}** удалён!\n\n"
        f"🏙️ **Города с офисами**\n\n{cities_text}\n\n"
        f"Всего: {len(cities)}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_cities")
async def back_to_cities(callback: CallbackQuery):
    cities = get_office_cities()
    cities_text = "\n".join([f"• {city}" for city in cities]) if cities else "Список пуст"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="add_city")],
        [InlineKeyboardButton(text="🗑 Удалить город", callback_data="remove_city")]
       
    ])
    
    await callback.message.edit_text(
        f"🏙️ **Города с офисами**\n\n{cities_text}\n\n"
        f"Всего: {len(cities)}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    from keyboards import admin_menu
    
    await callback.message.delete()
    await callback.message.answer(
        "👑 Панель администратора",
        reply_markup=admin_menu
    )
    await callback.answer()