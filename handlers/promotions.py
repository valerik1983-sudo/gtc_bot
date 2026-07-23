# handlers/promotions.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup

from database import (
    is_admin,
    get_all_promotions,
    get_promotion_by_id,
    add_promotion,
    update_promotion,
    delete_promotion
)

router = Router()

# Состояния для админ-добавления/редактирования
class PromotionEdit(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_photo = State()
    waiting_link = State()
    waiting_expires = State()
    waiting_confirm_delete = State()

# ----- ПОЛЬЗОВАТЕЛЬСКАЯ ЧАСТЬ -----
@router.message(F.text == "🎁 Акции и подарки")
async def show_promotions(message: Message):
    promotions = get_all_promotions(active_only=True)

    if not promotions:
        await message.answer(
            "🎁 **Акции и подарки**\n\n"
            "На данный момент активных акций нет.\n"
            "Следите за обновлениями!",
            parse_mode="Markdown"
        )
        return

    # Отправляем каждую акцию отдельно (с фото, если есть)
    for promo in promotions:
        text = f"🎁 **{promo['title']}**\n\n{promo['description']}"
        if promo.get('link'):
            text += f"\n\n🔗 [Подробнее]({promo['link']})"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Перейти по ссылке", url=promo['link'])]
        ]) if promo.get('link') else None

        if promo.get('photo_id'):
            await message.answer_photo(
                photo=promo['photo_id'],
                caption=text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                text,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )


# ----- АДМИНСКАЯ ЧАСТЬ -----
@router.message(F.text == "🎁 Управление акциями")
async def admin_promotions_menu(message: Message):
    if not is_admin(message.from_user.id):
        return

    promotions = get_all_promotions()

    if not promotions:
        await message.answer(
            "🎁 Управление акциями\n\n"
            "Акций пока нет. Нажмите «➕ Добавить акцию», чтобы создать первую.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить акцию", callback_data="admin_add_promo")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_admin")]
            ])
        )
        return

    # Формируем список акций с кнопками
    keyboard = []
    for promo in promotions:
        status_icon = "✅" if promo['is_active'] else "❌"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_icon} {promo['title'][:30]}",
                callback_data=f"admin_edit_promo_{promo['id']}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="➕ Добавить акцию", callback_data="admin_add_promo")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_admin")])

    await message.answer(
        "🎁 **Управление акциями**\n\n"
        "Выберите акцию для редактирования или добавьте новую.\n"
        "✅ — активна, ❌ — неактивна.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "admin_add_promo")
async def admin_add_promo_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(PromotionEdit.waiting_title)
    await callback.message.answer("✏️ Введите заголовок акции:")
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_title))
async def admin_add_promo_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(PromotionEdit.waiting_description)
    await message.answer("📄 Введите описание акции (можно с форматированием Markdown):")


@router.message(StateFilter(PromotionEdit.waiting_description))
async def admin_add_promo_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(PromotionEdit.waiting_photo)
    await message.answer(
        "🖼 Отправьте фото для акции (или отправьте 'пропустить'):\n\n"
        "Фото будет отображаться в карточке акции."
    )


@router.message(StateFilter(PromotionEdit.waiting_photo))
async def admin_add_promo_photo(message: Message, state: FSMContext):
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text.lower() == "пропустить":
        photo_id = None
    else:
        await message.answer("❌ Отправьте фото или напишите 'пропустить'")
        return

    await state.update_data(photo_id=photo_id)
    await state.set_state(PromotionEdit.waiting_link)
    await message.answer(
        "🔗 Введите ссылку для перехода (например, https://... ) или отправьте 'пропустить':"
    )


@router.message(StateFilter(PromotionEdit.waiting_link))
async def admin_add_promo_link(message: Message, state: FSMContext):
    link = None
    if message.text and message.text.lower() != "пропустить":
        if not message.text.startswith(('http://', 'https://')):
            await message.answer("❌ Ссылка должна начинаться с http:// или https://. Попробуйте снова:")
            return
        link = message.text
    await state.update_data(link=link)
    await state.set_state(PromotionEdit.waiting_expires)
    await message.answer(
        "📅 Введите дату истечения акции (необязательно) в формате ДД.ММ.ГГГГ\n"
        "или отправьте 'пропустить', если акция бессрочная:"
    )


@router.message(StateFilter(PromotionEdit.waiting_expires))
async def admin_add_promo_expires(message: Message, state: FSMContext):
    expires_at = None
    if message.text and message.text.lower() != "пропустить":
        try:
            from datetime import datetime
            expires_at = datetime.strptime(message.text, "%d.%m.%Y").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ или 'пропустить':")
            return

    data = await state.get_data()
    promo_id = add_promotion(
        title=data['title'],
        description=data['description'],
        photo_id=data.get('photo_id'),
        link=data.get('link'),
        expires_at=expires_at
    )

    await message.answer(f"✅ Акция **{data['title']}** успешно добавлена! (ID: {promo_id})")
    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data.startswith("admin_edit_promo_"))
