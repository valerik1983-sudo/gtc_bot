from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from database import is_admin, get_user, update_sponsor, add_event

router = Router()

class SponsorEdit(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_new_sponsor_id = State()


# Общий обработчик для /cancel (работает на любом состоянии)
@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нет активной операции для отмены.")
        return
    
    await state.clear()
    await message.answer("❌ Операция отменена.")


@router.message(lambda m: m.text == "🔄 Сменить спонсора")
async def start_sponsor_change(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён.")
        return
    
    await state.set_state(SponsorEdit.waiting_for_user_id)
    await message.answer(
        "Введите Telegram ID пользователя, которому нужно сменить спонсора.\n\n"
        "Отмена: /cancel"
    )


@router.message(SponsorEdit.waiting_for_user_id)
async def get_user_id(message: Message, state: FSMContext):
    # Проверка на отмену в этом состоянии
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=admin_menu)  # вернуть админ-меню
        return
    
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный числовой Telegram ID.\n\nОтмена: /cancel")
        return
    
    user = get_user(user_id)
    if not user:
        await message.answer("❌ Пользователь с таким ID не найден.\n\nОтмена: /cancel")
        return
    
    await state.update_data(user_id=user_id, user_fio=user["fio"])
    
    current_sponsor = get_user(user["sponsor_id"]) if user["sponsor_id"] else None
    current_text = f"{current_sponsor['fio']} ({current_sponsor['telegram_id']})" if current_sponsor else "Нет спонсора"
    
    await state.set_state(SponsorEdit.waiting_for_new_sponsor_id)
    await message.answer(
        f"👤 Пользователь: {user['fio']} ({user_id})\n"
        f"📌 Текущий спонсор: {current_text}\n\n"
        f"Введите Telegram ID НОВОГО спонсора:\n\nОтмена: /cancel"
    )


@router.message(SponsorEdit.waiting_for_new_sponsor_id)
async def set_new_sponsor(message: Message, state: FSMContext):
    # Проверка на отмену в этом состоянии
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    try:
        new_sponsor_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите корректный числовой Telegram ID.\n\nОтмена: /cancel")
        return
    
    data = await state.get_data()
    user_id = data["user_id"]
    
    # Нельзя назначить спонсором самого себя
    if user_id == new_sponsor_id:
        await message.answer("❌ Нельзя назначить спонсором самого себя.\n\nОтмена: /cancel")
        return
    
    # Проверяем, существует ли новый спонсор
    new_sponsor = get_user(new_sponsor_id)
    if not new_sponsor:
        await message.answer("❌ Новый спонсор не найден.\n\nОтмена: /cancel")
        return
    
    # Обновляем
    update_sponsor(user_id, new_sponsor_id)
    add_event(user_id, "sponsor_change", f"Спонсор изменён на {new_sponsor['fio']} ({new_sponsor_id})")
    
    await message.answer(
        f"✅ Спонсор для {data['user_fio']} изменён!\n\n"
        f"Новый спонсор: {new_sponsor['fio']} ({new_sponsor_id})"
    )
    
    await state.clear()