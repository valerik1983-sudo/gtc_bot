from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database import (
    is_admin, get_all_products_from_db, get_product_by_name, get_product_by_id,
    update_product_in_db, delete_product_from_db, sync_products_from_file
)

router = Router()

class EditProduct(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_photo = State()
    waiting_for_story_key = State()
    waiting_for_program_key = State()
    waiting_for_video = State()


'''@router.message(F.text == "🛍 Управление товарами")
async def manage_products(message: Message):
    if not is_admin(message.from_user.id):
        return
    
    from database import get_all_products_from_db
    products = get_all_products_from_db()
    await message.answer(f"📊 В БД найдено товаров: {len(products)}")

    keyboard = [
        [InlineKeyboardButton(text="📥 Синхронизировать из файла", callback_data="sync_products")],
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="add_product")],
        [InlineKeyboardButton(text="📋 Список товаров", callback_data="list_products")]
        
    ]
    
    await message.answer(
        "🛍 **Управление товарами**\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
'''

@router.callback_query(F.data == "sync_products")
async def sync_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    
    sync_products_from_file()
    await callback.message.answer("✅ Товары синхронизированы из файла в БД!")
    await callback.answer()


@router.callback_query(F.data == "list_products")
async def list_products(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    
    products = get_all_products_from_db()
    
    if not products:
        await callback.message.answer("📭 Товаров пока нет.")
        return
    
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"✏️ {product['name']}",
                callback_data=f"edit_product_{product['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_product_menu")])
    
    await callback.message.edit_text(
        "📋 **Список товаров**\n\nВыберите товар для редактирования:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("edit_product_"))
async def edit_product_form(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])
    await state.update_data(product_id=product_id)
    
    product = get_product_by_id(product_id)
    
    keyboard = [
        [InlineKeyboardButton(text="📝 Изменить название", callback_data="edit_name")],
        [InlineKeyboardButton(text="📄 Изменить описание", callback_data="edit_desc")],
        [InlineKeyboardButton(text="💰 Изменить цену", callback_data="edit_price")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="edit_photo")],
        [InlineKeyboardButton(text="🎬 Добавить видео", callback_data="admin_edit_video")],
        [InlineKeyboardButton(text="🔑 Изменить ключ истории", callback_data="edit_story")],
        [InlineKeyboardButton(text="🎁 Изменить ключ программы", callback_data="edit_program")],
        [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="delete_product")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="list_products")]
    ]
    
    text = f"**{product['name']}**\n\n"
    text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
    text += f"💰 {product['price'] or 'не указана'}\n"
    text += f"📖 История: {product['story_key'] or 'нет'}\n"
    text += f"🎁 Программа: {product['program_key'] or 'нет'}"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_product_menu")
async def back_to_product_menu(callback: CallbackQuery):
    await manage_products(callback.message)
    await callback.answer()

@router.callback_query(F.data == "edit_photo")
async def edit_photo_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProduct.waiting_for_photo)
    await callback.message.answer("📷 Отправьте новое фото для этого товара:")
    await callback.answer()


@router.message(EditProduct.waiting_for_photo, F.photo)
async def edit_photo_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("product_id")
    
    # Получаем file_id фото
    photo_file_id = message.photo[-1].file_id
    
    # Сохраняем в БД (путь будет храниться как file_id)
    from database import update_product_in_db
    update_product_in_db(product_id, photo_path=photo_file_id)
    
    await message.answer("✅ Фото товара обновлено!")
    await state.clear()
    
    # Возвращаемся к редактированию
    # Хорошо (стало)
    from types import SimpleNamespace
    fake_callback = SimpleNamespace(
         message=message,
         data=f"edit_product_{product_id}"
     )
    await edit_product_form(fake_callback, state)

@router.callback_query(F.data == "edit_name")
async def edit_name_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProduct.waiting_for_name)
    await callback.message.answer("✏️ Введите новое название товара:")
    await callback.answer()


@router.message(EditProduct.waiting_for_name)
async def edit_name_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("product_id")
    
    from database import update_product_in_db
    update_product_in_db(product_id, name=message.text)
    
    await message.answer(f"✅ Название изменено на: {message.text}")
    await state.clear()


@router.callback_query(F.data == "edit_desc")
async def edit_desc_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProduct.waiting_for_description)
    await callback.message.answer("✏️ Введите новое описание товара:")
    await callback.answer()


@router.message(EditProduct.waiting_for_description)
async def edit_desc_save(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data.get("product_id")
    
    from database import update_product_in_db
    update_product_in_db(product_id, description=message.text)
    
    await message.answer("✅ Описание товара обновлено!")
    await state.clear()    

@router.callback_query(F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery):
    from keyboards import admin_menu
    
    await callback.message.delete()
    await callback.message.answer(
        "👑 Панель администратора",
        reply_markup=admin_menu
    )
    await callback.answer()
    
@router.callback_query(F.data == "admin_edit_video")
async def admin_edit_video_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EditProduct.waiting_for_video)
    await callback.message.answer(
        "🎬 Введите ссылку на видео (YouTube, Vimeo или любой другой хостинг):\n\n"
        "Пример: https://www.youtube.com/watch?v=XXXXX"
    )
    await callback.answer()


@router.message(EditProduct.waiting_for_video)
async def admin_edit_video_save(message: Message, state: FSMContext):
    video_url = message.text.strip()
    if not video_url.startswith(('http://', 'https://')):
        await message.answer("❌ Введите корректную ссылку (начинается с http:// или https://):")
        return

    data = await state.get_data()
    product_id = data.get("editing_product_id")
    if not product_id:
        await message.answer("❌ Ошибка: товар не найден")
        await state.clear()
        return

    from database import update_product_in_db, get_product_by_id, get_product_price
    update_product_in_db(product_id, video_url=video_url)

    await message.answer("✅ Видео сохранено!")

    # Возвращаемся к форме редактирования
    product = get_product_by_id(product_id)
    if product:
        price = get_product_price(product['name'])
        price_display = f"{price} руб." if price and price > 0 else "не указана"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Изменить название", callback_data="admin_edit_name")],
            [InlineKeyboardButton(text="📄 Изменить описание", callback_data="admin_edit_desc")],
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data="admin_edit_price")],
            [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="admin_edit_photo")],
            [InlineKeyboardButton(text="🎬 Добавить видео", callback_data="admin_edit_video")],
            [InlineKeyboardButton(text="🗑 Удалить товар", callback_data="admin_delete_product")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_list_products")]
        ])

        text = f"**{product['name']}**\n\n"
        text += f"📄 {product['description'][:100]}...\n" if product['description'] else ""
        text += f"💰 {price_display}\n"
        text += f"🎬 Видео: {'есть' if product.get('video_url') else 'нет'}\n"

        await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer("❌ Товар не найден")

    await state.clear()    
  