async def admin_edit_promo(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    promo_id = int(callback.data.split("_")[3])
    promo = get_promotion_by_id(promo_id)
    if not promo:
        await callback.message.answer("❌ Акция не найдена")
        await callback.answer()
        return

    await state.update_data(edit_promo_id=promo_id)

    status_text = "🟢 Активна" if promo['is_active'] else "🔴 Неактивна"
    text = (
        f"🎁 **{promo['title']}**\n\n"
        f"{promo['description']}\n\n"
        f"📅 Создана: {promo['created_at']}\n"
        f"⏳ Истекает: {promo['expires_at'] or 'бессрочно'}\n"
        f"📊 Статус: {status_text}\n"
        f"🔗 Ссылка: {promo['link'] or 'нет'}\n"
        f"🖼 Фото: {'есть' if promo['photo_id'] else 'нет'}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить заголовок", callback_data="promo_edit_title")],
        [InlineKeyboardButton(text="✏️ Изменить описание", callback_data="promo_edit_desc")],
        [InlineKeyboardButton(text="🖼 Изменить фото", callback_data="promo_edit_photo")],
        [InlineKeyboardButton(text="🔗 Изменить ссылку", callback_data="promo_edit_link")],
        [InlineKeyboardButton(text="📅 Изменить срок", callback_data="promo_edit_expires")],
        [InlineKeyboardButton(text="🔄 Переключить статус", callback_data=f"promo_toggle_{promo_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"promo_delete_{promo_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_to_promos")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "promo_edit_title")
async def promo_edit_title(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_title)
    await callback.message.answer("✏️ Введите новый заголовок:")
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_title))
async def promo_save_title(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return
    update_promotion(promo_id, title=message.text)
    await message.answer("✅ Заголовок обновлён!")
    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data == "promo_edit_desc")
async def promo_edit_desc(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_description)
    await callback.message.answer("✏️ Введите новое описание:")
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_description))
async def promo_save_desc(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return
    update_promotion(promo_id, description=message.text)
    await message.answer("✅ Описание обновлено!")
    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data == "promo_edit_photo")
async def promo_edit_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_photo)
    await callback.message.answer("🖼 Отправьте новое фото (или 'удалить' чтобы убрать):")
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_photo))
async def promo_save_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return

    if message.photo:
        photo_id = message.photo[-1].file_id
        update_promotion(promo_id, photo_id=photo_id)
        await message.answer("✅ Фото обновлено!")
    elif message.text and message.text.lower() == "удалить":
        update_promotion(promo_id, photo_id=None)
        await message.answer("✅ Фото удалено!")
    else:
        await message.answer("❌ Отправьте фото или напишите 'удалить'")
        return

    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data == "promo_edit_link")
async def promo_edit_link(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_link)
    await callback.message.answer("🔗 Введите новую ссылку (или 'удалить' чтобы убрать):")
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_link))
async def promo_save_link(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return

    if message.text.lower() == "удалить":
        update_promotion(promo_id, link=None)
        await message.answer("✅ Ссылка удалена!")
    else:
        if not message.text.startswith(('http://', 'https://')):
            await message.answer("❌ Ссылка должна начинаться с http:// или https://. Попробуйте снова:")
            return
        update_promotion(promo_id, link=message.text)
        await message.answer("✅ Ссылка обновлена!")

    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data == "promo_edit_expires")
async def promo_edit_expires(callback: CallbackQuery, state: FSMContext):
    await state.set_state(PromotionEdit.waiting_expires)
    await callback.message.answer("📅 Введите новую дату истечения (ДД.ММ.ГГГГ) или 'удалить' чтобы сделать бессрочной:")
    await callback.answer()


@router.message(StateFilter(PromotionEdit.waiting_expires))
async def promo_save_expires(message: Message, state: FSMContext):
    data = await state.get_data()
    promo_id = data.get('edit_promo_id')
    if not promo_id:
        await message.answer("❌ Ошибка: акция не найдена")
        await state.clear()
        return

    if message.text.lower() == "удалить":
        update_promotion(promo_id, expires_at=None)
        await message.answer("✅ Срок истечения убран (бессрочная акция)")
    else:
        try:
            from datetime import datetime
            expires_at = datetime.strptime(message.text, "%d.%m.%Y").strftime("%Y-%m-%d %H:%M:%S")
            update_promotion(promo_id, expires_at=expires_at)
            await message.answer(f"✅ Дата истечения установлена на {message.text}")
        except ValueError:
            await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ или 'удалить'")
            return

    await state.clear()
    await admin_promotions_menu(message)


@router.callback_query(F.data.startswith("promo_toggle_"))
async def promo_toggle(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    promo_id = int(callback.data.split("_")[2])
    promo = get_promotion_by_id(promo_id)
    if not promo:
        await callback.message.answer("❌ Акция не найдена")
        await callback.answer()
        return
    new_status = 0 if promo['is_active'] else 1
    update_promotion(promo_id, is_active=new_status)
    status_text = "активирована" if new_status else "деактивирована"
    await callback.message.answer(f"✅ Акция {status_text}!")
    await callback.answer()
    await admin_promotions_menu(callback.message)


@router.callback_query(F.data.startswith("promo_delete_"))
async def promo_delete(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    promo_id = int(callback.data.split("_")[2])
    promo = get_promotion_by_id(promo_id)
    if not promo:
        await callback.message.answer("❌ Акция не найдена")
        await callback.answer()
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"promo_confirm_delete_{promo_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back_to_promos")]
    ])
    await callback.message.answer(
        f"⚠️ Вы уверены, что хотите удалить акцию **{promo['title']}**?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("promo_confirm_delete_"))
async def promo_confirm_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    promo_id = int(callback.data.split("_")[3])
    delete_promotion(promo_id)
    await callback.message.answer("✅ Акция удалена!")
    await callback.answer()
    await admin_promotions_menu(callback.message)


@router.callback_query(F.data == "admin_back_to_promos")
async def admin_back_to_promos(callback: CallbackQuery):
    await admin_promotions_menu(callback.message)
    await callback.answer()


@router.callback_query(F.data == "admin_back_to_admin")
async def admin_back_to_admin(callback: CallbackQuery):
    from keyboards import admin_menu
    await callback.message.delete()
    await callback.message.answer(
        "👑 Панель администратора",
        reply_markup=admin_menu
    )
    await callback.answer()